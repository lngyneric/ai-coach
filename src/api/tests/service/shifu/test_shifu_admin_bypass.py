"""Regression test for B2 — admin / role-admin course-content bypass.

docs/ROLE-ACCESS-TEST-REPORT.md B2 / P0-PERMISSION-GAP-AUDIT D-G1:

Before this fix ``shifu_permission_verification`` only admitted the course
creator or an ``ai_course_auth`` record, so admin had no bypass and could not
open 32 of 50 courses. After the fix a ``role-admin`` (or, transitionally,
a legacy ``is_operator=1`` user with no roles) gets full view/edit/publish
on every course without a per-course auth row.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import text

from flaskr.dao import db
from flaskr.service.shifu.funcs import shifu_permission_verification
from flaskr.service.shifu.models import DraftShifu
from flaskr.service.user.models import UserInfo as UserEntity


def _seed_owned_course(shifu_bid: str, owner_bid: str) -> None:
    db.session.add(
        DraftShifu(
            shifu_bid=shifu_bid,
            title=f"Course {shifu_bid[:6]}",
            description="desc",
            avatar_res_bid="",
            keywords="",
            llm="gpt-test",
            llm_temperature=Decimal("0"),
            llm_system_prompt="",
            price=Decimal("0"),
            created_user_bid=owner_bid,
            updated_user_bid=owner_bid,
        )
    )
    db.session.commit()


def _ensure_role_tables() -> None:
    db.session.execute(
        text(
            "CREATE TABLE IF NOT EXISTS coach_roles ("
            " role_bid VARCHAR(32) PRIMARY KEY,"
            " name VARCHAR(50) NOT NULL UNIQUE,"
            " label VARCHAR(100) DEFAULT '',"
            " permissions TEXT,"
            " is_active INTEGER DEFAULT 1)"
        )
    )
    db.session.execute(
        text(
            "CREATE TABLE IF NOT EXISTS user_role_assignments ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " user_bid VARCHAR(32) NOT NULL,"
            " role_bid VARCHAR(32) NOT NULL,"
            " UNIQUE (user_bid, role_bid))"
        )
    )
    db.session.execute(
        text(
            "INSERT OR REPLACE INTO coach_roles "
            "(role_bid, name, permissions, is_active) VALUES "
            "('role-admin', 'admin', '[\"all\"]', 1),"
            "('role-learner', 'learner',"
            " '[\"learner:read\",\"learner:write\",\"view_own_report\"]', 1)"
        )
    )
    db.session.commit()


def _assign_role(user_bid: str, role_bid: str) -> None:
    db.session.execute(
        text(
            "INSERT OR REPLACE INTO user_role_assignments "
            "(user_bid, role_bid) VALUES (:u, :r)"
        ),
        {"u": user_bid, "r": role_bid},
    )
    db.session.commit()


def _create_operator_user(user_bid: str) -> None:
    db.session.add(
        UserEntity(
            user_bid=user_bid,
            user_identify=f"{user_bid}@example.com",
            nickname="Legacy Operator",
            language="zh-CN",
            state=1,
            is_creator=0,
            is_operator=1,
            department="管理部",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    )
    db.session.commit()


def test_admin_role_bypasses_course_auth(app):
    """B2: a role-admin can view/edit/publish any course without auth rows."""
    shifu_bid = uuid.uuid4().hex[:32]
    owner_bid = uuid.uuid4().hex[:32]
    admin_bid = uuid.uuid4().hex[:32]
    with app.app_context():
        _seed_owned_course(shifu_bid, owner_bid)
        _ensure_role_tables()
        _assign_role(admin_bid, "role-admin")
        for perm in ("view", "edit", "publish"):
            assert (
                shifu_permission_verification(app, admin_bid, shifu_bid, perm)
                is True
            )


def test_legacy_operator_fallback_bypasses_course_auth(app):
    """B2 (transitional): is_operator=1 with no roles still gets full access."""
    shifu_bid = uuid.uuid4().hex[:32]
    owner_bid = uuid.uuid4().hex[:32]
    operator_bid = uuid.uuid4().hex[:32]
    with app.app_context():
        _seed_owned_course(shifu_bid, owner_bid)
        _create_operator_user(operator_bid)
        assert (
            shifu_permission_verification(app, operator_bid, shifu_bid, "view")
            is True
        )


def test_stranger_still_denied(app):
    """B2 regression: a plain user with no auth / no admin role stays denied."""
    shifu_bid = uuid.uuid4().hex[:32]
    owner_bid = uuid.uuid4().hex[:32]
    stranger_bid = uuid.uuid4().hex[:32]
    with app.app_context():
        _seed_owned_course(shifu_bid, owner_bid)
        _ensure_role_tables()
        _assign_role(stranger_bid, "role-learner")
        assert (
            shifu_permission_verification(app, stranger_bid, shifu_bid, "view")
            is False
        )


def test_operator_with_role_not_shortcircuited(app):
    """B2 × B6: is_operator=1 is ignored when the user holds a non-admin role."""
    shifu_bid = uuid.uuid4().hex[:32]
    owner_bid = uuid.uuid4().hex[:32]
    mixed_bid = uuid.uuid4().hex[:32]
    with app.app_context():
        _seed_owned_course(shifu_bid, owner_bid)
        _ensure_role_tables()
        _create_operator_user(mixed_bid)  # is_operator=1
        _assign_role(mixed_bid, "role-learner")  # but also holds a role
        # B6 semantics: roles are the source of truth, is_operator must not
        # short-circuit a role-holder into a course-content admin.
        assert (
            shifu_permission_verification(app, mixed_bid, shifu_bid, "view")
            is False
        )
