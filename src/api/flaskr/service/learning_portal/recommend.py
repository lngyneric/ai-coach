"""AI recommendation endpoint (W2, task 4) — position → course tags.

``GET /api/portal/recommend`` returns a list of published courses matching a
job position, ranked by ``course_position_tags.weight`` DESC.

Design rules:

- **Data first, LLM optional**: the course list always comes from the real
  ``course_position_tags`` ⋈ ``shifu_published_shifus`` join — no hallucinated
  courses. An optional ``reason=1`` query flag asks the LLM gateway for a
  short one-line recommendation rationale (cost-conscious: single short
  prompt, ``reason`` off by default).
- **Position resolution**: an explicit ``?position=`` code/Chinese label wins;
  otherwise the current user's position is read from ``learner_profiles``
  (or ``user_users.position_name``) and fuzzy-matched to a known position
  code. Unknown positions degrade to the ``general`` bucket (never an error).
- **Graceful degradation**: LLM reason generation never raises — on failure
  the endpoint still returns the ranked course list with ``reason`` empty.
- **No extra permission**: reading recommendations is login-only, enforced by
  the global ``before_request`` auth middleware (same as the other portal
  routes).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from flask import Flask, request
from sqlalchemy import text

from flaskr.api.langfuse import (
    create_trace_with_root_span,
    finalize_langfuse_trace,
    get_langfuse_client,
)
from flaskr.api.llm import chat_llm
from flaskr.dao import db
from flaskr.framework.plugin.inject import inject
from flaskr.route.common import make_common_response
from flaskr.service.learning_portal.models import (
    CoursePositionTag,
    LearnerProfile,
)
from flaskr.service.metering import UsageContext
from flaskr.service.metering.consts import BILL_USAGE_SCENE_PROD
from flaskr.service.shifu.models import PublishedShifu

logger = logging.getLogger(__name__)

MODEL_FALLBACK = "deepseek-v4-flash"
GENERATION_NAME = "portal_recommend_reason"
SPAN_NAME = "portal_recommend_reason_span"
DEFAULT_LIMIT = 6
MAX_LIMIT = 20

# Position code → (Chinese label, fuzzy keywords). Unknown labels fall back
# to "general". Kept small & explicit; extend as the course library grows.
_POSITIONS: dict[str, tuple[str, tuple[str, ...]]] = {
    "sales": ("销售", ("销售", "sales", "客服", "客户")),
    "medical": ("检验", ("检验", "检验科", "实验室", "medical", "流式")),
    "management": ("管理", ("管理", "经理", "管理者", "领导", "management")),
    "digital": ("数字化", ("数字化", "AI", "架构", "产品经理", "digital", "智能体")),
    "general": ("通用", ("通用", "general", "入职", "新员工")),
}

# Cost: ~1 line instruction. Kept intentionally short.
REASON_SYSTEM_PROMPT = (
    "你是企业大学课程推荐助手。基于学员岗位和推荐课程标题，用一句中文"
    "（40字内）说明推荐理由，只输出这句话，不要任何前后缀。"
)


def _normalize_position(raw: Any) -> str:
    """Turn ``?position=`` (code or Chinese label) into a canonical code."""
    value = str(raw or "").strip().lower()
    if not value:
        return ""
    if value in _POSITIONS:
        return value
    for code, (_label, keywords) in _POSITIONS.items():
        if any(keyword in value for keyword in keywords):
            return code
    # Unknown explicit position → general (safe degradation).
    return "general"


def _user_position_code(app: Flask, user: Any) -> str:
    """Fuzzy-map the current user's position_name to a canonical code."""
    user_id = str(getattr(user, "user_id", "") or "").strip()
    position_name = ""
    if user_id:
        profile = LearnerProfile.query.filter_by(user_bid=user_id).first()
        if profile and profile.position_name:
            position_name = str(profile.position_name)
    if not position_name:
        # Fall back to user_users.position_name.
        row = (
            db.session.execute(
                text(
                    "SELECT position_name FROM user_users "
                    "WHERE user_bid = :bid LIMIT 1"
                ),
                {"bid": user_id},
            ).first()
            if user_id
            else None
        )
        if row:
            position_name = str(row[0] or "")
    return _normalize_position(position_name)


