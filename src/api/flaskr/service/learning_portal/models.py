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
    __tablename__ = "mentorship_phases"

    phase_bid = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
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
    __tablename__ = "learner_mentorship"

    record_bid = db.Column(db.String(32), primary_key=True)
    learner_bid = db.Column(db.String(32), nullable=False, index=True)
    phase_bid = db.Column(db.String(32), nullable=False, index=True)
    status = db.Column(db.String(20), default="pending")
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    theory_score = db.Column(db.Numeric(5, 2), nullable=True)
    practice_score = db.Column(db.Numeric(5, 2), nullable=True)
    peer_review_score = db.Column(db.Numeric(5, 2), nullable=True)
    mentor_score = db.Column(db.Numeric(5, 2), nullable=True)
    total_score = db.Column(db.Numeric(5, 2), nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    remark = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class MentorshipChecklist(db.Model):
    __tablename__ = "mentorship_checklist"

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
    created_at = db.Column(db.DateTime)
