"""Portal course alignment tests — 闭环 1 (publish hook) + 闭环 2 (batch enroll).

Coverage (PORTAL-COURSE-ALIGNMENT.md / PORTAL-ALIGNMENT-FIX.md):

闭环 1 · 发布即入池
- ``sync_course_position_tags`` writes ``course_position_tags`` rows from
  ``role:*`` keywords; multi-role; idempotent upsert; combined ``tag`` column.
- No role tag / empty / malformed keywords → no-op, never raises.
- Publish route wiring: ``POST /shifus/<bid>/publish`` invokes the hook.

闭环 2 · 标签驱动批量分配
- ``POST /admin/enroll`` with ``role_tags`` matches learners by
  department / position_name, enrolls each, skips duplicates.
- No matching learners → ``enrolled 0`` without error; non-manager → 403.
- Single (``user_bid``) enroll mode is unchanged (regression).
"""

from __future__ import annotations

import json
from datetime import datetime
from unittest import mock

import sqlalchemy
from sqlalchemy import text
from sqlalchemy.ext.compiler import compiles

from flaskr.dao import db
from flaskr.service.learning_portal.models import (
    CourseEnrollment,
    CoursePositionTag,
    LearnerProfile,
)
from flaskr.service.shifu.models import PublishedShifu
from flaskr.service.shifu.tagging import (
    _parse_keywords,
    sync_course_position_tags,
)
from flaskr.service.user.models import UserInfo as UserEntity
from flaskr.service.user.utils import generate_token


# SQLite test quirk: a generic BigInteger PK renders as ``BIGINT`` which is not
# a rowid alias, so autoincrement silently fails (NOT NULL constraint). The
# shared conftest only compiles the MySQL-dialect BIGINT; register the generic
# BigInteger here so CoursePositionTag / CourseEnrollment inserts work under
# SQLite (production runs MySQL and is unaffected). Registered at import time =
# during collection, i.e. before the session-scoped ``app`` fixture creates
# tables.
@compiles(sqlalchemy.BigInteger, "sqlite")
def _compile_generic_bigint_sqlite(_type, _compiler, **_kw):
    return "INTEGER"


_ROLE_INSERT_SQL = """
INSERT OR REPLACE INTO coach_roles (role_bid, name, permissions, is_active) VALUES
('role-admin',  'admin',  '["all"]', 1),
('role-hr',     'hr',     '["manage_users","view_all_students"]', 1),
('role-learner','learner','["learner:read","view_own_report"]', 1)
"""


def _ensure_coach_tables():
    """coach_roles / user_role_assignments aren't ORM models — create in tests."""
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
    db.session.execute(text(_ROLE_INSERT_SQL))
    db.session.commit()


# ── helpers ────────────────────────────────────────────────────────────


