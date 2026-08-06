"""Learning Portal — Models for learner profiles, mentorship, tasks."""

from __future__ import annotations

from flaskr.dao import db


class LearnerProfile(db.Model):
    __tablename__ = "learner_profiles"

    learner_bid = db.Column(db.String(32), primary_key=True)
    user_bid = db.Column(db.String(32), nullable=False, index=True)
    employee_no = db.Column(db.String(50), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    position_name = db.Column(db.String(100), nullable=True)
    level = db.Column(db.String(20), nullable=True)
    mentor_bid = db.Column(db.String(32), nullable=True, index=True)
    supervisor_bid = db.Column(db.String(32), nullable=True)
    onboarding_date = db.Column(db.Date, nullable=True)
    probation_end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class MentorshipPhase(db.Model):
    # D1 fix: real table is `coach_phases` (was `mentorship_phases` → 500).
    __tablename__ = "coach_phases"

    phase_bid = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    # Course (shifu) bid linked to this phase. Nullable for backward compat;
    # when set, phase notifications build WeCom textcard links as /c/{shifu_bid}.
    shifu_bid = db.Column(db.String(32), nullable=True)
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    duration_days = db.Column(db.Integer, default=60)
    passing_score = db.Column(db.Numeric(5, 2), default=60.00)
    theory_weight = db.Column(db.Numeric(3, 2), default=0.40)
    practice_weight = db.Column(db.Numeric(3, 2), default=0.30)
    review_weight = db.Column(db.Numeric(3, 2), default=0.20)
    mentor_weight = db.Column(db.Numeric(3, 2), default=0.10)
    is_active = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class LearnerMentorship(db.Model):
    # D1 fix: real table is `learner_coaching` (was `learner_mentorship` → 500).
    __tablename__ = "learner_coaching"

    record_bid = db.Column(db.String(32), primary_key=True)
    learner_bid = db.Column(db.String(32), nullable=False, index=True)
    phase_bid = db.Column(db.String(32), nullable=False, index=True)
    status = db.Column(db.String(20), default="pending")
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    theory_score = db.Column(db.Numeric(5, 2), nullable=True)
    practice_score = db.Column(db.Numeric(5, 2), nullable=True)
    peer_review_score = db.Column(db.Numeric(5, 2), nullable=True)
    # D1 fix: real column is `coach_score` (was `mentor_score`).
    coach_score = db.Column(db.Numeric(5, 2), nullable=True)
    total_score = db.Column(db.Numeric(5, 2), nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    remark = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class CourseEnrollment(db.Model):
    """Records admin assigning a course to a user for a training module."""

    __tablename__ = "course_enrollments"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_bid = db.Column(db.String(32), nullable=False, index=True)
    shifu_bid = db.Column(db.String(32), nullable=False, index=True)
    trainer_bid = db.Column(db.String(32), nullable=True, comment="assigned by")
    module = db.Column(
        db.String(20),
        nullable=False,
        comment="onboarding | mentorship | intensive | leadership",
    )
    status = db.Column(
        db.String(20),
        default="active",
        comment="active | completed | expired",
    )
    deadline = db.Column(db.DateTime, nullable=True)
    progress_pct = db.Column(db.Integer, default=0, comment="0-100")
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    __table_args__ = (
        db.UniqueConstraint("user_bid", "shifu_bid", name="uq_user_course"),
    )


class MentorshipChecklist(db.Model):
    # D1 fix: real table is `coach_checklist` (was `mentorship_checklist` → 500).
    __tablename__ = "coach_checklist"

    item_bid = db.Column(db.String(32), primary_key=True)
    phase_bid = db.Column(db.String(32), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(20), nullable=False)
    max_score = db.Column(db.Numeric(5, 2), default=5.00)
    sort_order = db.Column(db.Integer, default=0)
    is_required = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class LearnerChecklistItem(db.Model):
    __tablename__ = "learner_checklist_items"

    record_bid = db.Column(db.String(32), primary_key=True)
    learner_bid = db.Column(db.String(32), nullable=False, index=True)
    item_bid = db.Column(db.String(32), nullable=False, index=True)
    score = db.Column(db.Numeric(5, 2), nullable=True)
    scored_by = db.Column(db.String(32), nullable=True)
    comment = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending")
    submitted_at = db.Column(db.DateTime, nullable=True)
    scored_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class LearnerTask(db.Model):
    __tablename__ = "learner_tasks"

    task_bid = db.Column(db.String(32), primary_key=True)
    learner_bid = db.Column(db.String(32), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    task_type = db.Column(db.String(20), nullable=False)
    related_bid = db.Column(db.String(32), nullable=True)
    due_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="pending")
    created_by = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class TaskNotification(db.Model):
    __tablename__ = "task_notifications"

    notif_bid = db.Column(db.String(32), primary_key=True)
    user_bid = db.Column(db.String(32), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=True)
    notif_type = db.Column(db.String(20), nullable=True)
    related_bid = db.Column(db.String(32), nullable=True)
    is_read = db.Column(db.Integer, default=0)
    # server_default matches the real column DEFAULT CURRENT_TIMESTAMP. Without
    # it the ORM emits an explicit NULL on INSERT (overriding the DB default),
    # so task-created rows end up with created_at IS NULL — breaking the
    # same-day dedup (phase_deadline_reminder) and the notifications ordering.
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class CoachSession(db.Model):
    """P2-4: minimal ORM mapping for the real `coach_sessions` table.

    Columns aligned 1:1 with SHOW COLUMNS on ai-shifu_dev.coach_sessions.
    Note: the mentoring column is ``mentor_bid`` (not ``coach_bid``) in the
    real table — see docs/P0-ACCEPTANCE-TEST-REPORT.md §10.5.
    """

    __tablename__ = "coach_sessions"

    session_bid = db.Column(db.String(32), primary_key=True)
    learner_bid = db.Column(db.String(32), nullable=False, index=True)
    mentor_bid = db.Column(db.String(32), nullable=False, index=True)
    phase_bid = db.Column(db.String(32), nullable=True, index=True)
    session_type = db.Column(db.String(20), nullable=False, default="regular")
    session_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=0)
    topic = db.Column(db.String(200), nullable=True)
    mentor_notes = db.Column(db.Text, nullable=True)
    learner_notes = db.Column(db.Text, nullable=True)
    action_items = db.Column(db.Text, nullable=True)
    next_session_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="completed")
    pre_course_bids = db.Column(db.Text, nullable=True)
    coach_rating = db.Column(db.Integer, nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    next_action = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class CoachProfile(db.Model):
    """P2-4: minimal ORM mapping for the real `coach_profiles` table."""

    __tablename__ = "coach_profiles"

    coach_bid = db.Column(db.String(32), primary_key=True)
    user_bid = db.Column(db.String(32), nullable=False, index=True, unique=True)
    employee_no = db.Column(db.String(50), nullable=True, index=True)
    name = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    specialties = db.Column(db.JSON, nullable=True)
    max_students = db.Column(db.Integer, default=5)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
