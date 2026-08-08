"""Regression tests for Batch 2-4 permission fixes (docs/ROLE-ACCESS-TEST-REPORT.md).

Covers, against the real Flask app + SQLite (via test_client):

- B1: ``GET /api/portal/mentor/students`` consumes ``visible_students_scope``
  (a dept_head sees only their own department, admin/hr see everyone);
- B3: coach/report permission denial returns business code 403 (not the
  old 2001 "parameter error");
- B4: HR (holds ``confirm_checklist`` but NOT ``create_session``) can confirm
  a checklist via ``POST /api/coach/checklist/<bid>/sync``; a learner cannot.

The seeded ``coach_roles`` matrix mirrors docs/P0-PERMISSION-KEYS.md §二.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import text

from flaskr.dao import db
from flaskr.service.learning_portal.models import (
    LearnerProfile,
    LearnerMentorship,
    CoachSession,
)
from flaskr.service.user.models import UserInfo as UserEntity
from flaskr.service.user.utils import generate_token


@pytest.fixture(autouse=True)
def _clean_batch234_tables(app):
    with app.app_context():
        db.session.query(CoachSession).delete()
        db.session.query(LearnerMentorship).delete()
        db.session.query(LearnerProfile).delete()
        db.session.commit()
    yield


def _create_user(
    *,
    user_bid: str,
    nickname: str = "Test User",
    is_operator: bool = False,
    department: str = "",
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


def _seed_role_tables(app):
    """Create coach_roles / user_role_assignments + the 5-role matrix."""
    with app.app_context():
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
                "('role-hr', 'hr',"
                " '[\"view_all_students\",\"view_any_report\",\"confirm_checklist\","
                " \"manage_users\",\"certify_content\",\"view_kpi\",\"audit\","
                " \"custom_dashboard\",\"view_own_report\"]', 1),"
                "('role-dept-head', 'dept_head',"
                " '[\"view_all_students\",\"view_any_report\",\"certify_content\","
                " \"view_kpi\",\"custom_dashboard\",\"view_own_report\"]', 1),"
                "('role-coach', 'coach',"
                " '[\"coach:read\",\"coach:write\",\"learner:read\","
                " \"view_all_students\",\"score\",\"edit_summary\","
                " \"create_session\",\"view_any_report\",\"confirm_checklist\","
                " \"view_kpi\",\"custom_dashboard\",\"view_own_report\"]', 1),"
                "('role-learner', 'learner',"
                " '[\"learner:read\",\"learner:write\",\"view_own_report\"]', 1)"
            )
        )
        db.session.commit()


def _assign_role(app, user_bid: str, role_bid: str) -> None:
    with app.app_context():
        db.session.execute(
            text(
                "INSERT OR REPLACE INTO user_role_assignments "
                "(user_bid, role_bid) VALUES (:u, :r)"
            ),
            {"u": user_bid, "r": role_bid},
        )
        db.session.commit()


def _add_learner(app, *, learner_bid: str, department: str) -> None:
    with app.app_context():
        db.session.add(
            LearnerProfile(
                learner_bid=learner_bid,
                user_bid=learner_bid,
                department=department,
                status="active",
                created_at=datetime(2026, 7, 1),
                updated_at=datetime(2026, 7, 1),
            )
        )
        db.session.commit()


def _add_mentorship(app, *, record_bid: str, learner_bid: str) -> None:
    with app.app_context():
        db.session.add(
            LearnerMentorship(
                record_bid=record_bid,
                learner_bid=learner_bid,
                phase_bid="ph-000",
                status="in_progress",
                created_at=datetime(2026, 7, 1),
                updated_at=datetime(2026, 7, 1),
            )
        )
        db.session.commit()


def test_mentor_students_respects_department_scope(app, test_client):
    """B1: dept_head sees only their own department in mentor/students."""
    dept_bid = "usr-b1-dept"
    _seed_role_tables(app)
    with app.app_context():
        _create_user(user_bid=dept_bid, nickname="B1 Dept", department="销售本部")
        db.session.commit()
    _assign_role(app, dept_bid, "role-dept-head")
    _add_learner(app, learner_bid="usr-b1-l1", department="销售本部")
    _add_learner(app, learner_bid="usr-b1-l2", department="培训部")
    token = generate_token(app, dept_bid)

    resp = test_client.get(
        "/api/portal/mentor/students", headers={"Token": token}
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    learner_bids = {item["learner_bid"] for item in payload["data"]}
    assert learner_bids == {"usr-b1-l1"}, payload


def test_mentor_students_admin_sees_all(app, test_client):
    """B1: admin (scope=all) sees every learner in mentor/students."""
    admin_bid = "usr-b1-admin"
    _seed_role_tables(app)
    with app.app_context():
        _create_user(user_bid=admin_bid, nickname="B1 Admin")
        db.session.commit()
    _assign_role(app, admin_bid, "role-admin")
    _add_learner(app, learner_bid="usr-b1-l1", department="销售本部")
    _add_learner(app, learner_bid="usr-b1-l2", department="培训部")
    token = generate_token(app, admin_bid)

    resp = test_client.get(
        "/api/portal/mentor/students", headers={"Token": token}
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert len(payload["data"]) == 2, payload


def test_coach_report_denied_with_403(app, test_client):
    """B3: learner denied another learner's report -> code 403 (not 2001)."""
    learner_bid = "usr-b3-learner"
    other_learner = "usr-b3-other"
    _seed_role_tables(app)
    with app.app_context():
        _create_user(user_bid=learner_bid, nickname="B3 Learner")
        db.session.commit()
    _assign_role(app, learner_bid, "role-learner")
    _add_learner(app, learner_bid=other_learner, department="培训部")
    token = generate_token(app, learner_bid)

    resp = test_client.get(
        f"/api/coach/report/{other_learner}?source=rule",
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 403, payload


def test_hr_can_confirm_checklist(app, test_client):
    """B4: HR (confirm_checklist, no create_session) may POST checklist sync."""
    hr_bid = "usr-b4-hr"
    record_bid = "rec-b4-1"
    _seed_role_tables(app)
    with app.app_context():
        _create_user(user_bid=hr_bid, nickname="B4 HR")
        db.session.commit()
    _assign_role(app, hr_bid, "role-hr")
    _add_learner(app, learner_bid="usr-b4-l1", department="销售本部")
    _add_mentorship(app, record_bid=record_bid, learner_bid="usr-b4-l1")
    token = generate_token(app, hr_bid)

    resp = test_client.post(
        f"/api/coach/checklist/{record_bid}/sync",
        json={"note": "确认"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload


def test_learner_cannot_confirm_checklist(app, test_client):
    """B4 (negative): a learner cannot confirm a checklist -> 403."""
    learner_bid = "usr-b4-ln"
    record_bid = "rec-b4-2"
    _seed_role_tables(app)
    with app.app_context():
        _create_user(user_bid=learner_bid, nickname="B4 Learner")
        db.session.commit()
    _assign_role(app, learner_bid, "role-learner")
    _add_learner(app, learner_bid=learner_bid, department="销售本部")
    _add_mentorship(app, record_bid=record_bid, learner_bid=learner_bid)
    token = generate_token(app, learner_bid)

    resp = test_client.post(
        f"/api/coach/checklist/{record_bid}/sync",
        json={"note": "hack"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 403, payload


def test_dept_head_report_filtered_by_department(app, test_client):
    """B5: dept_head may only view reports of learners in their department."""
    dept_bid = "usr-b5-dept"
    _seed_role_tables(app)
    with app.app_context():
        _create_user(user_bid=dept_bid, nickname="B5 Dept", department="销售本部")
        db.session.commit()
    _assign_role(app, dept_bid, "role-dept-head")
    _add_learner(app, learner_bid="usr-b5-inside", department="销售本部")
    _add_learner(app, learner_bid="usr-b5-outside", department="培训部")
    token = generate_token(app, dept_bid)

    inside = test_client.get(
        "/api/coach/report/usr-b5-inside?source=rule",
        headers={"Token": token},
    ).get_json(force=True)
    assert inside["code"] == 0, inside

    outside = test_client.get(
        "/api/coach/report/usr-b5-outside?source=rule",
        headers={"Token": token},
    ).get_json(force=True)
    assert outside["code"] == 403, outside
