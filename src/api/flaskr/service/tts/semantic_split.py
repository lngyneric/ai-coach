"""
Semantic TTS text segmentation helpers — jev (TypeSafe System One) boundary layer.

jev is a *typed-judgment* model (noul / choice / score), not a text generator,
so it cannot emit a segmentation. Instead it is used here as a **boundary
confidence classifier**: when a long clause must be split to satisfy a provider's
character/byte limit and deterministic sentence/clause boundaries are exhausted,
we ask jev (in a single batched request) which candidate break-point is the most
natural place to split. Any failure falls back to a deterministic split so TTS is
never blocked.

API reference: https://docs.typesafe.ai/api.md
"""

from __future__ import annotations

import logging
import os
import time

import requests


logger = logging.getLogger(__name__)

_TYPESAFE_URL = "https://api.typesafe.ai/v1/systemone"
_TYPESAFE_MODEL = "jev-latest"
_JEV_TIMEOUT = 8.0
_JEV_MAX_RETRIES = 3
_JEV_BACKOFF = (0.5, 1.0, 2.0)
# Minimum confidence for a jev-chosen break-point to be accepted.
_JEV_ACCEPT_THRESHOLD = 0.5
# Cap candidates per request so a super-long clause does not blow up token usage.
_JEV_MAX_CANDIDATES = 40


def _jev_available() -> bool:
    """True when a TypeSafe API key is present in the environment."""
    return bool(os.environ.get("TYPESAFE_API_KEY"))


def _extract_noul(answer: object) -> float:
    """Extract the yes-probability from a noul answer object."""
    if not isinstance(answer, dict):
        return 0.0
    value = answer.get("noul")
    if value is None:
        value = answer.get("value")
    if value is None:
        value = answer.get("probability")
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def _sample_candidates(candidates: list[int], limit: int) -> list[int]:
    """Evenly sample at most ``limit`` candidates, always keeping the first/last."""
    if len(candidates) <= limit:
        return candidates
    step = len(candidates) / limit
    sampled = [candidates[int(i * step)] for i in range(limit)]
    if sampled[-1] != candidates[-1]:
        sampled[-1] = candidates[-1]
    return sampled


def choose_split_point_via_jev(clause: str, candidate_points: list[int]) -> int | None:
    """
    Ask jev which candidate break-point inside ``clause`` is the best TTS split.

    All candidates are evaluated in a single System One request (one noul
    question per point). Returns the chosen character index, or ``None`` if no
    candidate meets the confidence threshold or the call fails.
    """
    if not candidate_points:
        return None
    if not _jev_available():
        logger.debug(
            "jev not available (no TYPESAFE_API_KEY); skipping boundary judgment"
        )
        return None

    api_key = os.environ["TYPESAFE_API_KEY"]
    points = _sample_candidates(candidate_points, _JEV_MAX_CANDIDATES)

    questions = {}
    for idx, pos in enumerate(points):
        # Present the two halves explicitly: asking the model to count character
        # offsets is unreliable, but judging a shown break is accurate.
        questions[f"p{idx}"] = {
            "type": "noul",
            "instructions": {
                "question": (
                    "这是一段待做语音合成（TTS）的中文文本，计划在 before 与 after "
                    "之间断开作为朗读停顿。这个断点作为朗读停顿是否自然？"
                    "是否会把一个词语、数字、专有名词或固定搭配从中间切断？"
                ),
                "before": clause[:pos],
                "after": clause[pos:],
            },
            "criteria": {
                "true": "断点自然、前后语义完整，适合作朗读停顿",
                "false": "断点生硬，或切断了词语/数字/专有名词",
            },
        }

    payload = {
        "state": clause,
        "model": _TYPESAFE_MODEL,
        "questions": questions,
    }
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
                # Overloaded — back off and retry.
                raise requests.RequestException(f"transient status {resp.status_code}")
            if resp.status_code != 200:
                # Non-retryable (e.g. 401/422); give up immediately.
                logger.error(
                    "jev returned status %s: %s", resp.status_code, resp.text[:300]
                )
                return None

            data = resp.json() or {}
            answers = data.get("answers") or {}
            best_point: int | None = None
            best_score = _JEV_ACCEPT_THRESHOLD
            for idx, pos in enumerate(points):
                score = _extract_noul(answers.get(f"p{idx}"))
                if score >= best_score:
                    best_score = score
                    best_point = pos
            if best_point is None:
                logger.debug(
                    "jev found no confident break-point (best<%.2f)",
                    _JEV_ACCEPT_THRESHOLD,
                )
                return None
            logger.info("jev chose break-point %d (score=%.2f)", best_point, best_score)
            return best_point
        except requests.RequestException as exc:
            last_err = exc
            wait = _JEV_BACKOFF[min(attempt, len(_JEV_BACKOFF) - 1)]
            logger.warning(
                "jev request failed (attempt %d/%d): %s; retrying in %.1fs",
                attempt + 1,
                _JEV_MAX_RETRIES,
                exc,
                wait,
            )
            time.sleep(wait)

    logger.error("jev request exhausted retries: %s", last_err)
    return None
