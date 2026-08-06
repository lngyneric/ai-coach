"""P2 fixes regression tests.

Covers:
- P2-1  ``_recalc_phase_score`` — sub-scores + weighted total are written back
        to ``learner_coaching`` after a mentor scores an item.
- P2-2  ``admin/learners`` PUT/POST guards — legacy ``is_operator`` replaced by
        ``has_permission(..., "manage_users")`` (learner 403 / hr allowed).
- P2-3  ``POST /api/user/logout`` — server-side token revocation (cache + DB)
        makes the old token unusable.
- P2-4  ``CoachSession`` / ``CoachProfile`` ORM mappings match the real tables.

Mirrors the test harness of ``test_portal_routes.py`` (SQLite via the session
``app`` fixture, roles seeded through raw SQL).
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


def _reset_p2_tables(app):
    """Isolate the shared session-scoped SQLite tables for P2 tests."""
    from flaskr.service.learning_portal.models import (
        CoachProfile,
        CoachSession,
        LearnerChecklistItem,
        LearnerMentorship,
        LearnerProfile,
        MentorshipChecklist,
        MentorshipPhase,
    )

    CoachProfile.query.delete()
    CoachSession.query.delete()
    LearnerChecklistItem.query.delete()
    LearnerMentorship.query.delete()
    LearnerProfile.query.delete()
    MentorshipChecklist.query.delete()
    MentorshipPhase.query.delete()
    db.session.commit()


# ═══════════════════════════════════════════════════════════════════
# P2-1 · _recalc_phase_score
# ═══════════════════════════════════════════════════════════════════

def test_recalc_phase_score_writes_subscores_and_total(app):
    """P2-1: sub-scores are bucketed by category and total is weighted."""
    from flaskr.service.learning_portal.models import (
        LearnerChecklistItem,
        LearnerMentorship,
        LearnerProfile,
        MentorshipChecklist,
        MentorshipPhase,
    )
    from flaskr.service.learning_portal.routes import _recalc_phase_score

    learner_bid = "usr-p21-lp"
    phase_bid = "ph-p21-01"
    rec_bid = "rec-p21-01"
    with app.app_context():
        _reset_p2_tables(app)
        db.session.add(
            LearnerProfile(
                learner_bid=learner_bid,
                user_bid=learner_bid,
                employee_no="P21LP",
                department="销售本部",
                coach_bid="usr-p21-coach",
                status="active",
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.add(
            MentorshipPhase(
                phase_bid=phase_bid,
                name="P2 Phase",
                code="phase_p21",
                theory_weight=0.40,
                practice_weight=0.30,
                review_weight=0.20,
                mentor_weight=0.10,
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.add(
            LearnerMentorship(
                record_bid=rec_bid,
                learner_bid=learner_bid,
                phase_bid=phase_bid,
                status="in_progress",
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        # checklist templates: exam + theory → theory bucket, practice, review
        for itm, cat in [
            ("itm-p21-t1", "exam"),
            ("itm-p21-t2", "theory"),
            ("itm-p21-p1", "practice"),
            ("itm-p21-r1", "review"),
        ]:
            db.session.add(
                MentorshipChecklist(
                    item_bid=itm,
                    phase_bid=phase_bid,
                    name=itm,
                    category=cat,
                    max_score=5.00,
                    created_at=datetime(2026, 1, 1),
                    updated_at=datetime(2026, 1, 1),
                )
            )
        # scored items: theory 4 & 5 → 4.5, practice 3 → 3.0, review 5 → 5.0
        for bid, score in [
            ("itm-p21-t1", 4),
            ("itm-p21-t2", 5),
            ("itm-p21-p1", 3),
            ("itm-p21-r1", 5),
        ]:
            db.session.add(
                LearnerChecklistItem(
                    record_bid="lci-" + bid,
                    learner_bid=learner_bid,
                    item_bid=bid,
                    score=score,
                    status="scored",
                    scored_at=datetime(2026, 1, 2),
                    created_at=datetime(2026, 1, 2),
                    updated_at=datetime(2026, 1, 2),
                )
            )
        db.session.commit()

        _recalc_phase_score(learner_bid)

        rec = LearnerMentorship.query.get(rec_bid)
        assert float(rec.theory_score) == 4.5, rec.theory_score
        assert float(rec.practice_score) == 3.0, rec.practice_score
        assert float(rec.peer_review_score) == 5.0, rec.peer_review_score
        assert rec.coach_score is None, rec.coach_score
        # total = 4.5*0.4 + 3.0*0.3 + 5.0*0.2 + 0*0.1 = 1.8+0.9+1.0 = 3.7
        assert float(rec.total_score) == 3.7, rec.total_score


def test_recalc_phase_score_falls_back_to_stored_coach_score(app):
    """P2-1: coach_score falls back to the value already on the coaching row."""
    from flaskr.service.learning_portal.models import (
        LearnerMentorship,
        LearnerProfile,
        MentorshipPhase,
    )
    from flaskr.service.learning_portal.routes import _recalc_phase_score

    learner_bid = "usr-p21b-lp"
    phase_bid = "ph-p21b-01"
    rec_bid = "rec-p21b-01"
    with app.app_context():
        _reset_p2_tables(app)
        db.session.add(
            LearnerProfile(
                learner_bid=learner_bid,
                user_bid=learner_bid,
                employee_no="P21BLP",
                department="销售本部",
                coach_bid="usr-p21b-coach",
                status="active",
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.add(
            MentorshipPhase(
                phase_bid=phase_bid,
                name="P2B",
                code="phase_p21b",
                theory_weight=0.4,
                practice_weight=0.3,
                review_weight=0.2,
                mentor_weight=0.1,
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.add(
            LearnerMentorship(
                record_bid=rec_bid,
                learner_bid=learner_bid,
                phase_bid=phase_bid,
                status="in_progress",
                coach_score=5.0,  # explicit coach score, no mentor-category items
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.commit()

        _recalc_phase_score(learner_bid)

        rec = LearnerMentorship.query.get(rec_bid)
        assert rec.coach_score is not None and float(rec.coach_score) == 5.0
        # total = 5.0*0.1 = 0.5
        assert float(rec.total_score) == 0.5, rec.total_score


def test_score_endpoint_recalculates_total(app, test_client):
    """P2-1 e2e: scoring a submitted item recomputes the phase total."""
    from flaskr.service.learning_portal.models import (
        LearnerChecklistItem,
        LearnerMentorship,
        LearnerProfile,
        MentorshipChecklist,
        MentorshipPhase,
    )

    coach_bid = "usr-p21c-coach"
    learner_bid = "usr-p21c-lp"
    phase_bid = "ph-p21c-01"
    rec_bid = "rec-p21c-01"
    item_bid = "itm-p21c-t1"
    with app.app_context():
        _reset_p2_tables(app)
        _create_user(user_bid=coach_bid, nickname="P2C Coach")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")
        db.session.add(
            LearnerProfile(
                learner_bid=learner_bid,
                user_bid=learner_bid,
                employee_no="P21CLP",
                department="培训部",
                coach_bid=coach_bid,
                status="active",
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.add(
            MentorshipPhase(
                phase_bid=phase_bid,
                name="P2C",
                code="phase_p21c",
                theory_weight=0.4,
                practice_weight=0.3,
                review_weight=0.2,
                mentor_weight=0.1,
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.add(
            LearnerMentorship(
                record_bid=rec_bid,
                learner_bid=learner_bid,
                phase_bid=phase_bid,
                status="in_progress",
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.add(
            MentorshipChecklist(
                item_bid=item_bid,
                phase_bid=phase_bid,
                name="T1",
                category="exam",
                max_score=5.00,
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.add(
            LearnerChecklistItem(
                record_bid="lci-" + item_bid,
                learner_bid=learner_bid,
                item_bid=item_bid,
                status="submitted",
                submitted_at=datetime(2026, 1, 2),
                created_at=datetime(2026, 1, 2),
                updated_at=datetime(2026, 1, 2),
            )
        )
        db.session.commit()
        token = generate_token(app, coach_bid)

    resp = test_client.post(
        f"/api/portal/mentorship/items/lci-{item_bid}/score",
        json={"score": 4},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload

    with app.app_context():
        rec = LearnerMentorship.query.get(rec_bid)
        assert float(rec.theory_score) == 4.0, rec.theory_score
        # total = 4.0*0.4 = 1.6
        assert float(rec.total_score) == 1.6, rec.total_score


# ═══════════════════════════════════════════════════════════════════
# P2-2 · admin/learners PUT/POST guards (is_operator → manage_users)
# ═══════════════════════════════════════════════════════════════════

def test_admin_learners_put_post_denies_learner(app, test_client):
    """P2-2: learner (no manage_users) is 403 on PUT & POST admin/learners."""
    from flaskr.service.learning_portal.models import LearnerProfile

    learner_bid = "usr-p22-learner"
    target_bid = "usr-p22-target"
    with app.app_context():
        _create_user(user_bid=learner_bid, nickname="P2 Learner")
        _create_user(user_bid=target_bid, nickname="P2 Target")
        _ensure_coach_tables(app)
        _assign_role(app, learner_bid, "role-learner")
        db.session.add(
            LearnerProfile(
                learner_bid=target_bid,
                user_bid=target_bid,
                employee_no="P22T",
                department="销售本部",
                status="active",
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.commit()
        token = generate_token(app, learner_bid)

    resp = test_client.put(
        f"/api/portal/admin/learners/{target_bid}",
        json={"department": "销售本部"},
        headers={"Token": token},
    )
    assert resp.get_json(force=True)["code"] == 403

    resp = test_client.post(
        "/api/portal/admin/learners",
        json={"user_bid": "usr-p22-new"},
        headers={"Token": token},
    )
    assert resp.get_json(force=True)["code"] == 403


def test_admin_learners_put_post_allows_hr(app, test_client):
    """P2-2: hr (manage_users) may update & create learners."""
    from flaskr.service.learning_portal.models import LearnerProfile

    hr_bid = "usr-p22-hr"
    target_bid = "usr-p22-tgt2"
    with app.app_context():
        _reset_p2_tables(app)
        _create_user(user_bid=hr_bid, nickname="P2 HR")
        _create_user(user_bid=target_bid, nickname="P2 Target2")
        _ensure_coach_tables(app)
        _assign_role(app, hr_bid, "role-hr")
        db.session.add(
            LearnerProfile(
                learner_bid=target_bid,
                user_bid=target_bid,
                employee_no="P22T2",
                department="人事课",
                status="active",
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.commit()
        token = generate_token(app, hr_bid)

    resp = test_client.put(
        f"/api/portal/admin/learners/{target_bid}",
        json={"department": "人事课2"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload

    resp = test_client.post(
        "/api/portal/admin/learners",
        json={"user_bid": "usr-p22-newhr"},
        headers={"Token": token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload


# ═══════════════════════════════════════════════════════════════════
# P2-3 · logout
# ═══════════════════════════════════════════════════════════════════

def test_logout_revokes_token(app, test_client):
    """P2-3: POST /api/user/logout revokes the token (DB row gone, auth fails)."""
    user_bid = "usr-p23-user"
    with app.app_context():
        _create_user(user_bid=user_bid, nickname="P2 Logout")
        db.session.commit()
        token = generate_token(app, user_bid)

        from flaskr.service.user.models import UserToken

        assert UserToken.query.filter_by(token=token).count() >= 1

    resp = test_client.post("/api/user/logout", headers={"Token": token})
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload

    with app.app_context():
        from flaskr.service.user.models import UserToken

        assert UserToken.query.filter_by(token=token).count() == 0

    # The revoked token can no longer reach a protected endpoint.
    resp = test_client.get("/api/portal/permissions", headers={"Token": token})
    payload = resp.get_json(force=True)
    # token revoked server-side -> no longer valid (Token Expired).
    assert payload["code"] == 1005, payload


# ═══════════════════════════════════════════════════════════════════
# P2-4 · ORM mappings
# ═══════════════════════════════════════════════════════════════════

def test_coach_session_and_profile_orm_mapping(app):
    """P2-4: CoachSession / CoachProfile map to the real tables & support CRUD."""
    from flaskr.service.learning_portal.models import CoachProfile, CoachSession

    assert CoachSession.__tablename__ == "coach_sessions"
    assert CoachProfile.__tablename__ == "coach_profiles"
    # Real column is `mentor_bid` (SHOW COLUMNS verified), not `coach_bid`.
    assert hasattr(CoachSession, "mentor_bid")
    assert hasattr(CoachSession, "learner_bid")
    assert hasattr(CoachProfile, "specialties")
    assert hasattr(CoachProfile, "max_students")

    with app.app_context():
        # Create the mapped tables for this session DB if not yet present.
        db.create_all()
        s = CoachSession(
            session_bid="sess-p24-1",
            learner_bid="usr-p24-lp",
            mentor_bid="usr-p24-coach",
            session_type="regular",
            session_date=datetime(2026, 1, 1),
            status="completed",
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
        db.session.add(s)
        db.session.commit()
        got = CoachSession.query.get("sess-p24-1")
        assert got is not None
        assert got.mentor_bid == "usr-p24-coach"
        db.session.delete(got)
        db.session.commit()
