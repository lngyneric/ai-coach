"""Tests for W2/W3 legacy closeout — coach_sessions full CRUD.

Covers, against the real Flask app + SQLite (via test_client):

- POST /api/coach/sessions → create (coach for mentored learner, learner
  themself, admin/hr scope-all); denies stranger coach / dept outside scope
- GET  /api/coach/sessions → list scoped by data scope (all / mentored /
  department / self) with paging
- GET  /api/coach/sessions/<bid> → single, data-scope checked
- PUT  /api/coach/sessions/<bid> → update, data-scope checked
- regression: existing GET/PUT behavior still works for the owner
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import text

from flaskr.dao import db
from flaskr.service.learning_portal.models import (
    CoachSession,
    LearnerProfile,
)
from flaskr.service.user.models import UserInfo as UserEntity
from flaskr.service.user.utils import generate_token


@pytest.fixture(autouse=True)
def _clean_coach_sessions(app):
    with app.app_context():
        db.session.query(CoachSession).delete()
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
    """Create coach_roles / user_role_assignments + the 5-role rows."""
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
                "('role-coach', 'coach',"
                " '[\"create_session\",\"view_own_report\"]', 1),"
                "('role-dept-head', 'dept_head',"
                " '[\"view_own_report\"]', 1),"
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


def _add_learner(
    app,
    *,
    learner_bid: str,
    user_bid: str,
    coach_bid: str | None = None,
    department: str | None = None,
):
    with app.app_context():
        db.session.add(
            LearnerProfile(
                learner_bid=learner_bid,
                user_bid=user_bid,
                coach_bid=coach_bid,
                department=department,
                status="active",
                created_at=datetime(2026, 7, 1),
                updated_at=datetime(2026, 7, 1),
            )
        )
        db.session.commit()


def _add_session(
    app,
    *,
    session_bid: str,
    learner_bid: str,
    mentor_bid: str,
    topic: str = "kickoff",
):
    with app.app_context():
        db.session.add(
            CoachSession(
                session_bid=session_bid,
                learner_bid=learner_bid,
                mentor_bid=mentor_bid,
                session_type="regular",
                session_date=datetime(2026, 7, 20, 9),
                topic=topic,
                status="completed",
                created_at=datetime(2026, 7, 20, 9),
                updated_at=datetime(2026, 7, 20, 9),
            )
        )
        db.session.commit()


def _setup(app):
    """Seed roles + users (admin/coach/learner/stranger) + one mentored learner."""
    _seed_role_tables(app)
    with app.app_context():
        _create_user(user_bid="adm-1", is_operator=True, nickname="Admin")
        _create_user(user_bid="coach-1", nickname="Coach")
        _create_user(user_bid="lrn-1", nickname="Learner")
        _create_user(user_bid="stranger-1", nickname="Stranger")
        db.session.commit()
    _assign_role(app, "coach-1", "role-coach")
    _assign_role(app, "lrn-1", "role-learner")
    _add_learner(
        app, learner_bid="ln-1", user_bid="lrn-1", coach_bid="coach-1"
    )


def _token(app, user_bid: str) -> str:
    return generate_token(app, user_bid)


# ---------------------------------------------------------------------------
# POST — create
# ---------------------------------------------------------------------------


def test_create_by_mentoring_coach(app, test_client):
    _setup(app)
    token = _token(app, "coach-1")
    resp = test_client.post(
        "/api/coach/sessions",
        json={"learner_bid": "ln-1", "topic": "月度辅导"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert payload["data"]["learner_bid"] == "ln-1"
    assert payload["data"]["mentor_bid"] == "coach-1"
    assert payload["data"]["topic"] == "月度辅导"


def test_create_by_learner_self(app, test_client):
    _setup(app)
    token = _token(app, "lrn-1")
    resp = test_client.post(
        "/api/coach/sessions",
        json={"learner_bid": "ln-1", "topic": "自我复盘"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert payload["data"]["mentor_bid"] == "lrn-1"  # falls back to user_id


def test_create_denies_stranger_coach(app, test_client):
    _setup(app)
    _assign_role(app, "stranger-1", "role-coach")
    _add_learner(
        app, learner_bid="ln-other", user_bid="lrn-1", coach_bid="coach-1"
    )
    token = _token(app, "stranger-1")
    resp = test_client.post(
        "/api/coach/sessions",
        json={"learner_bid": "ln-other", "topic": "越权创建"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] != 0  # not the mentored learner


def test_create_denies_learner_for_other(app, test_client):
    _setup(app)
    _add_learner(
        app, learner_bid="ln-2", user_bid="other-2", coach_bid="coach-1"
    )
    token = _token(app, "lrn-1")
    resp = test_client.post(
        "/api/coach/sessions",
        json={"learner_bid": "ln-2", "topic": "别人的"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] != 0


def test_create_by_admin_scope_all(app, test_client):
    _setup(app)
    _add_learner(
        app, learner_bid="ln-any", user_bid="other-any", coach_bid=None
    )
    token = _token(app, "adm-1")
    resp = test_client.post(
        "/api/coach/sessions",
        json={"learner_bid": "ln-any", "topic": "admin 创建"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload


def test_create_requires_learner_bid(app, test_client):
    _setup(app)
    token = _token(app, "coach-1")
    resp = test_client.post(
        "/api/coach/sessions",
        json={"topic": "no learner"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] != 0  # learner_bid required


# ---------------------------------------------------------------------------
# GET list — data scope
# ---------------------------------------------------------------------------


def test_list_mentored_scope_coach(app, test_client):
    _setup(app)
    _add_session(
        app, session_bid="sess-1", learner_bid="ln-1", mentor_bid="coach-1"
    )
    _add_learner(
        app, learner_bid="ln-other", user_bid="lrn-other", coach_bid="other-coach"
    )
    _add_session(
        app,
        session_bid="sess-2",
        learner_bid="ln-other",
        mentor_bid="other-coach",
    )
    token = _token(app, "coach-1")
    resp = test_client.get("/api/coach/sessions", headers={"Token": token})
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    bids = [item["session_bid"] for item in payload["data"]["items"]]
    assert bids == ["sess-1"]  # only own mentee
    assert payload["data"]["total"] == 1


def test_list_self_scope_learner(app, test_client):
    _setup(app)
    _add_session(
        app, session_bid="sess-1", learner_bid="ln-1", mentor_bid="coach-1"
    )
    _add_learner(
        app, learner_bid="ln-2", user_bid="other-2", coach_bid="coach-1"
    )
    _add_session(
        app, session_bid="sess-2", learner_bid="ln-2", mentor_bid="coach-1"
    )
    token = _token(app, "lrn-1")
    resp = test_client.get("/api/coach/sessions", headers={"Token": token})
    payload = resp.get_json(force=True)
    bids = [item["session_bid"] for item in payload["data"]["items"]]
    assert bids == ["sess-1"]  # only self


def test_list_all_scope_admin(app, test_client):
    _setup(app)
    _add_session(
        app, session_bid="sess-1", learner_bid="ln-1", mentor_bid="coach-1"
    )
    _add_learner(
        app, learner_bid="ln-2", user_bid="other-2", coach_bid=None
    )
    _add_session(
        app, session_bid="sess-2", learner_bid="ln-2", mentor_bid="coach-1"
    )
    token = _token(app, "adm-1")
    resp = test_client.get("/api/coach/sessions", headers={"Token": token})
    payload = resp.get_json(force=True)
    assert payload["data"]["total"] == 2


def test_list_department_scope_dept_head(app, test_client):
    _setup(app)
    _seed_role_tables(app)
    with app.app_context():
        _create_user(user_bid="dept-1", department="销售本部")
        db.session.commit()
    _assign_role(app, "dept-1", "role-dept-head")
    # ln-1 already exists from _setup — set its department in place
    with app.app_context():
        prof = LearnerProfile.query.filter_by(learner_bid="ln-1").first()
        prof.department = "销售本部"
        db.session.commit()
    _add_session(
        app, session_bid="sess-1", learner_bid="ln-1", mentor_bid="coach-1"
    )
    # session 2 in another department
    _add_learner(
        app,
        learner_bid="ln-other",
        user_bid="lrn-other",
        coach_bid="coach-1",
        department="市场部",
    )
    _add_session(
        app,
        session_bid="sess-2",
        learner_bid="ln-other",
        mentor_bid="coach-1",
    )
    token = _token(app, "dept-1")
    resp = test_client.get("/api/coach/sessions", headers={"Token": token})
    payload = resp.get_json(force=True)
    bids = [item["session_bid"] for item in payload["data"]["items"]]
    assert bids == ["sess-1"]  # only same-department learner
    assert payload["data"]["total"] == 1


def test_list_paging(app, test_client):
    _setup(app)
    for i in range(3):
        _add_session(
            app,
            session_bid=f"sess-{i}",
            learner_bid="ln-1",
            mentor_bid="coach-1",
            topic=f"t{i}",
        )
    token = _token(app, "adm-1")
    resp = test_client.get(
        "/api/coach/sessions?page=1&size=2", headers={"Token": token}
    )
    payload = resp.get_json(force=True)
    assert len(payload["data"]["items"]) == 2
    assert payload["data"]["total"] == 3


# ---------------------------------------------------------------------------
# GET single + PUT — data scope checks
# ---------------------------------------------------------------------------


def test_get_single_denies_stranger(app, test_client):
    _setup(app)
    # lrn-2 is a separate learner whose session lrn-1 must not see
    with app.app_context():
        _create_user(user_bid="lrn-2", nickname="Learner2")
        db.session.commit()
    _add_learner(
        app, learner_bid="ln-2", user_bid="lrn-2", coach_bid="coach-1"
    )
    _add_session(
        app, session_bid="sess-2", learner_bid="ln-2", mentor_bid="coach-1"
    )
    token = _token(app, "lrn-1")
    resp = test_client.get(
        "/api/coach/sessions/sess-2", headers={"Token": token}
    )
    payload = resp.get_json(force=True)
    assert payload["code"] != 0  # not self (learner only sees own sessions)


def test_get_single_allows_owner(app, test_client):
    _setup(app)
    _add_session(
        app, session_bid="sess-1", learner_bid="ln-1", mentor_bid="coach-1"
    )
    token = _token(app, "lrn-1")
    resp = test_client.get("/api/coach/sessions/sess-1", headers={"Token": token})
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert payload["data"]["session_bid"] == "sess-1"


def test_put_updates_session(app, test_client):
    _setup(app)
    _add_session(
        app, session_bid="sess-1", learner_bid="ln-1", mentor_bid="coach-1"
    )
    token = _token(app, "coach-1")
    resp = test_client.put(
        "/api/coach/sessions/sess-1",
        json={"topic": "更新主题", "status": "completed"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    with app.app_context():
        s = CoachSession.query.get("sess-1")
        assert s.topic == "更新主题"


def test_put_denies_out_of_scope(app, test_client):
    _setup(app)
    _add_session(
        app, session_bid="sess-1", learner_bid="ln-1", mentor_bid="coach-1"
    )
    _assign_role(app, "stranger-1", "role-coach")
    token = _token(app, "stranger-1")
    resp = test_client.put(
        "/api/coach/sessions/sess-1",
        json={"topic": "越权改"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] != 0
