"""Learner coaching report generation (W2, task 2) — real AI report.

No SmartPage/report placeholder was found in the codebase (grep over
``src/api`` and ``src/cook-web`` returned nothing), so this module implements
a self-contained report service in the coach domain:

- **Input**: one learner's coaching data — profile (``learner_profiles``),
  interview records (``coach_sessions``, including any ``ai_summary``),
  phase progress & scores (``learner_coaching``), and course enrollments
  (``course_enrollments``).
- **LLM**: a short system prompt asks for a structured JSON report
  ``{summary, strengths[], improvements[], suggestions[], next_actions[],
  overall_status}``; ``build_report_markdown`` renders it into the
  human-readable text (文字总结 + 建议).
- **Graceful degradation**: ``generate_ai_report`` never raises. On LLM /
  provider failure it logs a warning and returns ``{}``; the route then falls
  back to a rule-based summary built purely from the learner's data, so the
  report endpoint always answers with non-empty, data-backed content.
- **Cost conscious**: prompts are short, temperature fixed at 0.3, a single
  non-streaming call per request.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from flask import Flask

from flaskr.api.langfuse import (
    create_trace_with_root_span,
    finalize_langfuse_trace,
    get_langfuse_client,
)
from flaskr.api.llm import chat_llm
from flaskr.service.learning_portal.models import (
    CoachSession,
    CourseEnrollment,
    LearnerMentorship,
    LearnerProfile,
)
from flaskr.service.metering import UsageContext
from flaskr.service.metering.consts import BILL_USAGE_SCENE_PROD

logger = logging.getLogger(__name__)

MODEL_FALLBACK = "deepseek-v4-flash"
GENERATION_NAME = "coach_learner_report"
SPAN_NAME = "coach_learner_report_span"

# Cost: ~5 fields + 1 instruction line. Kept intentionally short.
SYSTEM_PROMPT = (
    "你是企业大学的学习教练。根据学员的带教数据生成结构化中文报告，只输出严格"
    "JSON（不要 markdown 代码块、不要额外文字），字段："
    '"summary"(整体评价,100字内), "strengths"(优势亮点,字符串数组,1-3条), '
    '"improvements"(待改进,字符串数组,1-3条), '
    '"suggestions"(提升建议,字符串数组,1-4条), '
    '"next_actions"(下一步行动计划,字符串数组,1-3条), '
    '"overall_status"(总评状态,取值 in_progress/on_track/at_risk/completed)'
)


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------


def collect_learner_context(learner_bid: str) -> dict[str, Any]:
    """Gather all coaching data for ``learner_bid`` into a plain dict.

    Every section degrades gracefully: if a table has no rows the key is an
    empty list / empty string — never ``None``-crashes the LLM prompt.
    """
    profile = LearnerProfile.query.filter_by(learner_bid=learner_bid).first()

    sessions = (
        CoachSession.query.filter_by(learner_bid=learner_bid)
        .order_by(CoachSession.session_date.desc())
        .limit(20)
        .all()
    )
    mentorships = (
        LearnerMentorship.query.filter_by(learner_bid=learner_bid)
        .order_by(LearnerMentorship.created_at.desc())
        .limit(20)
        .all()
    )
    enrollments = (
        CourseEnrollment.query.filter_by(user_bid=learner_bid)
        .limit(50)
        .all()
    )

    return {
        "learner_bid": learner_bid,
        "profile": {
            "department": str(profile.department or "") if profile else "",
            "position_name": str(profile.position_name or "") if profile else "",
            "mentor_bid": str(profile.mentor_bid or "") if profile else "",
            "onboarding_date": str(profile.onboarding_date)
            if profile and profile.onboarding_date
            else "",
            "status": str(profile.status or "") if profile else "",
        },
        "sessions": [
            {
                "session_type": s.session_type,
                "session_date": str(s.session_date) if s.session_date else "",
                "duration_minutes": s.duration_minutes,
                "topic": str(s.topic or ""),
                "mentor_notes": str(s.mentor_notes or ""),
                "learner_notes": str(s.learner_notes or ""),
                "action_items": str(s.action_items or ""),
                "coach_rating": s.coach_rating,
                "ai_summary": str(s.ai_summary or ""),
                "status": str(s.status or ""),
            }
            for s in sessions
        ],
        "mentorships": [
            {
                "phase_bid": m.phase_bid,
                "status": str(m.status or ""),
                "theory_score": float(m.theory_score)
                if m.theory_score is not None
                else None,
                "practice_score": float(m.practice_score)
                if m.practice_score is not None
                else None,
                "peer_review_score": float(m.peer_review_score)
                if m.peer_review_score is not None
                else None,
                "coach_score": float(m.coach_score)
                if m.coach_score is not None
                else None,
                "total_score": float(m.total_score)
                if m.total_score is not None
                else None,
                "retry_count": m.retry_count,
            }
            for m in mentorships
        ],
        "enrollments": [
            {
                "module": e.module,
                "status": str(e.status or ""),
                "progress_pct": e.progress_pct,
            }
            for e in enrollments
        ],
    }


# ---------------------------------------------------------------------------
# Rule-based fallback (used when the LLM call fails)
# ---------------------------------------------------------------------------


def build_rule_based_report(ctx: dict[str, Any]) -> dict[str, Any]:
    """Deterministic report derived purely from the learner's data.

    Guarantees a non-empty, data-backed answer for the report endpoint even
    when the LLM gateway is down.
    """
    profile = ctx.get("profile") or {}
    sessions = ctx.get("sessions") or []
    mentorships = ctx.get("mentorships") or []
    enrollments = ctx.get("enrollments") or []

    session_count = len(sessions)
    completed_sessions = [s for s in sessions if s.get("status") == "done"]
    avg_rating = None
    ratings = [s.get("coach_rating") for s in sessions if s.get("coach_rating")]
    if ratings:
        avg_rating = round(sum(ratings) / len(ratings), 1)

    scores = [
        m.get("total_score")
        for m in mentorships
        if m.get("total_score") is not None
    ]
    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    summary = (
        f"学员已完成 {session_count} 次面谈"
        + (f"，平均评分 {avg_rating}" if avg_rating else "")
        + (f"，阶段平均成绩 {avg_score}" if avg_score else "")
        + "，整体学习轨迹正常推进中。"
        if session_count or scores
        else "该学员暂无可用的带教数据，建议先建立学习档案与首次面谈。"
    )

    strengths = []
    if completed_sessions:
        strengths.append(
            f"已完成 {len(completed_sessions)} 次面谈，学习投入度高"
        )
    if avg_score is not None and avg_score >= 60:
        strengths.append(f"阶段考核平均分 {avg_score}，达到合格线")
    if enrollments:
        done = [e for e in enrollments if e.get("status") == "completed"]
        if done:
            strengths.append(f"已完成 {len(done)} 门课程学习")

    improvements = []
    if sessions and not completed_sessions:
        improvements.append("面谈记录尚无完成状态，需持续推进辅导闭环")
    if avg_score is not None and avg_score < 60:
        improvements.append(f"阶段平均分 {avg_score} 未达合格线，需重点帮扶")
    if not enrollments:
        improvements.append("暂未分配课程学习任务")

    suggestions = []
    if not sessions:
        suggestions.append("建议尽快安排首次面谈并制定学习计划")
    if sessions:
        suggestions.append("保持固定节奏的面谈跟进，落实行动项")

    next_actions = []
    if sessions:
        latest = sessions[0]
        if latest.get("action_items"):
            next_actions.append("跟进最近一次面谈的行动计划")
        else:
            next_actions.append("补充最近一次面谈的行动计划")
    if enrollments:
        pending = [e for e in enrollments if e.get("progress_pct", 0) < 100]
        if pending:
            next_actions.append("推进未完成课程的学习进度")

    return {
        "summary": summary,
        "strengths": strengths,
        "improvements": improvements,
        "suggestions": suggestions,
        "next_actions": next_actions,
        "overall_status": "in_progress"
        if sessions or mentorships
        else "not_started",
    }


# ---------------------------------------------------------------------------
# LLM path
# ---------------------------------------------------------------------------


def _parse_report_output(text: str) -> dict[str, Any]:
    """Best-effort JSON parse of the model output (code fences tolerated)."""
    raw = (text or "").strip()
    if not raw:
        return {}
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        try:
            start = raw.index("{")
            end = raw.rindex("}")
            parsed = json.loads(raw[start : end + 1])
        except (ValueError, TypeError):
            logger.warning("coach report: unparseable LLM output: %.200s", raw)
            return {}
    if not isinstance(parsed, dict):
        return {}
    return parsed


def _default_model(app: Flask) -> str:
    model = str(app.config.get("DEFAULT_LLM_MODEL", "") or "").strip()
    return model or MODEL_FALLBACK


def generate_ai_report(app: Flask, learner_bid: str) -> dict[str, Any]:
    """Generate a structured Chinese report for a learner (never raises).

    Returns ``{"summary", "strengths", "improvements", "suggestions",
    "next_actions", "overall_status"}`` on success, or ``{}`` when the LLM
    call / parse failed — the caller falls back to the rule-based report.
    """
    ctx = collect_learner_context(learner_bid)
    # Trim heavy fields to keep the prompt short.
    for s in ctx.get("sessions", []):
        s["ai_summary"] = s["ai_summary"][:300]
        s["mentor_notes"] = s["mentor_notes"][:200]
        s["learner_notes"] = s["learner_notes"][:200]

    user_prompt = json.dumps(ctx, ensure_ascii=False)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    user_id = learner_bid

    trace, span = create_trace_with_root_span(
        client=get_langfuse_client(),
        trace_payload={
            "user_id": user_id,
            "input": messages,
            "name": "coach_learner_report",
            "metadata": {"scene": "coach_learner_report"},
        },
        root_span_payload={"name": SPAN_NAME, "input": messages},
    )

    try:
        resp = chat_llm(
            app,
            user_id,
            span,
            model=_default_model(app),
            messages=messages,
            json=True,
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
        parsed = _parse_report_output(collected)
        finalize_langfuse_trace(
            trace=trace,
            root_span=span,
            root_span_payload={"output": collected},
        )
        return parsed
    except Exception as exc:  # noqa: BLE001 - side channel must not raise
        logger.warning("coach report generation failed: %s", exc)
        finalize_langfuse_trace(trace=trace, root_span=span)
        return {}


def build_report_markdown(parsed: dict[str, Any]) -> str:
    """Render a parsed report dict into human-readable markdown text."""
    lines: list[str] = []

    summary = str(parsed.get("summary") or "").strip()
    if summary:
        lines.append("## 整体评价")
        lines.append(summary)
        lines.append("")

    strengths = parsed.get("strengths") or []
    if isinstance(strengths, list) and strengths:
        lines.append("## 优势亮点")
        for item in strengths:
            lines.append(f"- {item}")
        lines.append("")

    improvements = parsed.get("improvements") or []
    if isinstance(improvements, list) and improvements:
        lines.append("## 待改进")
        for item in improvements:
            lines.append(f"- {item}")
        lines.append("")

    suggestions = parsed.get("suggestions") or []
    if isinstance(suggestions, list) and suggestions:
        lines.append("## 提升建议")
        for item in suggestions:
            lines.append(f"- {item}")
        lines.append("")

    next_actions = parsed.get("next_actions") or []
    if isinstance(next_actions, list) and next_actions:
        lines.append("## 下一步行动计划")
        for item in next_actions:
            lines.append(f"- {item}")
        lines.append("")

    status = str(parsed.get("overall_status") or "").strip()
    if status:
        lines.append(f"总评状态：{status}")

    return "\n".join(lines).strip()
