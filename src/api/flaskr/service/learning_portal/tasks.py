"""Learning Portal — Celery scheduled tasks.

Tasks:
- phase_deadline_reminder: Check phase deadlines and notify learners/mentors
- daily_task_push: Daily push of pending tasks at 09:00
- score_reminder: Remind mentors to score submitted items after 48h
- probation_check: Auto-check probation status when all phases completed
"""

from __future__ import annotations

import logging
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
        if profile and profile.mentor_bid not in reminded:
            _notify(
                user_bid=profile.mentor_bid,
                title="评分催办",
                content="学员有待评分项已超过48小时，请及时评分",
                notif_type="score_reminder",
            )
            reminded.add(profile.mentor_bid)

    db.session.commit()
    return f"reminded {len(reminded)} mentors"


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

        # Check if all phases passed
        phases = LearnerMentorship.query.filter_by(learner_bid=p.learner_bid).all()
        if not phases:
            continue

        all_passed = all(ph.status == "passed" for ph in phases)
        if all_passed:
            msg = "你已完成所有带教阶段学习，即将进行转正评定"
        else:
            failed = [ph for ph in phases if ph.status != "passed"]
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

