"""
JEV-based follow-up (追问) scoring.

After a learner's follow-up question is answered, JEV (TypeSafe System One — a
*typed-judgment* model returning noul / choice / score answers) scores both the
learner's question and the generated answer. Results are persisted to
``learn_followup_scores`` and distilled into a difficulty hint (easier / keep /
harder) that later steps can use to adapt the lesson.

Scoring runs in a background thread and never blocks or breaks the learner's
answer stream; any failure is swallowed and logged.

API reference: https://docs.typesafe.ai/api.md
"""

from __future__ import annotations

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests


logger = logging.getLogger(__name__)

_TYPESAFE_URL = "https://api.typesafe.ai/v1/systemone"
_TYPESAFE_MODEL = "jev-latest"
_JEV_TIMEOUT = 8.0
_JEV_MAX_RETRIES = 3
_JEV_BACKOFF = (0.5, 1.0, 2.0)

_ANSWER_EXCERPT_MAX = 2000

# Low concurrency: scoring must not compete with the LLM/TTS pipelines.
_scoring_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="jev_score_")

# Ordered mastery levels (Score primitive: index 0..4).
_MASTERY_LEVELS = [
    "完全不懂：提问显示对基本概念几乎没有理解",
    "初步接触：知道名词但理解模糊、有明显误解",
    "基本理解：掌握主要概念，细节或边界仍不清楚",
    "较好掌握：理解准确，能说明原理与用途",
    "熟练掌握：能举一反三、迁移到新场景并提出深入问题",
]

# Ordered answer-quality levels (Score primitive: index 0..4).
_ANSWER_QUALITY_LEVELS = [
    "很差：答非所问或存在事实性错误",
    "偏弱：部分切题但信息不准或过于笼统",
    "合格：切题且基本准确，深度适中",
    "良好：切题、准确、结构清晰，深浅适中",
    "优秀：切题准确，兼顾深度与可理解性，并能举例或延伸",
]


def _jev_available() -> bool:
    """True when a TypeSafe API key is present in the environment."""
    return bool(os.environ.get("TYPESAFE_API_KEY"))


def _extract_score(answer: Any) -> float | None:
    """Extract the probability-weighted score from a Score answer."""
    if not isinstance(answer, dict):
        return None
    value = answer.get("score")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_choice(answer: Any) -> str | None:
    """Extract the chosen option from a Choice answer."""
    if not isinstance(answer, dict):
        return None
    value = answer.get("choice")
    return str(value) if value is not None else None


def _extract_noul(answer: Any) -> float | None:
    """Extract the yes-probability from a Noul answer."""
    if not isinstance(answer, dict):
        return None
    value = answer.get("noul")
    if value is None:
        value = answer.get("value")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_confidence(answer: Any) -> float | None:
    """Extract confidence (Choice/Score answers carry it)."""
    if not isinstance(answer, dict):
        return None
    value = answer.get("confidence")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def derive_difficulty_hint(
    mastery: float | None,
    ask_type: str | None,
    on_topic: float | None,
) -> str:
    """
    Deterministically map JEV judgments to a next-step difficulty hint.

    - Low mastery or confusion → ``easier`` (slow down / re-explain).
    - High mastery with a deepening question → ``harder`` (go deeper).
    - Otherwise ``keep``.
    """
    normalized_type = (ask_type or "").strip().lower()
    if normalized_type == "off_topic":
        return "keep"
    if normalized_type == "confusion":
        return "easier"
    if mastery is not None:
        # mastery is a 0..4 weighted position (level indices).
        if mastery < 2.0:
            return "easier"
        if mastery >= 3.5 and normalized_type == "deepen":
            return "harder"
        if mastery >= 3.5:
            return "harder"
    return "keep"


