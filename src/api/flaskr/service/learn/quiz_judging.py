"""
JEV-based judgment for in-lesson quiz questions.

Provides three kinds of validity judgment via TypeSafe System One (JEV), a
typed-judgment model returning noul / choice / score answers:

1. ``judge_question_validity`` — is the generated question well-formed
   (unambiguous, unique correct answer, plausible distractors) and is it a
   trustworthy assessment (reliability meta-judgment)?
2. ``judge_open_answer`` — lenient semantic grading of fill-in / short-answer
   responses (instead of brittle exact string matching).

Transport (endpoint, retry/backoff, extract helpers) mirrors
``followup_scoring.py``. Every function returns ``None`` on failure so callers
can degrade gracefully and never block the learner.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests


logger = logging.getLogger(__name__)

_TYPESAFE_URL = "https://api.typesafe.ai/v1/systemone"
_TYPESAFE_MODEL = "jev-latest"
_JEV_TIMEOUT = 8.0
_JEV_MAX_RETRIES = 3
_JEV_BACKOFF = (0.5, 1.0, 2.0)

# Minimum validity score (0..4 scale) for a generated question to be accepted.
VALIDITY_ACCEPT_THRESHOLD = 2.5

_QUESTION_VALIDITY_LEVELS = [
    "无效：题干歧义、无唯一答案或选项不合理",
    "较差：题意含混，正确答案存疑",
    "尚可：基本可判，但表述或干扰项有明显瑕疵",
    "良好：题干清晰、答案唯一、干扰项合理",
    "优秀：题意精准、答案唯一、干扰项能有效区分理解程度",
]

_DIFFICULTY_LEVELS = [
    "非常容易：只需记忆/常识",
    "较容易：直接复述段落信息",
    "中等：需要理解而非照抄",
    "较难：需要整合多处信息或推理",
    "很难：需要迁移应用或深入推理",
]

_RELIABILITY_LEVELS = [
    "不可信：该题无法有效反映学员是否掌握",
    "偏弱：受表述/答案歧义影响，参考价值有限",
    "一般：有一定参考价值但需谨慎解读",
    "较可信：能较好地反映学员掌握情况",
    "可信：能准确反映学员对该知识点的掌握",
]

_MISCONCEPTION_OPTIONS = {
    "correct": "回答正确，覆盖了关键要点",
    "imprecise": "方向正确但表述不精确或要点不全",
    "misconception": "存在概念性错误或明显误解",
    "irrelevant": "答非所问或与题目无关",
}


def _jev_available() -> bool:
    return bool(os.environ.get("TYPESAFE_API_KEY"))


def _extract_score(answer: Any) -> float | None:
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
    if not isinstance(answer, dict):
        return None
    value = answer.get("choice")
    return str(value) if value is not None else None


def _extract_noul(answer: Any) -> float | None:
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
    if not isinstance(answer, dict):
        return None
    value = answer.get("confidence")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _call_systemone(
    state: dict[str, Any], questions: dict[str, Any]
) -> dict[str, Any] | None:
    """POST to TypeSafe System One with retry/backoff. None on failure."""
    if not _jev_available():
        logger.debug("jev not available (no TYPESAFE_API_KEY); skipping quiz judgment")
        return None

    payload = {"state": state, "model": _TYPESAFE_MODEL, "questions": questions}
    headers = {
        "Authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}",
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
                    "JEV quiz judgment returned status %s: %s",
                    resp.status_code,
                    resp.text[:300],
                )
                return None
            return resp.json() or {}
        except requests.RequestException as exc:
            last_err = exc
            wait = _JEV_BACKOFF[min(attempt, len(_JEV_BACKOFF) - 1)]
            logger.warning(
                "JEV quiz judgment request failed (attempt %d/%d): %s; retrying in %.1fs",
                attempt + 1,
                _JEV_MAX_RETRIES,
                exc,
                wait,
            )
            time.sleep(wait)

    logger.error("JEV quiz judgment exhausted retries: %s", last_err)
    return None


def judge_question_validity(
    *,
    stem: str,
    options: list[str] | None,
    correct_answer: str,
    paragraph: str = "",
    question_type: str = "",
) -> dict[str, Any] | None:
    """
    Judge whether a generated question is valid and trustworthy.

    Returns a dict with ``validity``, ``unique_answer``, ``difficulty``,
    ``reliability``, ``accepted``, ``model`` and ``raw``; or ``None`` on failure.
    """
    if not (stem or "").strip():
        return None

    state = {
        "paragraph": (paragraph or "")[:4000],
        "question_type": question_type or "",
        "stem": stem or "",
        "options": options or [],
        "correct_answer": correct_answer or "",
    }
    questions = {
        "validity": {
            "type": "score",
            "instructions": (
                "评估 state 中这道题作为检测学员理解的题目是否有效：题干是否清晰无歧义、"
                "正确答案是否正确且唯一（多选除外）、干扰项是否合理。"
            ),
            "criteria": list(_QUESTION_VALIDITY_LEVELS),
        },
        "unique_answer": {
            "type": "noul",
            "instructions": "state 中这道题的正确答案是否唯一且明确（多选题允许多个正确项）？",
            "criteria": {
                "true": "答案唯一明确，不存在其它可接受的正确答案",
                "false": "答案不唯一或存在歧义",
            },
        },
        "difficulty": {
            "type": "score",
            "instructions": "评估这道题相对于 state.paragraph 所讲内容的难度。",
            "criteria": list(_DIFFICULTY_LEVELS),
        },
        "reliability": {
            "type": "score",
            "instructions": (
                "元判断：这道题作为评估学员是否掌握 state.paragraph 内容的工具，"
                "其结论是否可信？"
            ),
            "criteria": list(_RELIABILITY_LEVELS),
        },
    }

    data = _call_systemone(state, questions)
    if not data:
        return None
    answers = data.get("answers") or {}
    validity = _extract_score(answers.get("validity"))
    unique = _extract_noul(answers.get("unique_answer"))
    difficulty = _extract_score(answers.get("difficulty"))
    reliability = _extract_score(answers.get("reliability"))
    accepted = bool(
        validity is not None
        and validity >= VALIDITY_ACCEPT_THRESHOLD
        and (unique is None or unique >= 0.5)
    )
    result = {
        "validity": validity,
        "unique_answer": unique,
        "difficulty": difficulty,
        "reliability": reliability,
        "accepted": accepted,
        "confidence": _extract_confidence(answers.get("validity")),
        "model": str(data.get("model") or _TYPESAFE_MODEL),
        "raw": data,
    }
    logger.info(
        "JEV quiz validity: validity=%s unique=%s difficulty=%s reliability=%s accepted=%s",
        validity,
        unique,
        difficulty,
        reliability,
        accepted,
    )
    return result


def judge_open_answer(
    *,
    question: str,
    reference_answer: str,
    learner_answer: str,
    paragraph: str = "",
) -> dict[str, Any] | None:
    """
    Leniently grade a fill-in / short-answer response semantically.

    Returns a dict with ``correct``, ``partial_score``, ``misconception``,
    ``model`` and ``raw``; or ``None`` on failure.
    """
    if not (learner_answer or "").strip():
        return None

    state = {
        "paragraph": (paragraph or "")[:3000],
        "question": question or "",
        "reference_answer": reference_answer or "",
        "learner_answer": learner_answer or "",
    }
    questions = {
        "correct": {
            "type": "noul",
            "instructions": (
                "state 中 learner_answer 是否在语义上正确回答了 question？"
                "允许同义表述、措辞不同但含义一致；只要关键要点正确即判为对。"
            ),
            "criteria": {
                "true": "语义正确，关键要点与 reference_answer 一致",
                "false": "语义错误、要点缺失或存在误解",
            },
        },
        "partial_score": {
            "type": "score",
            "instructions": "评估 learner_answer 的完整与准确程度（0~4 级）。",
            "criteria": [
                "完全错误或无关",
                "沾边但关键要点缺失",
                "部分正确，要点不全",
                "基本正确，略有遗漏或不精确",
                "完全正确且表述准确",
            ],
        },
        "misconception": {
            "type": "choice",
            "instructions": "判断 learner_answer 属于哪一类。",
            "criteria": dict(_MISCONCEPTION_OPTIONS),
        },
    }

    data = _call_systemone(state, questions)
    if not data:
        return None
    answers = data.get("answers") or {}
    correct = _extract_noul(answers.get("correct"))
    partial = _extract_score(answers.get("partial_score"))
    misconception = _extract_choice(answers.get("misconception"))
    result = {
        "correct": correct,
        "partial_score": partial,
        "misconception": misconception,
        "is_correct": (1 if correct is not None and correct >= 0.5 else (0 if correct is not None else None)),
        "confidence": _extract_confidence(answers.get("correct")),
        "model": str(data.get("model") or _TYPESAFE_MODEL),
        "raw": data,
    }
    logger.info(
        "JEV quiz open answer: correct=%s partial=%s misconception=%s",
        correct,
        partial,
        misconception,
    )
    return result
