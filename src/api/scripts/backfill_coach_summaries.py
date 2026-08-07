"""Backfill missing ``coach_sessions.ai_summary`` via the LLM (rate-limited).

Internal-system tool: finds coaching sessions that have meaningful free-text
input (``topic`` / ``mentor_notes`` / ``learner_notes`` / ``action_items``)
but no persisted ``ai_summary``, and generates one per session through
``flaskr.service.coach.summary.generate_ai_summary``.

Rate limiting: a small batch size (default 5) plus a ``--sleep-seconds`` pause
(default 1s) keeps LLM concurrency under provider limits — the same rationale
as the internal free-billing policy (usage recorded, never billed).

Usage (run inside the api container, from /app):

    python scripts/backfill_coach_summaries.py --dry-run
    python scripts/backfill_coach_summaries.py --limit 50 --batch-size 5 --sleep-seconds 1
    python scripts/backfill_coach_summaries.py --session-bid <bid> --session-bid <bid>

Never raises per-session: ``generate_ai_summary`` returns ``{}`` on LLM
failure, which leaves ``ai_summary`` untouched.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Ensure `src/api` is on sys.path when executed as a file path.
_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

# Avoid side-effectful app auto-creation on import.
os.environ.setdefault("SKIP_APP_AUTOCREATE", "1")

from app import create_app  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill missing coach_sessions.ai_summary via LLM, "
            "rate-limited in small batches."
        ),
    )
    parser.add_argument(
        "--session-bid",
        action="append",
        dest="session_bids",
        default=[],
        help="Specific session_bid(s) to summarize; repeatable. Skips the empty-summary scan.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of sessions to process when --session-bid is not used",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Sessions processed per batch before sleeping (rate limiting)",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=1.0,
        help="Pause between batches to respect LLM rate limits",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate summaries even when ai_summary is already set",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be processed without calling the LLM or writing",
    )
    return parser


def _load_candidates(
    session_bids: list[str],
    limit: int,
    overwrite: bool,
) -> list[object]:
    """Load CoachSession rows missing a summary (or all when --overwrite)."""
    from flaskr.service.learning_portal.models import CoachSession

    query = CoachSession.query
    if session_bids:
        query = query.filter(CoachSession.session_bid.in_(session_bids))
    elif not overwrite:
        query = query.filter(
            (CoachSession.ai_summary.is_(None))
            | (CoachSession.ai_summary == "")
        )
    query = query.order_by(CoachSession.session_date.desc())
    return query.limit(limit).all()


def _has_input(session: object) -> bool:
    return any(
        bool(getattr(session, field))
        for field in ("topic", "mentor_notes", "learner_notes", "action_items")
    )


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    app = create_app()

    from flaskr.dao import db
    from flaskr.service.coach.routes import _persist_generated_summary
    from flaskr.service.coach.summary import generate_ai_summary

    with app.app_context():
        candidates = _load_candidates(
            args.session_bids,
            args.limit,
            args.overwrite,
        )
        # Only sessions with something to summarize qualify.
        candidates = [s for s in candidates if _has_input(s)]

        report = {
            "candidates_total": len(candidates),
            "batch_size": args.batch_size,
            "sleep_seconds": args.sleep_seconds,
            "dry_run": args.dry_run,
            "summarized": 0,
            "failed": 0,
            "skipped": 0,
            "sessions": [],
        }

        for index, session in enumerate(candidates, start=1):
            if args.dry_run:
                report["sessions"].append(
                    {
                        "session_bid": session.session_bid,
                        "learner_bid": session.learner_bid,
                        "session_date": str(session.session_date or ""),
                        "status": "would_summarize",
                    }
                )
                report["skipped"] += 1
                continue

            parsed = generate_ai_summary(app, session)
            if parsed:
                _persist_generated_summary(app, session, parsed)
                session.updated_at = (
                    session.updated_at or session.created_at
                )
                db.session.commit()
                report["summarized"] += 1
                report["sessions"].append(
                    {
                        "session_bid": session.session_bid,
                        "learner_bid": session.learner_bid,
                        "status": "summarized",
                        "ai_summary": bool(session.ai_summary),
                    }
                )
            else:
                db.session.rollback()
                report["failed"] += 1
                report["sessions"].append(
                    {
                        "session_bid": session.session_bid,
                        "learner_bid": session.learner_bid,
                        "status": "llm_failed",
                    }
                )

            if (
                not args.dry_run
                and index % args.batch_size == 0
                and index < len(candidates)
            ):
                time.sleep(args.sleep_seconds)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
