"""Tests for W3 task 1 — phase auto-advance (learning_portal.phase_auto_advance).

Covers, against the real Flask app + SQLite:
- a completed phase advances to the next active phase (in_progress)
- re-runs are idempotent (no duplicate phase records)
- no next phase → whole chain finished (notification sent)
- learners with no completed record are skipped
- multiple learners advance independently
- an already-assigned next phase is never duplicated
- the beat schedule registers the new task
"""

from __future__ import annotations

from datetime import datetime

import pytest

from flaskr.dao import db
from flaskr.service.learning_portal.models import (
    LearnerProfile,
    LearnerMentorship,
    MentorshipPhase,
    TaskNotification,
)
from flaskr.service.learning_portal.tasks import advance_completed_phases


@pytest.fixture(autouse=True)
def _no_wecom(monkeypatch):
    """Never reach the real WeCom side-channel from tests."""
    monkeypatch.setattr(
        "flaskr.service.learning_portal.tasks.push_wecom_notification",
        lambda **kwargs: True,
    )


@pytest.fixture(autouse=True)
def _clean_learning_tables(app):
    """The SQLite ``app`` fixture is session-scoped — wipe rows between tests.

    Without this, a phase/learner/record created by one test survives into the
    next, causing primary-key collisions on the shared database file.
    """
    with app.app_context():
        for model in (
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


def _add_learner(learner_bid, user_bid):
    db.session.add(
        LearnerProfile(
            learner_bid=learner_bid,
            user_bid=user_bid,
            status="active",
            created_at=datetime(2026, 7, 1),
            updated_at=datetime(2026, 7, 1),
        )
    )


def _add_coaching(
    record_bid, learner_bid, phase_bid, status, started_at, completed_at=None
):
    db.session.add(
        LearnerMentorship(
            record_bid=record_bid,
            learner_bid=learner_bid,
            phase_bid=phase_bid,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            created_at=started_at,
            updated_at=datetime(2026, 7, 1),
        )
    )


def _records(learner_bid):
    return (
        LearnerMentorship.query.filter_by(learner_bid=learner_bid)
        .order_by(LearnerMentorship.started_at.asc())
        .all()
    )


def test_advance_completed_phase_creates_next_in_progress(app):
    with app.app_context():
        _add_phase("ph-000", "ph-000", 0)
        _add_phase("ph-001", "ph-001", 1)
        _add_learner("ln-adv", "usr-adv")
        _add_coaching(
            "rec-1", "ln-adv", "ph-000", "completed",
            datetime(2026, 7, 1, 9), datetime(2026, 7, 18, 18),
        )
        db.session.commit()

        result = advance_completed_phases()

        assert result == {"advanced": 1, "finished": 0, "skipped": 0}
        rows = _records("ln-adv")
        assert len(rows) == 2
        nxt = rows[-1]
        assert nxt.phase_bid == "ph-001"
        assert nxt.status == "in_progress"
        assert nxt.started_at is not None
        notif = TaskNotification.query.filter_by(
            user_bid="usr-adv", notif_type="phase_advance"
        ).first()
        assert notif is not None


def test_rerun_is_idempotent(app):
    with app.app_context():
        _add_phase("ph-000", "ph-000", 0)
        _add_phase("ph-001", "ph-001", 1)
        _add_learner("ln-idem", "usr-idem")
        _add_coaching(
            "rec-1", "ln-idem", "ph-000", "completed",
            datetime(2026, 7, 1, 9), datetime(2026, 7, 18, 18),
        )
        db.session.commit()

        first = advance_completed_phases()
        second = advance_completed_phases()

        assert first["advanced"] == 1
        assert second["advanced"] == 0
        assert second["skipped"] == 1
        assert len(_records("ln-idem")) == 2  # no third record


def test_no_next_phase_marks_chain_finished(app):
    with app.app_context():
        _add_phase("ph-000", "ph-000", 0)  # single phase in the chain
        _add_learner("ln-end", "usr-end")
        _add_coaching(
            "rec-1", "ln-end", "ph-000", "completed",
            datetime(2026, 7, 1, 9), datetime(2026, 7, 18, 18),
        )
        db.session.commit()

        result = advance_completed_phases()

        assert result["finished"] == 1
        assert len(_records("ln-end")) == 1  # nothing created
        notif = TaskNotification.query.filter_by(
            user_bid="usr-end", notif_type="phase_complete"
        ).first()
        assert notif is not None


def test_in_progress_learner_skipped(app):
    with app.app_context():
        _add_phase("ph-000", "ph-000", 0)
        _add_phase("ph-001", "ph-001", 1)
        _add_learner("ln-run", "usr-run")
        _add_coaching(
            "rec-1", "ln-run", "ph-001", "in_progress",
            datetime(2026, 7, 20, 9),
        )
        db.session.commit()

        result = advance_completed_phases()

        assert result["skipped"] == 1
        assert len(_records("ln-run")) == 1


def test_multiple_learners_advance_independently(app):
    with app.app_context():
        _add_phase("ph-000", "ph-000", 0)
        _add_phase("ph-001", "ph-001", 1)
        _add_learner("ln-m1", "usr-m1")
        _add_learner("ln-m2", "usr-m2")
        _add_coaching(
            "rec-m1", "ln-m1", "ph-000", "completed",
            datetime(2026, 7, 1, 9), datetime(2026, 7, 18, 18),
        )
        _add_coaching(
            "rec-m2", "ln-m2", "ph-000", "completed",
            datetime(2026, 7, 2, 9), datetime(2026, 7, 19, 18),
        )
        db.session.commit()

        result = advance_completed_phases()

        assert result["advanced"] == 2
        assert [r.phase_bid for r in _records("ln-m1")] == ["ph-000", "ph-001"]
        assert [r.phase_bid for r in _records("ln-m2")] == ["ph-000", "ph-001"]


def test_assigned_next_phase_never_duplicated(app):
    with app.app_context():
        _add_phase("ph-000", "ph-000", 0)
        _add_phase("ph-001", "ph-001", 1)
        _add_learner("ln-dup", "usr-dup")
        _add_coaching(
            "rec-1", "ln-dup", "ph-000", "completed",
            datetime(2026, 7, 1, 9), datetime(2026, 7, 18, 18),
        )
        _add_coaching(
            "rec-2", "ln-dup", "ph-001", "pending",
            datetime(2026, 7, 20, 9),
        )
        db.session.commit()

        result = advance_completed_phases()

        # newest non-completed record (ph-001 pending) is current → skipped
        assert result["skipped"] == 1
        assert len(_records("ln-dup")) == 2  # no duplicate ph-001


def test_beat_schedule_registers_phase_auto_advance():
    from flaskr.common.celery_app import _build_portal_beat_schedule

    schedule = _build_portal_beat_schedule()
    assert "learning_portal.phase_auto_advance.schedule" in schedule
    entry = schedule["learning_portal.phase_auto_advance.schedule"]
    assert entry["task"] == "learning_portal.phase_auto_advance"
    assert entry["schedule"] is not None


def test_celery_task_runs_end_to_end(app):
    with app.app_context():
        _add_phase("ph-000", "ph-000", 0)
        _add_phase("ph-001", "ph-001", 1)
        _add_learner("ln-task", "usr-task")
        _add_coaching(
            "rec-1", "ln-task", "ph-000", "completed",
            datetime(2026, 7, 1, 9), datetime(2026, 7, 18, 18),
        )
        db.session.commit()

        from flaskr.service.learning_portal.tasks import phase_auto_advance

        out = phase_auto_advance()
        assert "advanced=1" in out
