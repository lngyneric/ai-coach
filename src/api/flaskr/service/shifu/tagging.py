"""Course tagging — publish hook that syncs role tags into course_position_tags.

闭环 1 (PORTAL-COURSE-ALIGNMENT): when a course is published, extract
``role:*`` tags from its keywords and upsert rows into ``course_position_tags``
so the course enters the recommendation pool immediately.

Design rules (docs/P1P2-DESIGN.md §4 + docs/PORTAL-COURSE-ALIGNMENT.md 闭环 1):

- Read the published course's ``keywords``. The legacy format is a
  comma-separated string (e.g. ``"role:sales,lesson_type:practice,task:new-sales"``);
  a JSON array (``["role:sales", ...]``) is also accepted for forward-compat.
  Both ``None`` and malformed values degrade to no-op, never raise.
- Only ``role:<code>`` items become recommendation rows (position = role code).
  ``lesson_type:<type>`` / ``task:<task>`` items are combined into the row's
  ``tag`` column (pipe-separated, per P1P2 §4.2) so future L2/L3 weighting can
  use them; the ranking algorithm itself is untouched.
- No role tag → return False without writing anything (does not block publish).
- Upsert on the unique ``(shifu_bid, position)``: existing rows get
  weight/tag refreshed and ``is_active`` reset to 1 (idempotent re-publish).
- Every failure is caught and logged — syncing must never block publishing.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from flaskr.dao import db
from flaskr.service.learning_portal.models import CoursePositionTag
from flaskr.service.shifu.models import PublishedShifu

logger = logging.getLogger(__name__)

# Default recommendation weight for a published course (P1P2 §4.3 L1).
DEFAULT_ROLE_WEIGHT = 10

# role code → Chinese label (aligns with P1P2 Q2 role codes). Recommend.py's
# own fuzzy map stays authoritative for learner-side matching; this only fills
# course_position_tags.position_name for display.
_ROLE_LABELS: dict[str, str] = {
    "sales": "销售",
    "production": "生产",
    "hr": "人事",
    "qc": "质检",
    "management": "管理",
    "medical": "检验",
    "digital": "数字化",
    "general": "通用",
}

_PREFIX_ROLE = "role:"
_PREFIX_LESSON_TYPE = "lesson_type:"
_PREFIX_TASK = "task:"


def _parse_keywords(raw) -> list[str]:
    """Normalize the ``keywords`` column into a list of non-empty tags.

    Accepted shapes:
    - comma-separated string (legacy, ``String(100)`` column);
    - JSON array string / Python list (forward-compat).
    Any parse failure / empty value → ``[]`` (caller treats it as a no-op).
    """
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except (ValueError, TypeError):
                pass  # fall through to comma split below
        return [part.strip() for part in stripped.split(",") if part.strip()]
    return []


def _extract_tags(tags: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Split tags into ``(roles, lesson_types, tasks)`` by prefix."""
    roles: list[str] = []
    lesson_types: list[str] = []
    tasks: list[str] = []
    for tag in tags:
        if tag.startswith(_PREFIX_ROLE):
            value = tag[len(_PREFIX_ROLE) :].strip()
            if value:
                roles.append(value)
        elif tag.startswith(_PREFIX_LESSON_TYPE):
            value = tag[len(_PREFIX_LESSON_TYPE) :].strip()
            if value:
                lesson_types.append(value)
        elif tag.startswith(_PREFIX_TASK):
            value = tag[len(_PREFIX_TASK) :].strip()
            if value:
                tasks.append(value)
    return roles, lesson_types, tasks


def _build_combined_tag(lesson_types: list[str], tasks: list[str]) -> str:
    """lesson_type + task combined tag string (P1P2 §4.2), pipe-separated."""
    parts = [f"{_PREFIX_LESSON_TYPE}{t}" for t in lesson_types]
    parts += [f"{_PREFIX_TASK}{t}" for t in tasks]
    return "|".join(parts)


def sync_course_position_tags(app, shifu_bid: str) -> bool:
    """Upsert ``course_position_tags`` rows from a published course's tags.

    Returns ``True`` when at least one row was written, ``False`` on no-op.
    Never raises — all failures are logged so publishing is never blocked.

    Args:
        app: Flask application instance (``app.app_context()`` is entered here).
        shifu_bid: business id of the published course.
    """
    with app.app_context():
        course = (
            PublishedShifu.query.filter_by(shifu_bid=shifu_bid)
            .order_by(PublishedShifu.id.desc())
            .first()
        )
        if course is None:
            app.logger.warning(
                "[tagging] sync_course_position_tags: no published course %s",
                shifu_bid,
            )
            return False

        roles, lesson_types, tasks = _extract_tags(_parse_keywords(course.keywords))
        if not roles:
            app.logger.info(
                "[tagging] course %s has no role tag — skip recommendation sync",
                shifu_bid,
            )
            return False

        combined_tag = _build_combined_tag(lesson_types, tasks) or None
        now = datetime.now()
        try:
            written = 0
            for role in roles:
                existing = CoursePositionTag.query.filter_by(
                    shifu_bid=shifu_bid, position=role
                ).first()
                if existing is not None:
                    existing.weight = DEFAULT_ROLE_WEIGHT
                    if combined_tag:
                        existing.tag = combined_tag
                    existing.is_active = 1
                    existing.updated_at = now
                else:
                    db.session.add(
                        CoursePositionTag(
                            shifu_bid=shifu_bid,
                            position=role,
                            position_name=_ROLE_LABELS.get(role),
                            tag=combined_tag,
                            weight=DEFAULT_ROLE_WEIGHT,
                            is_active=1,
                            created_at=now,
                            updated_at=now,
                        )
                    )
                written += 1
            db.session.commit()
            app.logger.info(
                "[tagging] synced course %s → %d role position(s)", shifu_bid, written
            )
            return True
        except Exception as exc:  # noqa: BLE001 — must never block publishing
            db.session.rollback()
            app.logger.error(
                "[tagging] failed to sync course_position_tags for %s: %s",
                shifu_bid,
                exc,
            )
            return False
