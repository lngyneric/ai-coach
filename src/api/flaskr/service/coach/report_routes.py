"""Coach learner-report routes (W2, task 2) — real AI report endpoint.

``GET /api/coach/report/<learner_bid>`` returns a learner's coaching report:

- LLM-generated structured report (总结 + 建议) rendered to markdown
- always answers: on LLM failure it falls back to a rule-based report built
  from the learner's actual data (never empty, never 500)

Permissions (P0 5-role model, ``flaskr.service.coach.permissions``):

- ``view_any_report`` (coach / dept-head / hr / admin) → any learner
- ``view_own_report`` (learner) → only the caller's own profile

Everything runs under the global ``before_request`` auth middleware.
"""

from __future__ import annotations

from typing import Any

from flask import Flask, current_app, request

from flaskr.framework.plugin.inject import inject
from flaskr.route.common import make_common_response
from flaskr.service.coach.permissions import has_permission
from flaskr.service.coach.report import (
    build_report_markdown,
    build_rule_based_report,
    collect_learner_context,
    generate_ai_report,
)
from flaskr.service.common.models import raise_param_error
from flaskr.service.learning_portal.models import LearnerProfile

VIEW_ANY_REPORT = "view_any_report"
VIEW_OWN_REPORT = "view_own_report"


def _may_view_report(user: Any, learner_bid: str) -> bool:
    """True when ``user`` may view the report for ``learner_bid``.

    - ``view_any_report`` holders always pass;
    - learners may view their own profile (match by ``user_bid`` on the
      ``learner_profiles`` row, or by the learner_bid == user.user_id).
    """
    if has_permission(current_app, user, VIEW_ANY_REPORT):
        return True
    if not has_permission(current_app, user, VIEW_OWN_REPORT):
        return False
    user_id = str(getattr(user, "user_id", "") or "").strip()
    if user_id and user_id == learner_bid:
        return True
    profile = LearnerProfile.query.filter_by(learner_bid=learner_bid).first()
    if profile and profile.user_bid == user_id:
        return True
    return False


@inject
def register_report_routes(app: Flask, path_prefix: str = "/api/coach") -> None:
    app.logger.info("register coach report routes %s", path_prefix)

    @app.route(path_prefix + "/report/<learner_bid>", methods=["GET"])
    def get_learner_report(learner_bid: str):
        """AI-generated coaching report for one learner (markdown + structured).

        ---
        tags:
            - coach
        parameters:
            - name: learner_bid
              in: path
              required: true
              schema: {type: string}
            - name: source
              in: query
              schema: {type: string, enum: [auto, llm, rule]}
              description: 'auto=LLM w/ rule fallback (default), llm=LLM only, rule=rule only'
        responses:
            200:
                description: report markdown + structured fields
        """
        if not _may_view_report(request.user, learner_bid):
            raise_param_error("coach: no permission to view this learner report")

        source = (request.args.get("source") or "auto").strip().lower()
        ctx = collect_learner_context(learner_bid)

        if source == "rule":
            parsed = build_rule_based_report(ctx)
            generated_by = "rule"
        elif source == "llm":
            parsed = generate_ai_report(current_app, learner_bid)
            generated_by = "llm"
        else:  # auto — LLM first, rule fallback
            parsed = generate_ai_report(current_app, learner_bid)
            if not parsed:
                parsed = build_rule_based_report(ctx)
                generated_by = "rule"
            else:
                generated_by = "llm"

        markdown = build_report_markdown(parsed)
        return make_common_response(
            {
                "learner_bid": learner_bid,
                "generated_by": generated_by,
                "markdown": markdown,
                "report": parsed,
                "context": {
                    "session_count": len(ctx.get("sessions") or []),
                    "mentorship_count": len(ctx.get("mentorships") or []),
                    "enrollment_count": len(ctx.get("enrollments") or []),
                },
            }
        )
