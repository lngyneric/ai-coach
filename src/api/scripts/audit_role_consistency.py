#!/usr/bin/env python3
"""Audit `is_operator=1` vs `user_role_assignments` consistency (B6).

docs/ROLE-ACCESS-TEST-REPORT.md B6 / P0-PERMISSION-MODEL-UPGRADE.md §十:

After B6, `user_role_assignments` is the single source of truth for the
5-level role model. The legacy `user_users.is_operator` flag is honoured
ONLY as a transitional fallback for users with **zero** role assignments.
This script verifies that invariant across the whole `user_users` table:

  - VIOLATION (P0): `is_operator=1` AND the user holds roles but none is
    `role-admin`  -> the flag is being silently ignored (source-of-truth
    drift, and a privilege surprise: B2 would not treat them as course
    admin either).
  - TRANSITIONAL (P1): `is_operator=1` AND zero roles -> still treated as
    admin fallback (B6), but the retirement plan (§十) wants either a
    `role-admin` assignment added or the flag cleared.
  - INFO: `role-admin` assignment exists regardless of `is_operator`
    (role is authoritative and sufficient).
  - INFO: `is_operator=0` / `is_creator` flags are not part of this check
    (they are legacy markers being retired).

Exit code 0 = no P0/P1 findings; 1 = findings exist. The script is
read-only and safe to re-run; it never writes to the database.

Usage:
    python scripts/audit_role_consistency.py            # dry-run report
    python scripts/audit_role_consistency.py --json     # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from sqlalchemy import text  # noqa: E402

from app import create_app  # noqa: E402
from flaskr.dao import db  # noqa: E402

ROLE_ADMIN = "role-admin"


def _role_assignment_map() -> dict[str, list[str]]:
    """Return {user_bid: [role_bid, ...]} for all user_role_assignments."""
    rows = db.session.execute(
        text(
            "SELECT user_bid, role_bid FROM user_role_assignments"
        )
    ).fetchall()
    mapping: dict[str, list[str]] = {}
    for user_bid, role_bid in rows:
        mapping.setdefault(user_bid, []).append(role_bid)
    return mapping


def audit(app) -> tuple[list[dict], list[dict], list[dict]]:
    """Run the consistency audit.

    Returns (violations, transitional, info) as lists of dicts.
    """
    with app.app_context():
        assignments = _role_assignment_map()
        users = db.session.execute(
            text(
                "SELECT user_bid, nickname, is_operator, is_creator, "
                "is_certifier FROM user_users ORDER BY user_bid"
            )
        ).fetchall()

    violations: list[dict] = []
    transitional: list[dict] = []
    info: list[dict] = []
    for user_bid, nickname, is_operator, is_creator, is_certifier in users:
        roles = assignments.get(user_bid, [])
        row = {
            "user_bid": user_bid,
            "nickname": nickname,
            "is_operator": bool(is_operator),
            "roles": roles,
        }
        if is_operator:
            if roles and ROLE_ADMIN not in roles:
                row["detail"] = (
                    "is_operator=1 but roles present and no role-admin -> "
                    "flag ignored by B6; grant role-admin or clear the flag"
                )
                violations.append(row)
            elif not roles:
                row["detail"] = (
                    "is_operator=1 with zero roles -> legacy admin fallback "
                    "(B6); retirement wants role-admin assignment or clear"
                )
                transitional.append(row)
        if ROLE_ADMIN in roles:
            info.append(
                {
                    "user_bid": user_bid,
                    "nickname": nickname,
                    "is_operator": bool(is_operator),
                    "roles": roles,
                    "detail": "role-admin assigned (authoritative, ok)",
                }
            )
    return violations, transitional, info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json", action="store_true", help="emit a JSON report instead of text"
    )
    args = parser.parse_args()

    app = create_app()
    violations, transitional, info = audit(app)

    report = {
        "violations": violations,
        "transitional": transitional,
        "info_admin_users": info,
        "summary": {
            "violations": len(violations),
            "transitional": len(transitional),
            "role_admin_holders": len(info),
        },
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"== role consistency audit (B6) ==")
        print(f"is_operator=1 users with roles but no role-admin (P0): {len(violations)}")
        for v in violations:
            print(f"  [P0] {v['user_bid']!r} ({v['nickname']!r}) roles={v['roles']}")
        print(f"is_operator=1 users with zero roles (P1 transitional): {len(transitional)}")
        for t in transitional:
            print(f"  [P1] {t['user_bid']!r} ({t['nickname']!r})")
        print(f"role-admin holders (authoritative, ok): {len(info)}")

    # Exit code reflects only actionable findings (P0 violations; P1 is
    # transitional and advisory).
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
