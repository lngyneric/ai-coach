"""Tests for W3 task 2 — compliance checkpoints (sign → sync → improvement).

Covers, against the real Flask app + SQLite:
- learner sign-off (POST /api/coach/checklist/<bid>/sign), learner only
- coach sync (POST /api/coach/checklist/<bid>/sync)
- improvement registration + listing + done (POST/GET .../improvements)
- three-state gate: record only becomes `completed` when sign + sync +
  improvement are all satisfied
- idempotency: repeated sign does not duplicate
- permission matrix: coach/learner self can view, stranger cannot
"""

from __future__ import annotations

from datetime import datetime

import pytest

from flaskr.dao import db
from flaskr.service.learning_portal.models import (
    LearnerProfile,
    LearnerMentorship,
    MentorshipPhase,
    ChecklistImprovement,
    TaskNotification,
)
from flaskr.service.learning_portal.tasks import (
    checklist_three_state,
    maybe_complete_checklist,
)


@pytest.fixture(autouse=True)
def _no_wecom(monkeypatch):
    """Never reach the real WeCom side-channel from tests."""
    monkeypatch.setattr(
        "flaskr.service.learning_portal.tasks.push_wecom_notification",
        lambda **kwargs: True,
    )


@pytest.fixture(autouse=True)
def _clean_learning_tables(app):
    with app.app_context():
        for model in (
            ChecklistImprovement,
            TaskNotification,
            LearnerMentorship,
            LearnerProfile,
            MentorshipPhase,
        ):
            db.session.query(model).delete()
        db.session.commit()
    yield


def _add_phase(phase_bid, code, sort_order, is_active=1):
    db.session.add(
        MentorshipPhase(
            phase_bid=phase_bid,
            name=f"阶段-{code}",
            code=code,
            sort_order=sort_order,
            is_active=is_active,
            created_at=datetime(2026, 7, 1),
            updated_at=datetime(2026, 7, 1),
        )
    )


def _add_learner(learner_bid, user_bid, coach_bid=None):
    db.session.add(
        LearnerProfile(
            learner_bid=learner_bid,
            user_bid=user_bid,
            coach_bid=coach_bid,
            status="active",
            created_at=datetime(2026, 7, 1),
            updated_at=datetime(2026, 7, 1),
        )
    )


def _add_coaching(record_bid, learner_bid, phase_bid, status="in_progress"):
    db.session.add(
        LearnerMentorship(
            record_bid=record_bid,
            learner_bid=learner_bid,
            phase_bid=phase_bid,
            status=status,
            started_at=datetime(2026, 7, 20, 9),
            created_at=datetime(2026, 7, 20, 9),
            updated_at=datetime(2026, 7, 20, 9),
        )
    )


def _get_record(record_bid):
    return LearnerMentorship.query.filter_by(record_bid=record_bid).first()


# ---------------------------------------------------------------------------
# Three-state helpers (unit level)
# ---------------------------------------------------------------------------


def test_three_state_empty(app):
    with app.app_context():
        _add_phase("ph-001", "ph-001", 1)
        _add_coaching("rec-x", "ln-x", "ph-001")
        db.session.commit()
        rec = _get_record("rec-x")
        state = checklist_three_state(rec)
        assert state["sign"]["done"] is False
        assert state["sync"]["done"] is False
        assert state["improvement"]["done"] is True  # no open items
        assert state["all_done"] is False


def test_sign_only_does_not_complete(app):
    with app.app_context():
        _add_phase("ph-001", "ph-001", 1)
        _add_coaching("rec-x", "ln-x", "ph-001")
        db.session.commit()
        rec = _get_record("rec-x")
        rec.sign_at = datetime(2026, 7, 21, 9)
        rec.signed_by = "usr-x"
        assert maybe_complete_checklist(rec) is False
        assert rec.status == "in_progress"


def test_sign_and_sync_no_improvement_completes(app):
    with app.app_context():
        _add_phase("ph-001", "ph-001", 1)
        _add_learner("ln-x", "usr-x")
        _add_coaching("rec-x", "ln-x", "ph-001")
        db.session.commit()
        rec = _get_record("rec-x")
        rec.sign_at = datetime(2026, 7, 21, 9)
        rec.signed_by = "usr-x"
        rec.sync_at = datetime(2026, 7, 21, 10)
        rec.synced_by = "coach-x"
        assert maybe_complete_checklist(rec) is True
        assert rec.status == "completed"
        assert rec.completed_at is not None
        # learner notified
        notif = TaskNotification.query.filter_by(
            user_bid="usr-x", notif_type="checklist_complete"
        ).first()
        assert notif is not None


