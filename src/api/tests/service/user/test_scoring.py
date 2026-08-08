"""W3 task 3 — scoring interface regression tests.

Covers (against the real Flask app + SQLite, via test_client / direct calls):
- weighted total_score (theory 0.4 / practice 0.3 / review 0.2 / coach 0.1)
- score=0 is a real grade (regression: `float(score) if score else None` bug)
- score bounds (0..max_score) / NaN / non-numeric rejection
- duplicate scoring rejected (item must be `submitted`)
- permission: non-mentored coach 403, admin exception, learner 403
- scoring does NOT prematurely complete the phase (three-state gate owns it)
- full chain: score → three-state (sign/sync/improvement) → completed → advance
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text

from flaskr.dao import db
from flaskr.service.user.models import UserInfo as UserEntity
from flaskr.service.user.utils import generate_token

_ROLE_INSERT_SQL = """
INSERT OR REPLACE INTO coach_roles (role_bid, name, permissions, is_active) VALUES
('role-admin',     'admin', '["all"]', 1),
('role-coach',     'coach', '["coach:read","coach:write","learner:read","view_all_students","score","edit_summary","create_session","view_any_report","confirm_checklist","view_kpi","custom_dashboard","view_own_report"]', 1),
('role-learner',   'learner', '["learner:read","learner:write","view_own_report"]', 1)
"""


def _create_user(
    *,
    user_bid: str,
    nickname: str = "Test User",
    is_operator: bool = False,
) -> UserEntity:
    user = UserEntity(
        user_bid=user_bid,
        user_identify=f"{user_bid}@example.com",
        nickname=nickname,
        language="zh-CN",
        state=1,
        is_creator=0,
        is_operator=1 if is_operator else 0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.session.add(user)
    return user


def _ensure_coach_tables(app):
    """Create coach_roles / user_role_assignments and seed the roles."""
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


def _reset_scoring_tables(app):
    """Isolate the shared session-scoped tables for scoring tests."""
    from flaskr.service.learning_portal.models import (
        LearnerChecklistItem,
        LearnerMentorship,
        LearnerProfile,
        MentorshipChecklist,
        MentorshipPhase,
        ChecklistImprovement,
    )

    ChecklistImprovement.query.delete()
    LearnerChecklistItem.query.delete()
    LearnerMentorship.query.delete()
    MentorshipChecklist.query.delete()
    MentorshipPhase.query.delete()
    LearnerProfile.query.delete()
    db.session.commit()


def _seed_phase(
    app,
    *,
    learner_bid: str,
    coach_bid: str,
    record_bid: str,
    phase_bid: str,
    items: list[tuple[str, str, float]],
    weights=(0.4, 0.3, 0.2, 0.1),
    record_status="in_progress",
    item_status="submitted",
):
    """Seed learner + phase + checklist templates + one checklist item each.

    ``items`` is a list of ``(item_bid, category, max_score)``. The learner's
    checklist items are created in ``submitted`` state so the scoring endpoint
    can act on them.
    """
    from flaskr.service.learning_portal.models import (
        LearnerChecklistItem,
        LearnerMentorship,
        LearnerProfile,
        MentorshipChecklist,
        MentorshipPhase,
    )

    tw, pw, rw, mw = weights
    db.session.add(
        LearnerProfile(
            learner_bid=learner_bid,
            user_bid=learner_bid,
            employee_no="W3S",
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
            name="W3S Phase",
            code="phase_w3s",
            theory_weight=tw,
            practice_weight=pw,
            review_weight=rw,
            mentor_weight=mw,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
    )
    db.session.add(
        LearnerMentorship(
            record_bid=record_bid,
            learner_bid=learner_bid,
            phase_bid=phase_bid,
            status=record_status,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
    )
    for item_bid, category, max_score in items:
        db.session.add(
            MentorshipChecklist(
                item_bid=item_bid,
                phase_bid=phase_bid,
                name=item_bid,
                category=category,
                max_score=max_score,
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        db.session.add(
            LearnerChecklistItem(
                record_bid=f"lci-{item_bid}",
                learner_bid=learner_bid,
                item_bid=item_bid,
                status=item_status,
                submitted_at=datetime(2026, 1, 2),
                created_at=datetime(2026, 1, 2),
                updated_at=datetime(2026, 1, 2),
            )
        )
    db.session.commit()


def _score(app, test_client, record_bid, score, token):
    return test_client.post(
        f"/api/portal/mentorship/items/{record_bid}/score",
        json={"score": score},
        headers={"Token": token},
    )


def _get_record(record_bid):
    from flaskr.service.learning_portal.models import LearnerMentorship

    return LearnerMentorship.query.get(record_bid)


# ═══════════════════════════════════════════════════════════════════
# 权重计算（theory 0.4 / practice 0.3 / review 0.2 / coach 0.1）
# ═══════════════════════════════════════════════════════════════════


def test_score_full_weighted_total(app, test_client):
    """theory=4, practice=3, review=5, coach=2 → 4*0.4+3*0.3+5*0.2+2*0.1 = 3.7."""
    from flaskr.service.learning_portal.models import LearnerChecklistItem

    coach_bid = "usr-w3s-coach"
    learner_bid = "usr-w3s-lp"
    phase_bid = "ph-w3s-01"
    rec_bid = "rec-w3s-01"
    with app.app_context():
        _reset_scoring_tables(app)
        _create_user(user_bid=coach_bid, nickname="W3S Coach")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")
        _seed_phase(
            app,
            learner_bid=learner_bid,
            coach_bid=coach_bid,
            record_bid=rec_bid,
            phase_bid=phase_bid,
            items=[
                ("itm-t1", "theory", 5.0),
                ("itm-p1", "practice", 5.0),
                ("itm-r1", "review", 5.0),
                ("itm-m1", "mentor", 5.0),
            ],
        )
        token = generate_token(app, coach_bid)

    for item_bid, score in [
        ("itm-t1", 4),
        ("itm-p1", 3),
        ("itm-r1", 5),
        ("itm-m1", 2),
    ]:
        resp = _score(app, test_client, f"lci-{item_bid}", score, token)
        payload = resp.get_json(force=True)
        assert payload["code"] == 0, payload

    with app.app_context():
        rec = _get_record(rec_bid)
        assert float(rec.theory_score) == 4.0
        assert float(rec.practice_score) == 3.0
        assert float(rec.peer_review_score) == 5.0
        assert float(rec.coach_score) == 2.0
        # 4*0.4 + 3*0.3 + 5*0.2 + 2*0.1 = 1.6 + 0.9 + 1.0 + 0.2 = 3.7
        assert float(rec.total_score) == 3.7, rec.total_score


# ═══════════════════════════════════════════════════════════════════
# score=0 回归：0 是合法评分，不能丢成 None
# ═══════════════════════════════════════════════════════════════════


def test_score_zero_is_a_real_grade(app, test_client):
    from flaskr.service.learning_portal.models import LearnerChecklistItem

    coach_bid = "usr-w3s0-coach"
    learner_bid = "usr-w3s0-lp"
    phase_bid = "ph-w3s0-01"
    rec_bid = "rec-w3s0-01"
    with app.app_context():
        _reset_scoring_tables(app)
        _create_user(user_bid=coach_bid, nickname="W3S0 Coach")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")
        _seed_phase(
            app,
            learner_bid=learner_bid,
            coach_bid=coach_bid,
            record_bid=rec_bid,
            phase_bid=phase_bid,
            items=[("itm-z1", "theory", 5.0)],
        )
        token = generate_token(app, coach_bid)

    resp = _score(app, test_client, "lci-itm-z1", 0, token)
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload

    with app.app_context():
        item = LearnerChecklistItem.query.get("lci-itm-z1")
        assert item.score is not None, "score=0 must be stored, not None"
        assert float(item.score) == 0.0
        assert item.status == "scored"
        rec = _get_record(rec_bid)
        # total = 0.0 * 0.4 = 0.0
        assert float(rec.total_score) == 0.0


# ═══════════════════════════════════════════════════════════════════
# 评分边界：越界 / NaN / 非数字拒绝
# ═══════════════════════════════════════════════════════════════════


def test_score_bounds_rejected(app, test_client):
    coach_bid = "usr-w3sb-coach"
    learner_bid = "usr-w3sb-lp"
    phase_bid = "ph-w3sb-01"
    rec_bid = "rec-w3sb-01"
    with app.app_context():
        _reset_scoring_tables(app)
        _create_user(user_bid=coach_bid, nickname="W3SB Coach")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")
        _seed_phase(
            app,
            learner_bid=learner_bid,
            coach_bid=coach_bid,
            record_bid=rec_bid,
            phase_bid=phase_bid,
            items=[("itm-b1", "theory", 5.0)],
        )
        token = generate_token(app, coach_bid)

    # negative
    payload = _score(app, test_client, "lci-itm-b1", -1, token).get_json(force=True)
    assert payload["code"] == 2001, payload
    # above max_score
    payload = _score(app, test_client, "lci-itm-b1", 6, token).get_json(force=True)
    assert payload["code"] == 2001, payload
    # non-numeric
    payload = _score(app, test_client, "lci-itm-b1", "abc", token).get_json(force=True)
    assert payload["code"] == 2001, payload
    # NaN (JSON-safe string that float() parses)
    payload = _score(app, test_client, "lci-itm-b1", "nan", token).get_json(force=True)
    assert payload["code"] == 2001, payload

    # a valid in-range score still works after all the rejections
    resp = _score(app, test_client, "lci-itm-b1", 5, token)
    assert resp.get_json(force=True)["code"] == 0


def test_score_upper_bound_is_max_score(app, test_client):
    """A template with max_score=3 accepts 3 and rejects 4."""
    coach_bid = "usr-w3su-coach"
    learner_bid = "usr-w3su-lp"
    phase_bid = "ph-w3su-01"
    rec_bid = "rec-w3su-01"
    with app.app_context():
        _reset_scoring_tables(app)
        _create_user(user_bid=coach_bid, nickname="W3SU Coach")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")
        _seed_phase(
            app,
            learner_bid=learner_bid,
            coach_bid=coach_bid,
            record_bid=rec_bid,
            phase_bid=phase_bid,
            items=[("itm-u1", "theory", 3.0)],
        )
        token = generate_token(app, coach_bid)

    payload = _score(app, test_client, "lci-itm-u1", 4, token).get_json(force=True)
    assert payload["code"] == 2001, payload
    resp = _score(app, test_client, "lci-itm-u1", 3, token)
    assert resp.get_json(force=True)["code"] == 0, resp.get_json(force=True)


# ═══════════════════════════════════════════════════════════════════
# 重复评分：已 scored 项不能再评
# ═══════════════════════════════════════════════════════════════════


def test_duplicate_score_rejected(app, test_client):
    from flaskr.service.learning_portal.models import LearnerChecklistItem

    coach_bid = "usr-w3sd-coach"
    learner_bid = "usr-w3sd-lp"
    phase_bid = "ph-w3sd-01"
    rec_bid = "rec-w3sd-01"
    with app.app_context():
        _reset_scoring_tables(app)
        _create_user(user_bid=coach_bid, nickname="W3SD Coach")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")
        _seed_phase(
            app,
            learner_bid=learner_bid,
            coach_bid=coach_bid,
            record_bid=rec_bid,
            phase_bid=phase_bid,
            items=[("itm-d1", "theory", 5.0)],
        )
        token = generate_token(app, coach_bid)

    resp = _score(app, test_client, "lci-itm-d1", 4, token)
    assert resp.get_json(force=True)["code"] == 0

    # second POST on the same item → already scored
    resp = _score(app, test_client, "lci-itm-d1", 5, token)
    payload = resp.get_json(force=True)
    assert payload["code"] == 2001, payload

    with app.app_context():
        item = LearnerChecklistItem.query.get("lci-itm-d1")
        # original score preserved
        assert float(item.score) == 4.0


# ═══════════════════════════════════════════════════════════════════
# 权限：非带教 coach 403 / admin 例外 / learner 403
# ═══════════════════════════════════════════════════════════════════


def test_score_denies_non_mentored_coach(app, test_client):
    coach_bid = "usr-w3sp-coach"
    learner_bid = "usr-w3sp-lp"
    phase_bid = "ph-w3sp-01"
    rec_bid = "rec-w3sp-01"
    with app.app_context():
        _reset_scoring_tables(app)
        _create_user(user_bid=coach_bid, nickname="W3SP Coach")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")
        # learner is mentored by a different coach
        _seed_phase(
            app,
            learner_bid=learner_bid,
            coach_bid="usr-other-coach",
            record_bid=rec_bid,
            phase_bid=phase_bid,
            items=[("itm-p1", "theory", 5.0)],
        )
        token = generate_token(app, coach_bid)

    resp = _score(app, test_client, "lci-itm-p1", 4, token)
    assert resp.get_json(force=True)["code"] == 403


def test_score_denies_learner(app, test_client):
    learner_bid = "usr-w3sl-learner"
    phase_bid = "ph-w3sl-01"
    rec_bid = "rec-w3sl-01"
    with app.app_context():
        _reset_scoring_tables(app)
        _create_user(user_bid=learner_bid, nickname="W3SL Learner")
        _ensure_coach_tables(app)
        _assign_role(app, learner_bid, "role-learner")
        # learner is NOT their own coach (coach_bid points elsewhere)
        _seed_phase(
            app,
            learner_bid=learner_bid,
            coach_bid="usr-w3sl-coach",
            record_bid=rec_bid,
            phase_bid=phase_bid,
            items=[("itm-l1", "theory", 5.0)],
        )
        token = generate_token(app, learner_bid)

    resp = _score(app, test_client, "lci-itm-l1", 4, token)
    assert resp.get_json(force=True)["code"] == 403


def test_score_admin_exception(app, test_client):
    admin_bid = "usr-w3sa-admin"
    learner_bid = "usr-w3sa-lp"
    phase_bid = "ph-w3sa-01"
    rec_bid = "rec-w3sa-01"
    with app.app_context():
        _reset_scoring_tables(app)
        _create_user(user_bid=admin_bid, is_operator=True, nickname="W3SA Admin")
        _ensure_coach_tables(app)
        _assign_role(app, admin_bid, "role-admin")
        _seed_phase(
            app,
            learner_bid=learner_bid,
            coach_bid="usr-other-coach",
            record_bid=rec_bid,
            phase_bid=phase_bid,
            items=[("itm-a1", "theory", 5.0)],
        )
        token = generate_token(app, admin_bid)

    resp = _score(app, test_client, "lci-itm-a1", 4, token)
    assert resp.get_json(force=True)["code"] == 0


# ═══════════════════════════════════════════════════════════════════
# 评分不擅自完成阶段（completed 由三态合规门控制）
# ═══════════════════════════════════════════════════════════════════


def test_scoring_does_not_prematurely_complete_phase(app, test_client):
    coach_bid = "usr-w3sc-coach"
    learner_bid = "usr-w3sc-lp"
    phase_bid = "ph-w3sc-01"
    rec_bid = "rec-w3sc-01"
    with app.app_context():
        _reset_scoring_tables(app)
        _create_user(user_bid=coach_bid, nickname="W3SC Coach")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")
        _seed_phase(
            app,
            learner_bid=learner_bid,
            coach_bid=coach_bid,
            record_bid=rec_bid,
            phase_bid=phase_bid,
            items=[("itm-c1", "theory", 5.0)],
        )
        token = generate_token(app, coach_bid)

    resp = _score(app, test_client, "lci-itm-c1", 4, token)
    assert resp.get_json(force=True)["code"] == 0

    with app.app_context():
        rec = _get_record(rec_bid)
        # scoring alone must NOT flip the phase to completed — the three-state
        # compliance gate (sign + sync + improvement) owns that transition.
        assert rec.status == "in_progress", rec.status
        assert rec.completed_at is None


# ═══════════════════════════════════════════════════════════════════
# 全链路：评分 + 三态 → completed → 推进到下一阶段
# ═══════════════════════════════════════════════════════════════════


def test_scoring_then_three_state_completes_and_advances(app, test_client):
    """score → (improvement done) → sign + sync → completed → auto-advance."""
    from flaskr.service.learning_portal.tasks import advance_completed_phases

    coach_bid = "usr-w3se-coach"
    learner_bid = "usr-w3se-lp"
    phase_bid = "ph-w3se-01"
    next_phase_bid = "ph-w3se-02"
    rec_bid = "rec-w3se-01"
    with app.app_context():
        _reset_scoring_tables(app)
        _create_user(user_bid=coach_bid, nickname="W3SE Coach")
        _create_user(user_bid=learner_bid, nickname="W3SE Learner")
        _ensure_coach_tables(app)
        _assign_role(app, coach_bid, "role-coach")
        _assign_role(app, learner_bid, "role-learner")
        _seed_phase(
            app,
            learner_bid=learner_bid,
            coach_bid=coach_bid,
            record_bid=rec_bid,
            phase_bid=phase_bid,
            items=[("itm-e1", "theory", 5.0)],
        )
        # a next phase on the chain (sort_order greater)
        from flaskr.service.learning_portal.models import MentorshipPhase

        db.session.add(
            MentorshipPhase(
                phase_bid=next_phase_bid,
                name="W3SE Next",
                code="phase_w3se_next",
                sort_order=2,
                is_active=1,
                theory_weight=0.4,
                practice_weight=0.3,
                review_weight=0.2,
                mentor_weight=0.1,
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 1, 1),
            )
        )
        # give the current phase a smaller sort_order so the chain is valid
        from sqlalchemy import text as _text

        db.session.execute(
            _text("UPDATE coach_phases SET sort_order=1, is_active=1 WHERE phase_bid=:p"),
            {"p": phase_bid},
        )
        db.session.commit()
        coach_token = generate_token(app, coach_bid)
        learner_token = generate_token(app, learner_bid)

    # 1) score the submitted item
    resp = _score(app, test_client, "lci-itm-e1", 4, coach_token)
    assert resp.get_json(force=True)["code"] == 0

    # 2) three-state: sign (learner) + sync (coach); no improvement items → gate closed
    sign = test_client.post(
        f"/api/coach/checklist/{rec_bid}/sign",
        headers={"Token": learner_token},
    )
    assert sign.get_json(force=True)["code"] == 0
    sync = test_client.post(
        f"/api/coach/checklist/{rec_bid}/sync",
        json={"note": "face-to-face sync"},
        headers={"Token": coach_token},
    )
    assert sync.get_json(force=True)["code"] == 0

    with app.app_context():
        rec = _get_record(rec_bid)
        assert rec.status == "completed", rec.status
        assert rec.completed_at is not None
        assert float(rec.total_score) == 1.6  # 4*0.4

        # 3) phase auto-advance scans completed records → creates the next phase
        result = advance_completed_phases()
        assert result["advanced"] >= 1, result
        from flaskr.service.learning_portal.models import LearnerMentorship

        next_rec = (
            LearnerMentorship.query.filter_by(
                learner_bid=learner_bid, phase_bid=next_phase_bid
            )
            .filter(LearnerMentorship.status.in_(("pending", "in_progress")))
            .first()
        )
        assert next_rec is not None, "auto-advance must create the next phase"
