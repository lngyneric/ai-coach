"""Unit tests for AAD strong-login default-role assignment (P0 step12).

Covers the two core behaviors introduced by P0-REVIEW-PERMISSION-AAD A2/D14:

- ``ensure_user_for_identifier`` writes a default ``role-learner`` row to
  ``user_role_assignments`` when it creates a user (and only then).
- ``assign_default_role`` is idempotent (no duplicate rows, no overwrite).
- ``init_first_course`` is gated by ``ADMIN_LOGIN_GRANT_CREATOR_WITH_DEMO``
  (default False) so visitor paths no longer implicitly grant creator.
"""

from __future__ import annotations

import uuid

from flask import Flask
import pytest

import flaskr.dao as dao
from flaskr.dao import db
from flaskr.service.user.consts import USER_STATE_REGISTERED
from flaskr.service.user.repository import (
    assign_default_role,
    ensure_user_for_identifier,
)
from flaskr.service.user.phone_flow import init_first_course
from sqlalchemy import text

ROLE_TABLE_DDL = [
    text(
        "CREATE TABLE coach_roles ("
        " role_bid VARCHAR(32) PRIMARY KEY,"
        " name VARCHAR(50) NOT NULL,"
        " label VARCHAR(100) NOT NULL DEFAULT '',"
        " permissions JSON,"
        " is_active TINYINT(1) DEFAULT 1)"
    ),
    text(
        "CREATE TABLE user_role_assignments ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " user_bid VARCHAR(32) NOT NULL,"
        " role_bid VARCHAR(32) NOT NULL,"
        " UNIQUE (user_bid, role_bid))"
    ),
]


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_BINDS={
            "ai_shifu_saas": "sqlite:///:memory:",
            "ai_shifu_admin": "sqlite:///:memory:",
        },
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    dao.db.init_app(app)

    with app.app_context():
        dao.db.create_all()
        for stmt in ROLE_TABLE_DDL:
            db.session.execute(stmt)
        db.session.execute(
            text(
                "INSERT INTO coach_roles (role_bid, name, label, permissions, is_active) "
                "VALUES ('role-learner', 'learner', '学员', "
                "'[\"learner:read\",\"learner:write\",\"view_own_report\"]', 1)"
            )
        )
        db.session.commit()
        yield app
        db.session.remove()
        dao.db.drop_all()


def _role_rows(user_bid: str) -> list[tuple]:
    return db.session.execute(
        text(
            "SELECT role_bid FROM user_role_assignments "
            "WHERE user_bid = :ub"
        ),
        {"ub": user_bid},
    ).fetchall()


class TestEnsureUserDefaultRole:
    def test_new_user_gets_role_learner(self, app):
        with app.app_context():
            aggregate, created = ensure_user_for_identifier(
                app,
                provider="employee",
                identifier=f"sch{uuid.uuid4().int % 100000:05d}",
                defaults={
                    "nickname": "new-employee",
                    "state": USER_STATE_REGISTERED,
                },
            )
            assert created is True
            rows = _role_rows(aggregate.user_bid)
            assert [r[0] for r in rows] == ["role-learner"]

    def test_existing_user_does_not_get_duplicate_role(self, app):
        with app.app_context():
            identifier = f"sch{uuid.uuid4().int % 100000:05d}"
            aggregate, created = ensure_user_for_identifier(
                app,
                provider="employee",
                identifier=identifier,
                defaults={"state": USER_STATE_REGISTERED},
            )
            assert created is True
            # Second login reuses the same user (provider+identifier unique) —
            # no new role row, no duplicate.
            aggregate2, created2 = ensure_user_for_identifier(
                app,
                provider="employee",
                identifier=identifier,
                defaults={"state": USER_STATE_REGISTERED},
            )
            assert created2 is False
            assert aggregate2.user_bid == aggregate.user_bid
            assert len(_role_rows(aggregate.user_bid)) == 1

    def test_repeat_login_does_not_recreate_user(self, app):
        with app.app_context():
            identifier = f"sch{uuid.uuid4().int % 100000:05d}"
            first, created1 = ensure_user_for_identifier(
                app,
                provider="employee",
                identifier=identifier,
                defaults={"state": USER_STATE_REGISTERED},
            )
            second, created2 = ensure_user_for_identifier(
                app,
                provider="employee",
                identifier=identifier,
                defaults={"state": USER_STATE_REGISTERED},
            )
            assert created1 is True
            assert created2 is False
            assert first.user_bid == second.user_bid
            assert len(_role_rows(first.user_bid)) == 1


class TestAssignDefaultRole:
    def test_idempotent(self, app):
        with app.app_context():
            user_bid = uuid.uuid4().hex[:32]
            assert assign_default_role(app, user_bid, "role-learner") is True
            assert assign_default_role(app, user_bid, "role-learner") is False
            assert len(_role_rows(user_bid)) == 1

    def test_blank_input_is_safe(self, app):
        with app.app_context():
            assert assign_default_role(app, "") is False
            assert assign_default_role(app, "usr-x", "") is False


class TestInitFirstCourseGate:
    def test_flag_off_returns_false_without_roles(self, app, monkeypatch):
        with app.app_context():
            from flaskr.service.user.models import UserInfo as UserEntity

            app.config["ADMIN_LOGIN_GRANT_CREATOR_WITH_DEMO"] = False
            aggregate, _ = ensure_user_for_identifier(
                app,
                provider="email",
                identifier=f"{uuid.uuid4().hex[:8]}@sysmex.internal",
                defaults={"state": USER_STATE_REGISTERED},
            )
            entity = UserEntity.query.filter_by(
                user_bid=aggregate.user_bid
            ).first()
            assert entity is not None
            # Bootstrap must not run / not grant creator when flag off.
            assert init_first_course(app, aggregate.user_bid) is False
            db.session.refresh(entity)
            assert entity.is_creator == 0
            assert entity.is_operator == 0

    def test_flag_on_runs_bootstrap_for_first_user(self, app):
        with app.app_context():
            from flaskr.service.user.models import UserInfo as UserEntity

            app.config["ADMIN_LOGIN_GRANT_CREATOR_WITH_DEMO"] = True
            aggregate, _ = ensure_user_for_identifier(
                app,
                provider="email",
                identifier=f"{uuid.uuid4().hex[:8]}@sysmex.internal",
                defaults={"state": USER_STATE_REGISTERED},
            )
            granted = init_first_course(app, aggregate.user_bid)
            entity = UserEntity.query.filter_by(
                user_bid=aggregate.user_bid
            ).first()
            assert granted is True
            assert entity.is_creator == 1
            assert entity.is_operator == 1
