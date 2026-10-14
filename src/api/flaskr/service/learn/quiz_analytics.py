"""
Quiz analytics: persistence, chapter aggregation, and query helpers.

Follows the async pattern from ``followup_scoring.py`` — a module-level thread
pool plus an app context and its own DB session. All side-channel work is
best-effort and never raises into the caller.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from flask import Flask


logger = logging.getLogger(__name__)

_quiz_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="jev_quiz_")

# Ordered "weak point" threshold: below this partial score counts as weak.
_WEAK_PARTIAL_THRESHOLD = 2.0


def _utcnow():
    from datetime import datetime

    return datetime.now()


def record_quiz_question(
    app: Flask,
    *,
    shifu_bid: str,
    outline_item_bid: str,
    progress_record_bid: str,
    user_bid: str,
    block_bid: str,
    position: int,
    question: dict[str, Any],
    mdflow: str,
    paragraph: str = "",
    validity: dict[str, Any] | None = None,
    provider_model: str = "",
) -> str | None:
    """Insert a quiz question row (idempotent by block_bid). Returns question_bid."""
    from flaskr.dao import db
    from flaskr.service.learn.models import LearnQuizQuestion
    from flaskr.util import generate_id

    try:
        with app.app_context():
            existing = (
                LearnQuizQuestion.query.filter(
                    LearnQuizQuestion.block_bid == block_bid,
                    LearnQuizQuestion.deleted == 0,
                )
                .order_by(LearnQuizQuestion.id.desc())
                .first()
            )
            if existing:
                return existing.question_bid

            question_bid = generate_id(app)
            record = LearnQuizQuestion(
                question_bid=question_bid,
                user_bid=user_bid,
                shifu_bid=shifu_bid,
                outline_item_bid=outline_item_bid,
                progress_record_bid=progress_record_bid,
                block_bid=block_bid,
                position=position,
                question_type=str(question.get("question_type") or ""),
                source_excerpt=(paragraph or "")[:2000],
                mdflow=mdflow,
                options_json=json.dumps(question.get("options") or [], ensure_ascii=False),
                correct_answer=str(question.get("correct_answer") or ""),
                validity_score=(validity or {}).get("validity"),
                unique_answer=(validity or {}).get("unique_answer"),
                difficulty_score=(validity or {}).get("difficulty"),
                reliability_score=(validity or {}).get("reliability"),
                provider_model=provider_model or "",
                raw_json=json.dumps(
                    {"question": question, "validity": (validity or {}).get("raw")},
                    ensure_ascii=False,
                ),
                deleted=0,
            )
            db.session.add(record)
            db.session.commit()
            return question_bid
    except Exception as exc:  # best-effort
        logger.warning("record_quiz_question failed: %r", exc)
        return None


def _extract_question_stem(question_row) -> str:
    """Best-effort stem text for grading prompts (mdflow -> raw_json fallback)."""
    md = question_row.mdflow or ""
    try:
        from markdown_flow.parser.interaction import extract_interaction_question

        extracted = extract_interaction_question(md)
        if extracted:
            return extracted
    except Exception:
        pass
    try:
        raw = question_row.raw_json
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, dict):
            return str((raw.get("question") or {}).get("stem") or "")
    except Exception:
        pass
    return md


def _grade_attempt(
    app: Flask,
    *,
    question_row,
    learner_answer: str,
) -> dict[str, Any] | None:
    """Grade an attempt inline (called inside the worker with app context)."""
    from flaskr.service.learn.quiz_judging import judge_open_answer

    qtype = (question_row.question_type or "").strip()
    reference = question_row.correct_answer or ""
    options: list[str] = []
    try:
        options = json.loads(question_row.options_json) if question_row.options_json else []
    except (ValueError, TypeError):
        options = []

    # Choice questions: deterministic match first.
    if qtype in ("single_choice", "multi_choice"):
        import re

        norm = lambda s: re.sub(r"\s+", "", str(s or "")).strip()
        learner_tokens = set(
            t for t in re.split(r"[|,，、;；/／]+", norm(learner_answer)) if t
        )
        ref_tokens = set(t for t in re.split(r"[|,，、;；/／]+", norm(reference)) if t)
        if not learner_tokens or not ref_tokens:
            return None
        is_correct = 1 if learner_tokens == ref_tokens else 0
        return {"is_correct": is_correct, "score": 4.0 if is_correct else 0.0,
                "grading": {"method": "exact_choice"}}

    # Open (fill/short): JEV semantic grading; fall back to exact-ish match.
    judged = judge_open_answer(
        question=_extract_question_stem(question_row),
        reference_answer=reference,
        learner_answer=learner_answer,
        paragraph=question_row.source_excerpt or "",
    )
    if judged:
        return {
            "is_correct": judged.get("is_correct"),
            "score": judged.get("partial_score"),
            "confidence": judged.get("confidence"),
            "grading": judged,
        }
    # Fallback: normalized substring match.
    import re

    norm = lambda s: re.sub(r"\s+", "", str(s or ""))
    a, b = norm(learner_answer), norm(reference)
    is_correct = 1 if (b and (b in a or a in b)) else 0
    return {
        "is_correct": is_correct,
        "score": 4.0 if is_correct else 0.0,
        "grading": {"method": "fallback_match", "note": "jev unavailable"},
    }


def record_attempt(
    app: Flask,
    *,
    shifu_bid: str,
    outline_item_bid: str,
    progress_record_bid: str,
    user_bid: str,
    question_bid: str,
    answer_block_bid: str,
    learner_answer: str,
) -> None:
    """Grade and persist a learner's quiz attempt (idempotent), then aggregate."""
    from flaskr.dao import db
    from flaskr.service.learn.models import LearnQuizAttempt, LearnQuizQuestion
    from flaskr.util import generate_id

    with app.app_context():
        existing = (
            LearnQuizAttempt.query.filter(
                LearnQuizAttempt.answer_block_bid == answer_block_bid,
                LearnQuizAttempt.deleted == 0,
            )
            .order_by(LearnQuizAttempt.id.desc())
            .first()
        )
        if existing:
            return

        question_row = (
            LearnQuizQuestion.query.filter(
                LearnQuizQuestion.question_bid == question_bid,
                LearnQuizQuestion.deleted == 0,
            )
            .order_by(LearnQuizQuestion.id.desc())
            .first()
        )
        grading: dict[str, Any] | None = None
        if question_row:
            try:
                grading = _grade_attempt(app, question_row=question_row, learner_answer=learner_answer)
            except Exception as exc:
                logger.warning("quiz grading failed: %r", exc)

        record = LearnQuizAttempt(
            attempt_bid=generate_id(app),
            question_bid=question_bid,
            answer_block_bid=answer_block_bid,
            user_bid=user_bid,
            shifu_bid=shifu_bid,
            outline_item_bid=outline_item_bid,
            progress_record_bid=progress_record_bid,
            answer=learner_answer or "",
            is_correct=(grading or {}).get("is_correct"),
            score=(grading or {}).get("score"),
            grading_json=json.dumps((grading or {}).get("grading") or {}, ensure_ascii=False),
            confidence=(grading or {}).get("confidence"),
            deleted=0,
        )
        db.session.add(record)
        db.session.commit()

    # Aggregate for the chapter (best-effort).
    try:
        aggregate_chapter(
            app,
            user_bid=user_bid,
            shifu_bid=shifu_bid,
            outline_item_bid=outline_item_bid,
        )
    except Exception as exc:
        logger.warning("chapter aggregation failed: %r", exc)


