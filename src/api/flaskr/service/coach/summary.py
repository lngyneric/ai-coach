"""Coach session AI summary generation (W2, task 1).

Turns the four free-text coaching-session fields — ``topic``,
``mentor_notes``, ``learner_notes``, ``action_items`` — into a structured
Chinese summary via the LLM gateway (``flaskr.api.llm.chat_llm``).

Design rules:

- **Pure side-effect service**: ``generate_ai_summary`` never raises. Any
  LLM / provider failure is logged and returns ``{}`` so the caller (a
  session-save path or the explicit ``/summarize`` endpoint) degrades
  gracefully without blocking the session record.
- **Structured JSON out**: ``json=True`` requests a strict JSON object
  ``{summary, highlights[], action_items[], next_action, status}``.
  ``build_ai_summary_markdown`` renders it into the human-readable text that
  is persisted to ``coach_sessions.ai_summary`` (a TEXT column).
- **Cost conscious**: prompts are short; temperature fixed at 0.3; a single
  non-streaming call per session.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from flask import Flask

from flaskr.api.langfuse import (
    create_trace_with_root_span,
    finalize_langfuse_trace,
    get_langfuse_client,
)
from flaskr.api.llm import chat_llm
from flaskr.service.metering import UsageContext
from flaskr.service.metering.consts import BILL_USAGE_SCENE_PROD

logger = logging.getLogger(__name__)

MODEL_FALLBACK = "deepseek-v4-flash"
GENERATION_NAME = "coach_session_summary"
SPAN_NAME = "coach_session_summary_span"

# Cost: ~6 fields + 1 instruction line. Kept intentionally short.
SYSTEM_PROMPT = (
    "你是企业大学的面谈教练。根据面谈记录生成结构化中文总结，只输出严格 JSON"
    "（不要 markdown 代码块、不要额外文字），字段："
    '"summary"(面谈概要,80字内), "highlights"(关键要点,字符串数组,3-5条), '
    '"action_items"(后续行动计划,字符串数组,1-4条), '
    '"next_action"(下一步建议,30字内), "status"(面谈状态判定,取值 planned/ongoing/done)'
)


def _session_payload(session: Any) -> dict[str, Any]:
    """The four free-text fields plus minimal metadata for the LLM."""
    return {
        "topic": str(session.topic or "").strip(),
        "session_type": str(session.session_type or "").strip(),
        "duration_minutes": int(session.duration_minutes or 0),
        "session_date": str(session.session_date) if session.session_date else "",
        "mentor_notes": str(session.mentor_notes or "").strip(),
        "learner_notes": str(session.learner_notes or "").strip(),
        "action_items": str(session.action_items or "").strip(),
    }


def _default_model(app: Flask) -> str:
    model = str(app.config.get("DEFAULT_LLM_MODEL", "") or "").strip()
    return model or MODEL_FALLBACK


def _parse_summary_output(text: str) -> dict[str, Any]:
    """Best-effort JSON parse of the model output (code fences tolerated)."""
    raw = (text or "").strip()
    if not raw:
        return {}
    # Strip ```json ... ``` fences if the model wrapped the JSON.
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        # Some models return a plain object starting after a newline.
        try:
            start = raw.index("{")
            end = raw.rindex("}")
            parsed = json.loads(raw[start : end + 1])
        except (ValueError, TypeError):
            logger.warning("coach summary: unparseable LLM output: %.200s", raw)
            return {}
    if not isinstance(parsed, dict):
        return {}
    return parsed


def generate_ai_summary(app: Flask, session: Any) -> dict[str, Any]:
    """Generate a structured summary dict for a CoachSession (never raises).

    Returns ``{"summary", "highlights", "action_items", "next_action",
    "status"}`` on success, or ``{}`` when the LLM call / parse failed.
    """
    payload = _session_payload(session)
    user_prompt = json.dumps(payload, ensure_ascii=False)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    user_id = str(getattr(session, "learner_bid", "") or "").strip() or "coach-summary"

    trace, span = create_trace_with_root_span(
        client=get_langfuse_client(),
        trace_payload={
            "user_id": user_id,
            "input": messages,
            "name": "coach_session_summary",
            "metadata": {"scene": "coach_session_summary"},
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
        parsed = _parse_summary_output(collected)
        finalize_langfuse_trace(
            trace=trace,
            root_span=span,
            root_span_payload={"output": collected},
        )
        return parsed
    except Exception as exc:  # noqa: BLE001 - side channel must not raise
        logger.warning("coach summary generation failed: %s", exc)
        finalize_langfuse_trace(trace=trace, root_span=span)
        return {}


def build_ai_summary_markdown(parsed: dict[str, Any]) -> str:
    """Render the parsed JSON summary into human-readable markdown text."""
    lines: list[str] = []

    summary = str(parsed.get("summary") or "").strip()
    if summary:
        lines.append("## 面谈概要")
        lines.append(summary)
        lines.append("")

    highlights = parsed.get("highlights") or []
    if isinstance(highlights, list) and highlights:
        lines.append("## 关键要点")
        for item in highlights:
            lines.append(f"- {item}")
        lines.append("")

    action_items = parsed.get("action_items") or []
    if isinstance(action_items, list) and action_items:
        lines.append("## 行动计划")
        for item in action_items:
            lines.append(f"- {item}")
        lines.append("")

    next_action = str(parsed.get("next_action") or "").strip()
    if next_action:
        lines.append("## 下一步建议")
        lines.append(next_action)
        lines.append("")

    status = str(parsed.get("status") or "").strip()
    if status:
        lines.append(f"面谈状态：{status}")

    return "\n".join(lines).strip()