def _create_user(
    user_bid: str,
    *,
    is_operator: bool = False,
    department: str = "",
    nickname: str = "User",
) -> UserEntity:
    user = UserEntity(
        user_bid=user_bid,
        user_identify=f"{user_bid}@example.com",
        nickname=nickname,
        language="zh-CN",
        state=1,
        is_creator=0,
        is_operator=1 if is_operator else 0,
        department=department,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.session.add(user)
    return user


def _seed_published(shifu_bid: str, keywords: str, title: str = "Tagged Course"):
    db.session.add(
        PublishedShifu(shifu_bid=shifu_bid, title=title, keywords=keywords or "")
    )
    db.session.commit()


def _reset_tags(shifu_bid: str):
    CoursePositionTag.query.filter_by(shifu_bid=shifu_bid).delete()
    db.session.commit()


def _seed_learner_profiles():
    LearnerProfile.query.delete()
    db.session.commit()
    learners = [
        ("usr-pa-sales1", "销售本部", "销售经理"),
        ("usr-pa-sales2", "销售本部", "客户经理"),
        ("usr-pa-prod1", "生产一部", "产线操作员"),
        ("usr-pa-hr1", "人事部", "招聘专员"),
    ]
    for i, (lb, dept, pos) in enumerate(learners, start=1):
        db.session.add(
            LearnerProfile(
                learner_bid=lb,
                user_bid=lb,
                employee_no=f"PA{i:03d}",
                department=dept,
                position_name=pos,
                status="active",
                created_at=datetime(2026, 1, i),
                updated_at=datetime(2026, 1, i),
            )
        )
    db.session.commit()


def _clear_enrollments(shifu_bid: str):
    CourseEnrollment.query.filter_by(shifu_bid=shifu_bid).delete()
    db.session.commit()


# ── 闭环 1 · publish hook ──────────────────────────────────────────────


def test_sync_writes_role_tags_and_combined_tag(app):
    shifu_bid = "crs-tag-1"
    with app.app_context():
        _reset_tags(shifu_bid)
        _seed_published(
            shifu_bid,
            "role:sales,lesson_type:practice,task:new-sales,role:production",
        )
        assert sync_course_position_tags(app, shifu_bid) is True
        rows = CoursePositionTag.query.filter_by(shifu_bid=shifu_bid).all()
        assert len(rows) == 2
        by_pos = {r.position: r for r in rows}
        sales = by_pos["sales"]
        assert sales.weight == 10
        assert sales.position_name == "销售"
        assert sales.is_active == 1
        assert sales.tag == "lesson_type:practice|task:new-sales"
        assert by_pos["production"].weight == 10


def test_sync_upsert_is_idempotent(app):
    shifu_bid = "crs-tag-2"
    with app.app_context():
        _reset_tags(shifu_bid)
        _seed_published(shifu_bid, "role:sales")
        assert sync_course_position_tags(app, shifu_bid) is True
        assert sync_course_position_tags(app, shifu_bid) is True
        rows = CoursePositionTag.query.filter_by(shifu_bid=shifu_bid).all()
        assert len(rows) == 1
        assert rows[0].weight == 10
        assert rows[0].is_active == 1


def test_sync_no_role_tag_is_noop(app):
    shifu_bid = "crs-tag-3"
    with app.app_context():
        _reset_tags(shifu_bid)
        _seed_published(shifu_bid, "lesson_type:onboarding,task:new-sales")
        assert sync_course_position_tags(app, shifu_bid) is False
        assert CoursePositionTag.query.filter_by(shifu_bid=shifu_bid).count() == 0


def test_sync_empty_keywords_is_noop(app):
    for i, kw in enumerate(["", "   "]):
        shifu_bid = f"crs-tag-empty-{i}"
        with app.app_context():
            _reset_tags(shifu_bid)
            _seed_published(shifu_bid, kw)
            assert sync_course_position_tags(app, shifu_bid) is False


def test_sync_malformed_json_keywords_is_noop(app):
    """Non-JSON content must not raise (keywords is a legacy String column)."""
    shifu_bid = "crs-tag-badjson"
    with app.app_context():
        _reset_tags(shifu_bid)
        _seed_published(shifu_bid, '[role:sales, not valid json')
        assert sync_course_position_tags(app, shifu_bid) is False


def test_sync_json_array_keywords(app):
    shifu_bid = "crs-tag-json"
    with app.app_context():
        _reset_tags(shifu_bid)
        _seed_published(shifu_bid, json.dumps(["role:hr", "lesson_type:compliance"]))
        assert sync_course_position_tags(app, shifu_bid) is True
        row = CoursePositionTag.query.filter_by(shifu_bid=shifu_bid).first()
        assert row.position == "hr"
        assert row.tag == "lesson_type:compliance"


def test_parse_keywords_none_or_malformed(app):
    with app.app_context():
        assert _parse_keywords(None) == []
        assert _parse_keywords("") == []
        assert _parse_keywords([" role:sales ", ""]) == ["role:sales"]
        assert _parse_keywords("role:sales,role:production") == [
            "role:sales",
            "role:production",
        ]


def test_publish_route_invokes_sync_hook(app, test_client):
    """Wiring: publish endpoint must call sync_course_position_tags after publish."""
    from flaskr.service.shifu import route as shifu_route

    shifu_bid = "crs-route-1"
    operator_bid = "usr-pub-route-1"
    with app.app_context():
        _create_user(user_bid=operator_bid, is_operator=True, nickname="PubOp")
        db.session.commit()
        token = generate_token(app, operator_bid)

    with (
        mock.patch.object(shifu_route, "publish_shifu_draft", return_value=f"/c/{shifu_bid}"),
        mock.patch.object(
            shifu_route, "sync_course_position_tags", return_value=True
        ) as mocked_sync,
    ):
        resp = test_client.post(
            f"/api/shifu/shifus/{shifu_bid}/publish", headers={"Token": token}
        )
    assert resp.status_code == 200
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    mocked_sync.assert_called_once_with(mock.ANY, shifu_bid)


def test_publish_route_hook_failure_does_not_block(app, test_client):
    """A sync failure must not turn the publish response into an error."""
    from flaskr.service.shifu import route as shifu_route

    shifu_bid = "crs-route-2"
    operator_bid = "usr-pub-route-2"
    with app.app_context():
        _create_user(user_bid=operator_bid, is_operator=True, nickname="PubOp2")
        db.session.commit()
        token = generate_token(app, operator_bid)

    with (
        mock.patch.object(shifu_route, "publish_shifu_draft", return_value="/c/x"),
        mock.patch.object(
            shifu_route, "sync_course_position_tags", side_effect=RuntimeError("boom")
        ),
    ):
        resp = test_client.post(
            f"/api/shifu/shifus/{shifu_bid}/publish", headers={"Token": token}
        )
    assert resp.status_code == 200
    assert resp.get_json(force=True)["code"] == 0


# ── 闭环 2 · batch enroll (role_tags) ──────────────────────────────────


def test_batch_enroll_by_role_tags(app, test_client):
    admin_bid = "usr-pa-admin1"
    shifu_bid = "crs-pa-batch1"
    with app.app_context():
        _ensure_coach_tables()
        _create_user(user_bid=admin_bid, is_operator=True, nickname="BatchAdmin")
        _seed_learner_profiles()
        _clear_enrollments(shifu_bid)
        db.session.commit()
        token = generate_token(app, admin_bid)

    resp = test_client.post(
        "/api/portal/admin/enroll",
        json={"role_tags": ["sales"], "shifu_bid": shifu_bid, "module": "onboarding"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    data = payload["data"]
    assert data["enrolled"] == 2
    assert data["skipped"] == 0
    assert data["errors"] == []

    with app.app_context():
        rows = CourseEnrollment.query.filter_by(shifu_bid=shifu_bid).all()
        assert {r.user_bid for r in rows} == {"usr-pa-sales1", "usr-pa-sales2"}
        assert all(r.module == "onboarding" for r in rows)
        assert all(r.trainer_bid == admin_bid for r in rows)


def test_batch_enroll_skips_duplicates(app, test_client):
    admin_bid = "usr-pa-admin2"
    shifu_bid = "crs-pa-batch2"
    with app.app_context():
        _ensure_coach_tables()
        _create_user(user_bid=admin_bid, is_operator=True, nickname="BatchAdmin2")
        _seed_learner_profiles()
        _clear_enrollments(shifu_bid)
        db.session.commit()
        token = generate_token(app, admin_bid)

    body = {"role_tags": ["sales"], "shifu_bid": shifu_bid, "module": "mentorship"}
    first = test_client.post("/api/portal/admin/enroll", json=body, headers={"Token": token})
    assert first.get_json(force=True)["data"]["enrolled"] == 2

    second = test_client.post("/api/portal/admin/enroll", json=body, headers={"Token": token})
    payload = second.get_json(force=True)
    assert payload["code"] == 0, payload
    assert payload["data"]["enrolled"] == 0
    assert payload["data"]["skipped"] == 2
    assert payload["data"]["errors"] == []


def test_batch_enroll_no_match_is_noop(app, test_client):
    admin_bid = "usr-pa-admin3"
    shifu_bid = "crs-pa-batch3"
    with app.app_context():
        _ensure_coach_tables()
        _create_user(user_bid=admin_bid, is_operator=True, nickname="BatchAdmin3")
        _seed_learner_profiles()
        _clear_enrollments(shifu_bid)
        db.session.commit()
        token = generate_token(app, admin_bid)

    resp = test_client.post(
        "/api/portal/admin/enroll",
        json={"role_tags": ["qc"], "shifu_bid": shifu_bid, "module": "onboarding"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert payload["data"] == {"enrolled": 0, "skipped": 0, "errors": []}


def test_batch_enroll_requires_manage_users(app, test_client):
    learner_bid = "usr-pa-plain"
    with app.app_context():
        _ensure_coach_tables()
        _create_user(user_bid=learner_bid, nickname="PlainLearner")
        db.session.commit()
        token = generate_token(app, learner_bid)

    resp = test_client.post(
        "/api/portal/admin/enroll",
        json={"role_tags": ["sales"], "shifu_bid": "crs-pa-x", "module": "onboarding"},
        headers={"Token": token},
    )
    assert resp.get_json(force=True)["code"] == 403


def test_batch_enroll_rejects_empty_or_bad_role_tags(app, test_client):
    admin_bid = "usr-pa-admin4"
    with app.app_context():
        _ensure_coach_tables()
        _create_user(user_bid=admin_bid, is_operator=True, nickname="BatchAdmin4")
        db.session.commit()
        token = generate_token(app, admin_bid)

    for bad in ([], "sales"):
        resp = test_client.post(
            "/api/portal/admin/enroll",
            json={"role_tags": bad, "shifu_bid": "crs-pa-y", "module": "onboarding"},
            headers={"Token": token},
        )
        assert resp.get_json(force=True)["code"] != 0


# ── regression · single enroll unchanged ───────────────────────────────


def test_single_enroll_regression(app, test_client):
    admin_bid = "usr-pa-single-admin"
    user_bid = "usr-pa-single-u"
    shifu_bid = "crs-pa-single1"
    with app.app_context():
        _ensure_coach_tables()
        _create_user(user_bid=admin_bid, is_operator=True, nickname="SingleAdmin")
        _create_user(user_bid=user_bid, nickname="SingleUser")
        CourseEnrollment.query.filter_by(user_bid=user_bid, shifu_bid=shifu_bid).delete()
        db.session.commit()
        token = generate_token(app, admin_bid)

    resp = test_client.post(
        "/api/portal/admin/enroll",
        json={"user_bid": user_bid, "shifu_bid": shifu_bid, "module": "intensive"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert payload["data"]["enroll_id"] is not None
    assert payload["data"]["status"] == "active"
