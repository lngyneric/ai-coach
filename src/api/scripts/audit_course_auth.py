#!/usr/bin/env python3
"""Audit and optionally normalize ai_course_auth.auth_type formats.

Scans the full `ai_course_auth` table and reports the auth_type format
distribution:
  - JSON_ARRAY     : canonical form, e.g. ["view"] / ["view","edit","publish"]
  - JSON_STRING    : JSON-encoded string, e.g. "view"
  - JSON_SCALAR    : JSON-encoded number, e.g. 1 / 2 / 4
  - JSON_OTHER     : other valid JSON (bool / dict / null)
  - PLAIN_SINGLE   : plain string token, e.g. view / edit / publish
  - PLAIN_COMMA    : comma separated plain string, e.g. view,edit
  - PLAIN_NUMERIC  : plain numeric string, e.g. 1 / 2 / 4
  - PLAIN_OTHER    : anything else (unrecognized plain text)
  - EMPTY          : empty / null

Flags every non-JSON_ARRAY record (id, course_id, user_id, auth_type,
status) so legacy formats can be located and fixed.

`--fix` normalizes non-JSON_ARRAY values into the canonical JSON array form
(e.g. "view" -> ["view"], "view,edit" -> ["view","edit"], "1" -> ["1"]),
preserving the authorization semantics of status=1 records. The script is
idempotent and safe to re-run: after a successful --fix pass the table should
report 100% JSON_ARRAY.

Usage:
    python scripts/audit_course_auth.py          # dry-run report only
    python scripts/audit_course_auth.py --fix    # normalize legacy formats
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app import create_app  # noqa: E402
from flaskr.dao import db  # noqa: E402
from flaskr.service.shifu.models import AiCourseAuth  # noqa: E402

# Canonical permission tokens recognized by shifu_permission_verification.
_KNOWN_TOKENS = {"view", "edit", "publish"}


def classify(auth_type: object) -> str:
    """Return a format category label for an auth_type value."""
    text = str(auth_type or "").strip()
    if not text:
        return "EMPTY"
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        parsed = None
    if isinstance(parsed, list):
        return "JSON_ARRAY"
    if isinstance(parsed, str):
        return "JSON_STRING"
    if isinstance(parsed, bool):
        return "JSON_OTHER"
    if isinstance(parsed, (int, float)):
        return "JSON_SCALAR"
    if parsed is not None:
        return "JSON_OTHER"
    # Not valid JSON: legacy plain-text formats.
    if text.lower() in _KNOWN_TOKENS:
        return "PLAIN_SINGLE"
    if "," in text:
        return "PLAIN_COMMA"
    if text.isdigit():
        return "PLAIN_NUMERIC"
    return "PLAIN_OTHER"


def normalize_to_json_array(auth_type: object):
    """Convert a legacy auth_type value to the canonical JSON array form.

    Returns None when the value is already canonical JSON, is empty, or
    cannot be safely normalized (left untouched for manual review).
    """
    text = str(auth_type or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        parsed = None
    if isinstance(parsed, list):
        return None  # already canonical
    if isinstance(parsed, str):
        return json.dumps([parsed]) if parsed.strip() else None
    if isinstance(parsed, bool):
        return None  # not a permission token - manual review
    if isinstance(parsed, (int, float)):
        return json.dumps([str(int(parsed))])
    if parsed is not None:
        return None  # dict/other JSON - manual review
    # Plain text: split on comma, keep non-empty tokens.
    tokens = [part.strip() for part in text.split(",") if part.strip()]
    if not tokens:
        return None
    return json.dumps(tokens)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fix",
        action="store_true",
        help="normalize non-JSON_ARRAY auth_type values to JSON arrays",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        rows = AiCourseAuth.query.order_by(AiCourseAuth.id).all()
        total = len(rows)
        dist: dict[str, int] = {}
        anomalies = []
        for row in rows:
            cat = classify(row.auth_type)
            dist[cat] = dist.get(cat, 0) + 1
            if cat != "JSON_ARRAY":
                anomalies.append(row)

        print(f"== ai_course_auth auth_type 格式分布 (total={total}) ==")
        for cat, cnt in sorted(dist.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {cat:<14} {cnt}")

        if not anomalies:
            print("\n无异常记录：全部为 JSON_ARRAY 规范格式。")
            return 0

        print(f"\n== 非 JSON_ARRAY 记录 ({len(anomalies)}) ==")
        for row in anomalies:
            print(
                f"  id={row.id} course_id={row.course_id} "
                f"user_id={row.user_id} auth_type={row.auth_type!r} status={row.status}"
            )

        if not args.fix:
            print("\n[dry-run] 未执行修改。加 --fix 可将纯字符串 auth_type 规范化为 JSON 数组。")
            return 1

        print("\n== 执行 --fix 规范化 ==")
        changed = 0
        skipped = 0
        for row in anomalies:
            new_value = normalize_to_json_array(row.auth_type)
            if new_value is None or new_value == row.auth_type:
                skipped += 1
                print(f"  [skip] id={row.id} {row.auth_type!r} 无法安全规范化")
                continue
            print(f"  id={row.id} {row.auth_type!r} -> {new_value}")
            row.auth_type = new_value
            changed += 1
        db.session.commit()
        print(f"已更新 {changed} 条，跳过 {skipped} 条。")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