def aggregate_chapter(
    app: Flask,
    *,
    user_bid: str,
    shifu_bid: str,
    outline_item_bid: str,
) -> dict[str, Any] | None:
    """Recompute the chapter-level aggregate for one learner and upsert it."""
    from flaskr.dao import db
    from flaskr.service.learn.models import (
        LearnQuizAttempt,
        LearnQuizChapterAggregate,
        LearnQuizQuestion,
    )
    from flaskr.util import generate_id

    with app.app_context():
        question_rows = (
            LearnQuizQuestion.query.filter(
                LearnQuizQuestion.user_bid == user_bid,
                LearnQuizQuestion.shifu_bid == shifu_bid,
                LearnQuizQuestion.outline_item_bid == outline_item_bid,
                LearnQuizQuestion.deleted == 0,
            ).all()
        )
        question_count = len(question_rows)
        qbid_to_meta = {
            q.question_bid: {
                "type": q.question_type or "",
                "stem": _extract_question_stem(q),
                "difficulty": float(q.difficulty_score) if q.difficulty_score is not None else None,
            }
            for q in question_rows
        }

        attempts = (
            LearnQuizAttempt.query.filter(
                LearnQuizAttempt.user_bid == user_bid,
                LearnQuizAttempt.shifu_bid == shifu_bid,
                LearnQuizAttempt.outline_item_bid == outline_item_bid,
                LearnQuizAttempt.deleted == 0,
            ).all()
        )
        attempt_count = len(attempts)
        correct_count = sum(1 for a in attempts if a.is_correct == 1)
        scored = [float(a.score) for a in attempts if a.score is not None]
        accuracy = (correct_count / attempt_count) if attempt_count else None
        mastery = (sum(scored) / len(scored)) if scored else None

        # Weak points: attempt with is_correct==0 or low score.
        weak: list[dict[str, Any]] = []
        for a in attempts:
            score = float(a.score) if a.score is not None else None
            is_weak = a.is_correct == 0 or (score is not None and score < _WEAK_PARTIAL_THRESHOLD)
            if is_weak:
                meta = qbid_to_meta.get(a.question_bid) or {}
                weak.append(
                    {
                        "question_bid": a.question_bid,
                        "type": meta.get("type", ""),
                        "stem": (meta.get("stem") or "")[:200],
                        "score": score,
                        "answer": (a.answer or "")[:200],
                    }
                )

        existing = (
            LearnQuizChapterAggregate.query.filter(
                LearnQuizChapterAggregate.user_bid == user_bid,
                LearnQuizChapterAggregate.shifu_bid == shifu_bid,
                LearnQuizChapterAggregate.outline_item_bid == outline_item_bid,
                LearnQuizChapterAggregate.deleted == 0,
            )
            .order_by(LearnQuizChapterAggregate.id.desc())
            .first()
        )
        payload = dict(
            question_count=question_count,
            attempt_count=attempt_count,
            correct_count=correct_count,
            accuracy=accuracy,
            mastery_score=mastery,
            weak_points_json=json.dumps(weak, ensure_ascii=False),
        )
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            record = existing
        else:
            record = LearnQuizChapterAggregate(
                aggregate_bid=generate_id(app),
                user_bid=user_bid,
                shifu_bid=shifu_bid,
                outline_item_bid=outline_item_bid,
                deleted=0,
                **payload,
            )
            db.session.add(record)
        db.session.commit()
        return {
            "outline_item_bid": outline_item_bid,
            "question_count": question_count,
            "attempt_count": attempt_count,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "mastery_score": mastery,
            "weak_point_count": len(weak),
        }