def score_followup(
    question: str,
    answer: str,
    chapter_title: str = "",
) -> dict[str, Any] | None:
    """
    Score a learner follow-up question and its generated answer with JEV.

    Returns a dict with ``mastery``, ``ask_type``, ``answer_on_topic``,
    ``answer_quality``, ``confidence``, ``difficulty_hint``, ``model`` and
    ``raw``; or ``None`` when JEV is unavailable or the call fails.
    """
    if not _jev_available():
        logger.debug("jev not available (no TYPESAFE_API_KEY); skipping follow-up scoring")
        return None
    if not (question or "").strip() and not (answer or "").strip():
        return None

    api_key = os.environ["TYPESAFE_API_KEY"]

    state = {
        "chapter": chapter_title or "",
        "learner_question": question or "",
        "tutor_answer": answer or "",
    }

    questions = {
        "mastery": {
            "type": "score",
            "instructions": (
                "根据 state 中学习者的问题与其对课程内容的掌握表现，评估该学习者"
                "对本章节知识的掌握程度。"
            ),
            "criteria": list(_MASTERY_LEVELS),
        },
        "ask_type": {
            "type": "choice",
            "instructions": (
                "判断 state 中 learner_question 的提问意图属于哪一类。"
            ),
            "criteria": {
                "confusion": "表现出困惑或误解，需要重新讲解基础",
                "clarify": "对某个细节/术语求澄清",
                "deepen": "在已理解基础上追问更深入的原因、延伸或应用",
                "off_topic": "与本章节内容无关",
            },
        },
        "answer_on_topic": {
            "type": "noul",
            "instructions": (
                "state 中的 tutor_answer 是否切合 learner_question 与本章节主题、"
                "没有答非所问？"
            ),
            "criteria": {
                "true": "切题，正面回应了学习者的提问",
                "false": "答非所问，或偏离了本章节主题",
            },
        },
        "answer_quality": {
            "type": "score",
            "instructions": (
                "评估 state 中 tutor_answer 作为教学回答的质量：是否准确、切题、"
                "对当前学习者而言深浅适中。"
            ),
            "criteria": list(_ANSWER_QUALITY_LEVELS),
        },
    }

    payload = {"state": state, "model": _TYPESAFE_MODEL, "questions": questions}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_err: Exception | None = None
    for attempt in range(_JEV_MAX_RETRIES):
        try:
            resp = requests.post(
                _TYPESAFE_URL, json=payload, headers=headers, timeout=_JEV_TIMEOUT
            )
            if resp.status_code in (429, 529):
                raise requests.RequestException(f"transient status {resp.status_code}")
            if resp.status_code != 200:
                logger.warning(
                    "JEV follow-up scoring returned status %s: %s",
                    resp.status_code,
                    resp.text[:300],
                )
                return None

            data = resp.json() or {}
            answers = data.get("answers") or {}

            mastery = _extract_score(answers.get("mastery"))
            ask_type = _extract_choice(answers.get("ask_type"))
            on_topic = _extract_noul(answers.get("answer_on_topic"))
            quality = _extract_score(answers.get("answer_quality"))
            confidence = (
                _extract_confidence(answers.get("ask_type"))
                or _extract_confidence(answers.get("answer_quality"))
            )

            result = {
                "mastery": mastery,
                "ask_type": ask_type,
                "answer_on_topic": on_topic,
                "answer_quality": quality,
                "confidence": confidence,
                "difficulty_hint": derive_difficulty_hint(mastery, ask_type, on_topic),
                "model": str(data.get("model") or _TYPESAFE_MODEL),
                "raw": data,
            }
            logger.info(
                "JEV follow-up score: mastery=%s ask_type=%s on_topic=%s quality=%s hint=%s",
                mastery,
                ask_type,
                on_topic,
                quality,
                result["difficulty_hint"],
            )
            return result
        except requests.RequestException as exc:
            last_err = exc
            wait = _JEV_BACKOFF[min(attempt, len(_JEV_BACKOFF) - 1)]
            logger.warning(
                "JEV follow-up scoring request failed (attempt %d/%d): %s; retrying in %.1fs",
                attempt + 1,
                _JEV_MAX_RETRIES,
                exc,
                wait,
            )
            time.sleep(wait)

    logger.error("JEV follow-up scoring exhausted retries: %s", last_err)
    return None


def _persist_followup_score(
    app,
    *,
    shifu_bid: str,
    outline_item_bid: str,
    progress_record_bid: str,
    answer_block_bid: str,
    user_bid: str,
    question: str,
    answer: str,
    result: dict[str, Any],
) -> None:
    """Persist a scoring result using its own session inside an app context."""
    from flaskr.dao import db
    from flaskr.service.learn.models import LearnFollowupScore
    from flaskr.util import generate_id

    with app.app_context():
        # Idempotency: one row per answer block.
        existing = (
            LearnFollowupScore.query.filter(
                LearnFollowupScore.answer_block_bid == answer_block_bid,
                LearnFollowupScore.deleted == 0,
            )
            .order_by(LearnFollowupScore.id.desc())
            .first()
        )
        if existing:
            return

        record = LearnFollowupScore(
            score_bid=generate_id(app),
            user_bid=user_bid,
            shifu_bid=shifu_bid,
            outline_item_bid=outline_item_bid,
            progress_record_bid=progress_record_bid,
            answer_block_bid=answer_block_bid,
            question=question or "",
            answer_excerpt=(answer or "")[:_ANSWER_EXCERPT_MAX],
            mastery_score=result.get("mastery"),
            ask_type=result.get("ask_type"),
            answer_on_topic=result.get("answer_on_topic"),
            answer_quality=result.get("answer_quality"),
            difficulty_hint=result.get("difficulty_hint"),
            confidence=result.get("confidence"),
            provider_model=result.get("model") or "",
            raw_json=json.dumps(result.get("raw") or {}, ensure_ascii=False),
            deleted=0,
        )
        db.session.add(record)
        db.session.commit()


def schedule_followup_scoring(
    app,
    *,
    shifu_bid: str,
    outline_item_bid: str,
    progress_record_bid: str,
    answer_block_bid: str,
    user_bid: str,
    question: str,
    answer: str,
    chapter_title: str = "",
) -> None:
    """
    Fire-and-forget JEV scoring for a follow-up Q&A. Never raises.
    """
    try:
        if not _jev_available():
            return

        def _run() -> None:
            try:
                result = score_followup(question, answer, chapter_title)
                if not result:
                    return
                _persist_followup_score(
                    app,
                    shifu_bid=shifu_bid,
                    outline_item_bid=outline_item_bid,
                    progress_record_bid=progress_record_bid,
                    answer_block_bid=answer_block_bid,
                    user_bid=user_bid,
                    question=question,
                    answer=answer,
                    result=result,
                )
            except Exception as exc:  # never propagate to the request
                logger.warning("follow-up scoring failed: %r", exc)

        _scoring_executor.submit(_run)
    except Exception as exc:  # submission itself must never break the ask flow
        logger.warning("failed to schedule follow-up scoring: %r", exc)
