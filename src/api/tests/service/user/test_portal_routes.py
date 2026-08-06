"""Tests for P0 step 7: admin/roles extension + /api/portal/permissions + guards.

Covers (against the real Flask app + SQLite, via test_client):
- GET  /api/portal/admin/roles  → returns `roles` array (5-level) + legacy flags
- PUT  /api/portal/admin/roles/<user_bid> → grants/revokes 5-level roles
- GET  /api/portal/permissions → roles + permissions + data_scope
- learning_portal guards: learner is denied on score / mentor endpoints (403)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text

from flaskr.dao import db
from flaskr.service.user.models import UserInfo as UserEntity
from flaskr.service.user.utils import generate_token


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


def test_admin_roles_list_includes_roles_array(app, test_client):
    from flaskr.service.coach.permissions import resolve_user_roles
    from flaskr.dao import db as _db

    admin_bid = "usr-step7-admin"
    target_bid = "usr-step7-target"
    with app.app_context():
        _create_user(user_bid=admin_bid, is_operator=True, nickname="Step7 Admin")
        _create_user(user_bid=target_bid, nickname="Step7 Target")
        _db.session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS coach_roles ("
                " role_bid VARCHAR(32) PRIMARY KEY,"
                " name VARCHAR(50) NOT NULL UNIQUE,"
                " label VARCHAR(100) DEFAULT '',"
                " permissions TEXT,"
                " is_active INTEGER DEFAULT 1)"
            )
        )
        _db.session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS user_role_assignments ("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " user_bid VARCHAR(32) NOT NULL,"
                " role_bid VARCHAR(32) NOT NULL,"
                " UNIQUE (user_bid, role_bid))"
            )
        )
        _db.session.execute(
            text(
                "INSERT OR REPLACE INTO coach_roles "
                "(role_bid, name, permissions, is_active) VALUES "
                "('role-admin', 'admin', '[\"all\"]', 1),"
                "('role-learner', 'learner',"
                " '[\"learner:read\",\"learner:write\",\"view_own_report\"]', 1),"
                "('role-coach', 'coach', '[\"score\",\"view_own_report\"]', 1)"
            )
        )
        _db.session.execute(
            text(
                "INSERT OR REPLACE INTO user_role_assignments "
                "(user_bid, role_bid) VALUES "
                "('usr-step7-target', 'role-learner')"
            )
        )
        _db.session.commit()
        token = generate_token(app, admin_bid)

    resp = test_client.get(
        "/api/portal/admin/roles?page=1&size=50",
        headers={"Token": token},
    )
    assert resp.status_code == 200
    payload = resp.get_json(force=True)
    assert payload["code"] == 0
    items = payload["data"]["items"]
    target = next(u for u in items if u["user_bid"] == target_bid)
    assert target["is_operator"] is False
    assert target["is_creator"] is False
    # 5-level roles array present (from resolve_user_roles)
    assert isinstance(target["roles"], list)
    assert any(r["role_bid"] == "role-learner" for r in target["roles"])


def test_admin_roles_list_denies_non_manager(app, test_client):
    learner_bid = "usr-step7-nomanager"
    with app.app_context():
        _create_user(user_bid=learner_bid, nickname="Step7 Learner")
        db.session.commit()
        token = generate_token(app, learner_bid)

    resp = test_client.get(
        "/api/portal/admin/roles",
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 403


def test_admin_roles_put_grants_and_revokes(app, test_client):
    from flaskr.dao import db as _db

    admin_bid = "usr-step7-adm2"
    target_bid = "usr-step7-tgt2"
    with app.app_context():
        _create_user(user_bid=admin_bid, is_operator=True, nickname="Adm2")
        _create_user(user_bid=target_bid, nickname="Tgt2")
        _db.session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS coach_roles ("
                " role_bid VARCHAR(32) PRIMARY KEY,"
                " name VARCHAR(50) NOT NULL UNIQUE,"
                " label VARCHAR(100) DEFAULT '',"
                " permissions TEXT,"
                " is_active INTEGER DEFAULT 1)"
            )
        )
        _db.session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS user_role_assignments ("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " user_bid VARCHAR(32) NOT NULL,"
                " role_bid VARCHAR(32) NOT NULL,"
                " UNIQUE (user_bid, role_bid))"
            )
        )
        _db.session.execute(
            text(
                "INSERT OR REPLACE INTO coach_roles "
                "(role_bid, name, permissions, is_active) VALUES "
                "('role-admin', 'admin', '[\"all\"]', 1),"
                "('role-learner', 'learner',"
                " '[\"learner:read\",\"learner:write\",\"view_own_report\"]', 1),"
                "('role-coach', 'coach', '[\"score\",\"view_own_report\"]', 1)"
            )
        )
        _db.session.execute(
            text(
                "INSERT OR REPLACE INTO user_role_assignments "
                "(user_bid, role_bid) VALUES "
                "('usr-step7-tgt2', 'role-learner')"
            )
        )
        _db.session.commit()
        token = generate_token(app, admin_bid)

    # Grant role-coach
    resp = test_client.put(
        f"/api/portal/admin/roles/{target_bid}",
        json={"grant_roles": ["role-coach"]},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert any(r["role_bid"] == "role-coach" for r in payload["data"]["roles"])

    # Persisted in user_role_assignments
    with app.app_context():
        row = _db.session.execute(
            text(
                "SELECT 1 FROM user_role_assignments "
                "WHERE user_bid = :ub AND role_bid = 'role-coach'"
            ),
            {"ub": target_bid},
        ).first()
        assert row is not None

    # Revoke role-learner
    resp = test_client.put(
        f"/api/portal/admin/roles/{target_bid}",
        json={"revoke_roles": ["role-learner"]},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert not any(r["role_bid"] == "role-learner" for r in payload["data"]["roles"])

    with app.app_context():
        row = _db.session.execute(
            text(
                "SELECT 1 FROM user_role_assignments "
                "WHERE user_bid = :ub AND role_bid = 'role-learner'"
            ),
            {"ub": target_bid},
        ).first()
        assert row is None


def test_portal_permissions_admin(app, test_client):
    from flaskr.dao import db as _db

    admin_bid = "usr-step7-perm-admin"
    with app.app_context():
        _create_user(user_bid=admin_bid, is_operator=True, nickname="PermAdmin")
        _db.session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS coach_roles ("
                " role_bid VARCHAR(32) PRIMARY KEY,"
                " name VARCHAR(50) NOT NULL UNIQUE,"
                " label VARCHAR(100) DEFAULT '',"
                " permissions TEXT,"
                " is_active INTEGER DEFAULT 1)"
            )
        )
        _db.session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS user_role_assignments ("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " user_bid VARCHAR(32) NOT NULL,"
                " role_bid VARCHAR(32) NOT NULL,"
                " UNIQUE (user_bid, role_bid))"
            )
        )
        _db.session.execute(
            text(
                "INSERT OR REPLACE INTO coach_roles "
                "(role_bid, name, permissions, is_active) VALUES "
                "('role-admin', 'admin', '[\"all\"]', 1)"
            )
        )
        _db.session.execute(
            text(
                "INSERT OR REPLACE INTO user_role_assignments "
                "(user_bid, role_bid) VALUES "
                "('usr-step7-perm-admin', 'role-admin')"
            )
        )
        _db.session.commit()
        token = generate_token(app, admin_bid)

    resp = test_client.get(
        "/api/portal/permissions",
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    data = payload["data"]
    assert any(r["role_bid"] == "role-admin" for r in data["roles"])
    assert "all" in data["permissions"]
    assert "score" in data["permissions"]
    assert data["data_scope"] == "all"


def test_portal_permissions_learner_scoped(app, test_client):
    from flaskr.dao import db as _db

    learner_bid = "usr-step7-perm-learner"
    with app.app_context():
        _create_user(user_bid=learner_bid, nickname="PermLearner")
        _db.session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS coach_roles ("
                " role_bid VARCHAR(32) PRIMARY KEY,"
                " name VARCHAR(50) NOT NULL UNIQUE,"
                " label VARCHAR(100) DEFAULT '',"
                " permissions TEXT,"
                " is_active INTEGER DEFAULT 1)"
            )
        )
        _db.session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS user_role_assignments ("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " user_bid VARCHAR(32) NOT NULL,"
                " role_bid VARCHAR(32) NOT NULL,"
                " UNIQUE (user_bid, role_bid))"
            )
        )
        _db.session.execute(
            text(
                "INSERT OR REPLACE INTO coach_roles "
                "(role_bid, name, permissions, is_active) VALUES "
                "('role-learner', 'learner',"
                " '[\"learner:read\",\"learner:write\",\"view_own_report\"]', 1)"
            )
        )
        _db.session.execute(
            text(
                "INSERT OR REPLACE INTO user_role_assignments "
                "(user_bid, role_bid) VALUES "
                "('usr-step7-perm-learner', 'role-learner')"
            )
        )
        _db.session.commit()
        token = generate_token(app, learner_bid)

    resp = test_client.get(
        "/api/portal/permissions",
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    data = payload["data"]
    assert any(r["role_bid"] == "role-learner" for r in data["roles"])
    assert "score" not in data["permissions"]
    assert "view_own_report" in data["permissions"]
    assert data["data_scope"] == f"self:{learner_bid}"


def test_score_guard_denies_learner(app, test_client):
    learner_bid = "usr-step7-guard-learner"
    with app.app_context():
        _create_user(user_bid=learner_bid, nickname="GuardLearner")
        db.session.commit()
        token = generate_token(app, learner_bid)

    # learner has no `score` permission → 403, even with an arbitrary record_bid
    resp = test_client.post(
        "/api/portal/mentorship/items/nonexistent/score",
        json={"score": 4},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 403, payload


def test_score_guard_allows_admin(app, test_client):
    admin_bid = "usr-step7-guard-admin"
    with app.app_context():
        _create_user(user_bid=admin_bid, is_operator=True, nickname="GuardAdmin")
        db.session.commit()
        token = generate_token(app, admin_bid)

    # admin is allowed through the permission guard; with an unknown record_bid
    # it must fail downstream with a params error (NOT 403).
    resp = test_client.post(
        "/api/portal/mentorship/items/nonexistent/score",
        json={"score": 4},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] != 403, payload


# ═══════════════════════════════════════════════════════════════════════
#  P0 step 9 — D1: ORM table/column names match the real ai-shifu_dev DB
#  P0 step 9 — D2/D3: admin/learners permission guard + data-scope filter
# ═══════════════════════════════════════════════════════════════════════

_ROLE_INSERT_SQL = """
INSERT OR REPLACE INTO coach_roles (role_bid, name, permissions, is_active) VALUES
('role-admin',     'admin', '["all"]', 1),
('role-hr',        'hr', '["view_all_students","view_any_report","confirm_checklist","manage_users","certify_content","view_kpi","audit","custom_dashboard","view_own_report"]', 1),
('role-dept-head', 'dept_head', '["view_all_students","view_any_report","certify_content","view_kpi","custom_dashboard","view_own_report"]', 1),
('role-coach',     'coach', '["coach:read","coach:write","learner:read","view_all_students","score","edit_summary","create_session","view_any_report","confirm_checklist","view_kpi","custom_dashboard","view_own_report"]', 1),
('role-learner',   'learner', '["learner:read","learner:write","view_own_report"]', 1)
"""


def _ensure_coach_tables(app):
    """Create coach_roles / user_role_assignments and seed the 5 roles."""
    from flaskr.dao import db as _db

    _db.session.execute(
        text(
            "CREATE TABLE IF NOT EXISTS coach_roles ("
            " role_bid VARCHAR(32) PRIMARY KEY,"
            " name VARCHAR(50) NOT NULL UNIQUE,"
            " label VARCHAR(100) DEFAULT '',"
            " permissions TEXT,"
            " is_active INTEGER DEFAULT 1)"
        )
    )
    _db.session.execute(
        text(
            "CREATE TABLE IF NOT EXISTS user_role_assignments ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " user_bid VARCHAR(32) NOT NULL,"
            " role_bid VARCHAR(32) NOT NULL,"
            " UNIQUE (user_bid, role_bid))"
        )
    )
    _db.session.execute(text(_ROLE_INSERT_SQL))
    _db.session.commit()


def _assign_role(app, user_bid: str, role_bid: str) -> None:
    from flaskr.dao import db as _db

    _db.session.execute(
        text(
            "INSERT OR REPLACE INTO user_role_assignments "
            "(user_bid, role_bid) VALUES (:ub, :rb)"
        ),
        {"ub": user_bid, "rb": role_bid},
    )
    _db.session.commit()


def test_orm_tablenames_match_real_db():
    """D1: models map to real ai-shifu_dev tables + coach_score column."""
    from flaskr.service.learning_portal.models import (
        LearnerMentorship,
        MentorshipChecklist,
        MentorshipPhase,
    )

    assert MentorshipPhase.__tablename__ == "coach_phases"
    assert LearnerMentorship.__tablename__ == "learner_coaching"
    assert MentorshipChecklist.__tablename__ == "coach_checklist"
    # learner_coaching uses coach_score (legacy mentor_score is gone)
    assert hasattr(LearnerMentorship, "coach_score")
    assert not hasattr(LearnerMentorship, "mentor_score")


def test_admin_learners_guard_denies_learner(app, test_client):
    """D2: learner calling admin/learners gets a 403 business code."""
    learner_bid = "usr-step9-learner"
    with app.app_context():
        _create_user(user_bid=learner_bid, nickname="Step9 Learner")
        _ensure_coach_tables(app)
        _assign_role(app, learner_bid, "role-learner")
        db.session.commit()
        token = generate_token(app, learner_bid)

    resp = test_client.get(
        "/api/portal/admin/learners",
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 403, payload


def test_admin_learners_dept_scope(app, test_client):
    """D3: dept_head only sees learners in their own department."""
    from flaskr.service.learning_portal.models import LearnerProfile

    dept_head_bid = "usr-step9-dept"
    coach_bid = "usr-step9-coach"
    with app.app_context():
        # Session-scoped SQLite is shared across tests → isolate the table.
        LearnerProfile.query.delete()
        db.session.commit()
        _create_user(
            user_bid=dept_head_bid,
            nickname="Step9 DeptHead",
            department="销售本部",
        )
        _create_user(user_bid=coach_bid, nickname="Step9 Coach")
        _ensure_coach_tables(app)
        _assign_role(app, dept_head_bid, "role-dept-head")
        _assign_role(app, coach_bid, "role-coach")

        # two learners in the same dept as the dept_head, one elsewhere
        for i, (lb, dept, mentor) in enumerate(
            [
                ("usr-lp-sales1", "销售本部", coach_bid),
                ("usr-lp-sales2", "销售本部", "usr-other-coach"),
                ("usr-lp-train1", "培训部", coach_bid),
            ],
            start=1,
        ):
            db.session.add(
                LearnerProfile(
                    learner_bid=lb,
                    user_bid=lb,
                    employee_no=f"LP{i:04d}",
                    department=dept,
                    coach_bid=mentor,
                    status="active",
                    created_at=datetime(2026, 1, i),
                    updated_at=datetime(2026, 1, i),
                )
            )
        db.session.commit()
        token = generate_token(app, dept_head_bid)

    resp = test_client.get(
        "/api/portal/admin/learners",
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    data = payload["data"]
    depts = {item["department"] for item in data["items"]}
    assert data["total"] == 2, payload
    assert depts == {"销售本部"}


def test_admin_learners_mentored_scope(app, test_client):
    """D3: coach only sees learners they mentor (coach_bid == own user_bid)."""
    from flaskr.service.learning_portal.models import LearnerProfile

    coach_bid = "usr-step9-coach2"
    with app.app_context():
        # Session-scoped SQLite is shared across tests → isolate the table.
        LearnerProfile.query.delete()
        db.session.commit()
        _create_user(user_bid=coach_bid, nickname="Step9 Coach2")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")

        for i, (lb, mentor) in enumerate(
            [
                ("usr-lp-my1", coach_bid),
                ("usr-lp-my2", coach_bid),
                ("usr-lp-other1", "usr-other-coach"),
            ],
            start=1,
        ):
            db.session.add(
                LearnerProfile(
                    learner_bid=lb,
                    user_bid=lb,
                    employee_no=f"M{i:04d}",
                    department="销售本部",
                    coach_bid=mentor,
                    status="active",
                    created_at=datetime(2026, 1, i),
                    updated_at=datetime(2026, 1, i),
                )
            )
        db.session.commit()
        token = generate_token(app, coach_bid)

    resp = test_client.get(
        "/api/portal/admin/learners",
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    data = payload["data"]
    assert data["total"] == 2, payload
    assert all(item["coach_bid"] == coach_bid for item in data["items"])


def test_admin_learners_all_scope(app, test_client):
    """D3 regression: admin sees all learners (scope=all → no filter)."""
    from flaskr.service.learning_portal.models import LearnerProfile

    admin_bid = "usr-step9-admin"
    with app.app_context():
        # Session-scoped SQLite is shared across tests → isolate the table.
        LearnerProfile.query.delete()
        db.session.commit()
        _create_user(user_bid=admin_bid, is_operator=True, nickname="Step9 Admin")
        _ensure_coach_tables(app)
        _assign_role(app, admin_bid, "role-admin")

        for i, (lb, dept) in enumerate(
            [
                ("usr-lp-a1", "销售本部"),
                ("usr-lp-a2", "培训部"),
                ("usr-lp-a3", "人事课"),
            ],
            start=1,
        ):
            db.session.add(
                LearnerProfile(
                    learner_bid=lb,
                    user_bid=lb,
                    employee_no=f"A{i:04d}",
                    department=dept,
                    status="active",
                    created_at=datetime(2026, 1, i),
                    updated_at=datetime(2026, 1, i),
                )
            )
        db.session.commit()
        token = generate_token(app, admin_bid)

    resp = test_client.get(
        "/api/portal/admin/learners",
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert payload["data"]["total"] == 3, payload



# ═══════════════════════════════════════════════════════════════════════
#  P0 step 10 — D4: score / start ownership (coach horizontal privilege
#  escalation). A coach may only score / start a phase for learners they
#  coach (LearnerProfile.coach_bid == own user_bid); admin/hr (scope=all)
#  keep the exception.
# ═══════════════════════════════════════════════════════════════════════


def _reset_d4_tables(app):
    """Isolate the shared session-scoped SQLite tables for D4 tests."""
    from flaskr.service.learning_portal.models import (
        LearnerChecklistItem,
        LearnerMentorship,
        LearnerProfile,
    )

    LearnerChecklistItem.query.delete()
    LearnerMentorship.query.delete()
    LearnerProfile.query.delete()
    db.session.commit()


def _seed_mentored_learner(app, learner_bid, coach_bid, record_bid):
    """Insert one LearnerProfile + one submitted checklist item for a learner."""
    from flaskr.service.learning_portal.models import (
        LearnerChecklistItem,
        LearnerProfile,
    )

    db.session.add(
        LearnerProfile(
            learner_bid=learner_bid,
            user_bid=learner_bid,
            employee_no="D4LP01",
            department="培训部",
            coach_bid=coach_bid,
            status="active",
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
    )
    db.session.add(
        LearnerChecklistItem(
            record_bid=record_bid,
            learner_bid=learner_bid,
            item_bid="itm-d4-01",
            status="submitted",
            submitted_at=datetime(2026, 1, 2),
            created_at=datetime(2026, 1, 2),
            updated_at=datetime(2026, 1, 2),
        )
    )
    db.session.commit()


def test_score_ownership_allows_own_mentored(app, test_client):
    """D4: coach may score a learner they mentor (coach_bid == own user_bid)."""
    coach_bid = "usr-d4-coach-ok"
    learner_bid = "usr-d4-lp-ok"
    record_bid = "rec-d4-ok"
    with app.app_context():
        _reset_d4_tables(app)
        _create_user(user_bid=coach_bid, nickname="D4 Coach OK")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")
        _seed_mentored_learner(app, learner_bid, coach_bid, record_bid)
        token = generate_token(app, coach_bid)

    resp = test_client.post(
        f"/api/portal/mentorship/items/{record_bid}/score",
        json={"score": 4},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload


def test_score_ownership_denies_non_mentored(app, test_client):
    """D4: coach may NOT score a learner they do not mentor -> 403."""
    coach_bid = "usr-d4-coach-x"
    learner_bid = "usr-d4-lp-x"
    record_bid = "rec-d4-x"
    with app.app_context():
        _reset_d4_tables(app)
        _create_user(user_bid=coach_bid, nickname="D4 Coach X")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")
        # learner is mentored by another coach (not coach_bid)
        _seed_mentored_learner(app, learner_bid, "usr-other-coach", record_bid)
        token = generate_token(app, coach_bid)

    resp = test_client.post(
        f"/api/portal/mentorship/items/{record_bid}/score",
        json={"score": 4},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 403, payload


def test_score_ownership_allows_admin_non_mentored(app, test_client):
    """D4 regression: admin (scope=all) may still score any learner."""
    admin_bid = "usr-d4-admin-x"
    learner_bid = "usr-d4-lp-adm"
    record_bid = "rec-d4-adm"
    with app.app_context():
        _reset_d4_tables(app)
        _create_user(user_bid=admin_bid, is_operator=True, nickname="D4 Admin")
        _ensure_coach_tables(app)
        _assign_role(app, admin_bid, "role-admin")
        # learner mentored by someone else entirely -> admin exception applies
        _seed_mentored_learner(app, learner_bid, "usr-other-coach", record_bid)
        token = generate_token(app, admin_bid)

    resp = test_client.post(
        f"/api/portal/mentorship/items/{record_bid}/score",
        json={"score": 4},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload


def test_start_mentorship_denies_non_mentored(app, test_client):
    """D4 (same class): coach may NOT start a phase for a non-mentored learner."""
    from flaskr.service.learning_portal.models import LearnerProfile

    coach_bid = "usr-d4-coach-start"
    learner_bid = "usr-d4-lp-start"
    with app.app_context():
        _reset_d4_tables(app)
        _create_user(user_bid=coach_bid, nickname="D4 Coach Start")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")
        # learner mentored by another coach
        db.session.add(
            LearnerProfile(
                learner_bid=learner_bid,
                user_bid=learner_bid,
                employee_no="D4LP02",
                department="培训部",
                coach_bid="usr-other-coach",
                status="active",
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.commit()
        token = generate_token(app, coach_bid)

    resp = test_client.post(
        "/api/portal/mentorship/start",
        json={"learner_bid": learner_bid, "phase_bid": "phase-d4-x"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 403, payload


def test_start_mentorship_allows_admin(app, test_client):
    """D4 regression: admin may still start a phase for any learner."""
    admin_bid = "usr-d4-admin-start"
    learner_bid = "usr-d4-lp-start2"
    with app.app_context():
        _reset_d4_tables(app)
        _create_user(user_bid=admin_bid, is_operator=True, nickname="D4 Admin Start")
        _ensure_coach_tables(app)
        _assign_role(app, admin_bid, "role-admin")
        token = generate_token(app, admin_bid)

    resp = test_client.post(
        "/api/portal/mentorship/start",
        json={"learner_bid": learner_bid, "phase_bid": "phase-d4-y"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload

