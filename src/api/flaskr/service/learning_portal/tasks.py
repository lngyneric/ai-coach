"""Learning Portal — Celery scheduled tasks.

Tasks:
- phase_deadline_reminder: Check phase deadlines and notify learners/mentors
- daily_task_push: Daily push of pending tasks at 09:00
- score_reminder: Remind mentors to score submitted items after 48h
- phase_auto_advance: Auto-advance a completed phase to the next one (W3)
- probation_check: Auto-check probation status when all phases completed
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, date

from celery import shared_task
from flaskr.dao import db
from flaskr.service.learning_portal.models import (
    LearnerProfile,
    LearnerMentorship,
    MentorshipPhase,
    LearnerChecklistItem,
    LearnerTask,
    TaskNotification,
    ChecklistImprovement,
)
from flaskr.service.learning_portal.wecom_push import push_wecom_notification

logger = logging.getLogger(__name__)


def _notify(*, user_bid, title, content, notif_type, related_bid=None):
    """Write a TaskNotification row (in-app banner) and fire the W1 WeCom side-channel.

    The DB write is byte-for-byte what the tasks did before; the WeCom push is
    purely additive and must never break the pipeline (push_wecom_notification
    never raises, and we also guard here as a belt-and-suspenders measure).
    """
    notif = TaskNotification(
        notif_bid=__import__("uuid").uuid4().hex,
        user_bid=user_bid,
        title=title,
        content=content,
        notif_type=notif_type,
        related_bid=related_bid,
    )
    db.session.add(notif)
    try:
        push_wecom_notification(
            user_bid=user_bid,
            title=title,
            content=content,
            notif_type=notif_type,
            related_bid=related_bid or "",
        )
    except Exception:  # noqa: BLE001 - side channel must not break the task
        logger.exception("WECOM push failed (non-fatal): user_bid=%s", user_bid)
    return notif


@shared_task(name="learning_portal.phase_deadline_reminder")
def phase_deadline_reminder():
    """Check phase deadlines and send reminders 7/3/1 day before."""
    now = datetime.utcnow()
    active = LearnerMentorship.query.filter_by(status="in_progress").all()

    for rec in active:
        phase = MentorshipPhase.query.get(rec.phase_bid)
        if not phase or not rec.started_at:
            continue

        deadline = rec.started_at + timedelta(days=int(phase.duration_days or 60))
        remaining = (deadline - now).days

        if remaining in (7, 3, 1):
            profile = LearnerProfile.query.get(rec.learner_bid)
            if profile:
                # Card link bid: use the phase's course (shifu) bid when set so
                # the WeCom textcard URL /c/{related_bid} points at a real course;
                # fall back to the coaching record bid (legacy behavior).
                card_bid = (phase.shifu_bid or "").strip() or rec.record_bid
                today = date.today()
                # Dedup within the same day. Use a half-open [today, tomorrow)
                # window instead of created_at == today: the latter binds a DATE
                # and MySQL coerces it to midnight, so real rows (e.g. 08:00)
                # never matched and every run re-sent.
                existing = TaskNotification.query.filter(
                    TaskNotification.user_bid == profile.user_bid,
                    TaskNotification.notif_type == "phase_end",
                    TaskNotification.related_bid == card_bid,
                    TaskNotification.created_at >= today,
                    TaskNotification.created_at < today + timedelta(days=1),
                ).first()
                if not existing:
                    _notify(
                        user_bid=profile.user_bid,
                        title="阶段截止提醒",
                        content=f"你的阶段「{phase.name}」还剩 {remaining} 天",
                        notif_type="phase_end",
                        related_bid=card_bid,
                    )
                    db.session.commit()

    return f"checked {len(active)} active phases"


@shared_task(name="learning_portal.daily_task_push")
def daily_task_push():
    """Push pending task summary to learners every morning."""
    pending = (
        LearnerTask.query.filter_by(status="pending")
        .filter(LearnerTask.due_at != None)
        .order_by(LearnerTask.learner_bid)
        .all()
    )

    by_learner = {}
    for t in pending:
        by_learner.setdefault(t.learner_bid, []).append(t)

    count = 0
    for learner_bid, tasks in by_learner.items():
        profile = LearnerProfile.query.get(learner_bid)
        if not profile:
            continue

        today_due = [t for t in tasks if t.due_at and t.due_at.date() == date.today()]
        overdue = [t for t in tasks if t.due_at and t.due_at.date() < date.today()]

        _notify(
            user_bid=profile.user_bid,
            title="每日学习提醒",
            content=f"今日待办 {len(today_due)} 项，逾期 {len(overdue)} 项",
            notif_type="task_assign",
        )
        count += 1

    db.session.commit()
    return f"pushed to {count} learners"


@shared_task(name="learning_portal.score_reminder")
def score_reminder():
    """Remind mentors to score items submitted more than 48h ago."""
    cutoff = datetime.utcnow() - timedelta(hours=48)
    items = (
        LearnerChecklistItem.query.filter(
            LearnerChecklistItem.status == "submitted",
            LearnerChecklistItem.submitted_at <= cutoff,
        )
        .all()
    )
    reminded = set()
    for item in items:
        profile = LearnerProfile.query.get(item.learner_bid)
        if profile and profile.coach_bid not in reminded:
            _notify(
                user_bid=profile.coach_bid,
                title="评分催办",
                content="学员有待评分项已超过48小时，请及时评分",
                notif_type="score_reminder",
            )
            reminded.add(profile.coach_bid)

    db.session.commit()
    return f"reminded {len(reminded)} mentors"


# ---------------------------------------------------------------------------
# W3 task 1 — phase auto-advance (ph-000 → ph-001 → ...)
# ---------------------------------------------------------------------------


def _find_next_phase(sort_order: int | None):
    """Return the next active phase after ``sort_order`` (ascending), or None.

    ``coach_phases.sort_order`` drives the chain; a phase with a larger
    ``sort_order`` and ``is_active=1`` is the next stage. When none exists the
    learner has completed every phase (probation_check takes over).
    """
    base = sort_order if sort_order is not None else -1
    return (
        MentorshipPhase.query.filter(
            MentorshipPhase.sort_order > base,
            MentorshipPhase.is_active == 1,
        )
        .order_by(MentorshipPhase.sort_order.asc())
        .first()
    )


def advance_completed_phases() -> dict:
    """Scan ``learner_coaching`` and advance each learner one phase ahead.

    Rule (W3): when a learner's current coaching record is ``completed`` and a
    next active phase exists (by ``sort_order``), create the next phase's
    record with ``status=in_progress`` and ``started_at=now``. When no next
    phase exists, the learner has finished the whole chain — send a
    notification and let ``probation_check`` handle probation afterwards.

    Idempotency: after a successful advance the learner always owns an
    ``in_progress`` record, so a re-run treats that as the current phase and
    skips it. A second guard skips when the target phase already has a
    pending/in_progress record (e.g. after a manual re-create).

    Returns ``{"advanced": int, "finished": int, "skipped": int}``.
    """
    logger.info("phase_auto_advance: scanning completed phases")
    now = datetime.utcnow()
    advanced = 0
    finished = 0
    skipped = 0

    learner_rows = (
        db.session.query(LearnerMentorship.learner_bid).distinct().all()
    )
    for (learner_bid,) in learner_rows:
        records = (
            LearnerMentorship.query.filter_by(learner_bid=learner_bid)
            .order_by(
                LearnerMentorship.started_at.asc(),
                LearnerMentorship.created_at.asc(),
            )
            .all()
        )
        if not records:
            continue

        # Current phase = the newest pending/in_progress record; if the learner
        # has none, the newest completed record is the chain head.
        active = [r for r in records if r.status in ("pending", "in_progress")]
        current = active[-1] if active else records[-1]
        if current.status != "completed":
            skipped += 1
            continue

        phase = MentorshipPhase.query.get(current.phase_bid)
        if phase is None:
            skipped += 1
            continue

        next_phase = _find_next_phase(phase.sort_order)
        profile = LearnerProfile.query.get(learner_bid)

        if next_phase is None:
            # Whole chain finished → notify once per day per learner; the
            # learner's records stay 'completed' so a re-run is a no-op here,
            # and probation_check takes over the transition.
            if profile is not None:
                today = date.today()
                already = (
                    TaskNotification.query.filter(
                        TaskNotification.user_bid == profile.user_bid,
                        TaskNotification.notif_type == "phase_complete",
                        TaskNotification.related_bid == current.record_bid,
                        TaskNotification.created_at >= today,
                        TaskNotification.created_at < today
                        + timedelta(days=1),
                    )
                    .first()
                )
                if not already:
                    _notify(
                        user_bid=profile.user_bid,
                        title="阶段全部完成",
                        content="你已完成全部带教阶段，即将进入转正评定",
                        notif_type="phase_complete",
                        related_bid=current.record_bid,
                    )
                    db.session.commit()
            finished += 1
            continue

        # Guard: never create a duplicate pending/in_progress row for a phase.
        duplicate = (
            LearnerMentorship.query.filter_by(
                learner_bid=learner_bid,
                phase_bid=next_phase.phase_bid,
            )
            .filter(LearnerMentorship.status.in_(("pending", "in_progress")))
            .first()
        )
        if duplicate is not None:
            skipped += 1
            continue

        record = LearnerMentorship(
            record_bid=uuid.uuid4().hex,
            learner_bid=learner_bid,
            phase_bid=next_phase.phase_bid,
            status="in_progress",
            started_at=now,
            created_at=now,
            updated_at=now,
        )
        db.session.add(record)
        if profile is not None:
            _notify(
                user_bid=profile.user_bid,
                title="阶段自动推进",
                content=f"你的阶段「{next_phase.name}」已开始，请按时完成学习",
                notif_type="phase_advance",
                related_bid=(next_phase.shifu_bid or "").strip()
                or record.record_bid,
            )
        db.session.commit()
        advanced += 1

    return {"advanced": advanced, "finished": finished, "skipped": skipped}


@shared_task(name="learning_portal.phase_auto_advance")
def phase_auto_advance():
    """W3: auto-advance learners to the next phase (daily 06:30, idempotent).

    Same logic as the manual ``POST /api/coach/phases/advance`` endpoint; both
    call :func:`advance_completed_phases`.
    """
    result = advance_completed_phases()
    return (
        f"advanced={result['advanced']} "
        f"finished={result['finished']} "
        f"skipped={result['skipped']}"
    )


# ---------------------------------------------------------------------------
# W3 task 2 — compliance checkpoints (sign → sync → improvement)
# ---------------------------------------------------------------------------


def checklist_three_state(record) -> dict:
    """Return the three-state compliance progress of a coaching record.

    A ``learner_coaching`` phase only counts as ``completed`` once **all three**
    checkpoints are satisfied (W3 requirement: sign + sync + improvement):

    - ``sign``        — learner confirmed they understand/agree (``sign_at``)
    - ``sync``        — coach held the face-to-face sync (``sync_at``)
    - ``improvement`` — every registered improvement item is done (no open item)

    Idempotent helpers: each checkpoint is set once (timestamp + actor); a
    second POST returns the same state without duplicating work.
    """
    open_items = (
        ChecklistImprovement.query.filter_by(
            record_bid=record.record_bid, status="pending"
        ).count()
        if hasattr(record, "record_bid")
        else 0
    )
    improvement_done = open_items == 0
    return {
        "sign": {
            "done": record.sign_at is not None,
            "at": str(record.sign_at) if record.sign_at else None,
            "by": record.signed_by,
        },
        "sync": {
            "done": record.sync_at is not None,
            "at": str(record.sync_at) if record.sync_at else None,
            "by": record.synced_by,
        },
        "improvement": {
            "done": improvement_done,
            "open_count": open_items,
        },
        "all_done": (
            record.sign_at is not None
            and record.sync_at is not None
            and improvement_done
        ),
    }


def maybe_complete_checklist(record) -> bool:
    """Mark ``record`` completed when all three checkpoints are satisfied.

    Called after every sign / sync / improvement operation (idempotent): when
    the three-state gate finally passes, the coaching record is flipped to
    ``completed`` (``completed_at=now``) and the learner gets an in-app + WeCom
    notification. This is the seam that feeds W3 task 1 — the phase
    auto-advance task only scans ``status == 'completed'`` records.

    Returns True when the record transitioned to completed by this call.
    """
    if record.status == "completed":
        return False
    state = checklist_three_state(record)
    if not state["all_done"]:
        return False

    now = datetime.utcnow()
    record.status = "completed"
    record.completed_at = now
    record.updated_at = now
    db.session.flush()

    profile = LearnerProfile.query.get(record.learner_bid)
    phase = MentorshipPhase.query.get(record.phase_bid)
    if profile is not None:
        _notify(
            user_bid=profile.user_bid,
            title="阶段合规确认完成",
            content=(
                f"你的阶段「{phase.name if phase else ''}」已通过"
                "学员签字、导师同步、改进项全部完成确认"
            ),
            notif_type="checklist_complete",
            related_bid=record.record_bid,
        )
    return True


@shared_task(name="learning_portal.probation_check")
def probation_check():
    """Auto-check learners whose probation is ending soon."""
    today = date.today()
    profiles = LearnerProfile.query.filter_by(status="active").all()

    checked = 0
    for p in profiles:
        if not p.probation_end_date:
            continue

        remaining = (p.probation_end_date - today).days
        if remaining != 14:  # 2 weeks before end
            continue

        # Check if all phases passed (accept both 'passed' and 'completed' —
        # the auto-advance task marks finished records 'completed', while older
        # data / the portal may use 'passed').
        phases = LearnerMentorship.query.filter_by(learner_bid=p.learner_bid).all()
        if not phases:
            continue

        def _is_done(status: str) -> bool:
            return status in ("passed", "completed")

        all_passed = all(_is_done(ph.status) for ph in phases)
        if all_passed:
            msg = "你已完成所有带教阶段学习，即将进行转正评定"
        else:
            failed = [ph for ph in phases if not _is_done(ph.status)]
            msg = f"你还有 {len(failed)} 个阶段未完成，可能影响转正"

        _notify(
            user_bid=p.user_bid,
            title="转正提醒",
            content=msg,
            notif_type="system",
        )
        checked += 1

    db.session.commit()
    return f"checked {checked} learners for probation"