def _load_recommendations(
    position_code: str, limit: int
) -> list[dict[str, Any]]:
    """Join course_position_tags ⋈ shifu_published_shifus, weight DESC.

    Uses ``with_entities`` so each row exposes the joined course columns
    (``title`` / ``description``) in addition to the tag columns.
    """
    rows = (
        db.session.query(CoursePositionTag, PublishedShifu)
        .join(
            PublishedShifu,
            PublishedShifu.shifu_bid == CoursePositionTag.shifu_bid,
        )
        .filter(
            CoursePositionTag.position == position_code,
            CoursePositionTag.is_active == 1,
            PublishedShifu.deleted == 0,
        )
        .order_by(
            CoursePositionTag.weight.desc(),
            CoursePositionTag.id.asc(),
        )
        .limit(limit)
        .all()
    )
    result: list[dict[str, Any]] = []
    for tag, course in rows:
        result.append(
            {
                "shifu_bid": course.shifu_bid,
                "title": course.title,
                "description": course.description,
                "position": tag.position,
                "position_name": tag.position_name or position_code,
                "tag": tag.tag,
                "weight": tag.weight,
            }
        )
    return result


def _generate_reason(
    app: Flask, user_id: str, position_name: str, courses: list[dict[str, Any]]
) -> str:
    """Short one-line recommendation reason via the LLM gateway (never raises).

    Returns ``""`` on failure so the caller keeps serving the course list.
    """
    titles = "、".join(c["title"] for c in courses[:3])
    user_prompt = f"岗位：{position_name}。推荐课程：{titles}。请说明推荐理由。"
    messages = [
        {"role": "system", "content": REASON_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    trace, span = create_trace_with_root_span(
        client=get_langfuse_client(),
        trace_payload={
            "user_id": user_id,
            "input": messages,
            "name": "portal_recommend_reason",
            "metadata": {"scene": "portal_recommend_reason"},
        },
        root_span_payload={"name": SPAN_NAME, "input": messages},
    )
    try:
        resp = chat_llm(
            app,
            user_id,
            span,
            model=str(app.config.get("DEFAULT_LLM_MODEL", "") or "").strip()
            or MODEL_FALLBACK,
            messages=messages,
            json=False,
            stream=False,
            generation_name=GENERATION_NAME,
            temperature=0.3,
            usage_context=UsageContext(
                user_bid=user_id,
                usage_scene=BILL_USAGE_SCENE_PROD,
                billable=0,
            ),
            usage_scene=BILL_USAGE_SCENE_PROD,
            billable=0,
        )
        collected = "".join(chunk.result for chunk in resp if chunk.result)
        finalize_langfuse_trace(
            trace=trace,
            root_span=span,
            root_span_payload={"output": collected},
        )
        return str(collected or "").strip()
    except Exception as exc:  # noqa: BLE001 - side channel must not raise
        logger.warning("recommend reason generation failed: %s", exc)
        finalize_langfuse_trace(trace=trace, root_span=span)
        return ""


@inject
def register_recommend_routes(
    app: Flask, path_prefix: str = "/api/portal"
) -> None:
    app.logger.info("register recommend routes %s", path_prefix)

    @app.route(path_prefix + "/recommend", methods=["GET"])
    def portal_recommend():
        """AI course recommendation by job position.

        ---
        tags:
            - learning_portal
        parameters:
            - name: position
              in: query
              schema: {type: string}
              description: position code (sales/medical/management/digital/general)
                           or Chinese label; defaults to the user's position
            - name: limit
              in: query
              schema: {type: integer, default: 6}
              description: max rows (1-20)
            - name: reason
              in: query
              schema: {type: integer, default: 0}
              description: set to 1 to generate a one-line LLM rationale
        responses:
            200:
                description: ranked course list
        """
        raw_position = request.args.get("position")
        explicit = bool(str(raw_position or "").strip())
        position_code = _normalize_position(raw_position)

        try:
            limit = int(request.args.get("limit") or DEFAULT_LIMIT)
        except (TypeError, ValueError):
            limit = DEFAULT_LIMIT
        limit = max(1, min(limit, MAX_LIMIT))

        # Resolve the position: explicit query param wins, else the user's.
        resolved_code = position_code if explicit else _user_position_code(
            app, getattr(request, "user", None)
        )
        if not resolved_code:
            resolved_code = "general"
        position_label = _POSITIONS.get(resolved_code, ("通用", ()))[0]

        courses = _load_recommendations(resolved_code, limit)

        reason = ""
        if request.args.get("reason") in ("1", "true", "yes"):
            user_id = str(getattr(request, "user", None).user_id or "")
            reason = _generate_reason(app, user_id, position_label, courses)

        return make_common_response(
            {
                "position": resolved_code,
                "position_name": position_label,
                "count": len(courses),
                "reason": reason,
                "courses": courses,
            }
        )
