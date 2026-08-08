"""Coach permission service — 5-role permission model (AI-Coach P0).

This module is the backend half of the P0 permission model upgrade
(``docs/P0-PERMISSION-MODEL-UPGRADE.md`` + ``docs/P0-DESIGN-CORRECTION.md``).
It supplements the legacy two-flag (``is_creator`` / ``is_operator``) checks
with the 5-level role model stored in ``coach_roles`` +
``user_role_assignments``:

=====================  ===============================================
``resolve_user_roles``      roles for a user (role_bid + permissions)
``has_permission``          boolean permission check
``visible_students_scope``  data-scope string for learner-list filtering
``get_user_permissions``    union of permission keys (portal endpoint)
=====================  ===============================================

Roles are matched by the stable ``role_bid`` (``role-admin`` / ``role-hr`` /
``role-dept-head`` / ``role-coach`` / ``role-learner``). ``coach_roles`` has
no ``sort_order`` column (P0-DESIGN-CORRECTION D2), so multi-role resolution
uses the fixed priority table ``ROLE_PRIORITY`` instead (option b: no DDL).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Sequence, Set

from sqlalchemy import text

from flaskr.dao import db


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Fixed role priority (highest first). Used when a user holds several roles
# and to give ``resolve_user_roles`` a deterministic order. Mirrors the
# ``sort_order`` column from the original design (absent in the real schema).
ROLE_PRIORITY: Sequence[str] = (
    "role-admin",
    "role-hr",
    "role-dept-head",
    "role-coach",
    "role-learner",
)

ROLE_ADMIN = "role-admin"
ROLE_HR = "role-hr"
ROLE_DEPT_HEAD = "role-dept-head"
ROLE_COACH = "role-coach"
ROLE_LEARNER = "role-learner"

# The full known permission key set (docs/P0-PERMISSION-KEYS.md, 12 keys).
# Used to expand an admin's wildcard "all" into concrete keys so the frontend
# permission gate does not need to special-case the wildcard.
ALL_PERMISSION_KEYS: Sequence[str] = (
    "view_all_students",
    "score",
    "edit_summary",
    "create_session",
    "view_any_report",
    "confirm_checklist",
    "manage_users",
    "certify_content",
    "view_kpi",
    "audit",
    "custom_dashboard",
    "view_own_report",
)

# Wildcard permission key (role-admin).
PERMISSION_ALL = "all"

# Data-scope string prefixes returned by ``visible_students_scope``.
SCOPE_ALL = "all"
SCOPE_DEPARTMENT = "department"
SCOPE_MENTORED = "mentored"
SCOPE_SELF = "self"


# ---------------------------------------------------------------------------
# Attribute helpers — tolerate UserInfo / UserAggregate / dict / test mocks.
# ---------------------------------------------------------------------------


def _user_bid(user: Any) -> str:
    """Return the user business id from a user-like object or dict."""
    if user is None:
        return ""
    if isinstance(user, dict):
        return str(user.get("user_bid") or user.get("user_id") or "").strip()
    bid = getattr(user, "user_bid", None) or getattr(user, "user_id", None)
    return str(bid or "").strip()


def _user_bool(user: Any, name: str) -> bool:
    if user is None:
        return False
    if isinstance(user, dict):
        return bool(user.get(name))
    return bool(getattr(user, name, False))


def _user_str(user: Any, name: str) -> str:
    if user is None:
        return ""
    if isinstance(user, dict):
        return str(user.get(name) or "").strip()
    return str(getattr(user, name, None) or "").strip()


def _parse_permissions(raw_value: Any) -> Set[str]:
    """Parse a ``coach_roles.permissions`` JSON value into a set of keys.

    Accepts a JSON array string (as stored by MySQL), an already-parsed
    list/tuple/set, or a JSON object (legacy map form). A plain non-JSON
    string is treated as a single key.
    """
    if raw_value is None:
        return set()
    if isinstance(raw_value, (list, tuple, set)):
        return {str(item).strip() for item in raw_value if str(item).strip()}
    if isinstance(raw_value, dict):
        return {str(key) for key in raw_value.keys() if str(key).strip()}
    if isinstance(raw_value, str):
        trimmed = raw_value.strip()
        if not trimmed:
            return set()
        try:
            parsed = json.loads(trimmed)
        except (json.JSONDecodeError, TypeError):
            return {trimmed}
        if isinstance(parsed, (list, tuple, set)):
            return {str(item).strip() for item in parsed if str(item).strip()}
        if isinstance(parsed, dict):
            return {str(key) for key in parsed.keys() if str(key).strip()}
        if isinstance(parsed, str):
            return {parsed.strip()} if parsed.strip() else set()
    return set()


def _role_priority_index(role_bid: str) -> int:
    try:
        return ROLE_PRIORITY.index(role_bid)
    except ValueError:
        return len(ROLE_PRIORITY)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_user_roles(app, user_bid: str) -> List[Dict[str, Any]]:
    """Return all active roles assigned to ``user_bid``.

    Reads from ``user_role_assignments`` JOIN ``coach_roles`` (only roles with
    ``is_active = 1``) and returns a list sorted by ``ROLE_PRIORITY``::

        [{"role_bid": "role-admin", "name": "admin", "permissions": ["all"]}]

    ``permissions`` is the parsed JSON permission key list (sorted). An empty
    ``user_bid`` or a user with no assignments yields ``[]``.
    """
    normalized_bid = str(user_bid or "").strip()
    if not normalized_bid:
        return []

    rows = db.session.execute(
        text(
            "SELECT cr.role_bid, cr.name, cr.permissions "
            "FROM user_role_assignments ura "
            "JOIN coach_roles cr ON ura.role_bid = cr.role_bid "
            "WHERE ura.user_bid = :user_bid AND cr.is_active = 1"
        ),
        {"user_bid": normalized_bid},
    ).fetchall()

    roles: List[Dict[str, Any]] = []
    for row in rows:
        roles.append(
            {
                "role_bid": str(getattr(row, "role_bid", "") or ""),
                "name": str(getattr(row, "name", "") or ""),
                "permissions": sorted(
                    _parse_permissions(getattr(row, "permissions", None))
                ),
            }
        )
    roles.sort(key=lambda role: _role_priority_index(role["role_bid"]))
    return roles


def has_permission(app, user, permission: str) -> bool:
    """Check whether ``user`` holds ``permission``.

    Rules (in order):

    1. No user, or empty permission key → ``False``.
    2. Legacy flag ``is_operator=1`` is treated as admin → ``True``
       (backward compatibility, P0-PERMISSION-MODEL-UPGRADE §四).
    3. Any role whose permissions contain the wildcard ``"all"`` → ``True``.
    4. Otherwise ``True`` iff the permission key is present in any role's
       permissions.

    ``user`` may be a ``UserInfo`` / ``UserAggregate`` DTO, a dict, or any
    object exposing ``user_bid``/``user_id`` and ``is_operator``. Callers are
    expected to run inside an app context (as all route handlers do).
    """
    if user is None or not permission:
        return False

    user_bid = _user_bid(user)
    roles = resolve_user_roles(app, user_bid)
    for role in roles:
        permissions = role.get("permissions") or set()
        if PERMISSION_ALL in permissions or permission in permissions:
            return True

    # Legacy fallback (B6, P0-PERMISSION-GAP-AUDIT D-G4): ``is_operator=1``
    # only counts as admin when the user has NO 5-level role assignment, so
    # ``user_role_assignments`` stays the source of truth while legacy flags
    # are retired. A user holding a role never falls through to the flag.
    if not roles and _user_bool(user, "is_operator"):
        return True
    return False


def visible_students_scope(app, user) -> str:
    """Return the data scope for the learner list as a string.

    Result formats:

    - ``"all"``                  admin / hr (or legacy ``is_operator=1``)
    - ``"department:<dept>"``    dept_head within their own department
    - ``"mentored:<user_bid>"``  coach (``learner_profiles.coach_bid = user_bid``)
    - ``"self:<user_bid>"``      learner / fallback

    Scope priority is ``ROLE_PRIORITY`` (first matching role wins). Safe
    degradation: a dept_head without a department value, or a user with no
    roles, falls back to ``"self:<user_bid>"``.
    """
    user_bid = _user_bid(user)
    if not user_bid:
        return SCOPE_SELF  # cannot identify → most restrictive scope

    roles = resolve_user_roles(app, user_bid)
    role_bids = {role.get("role_bid") for role in roles}
    for role_bid in ROLE_PRIORITY:
        if role_bid not in role_bids:
            continue
        if role_bid in (ROLE_ADMIN, ROLE_HR):
            return SCOPE_ALL
        if role_bid == ROLE_DEPT_HEAD:
            department = _user_str(user, "department")
            if department:
                return f"{SCOPE_DEPARTMENT}:{department}"
            return f"{SCOPE_SELF}:{user_bid}"
        if role_bid == ROLE_COACH:
            return f"{SCOPE_MENTORED}:{user_bid}"
        # role-learner (and any unknown role) → self only
        return f"{SCOPE_SELF}:{user_bid}"

    # Legacy fallback (B6, D-G4): is_operator=1 without any role assignment.
    if not role_bids and _user_bool(user, "is_operator"):
        return SCOPE_ALL
    return f"{SCOPE_SELF}:{user_bid}"


def get_user_permissions(app, user) -> List[str]:
    """Return the union of the user's permission keys (sorted, unique).

    An admin — a role carrying the wildcard ``"all"``, or the legacy
    ``is_operator=1`` — gets the full known key set (``ALL_PERMISSION_KEYS``)
    plus ``"all"``, so the frontend gate can test every flag without special
    casing. This is the backing data for ``GET /api/portal/permissions``.
    """
    keys: Set[str] = set()
    roles = resolve_user_roles(app, _user_bid(user))
    has_all = False
    for role in roles:
        permissions = role.get("permissions") or set()
        keys.update(permissions)
        if PERMISSION_ALL in permissions:
            has_all = True
    # Legacy fallback (B6, D-G4): is_operator=1 with no role assignment.
    if not roles and _user_bool(user, "is_operator"):
        has_all = True
    if has_all:
        keys.update(ALL_PERMISSION_KEYS)
        keys.add(PERMISSION_ALL)
    return sorted(keys)