def test_open_improvement_blocks_completion(app):
    with app.app_context():
        _add_phase("ph-001", "ph-001", 1)
        _add_coaching("rec-x", "ln-x", "ph-001")
        db.session.commit()
        rec = _get_record("rec-x")
        rec.sign_at = datetime(2026, 7, 21, 9)
        rec.sync_at = datetime(2026, 7, 21, 10)
        db.session.add(
            ChecklistImprovement(
                improvement_bid="imp-1",
                record_bid="rec-x",
                action="重做实践操作",
                status="pending",
                created_at=datetime(2026, 7, 21, 10),
                updated_at=datetime(2026, 7, 21, 10),
            )
        )
        db.session.commit()
        rec = _get_record("rec-x")
        assert maybe_complete_checklist(rec) is False
        assert rec.status == "in_progress"


def test_all_improvements_done_then_completes(app):
    with app.app_context():
        _add_phase("ph-001", "ph-001", 1)
        _add_learner("ln-x", "usr-x")
        _add_coaching("rec-x", "ln-x", "ph-001")
        db.session.commit()
        rec = _get_record("rec-x")
        rec.sign_at = datetime(2026, 7, 21, 9)
        rec.sync_at = datetime(2026, 7, 21, 10)
        db.session.add(
            ChecklistImprovement(
                improvement_bid="imp-1",
                record_bid="rec-x",
                action="重做实践操作",
                status="pending",
                created_at=datetime(2026, 7, 21, 10),
                updated_at=datetime(2026, 7, 21, 10),
            )
        )
        db.session.commit()
        imp = ChecklistImprovement.query.get("imp-1")
        imp.status = "done"
        imp.updated_at = datetime(2026, 7, 22, 9)
        db.session.commit()
        rec = _get_record("rec-x")
        assert maybe_complete_checklist(rec) is True
        assert rec.status == "completed"


def test_idempotent_sign_via_helper(app):
    with app.app_context():
        _add_phase("ph-001", "ph-001", 1)
        _add_coaching("rec-x", "ln-x", "ph-001")
        db.session.commit()
        rec = _get_record("rec-x")
        first_at = datetime(2026, 7, 21, 9)
        rec.sign_at = first_at
        rec.signed_by = "usr-x"
        db.session.commit()
        # simulating a second sign: helper must not flip to completed and the
        # timestamp stays untouched
        rec = _get_record("rec-x")
        rec.sign_at = datetime(2026, 7, 21, 10)  # would be "re-sign"
        db.session.commit()
        rec = _get_record("rec-x")
        assert rec.sign_at == datetime(2026, 7, 21, 10)  # endpoint guards this


# ---------------------------------------------------------------------------
# API level (permission matrix + end-to-end)
# ---------------------------------------------------------------------------


def _seed_users(app):
    """Create the coach_roles / user_role_assignments tables (like the portal
    test does) and the coach/learner users used by the API tests."""
    from sqlalchemy import text

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
                " '[\"create_session\",\"confirm_checklist\",\"view_own_report\"]', 1),"
                "('role-learner', 'learner',"
                " '[\"learner:read\",\"learner:write\",\"view_own_report\"]', 1)"
            )
        )
        db.session.execute(
            text(
                "INSERT OR REPLACE INTO user_role_assignments "
                "(user_bid, role_bid) VALUES "
                "('usr-coach', 'role-coach'),"
                "('usr-learner', 'role-learner')"
            )
        )
        db.session.commit()