def schedule_quiz_grading(
    app: Flask,
    *,
    shifu_bid: str,
    outline_item_bid: str,
    progress_record_bid: str,
    user_bid: str,
    question_bid: str,
    answer_block_bid: str,
    learner_answer: str,
) -> None:
    """Fire-and-forget grading of one quiz attempt. Never raises."""
    if not question_bid:
        return

    def _run() -> None:
        try:
            record_attempt(
                app,
                shifu_bid=shifu_bid,
                outline_item_bid=outline_item_bid,
                progress_record_bid=progress_record_bid,
                user_bid=user_bid,
                question_bid=question_bid,
                answer_block_bid=answer_block_bid,
                learner_answer=learner_answer,
            )
        except Exception as exc:
            logger.warning("quiz attempt grading failed: %r", exc)

    try:
        _quiz_executor.submit(_run)
    except Exception as exc:
        logger.warning("failed to schedule quiz grading: %r", exc)


def schedule_chapter_aggregate(
    app: Flask,
    *,
    user_bid: str,
    shifu_bid: str,
    outline_item_bid: str,
) -> None:
    """Fire-and-forget chapter aggregation. Never raises."""

    def _run() -> None:
        try:
            aggregate_chapter(
                app,
                user_bid=user_bid,
                shifu_bid=shifu_bid,
                outline_item_bid=outline_item_bid,
            )
        except Exception as exc:
            logger.warning("scheduled chapter aggregation failed: %r", exc)

    try:
        _quiz_executor.submit(_run)
    except Exception as exc:
        logger.warning("failed to schedule chapter aggregate: %r", exc)


