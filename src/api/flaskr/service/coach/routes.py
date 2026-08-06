"""Coach session routes (W2, task 1) — AI summary generation triggers.

Endpoints (all under the global ``before_request`` auth middleware):

- ``GET  /api/coach/sessions/<session_bid>``        → single session (login only)
- ``PUT  /api/coach/sessions/<session_bid>``        → update notes/topic; then
  **auto-generate** ``ai_summary`` via the LLM (non-blocking on failure)
- ``POST /api/coach/sessions/<session_bid>/summarize`` → explicitly regenerate
  ``ai_summary`` and persist it

Write operations require the ``create_session`` permission (coach or above;
admin/operator always passes — P0 permission model).

The generation itself lives in ``flaskr.service.coach.summary`` and is a pure
side-effect helper: on LLM failure it returns ``{}`` and the save still
commits, so a broken gateway never blocks session persistence.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from flask import Flask, request

from flaskr.dao import db
from flaskr.framework.plugin.inject import inject
from flaskr.route.common import make_common_response
from flaskr.service.coach.permissions import has_permission, visible_students_scope
from flaskr.service.coach.summary import build_ai_summary_markdown, generate_ai_summary
from flaskr.service.common.models import raise_param_error
from flaskr.service.learning_portal.models import (
    CoachSession,
    LearnerMentorship,
    LearnerProfile,
    ChecklistImprovement,
    MentorshipPhase,
)

CREATE_SESSION_PERMISSION = "create_session"

# Fields the mentor/client can update through PUT (subset of the real table).
_EDITABLE_FIELDS = (
    "topic",
    "session_type",
    "session_date",
    "duration_minutes",
    "mentor_notes",
    "learner_notes",
    "action_items",
    "next_session_date",
    "status",
    "coach_rating",
)


def _require_coach_write(app, user) -> None:
    """Raise when the user may not create/edit coaching sessions."""
    if not has_permission(app, user, CREATE_SESSION_PERMISSION):
        raise_param_error("coach: create_session permission required")


def _require_mentored_learner(app, user, learner_bid: str) -> None:
    """Raise unless ``user`` may act on ``learner_bid``.

    Mirror of ``learning_portal.routes._require_mentored_learner``: admin/hr
    (scope ``all``) keep the exception; everyone else must be the learner's
    own mentor (``LearnerProfile.coach_bid == user.user_id``).
    """
    scope = visible_students_scope(app, user)
    if scope == "all":
        return
    profile = LearnerProfile.query.filter_by(learner_bid=learner_bid).first()
    if profile is None or profile.coach_bid != getattr(user, "user_id", None):
        raise_param_error("coach: not the mentored learner")


def _require_learner_self(app, user, learner_bid: str) -> None:
    """Raise unless ``user`` is the learner themself (for sign-off).

    admin/hr (scope ``all``) keep the exception (consistent with the P0 data
    scope); any other caller must own the learner profile.
    """
    scope = visible_students_scope(app, user)
    if scope == "all":
        return
    profile = LearnerProfile.query.filter_by(learner_bid=learner_bid).first()
    if profile is None or profile.user_bid != getattr(user, "user_id", None):
        raise_param_error("coach: only the learner can sign-off")


def _require_checklist_view(app, user, learner_bid: str) -> None:
    """Raise unless ``user`` may view the checklist progress.

    Allowed viewers: admin/hr (scope ``all``), the learner's own mentor, or
    the learner themself.
    """
    scope = visible_students_scope(app, user)
    if scope == "all":
        return
    profile = LearnerProfile.query.filter_by(learner_bid=learner_bid).first()
    user_id = getattr(user, "user_id", None)
    if profile is not None and profile.user_bid == user_id:
        return  # learner themself
    if profile is not None and profile.coach_bid == user_id:
        return  # own mentor
    raise_param_error("coach: not allowed to view this checklist")


def _get_coaching_record(record_bid: str) -> LearnerMentorship:
    record = LearnerMentorship.query.filter_by(record_bid=record_bid).first()
    if record is None:
        raise_param_error("coach: coaching record not found")
    return record


def _checklist_view_payload(record: LearnerMentorship) -> dict[str, Any]:
    """Assemble the three-state progress + improvements payload."""
    from flaskr.service.learning_portal.tasks import checklist_three_state

    phase = MentorshipPhase.query.get(record.phase_bid)
    improvements = (
        ChecklistImprovement.query.filter_by(record_bid=record.record_bid)
        .order_by(ChecklistImprovement.created_at.asc())
        .all()
    )
    state = checklist_three_state(record)
    return {
        "record_bid": record.record_bid,
        "learner_bid": record.learner_bid,
        "phase_bid": record.phase_bid,
        "phase_name": phase.name if phase else None,
        "status": record.status,
        "checkpoints": state,
        "improvements": [
            {
                "improvement_bid": i.improvement_bid,
                "action": i.action,
                "owner_bid": i.owner_bid,
                "owner_name": i.owner_name,
                "due_at": str(i.due_at) if i.due_at else None,
                "status": i.status,
                "created_by": i.created_by,
            }
            for i in improvements
        ],
    }


def _apply_editable_fields(session: CoachSession, payload: dict[str, Any]) -> None:
    """Apply the whitelisted editable fields to ``session`` (in place)."""
    for field in _EDITABLE_FIELDS:
        if field not in payload:
            continue
        value = payload.get(field)
        if field in ("duration_minutes", "coach_rating"):
            try:
                value = int(value) if value is not None else None
            except (TypeError, ValueError):
                raise_param_error(f"coach: {field} must be an integer")
        elif field in ("session_date", "next_session_date"):
            value = str(value or "").strip()
            if not value:
                value = None
            else:
                try:
                    value = datetime.fromisoformat(
                        value.replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                except ValueError:
                    raise_param_error(f"coach: {field} must be ISO datetime")
        elif field == "status":
            value = str(value or "").strip() or None
        else:
            value = str(value or "").strip() or None
        setattr(session, field, value)


def _persist_generated_summary(
    app: Flask, session: CoachSession, parsed: dict[str, Any]
) -> None:
    """Write the generated summary back to the session row (never raises).

    ``parsed`` is ``{}`` when the LLM call failed — in that case the previous
    ``ai_summary`` is left untouched and only ``updated_at`` is refreshed.
    """
    if not parsed:
        return
    markdown = build_ai_summary_markdown(parsed)
    if markdown:
        session.ai_summary = markdown
    next_action = str(parsed.get("next_action") or "").strip()
    if next_action:
        session.next_action = next_action


@inject
def register_coach_routes(app: Flask, path_prefix: str = "/api/coach") -> None:
    app.logger.info("register coach routes %s", path_prefix)

    @app.route(path_prefix + "/sessions/<session_bid>", methods=["GET"])
    def get_coach_session(session_bid: str):
        """Return one coaching session (login required)."""
        session = CoachSession.query.filter_by(session_bid=session_bid).first()
        if session is None:
            raise_param_error("coach: session not found")
        return make_common_response(
            {
                "session_bid": session.session_bid,
                "learner_bid": session.learner_bid,
                "mentor_bid": session.mentor_bid,
                "phase_bid": session.phase_bid,
                "session_type": session.session_type,
                "session_date": str(session.session_date)
                if session.session_date
                else None,
                "duration_minutes": session.duration_minutes,
                "topic": session.topic,
                "mentor_notes": session.mentor_notes,
                "learner_notes": session.learner_notes,
                "action_items": session.action_items,
                "next_session_date": str(session.next_session_date)
                if session.next_session_date
                else None,
                "status": session.status,
                "coach_rating": session.coach_rating,
                "ai_summary": session.ai_summary,
                "next_action": session.next_action,
            }
        )

    @app.route(path_prefix + "/sessions/<session_bid>", methods=["PUT"])
    def update_coach_session(session_bid: str):
        """Update a coaching session; auto-generate ``ai_summary`` when notes
        or topic are present. LLM failure never blocks the save."""
        _require_coach_write(app, request.user)
        session = CoachSession.query.filter_by(session_bid=session_bid).first()
        if session is None:
            raise_param_error("coach: session not found")

        payload = request.get_json(silent=True) or {}
        _apply_editable_fields(session, payload)
        session.updated_at = datetime.now()

        # Auto-generate summary when there is something meaningful to summarize.
        has_input = any(
            bool(getattr(session, field))
            for field in ("topic", "mentor_notes", "learner_notes", "action_items")
        )
        if has_input:
            parsed = generate_ai_summary(app, session)
            _persist_generated_summary(app, session, parsed)

        db.session.commit()
        return make_common_response(
            {
                "session_bid": session.session_bid,
                "ai_summary": session.ai_summary,
                "next_action": session.next_action,
                "summary_generated": bool(session.ai_summary),
            }
        )

    @app.route(
        path_prefix + "/sessions/<session_bid>/summarize", methods=["POST"]
    )
    def summarize_coach_session(session_bid: str):
        """Explicitly regenerate the AI summary for a session."""
        _require_coach_write(app, request.user)
        session = CoachSession.query.filter_by(session_bid=session_bid).first()
        if session is None:
            raise_param_error("coach: session not found")

        parsed = generate_ai_summary(app, session)
        _persist_generated_summary(app, session, parsed)
        session.updated_at = datetime.now()
        db.session.commit()

        return make_common_response(
            {
                "session_bid": session.session_bid,
                "ai_summary": session.ai_summary,
                "next_action": session.next_action,
                "summary_generated": bool(session.ai_summary),
                "raw": parsed,
            }
        )

    # ------------------------------------------------------------------
    # W3 task 2 — compliance checkpoints (sign / sync / improvement)
    # ------------------------------------------------------------------

    @app.route(path_prefix + "/checklist/<record_bid>", methods=["GET"])
    def get_checklist_status(record_bid: str):
        """Return the three-state compliance progress of a coaching record.

        Viewable by the coach (mentor) or the learner themself.
        """
        record = _get_coaching_record(record_bid)
        _require_checklist_view(app, request.user, record.learner_bid)
        return make_common_response(_checklist_view_payload(record))

    @app.route(path_prefix + "/checklist/<record_bid>/sign", methods=["POST"])
    def sign_checklist(record_bid: str):
        """Learner signs off that they understood / agree (idempotent).

        Only the learner themself may sign. A second POST keeps the original
        timestamp and simply returns the current state.
        """
        record = _get_coaching_record(record_bid)
        _require_learner_self(app, request.user, record.learner_bid)

        if record.sign_at is None:
            record.sign_at = datetime.now()
            record.signed_by = getattr(request.user, "user_id", None)
            record.updated_at = datetime.now()
        from flaskr.service.learning_portal.tasks import maybe_complete_checklist

        maybe_complete_checklist(record)
        db.session.commit()
        return make_common_response(_checklist_view_payload(record))

    @app.route(path_prefix + "/checklist/<record_bid>/sync", methods=["POST"])
    def sync_checklist(record_bid: str):
        """Coach records the face-to-face sync (confirmation + note, idempotent)."""
        _require_coach_write(app, request.user)
        record = _get_coaching_record(record_bid)
        _require_mentored_learner(app, request.user, record.learner_bid)

        payload = request.get_json(silent=True) or {}
        note = str(payload.get("note") or "").strip()
        if record.sync_at is None:
            record.sync_at = datetime.now()
            record.synced_by = getattr(request.user, "user_id", None)
        if note:
            record.sync_note = note
        record.updated_at = datetime.now()

        from flaskr.service.learning_portal.tasks import maybe_complete_checklist

        maybe_complete_checklist(record)
        db.session.commit()
        return make_common_response(_checklist_view_payload(record))

    @app.route(
        path_prefix + "/checklist/<record_bid>/improvements", methods=["POST"]
    )
    def add_checklist_improvement(record_bid: str):
        """Coach registers an improvement item found during the sync."""
        _require_coach_write(app, request.user)
        record = _get_coaching_record(record_bid)
        _require_mentored_learner(app, request.user, record.learner_bid)

        payload = request.get_json(silent=True) or {}
        action = str(payload.get("action") or "").strip()
        if not action:
            raise_param_error("coach: action is required")
        due_raw = str(payload.get("due_at") or "").strip()
        due_at = None
        if due_raw:
            try:
                due_at = datetime.fromisoformat(
                    due_raw.replace("Z", "+00:00")
                ).replace(tzinfo=None)
            except ValueError:
                raise_param_error("coach: due_at must be ISO datetime")

        item = ChecklistImprovement(
            improvement_bid=uuid.uuid4().hex,
            record_bid=record.record_bid,
            action=action,
            owner_bid=str(payload.get("owner_bid") or "").strip() or None,
            owner_name=str(payload.get("owner_name") or "").strip() or None,
            due_at=due_at,
            status="pending",
            created_by=getattr(request.user, "user_id", None),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.session.add(item)

        from flaskr.service.learning_portal.tasks import maybe_complete_checklist

        maybe_complete_checklist(record)
        db.session.commit()
        return make_common_response(_checklist_view_payload(record))

    @app.route(
        path_prefix
        + "/checklist/<record_bid>/improvements/<improvement_bid>/done",
        methods=["POST"],
    )
    def done_checklist_improvement(record_bid: str, improvement_bid: str):
        """Coach marks an improvement item as done (closes the improvement gate)."""
        _require_coach_write(app, request.user)
        record = _get_coaching_record(record_bid)
        _require_mentored_learner(app, request.user, record.learner_bid)

        item = ChecklistImprovement.query.filter_by(
            improvement_bid=improvement_bid, record_bid=record.record_bid
        ).first()
        if item is None:
            raise_param_error("coach: improvement not found")
        if item.status != "done":
            item.status = "done"
            item.updated_at = datetime.now()

        from flaskr.service.learning_portal.tasks import maybe_complete_checklist

        maybe_complete_checklist(record)
        db.session.commit()
        return make_common_response(_checklist_view_payload(record))

    @app.route(
        path_prefix + "/checklist/<record_bid>/improvements", methods=["GET"]
    )
    def list_checklist_improvements(record_bid: str):
        """List improvement items (coach mentor / learner themself)."""
        record = _get_coaching_record(record_bid)
        _require_checklist_view(app, request.user, record.learner_bid)
        items = (
            ChecklistImprovement.query.filter_by(record_bid=record.record_bid)
            .order_by(ChecklistImprovement.created_at.asc())
            .all()
        )
        return make_common_response(
            [
                {
                    "improvement_bid": i.improvement_bid,
                    "action": i.action,
                    "owner_bid": i.owner_bid,
                    "owner_name": i.owner_name,
                    "due_at": str(i.due_at) if i.due_at else None,
                    "status": i.status,
                    "created_by": i.created_by,
                }
                for i in items
            ]
        )

    @app.route(path_prefix + "/phases/advance", methods=["POST"])
    def coach_phases_advance():
        """W3: manually trigger the phase auto-advance scan (idempotent).

        Coach (``create_session`` permission) and above may run the same
        scan as the ``learning_portal.phase_auto_advance`` beat task. Repeated
        calls are safe — an already-advanced learner owns an ``in_progress``
        record and is skipped on the next run.
        """
        _require_coach_write(app, request.user)
        from flaskr.service.learning_portal.tasks import advance_completed_phases

        result = advance_completed_phases()
        return make_common_response(
            {
                "advanced": result["advanced"],
                "finished": result["finished"],
                "skipped": result["skipped"],
            }
        )