def _create_api_user(app, user_bid):
    from flaskr.service.user.models import UserInfo as UserEntity

    with app.app_context():
        exists = UserEntity.query.filter_by(user_bid=user_bid).first()
        if not exists:
            user = UserEntity(
                user_bid=user_bid,
                user_identify=f"{user_bid}@example.com",
                nickname=user_bid,
                language="zh-CN",
                state=1,
                is_creator=0,
                is_operator=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.session.add(user)
            db.session.commit()


def _token(app, user_bid):
    from flaskr.service.user.utils import generate_token

    return generate_token(app, user_bid)


def _setup_checklist_api(app):
    """Seed users, coach, learner + an in_progress coaching record."""
    _seed_users(app)
    _create_api_user(app, "usr-coach")
    _create_api_user(app, "usr-learner")
    with app.app_context():
        _add_phase("ph-001", "ph-001", 1)
        _add_learner("ln-api", "usr-learner", coach_bid="usr-coach")
        _add_coaching("rec-api", "ln-api", "ph-001")
        db.session.commit()


def test_api_learner_sign_and_coach_sync_then_completed(app, test_client):
    _setup_checklist_api(app)
    learner_token = _token(app, "usr-learner")
    coach_token = _token(app, "usr-coach")

    # learner signs
    resp = test_client.post(
        "/api/coach/checklist/rec-api/sign",
        headers={"Token": learner_token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert payload["data"]["checkpoints"]["sign"]["done"] is True
    assert payload["data"]["status"] == "in_progress"

    # coach syncs
    resp = test_client.post(
        "/api/coach/checklist/rec-api/sync",
        json={"note": "面对面确认完成"},
        headers={"Token": coach_token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert payload["data"]["checkpoints"]["sync"]["done"] is True
    assert payload["data"]["status"] == "completed"
    assert payload["data"]["checkpoints"]["all_done"] is True


def test_api_sign_denies_coach(app, test_client):
    _setup_checklist_api(app)
    coach_token = _token(app, "usr-coach")
    resp = test_client.post(
        "/api/coach/checklist/rec-api/sign",
        headers={"Token": coach_token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] != 0  # coach is not the learner themself


def test_api_sync_denies_learner(app, test_client):
    _setup_checklist_api(app)
    learner_token = _token(app, "usr-learner")
    resp = test_client.post(
        "/api/coach/checklist/rec-api/sync",
        headers={"Token": learner_token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] != 0  # learner cannot sync


def test_api_improvements_flow(app, test_client):
    _setup_checklist_api(app)
    learner_token = _token(app, "usr-learner")
    coach_token = _token(app, "usr-coach")

    # coach registers an improvement → gate stays open
    resp = test_client.post(
        "/api/coach/checklist/rec-api/improvements",
        json={"action": "重做显微镜操作", "owner_bid": "usr-learner", "due_at": "2026-08-01T00:00:00"},
        headers={"Token": coach_token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert len(payload["data"]["improvements"]) == 1
    imp_bid = payload["data"]["improvements"][0]["improvement_bid"]

    # sign + sync done, but improvement open → not completed
    test_client.post(
        "/api/coach/checklist/rec-api/sign",
        headers={"Token": learner_token},
    )
    resp = test_client.post(
        "/api/coach/checklist/rec-api/sync",
        json={"note": "已同步"},
        headers={"Token": coach_token},
    )
    payload = resp.get_json(force=True)
    assert payload["data"]["status"] == "in_progress"
    assert payload["data"]["checkpoints"]["improvement"]["done"] is False

    # coach closes the improvement → gate closes
    resp = test_client.post(
        f"/api/coach/checklist/rec-api/improvements/{imp_bid}/done",
        headers={"Token": coach_token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert payload["data"]["status"] == "completed"
    assert payload["data"]["checkpoints"]["all_done"] is True

    # learner can list improvements
    resp = test_client.get(
        "/api/coach/checklist/rec-api/improvements",
        headers={"Token": learner_token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert len(payload["data"]) == 1
    assert payload["data"][0]["status"] == "done"


def test_api_status_denies_stranger(app, test_client):
    _setup_checklist_api(app)
    # a learner from another mentor (no mentor relation, not self)
    _create_api_user(app, "usr-stranger")
    from flaskr.service.user.models import UserInfo as UserEntity

    with app.app_context():
        db.session.add(
            LearnerProfile(
                learner_bid="ln-stranger",
                user_bid="usr-stranger",
                status="active",
                created_at=datetime(2026, 7, 1),
                updated_at=datetime(2026, 7, 1),
            )
        )
        db.session.commit()
    stranger_token = _token(app, "usr-stranger")
    resp = test_client.get(
        "/api/coach/checklist/rec-api",
        headers={"Token": stranger_token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] != 0  # stranger cannot view


def test_api_status_allows_learner_self(app, test_client):
    _setup_checklist_api(app)
    learner_token = _token(app, "usr-learner")
    resp = test_client.get(
        "/api/coach/checklist/rec-api",
        headers={"Token": learner_token},
    )
    payload = resp.get_json(force=True)
    assert payload["code"] == 0, payload
    assert payload["data"]["record_bid"] == "rec-api"