# --------------------------------------------------------------------------
# Query helpers (synchronous, for the API layer)
# --------------------------------------------------------------------------
def get_learner_quiz_analysis(
    app: Flask, *, user_bid: str, shifu_bid: str
) -> dict[str, Any]:
    """Return per-chapter quiz analysis for one learner in one course."""
    from flaskr.service.learn.models import (
        LearnQuizAttempt,
        LearnQuizChapterAggregate,
    )

    with app.app_context():
        aggregates = (
            LearnQuizChapterAggregate.query.filter(
                LearnQuizChapterAggregate.user_bid == user_bid,
                LearnQuizChapterAggregate.shifu_bid == shifu_bid,
                LearnQuizChapterAggregate.deleted == 0,
            )
            .order_by(LearnQuizChapterAggregate.id.asc())
            .all()
        )
        attempts = (
            LearnQuizAttempt.query.filter(
                LearnQuizAttempt.user_bid == user_bid,
                LearnQuizAttempt.shifu_bid == shifu_bid,
                LearnQuizAttempt.deleted == 0,
            ).all()
        )
        total_attempts = len(attempts)
        total_correct = sum(1 for a in attempts if a.is_correct == 1)
        return {
            "user_bid": user_bid,
            "shifu_bid": shifu_bid,
            "total_attempts": total_attempts,
            "total_correct": total_correct,
            "overall_accuracy": (total_correct / total_attempts) if total_attempts else None,
            "chapters": [
                {
                    "outline_item_bid": a.outline_item_bid,
                    "question_count": a.question_count,
                    "attempt_count": a.attempt_count,
                    "correct_count": a.correct_count,
                    "accuracy": float(a.accuracy) if a.accuracy is not None else None,
                    "mastery_score": float(a.mastery_score) if a.mastery_score is not None else None,
                    "weak_points": _safe_json_list(a.weak_points_json),
                    "updated_at": a.updated_at.isoformat() if a.updated_at else None,
                }
                for a in aggregates
            ],
        }


def list_course_quiz_stats(
    app: Flask, *, shifu_bid: str, outline_item_bids: list[str] | None = None
) -> list[dict[str, Any]]:
    """Return chapter-level quiz stats for a course (admin/mentor view)."""
    from flaskr.service.learn.models import LearnQuizChapterAggregate

    with app.app_context():
        query = LearnQuizChapterAggregate.query.filter(
            LearnQuizChapterAggregate.shifu_bid == shifu_bid,
            LearnQuizChapterAggregate.deleted == 0,
        )
        if outline_item_bids:
            query = query.filter(
                LearnQuizChapterAggregate.outline_item_bid.in_(outline_item_bids)
            )
        rows = query.order_by(LearnQuizChapterAggregate.id.asc()).all()
        return [
            {
                "outline_item_bid": r.outline_item_bid,
                "user_bid": r.user_bid,
                "question_count": r.question_count,
                "attempt_count": r.attempt_count,
                "correct_count": r.correct_count,
                "accuracy": float(r.accuracy) if r.accuracy is not None else None,
                "mastery_score": float(r.mastery_score) if r.mastery_score is not None else None,
                "weak_point_count": len(_safe_json_list(r.weak_points_json)),
            }
            for r in rows
        ]


def _safe_json_list(raw: Any) -> list[Any]:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except (ValueError, TypeError):
        return []
