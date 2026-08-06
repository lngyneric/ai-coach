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

from datetime import datetime
from typing import Any

from flask import Flask, request

from flaskr.dao import db
from flaskr.framework.plugin.inject import inject
from flaskr.route.common import make_common_response
from flaskr.service.coach.permissions import has_permission
from flaskr.service.coach.summary import build_ai_summary_markdown, generate_ai_summary
from flaskr.service.common.models import raise_param_error
from flaskr.service.learning_portal.models import CoachSession

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
