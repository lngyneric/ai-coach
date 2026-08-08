"""Tests for flaskr.service.coach.permissions (P0 permission model, step 6).

Covers:
- permission parsing (``_parse_permissions``)
- ``has_permission`` (admin wildcard / legacy is_operator / learner denies score)
- ``visible_students_scope`` (all / department / mentored / self + degradation)
- ``get_user_permissions`` (admin expansion, learner union)
- ``resolve_user_roles`` against a real SQLite schema (app fixture)
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy import text

from flaskr.dao import db

import flaskr.service.coach.permissions as perms


class _MockUser:
    """Mimics UserInfo/UserAggregate: user_id=user_bid alias + role flags."""

    def __init__(
        self,
        user_bid="usr-test",
        is_operator=False,
        is_creator=False,
        department="",
        mentor_bid="",
        employee_no="",
    ):
        self.user_bid = user_bid
        self.user_id = user_bid  # UserInfo-style alias
        self.is_operator = is_operator
        self.is_creator = is_creator
        self.department = department
        self.mentor_bid = mentor_bid
        self.employee_no = employee_no


_ROLE_LEARNER = {
    "role_bid": "role-learner",
    "name": "learner",
    "permissions": ["learner:read", "learner:write", "view_own_report"],
}
_ROLE_COACH = {
    "role_bid": "role-coach",
    "name": "coach",
    "permissions": [
        "coach:read",
        "coach:write",
        "learner:read",
        "view_all_students",
        "score",
        "edit_summary",
        "create_session",
        "view_any_report",
        "confirm_checklist",
        "view_kpi",
        "custom_dashboard",
        "view_own_report",
    ],
}
_ROLE_ADMIN = {"role_bid": "role-admin", "name": "admin", "permissions": ["all"]}


# ---------------------------------------------------------------------------
# _parse_permissions
# ---------------------------------------------------------------------------


def test_parse_permissions_list():
    assert perms._parse_permissions(["all", "score"]) == {"all", "score"}


def test_parse_permissions_json_array_string():
    assert perms._parse_permissions('["score", "view_own_report"]') == {
        "score",
        "view_own_report",
    }


def test_parse_permissions_none_and_empty():
    assert perms._parse_permissions(None) == set()
    assert perms._parse_permissions("") == set()


def test_parse_permissions_plain_string():
    assert perms._parse_permissions("view_kpi") == {"view_kpi"}


def test_parse_permissions_dict_map():
    assert perms._parse_permissions({"score": True, "audit": False}) == {
        "score",
        "audit",
    }


# ---------------------------------------------------------------------------
# has_permission (resolve_user_roles monkeypatched)
# ---------------------------------------------------------------------------


def test_has_permission_admin_operator_always_true(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [])
    user = _MockUser(is_operator=True)
    assert perms.has_permission(None, user, "audit") is True
    assert perms.has_permission(None, user, "not-a-real-key") is True


def test_has_permission_operator_ignored_when_roles_present(monkeypatch):
    """B6: is_operator=1 no longer short-circuits when the user has a role."""
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [_ROLE_LEARNER])
    user = _MockUser(is_operator=True)
    assert perms.has_permission(None, user, "manage_users") is False
    assert perms.has_permission(None, user, "view_own_report") is True


def test_has_permission_admin_role_wildcard(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [_ROLE_ADMIN])
    user = _MockUser()
    assert perms.has_permission(None, user, "audit") is True
    assert perms.has_permission(None, user, "manage_users") is True


def test_has_permission_learner_denies_score(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [_ROLE_LEARNER])
    user = _MockUser()
    # negative: learner must NOT be able to score
    assert perms.has_permission(None, user, "score") is False
    assert perms.has_permission(None, user, "manage_users") is False
    # positive: learner's own report
    assert perms.has_permission(None, user, "view_own_report") is True


def test_has_permission_coach_allows_score(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [_ROLE_COACH])
    user = _MockUser()
    assert perms.has_permission(None, user, "score") is True
    assert perms.has_permission(None, user, "edit_summary") is True
    assert perms.has_permission(None, user, "audit") is False


def test_has_permission_empty_permission_and_no_user(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [_ROLE_ADMIN])
    assert perms.has_permission(None, _MockUser(), "") is False
    assert perms.has_permission(None, None, "score") is False


def test_has_permission_multiple_roles_union(monkeypatch):
    monkeypatch.setattr(
        perms,
        "resolve_user_roles",
        lambda app, bid: [_ROLE_LEARNER, _ROLE_COACH],
    )
    user = _MockUser()
    assert perms.has_permission(None, user, "score") is True  # via coach role
    assert perms.has_permission(None, user, "view_own_report") is True


# ---------------------------------------------------------------------------
# visible_students_scope (resolve_user_roles monkeypatched)
# ---------------------------------------------------------------------------


def test_scope_admin_hr_all(monkeypatch):
    monkeypatch.setattr(
        perms, "resolve_user_roles", lambda app, bid: [{"role_bid": "role-admin",
                                                        "name": "admin",
                                                        "permissions": ["all"]}]
    )
    assert perms.visible_students_scope(None, _MockUser()) == "all"

    monkeypatch.setattr(
        perms, "resolve_user_roles", lambda app, bid: [{"role_bid": "role-hr",
                                                        "name": "hr",
                                                        "permissions": []}]
    )
    assert perms.visible_students_scope(None, _MockUser()) == "all"


def test_scope_operator_legacy_all(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [])
    assert perms.visible_students_scope(None, _MockUser(is_operator=True)) == "all"


def test_scope_dept_head_with_department(monkeypatch):
    monkeypatch.setattr(
        perms,
        "resolve_user_roles",
        lambda app, bid: [
            {"role_bid": "role-dept-head", "name": "dept_head", "permissions": []}
        ],
    )
    user = _MockUser(department="销售本部")
    assert perms.visible_students_scope(None, user) == "department:销售本部"


def test_scope_dept_head_without_department_degrades_to_self(monkeypatch):
    monkeypatch.setattr(
        perms,
        "resolve_user_roles",
        lambda app, bid: [
            {"role_bid": "role-dept-head", "name": "dept_head", "permissions": []}
        ],
    )
    user = _MockUser(department="")  # field missing → safe degradation
    assert perms.visible_students_scope(None, user) == "self:usr-test"


def test_scope_coach_mentored(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [_ROLE_COACH])
    user = _MockUser(user_bid="usr-coach")
    assert perms.visible_students_scope(None, user) == "mentored:usr-coach"


def test_scope_learner_self(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [_ROLE_LEARNER])
    user = _MockUser(user_bid="usr-learner")
    assert perms.visible_students_scope(None, user) == "self:usr-learner"


def test_scope_no_roles_falls_back_to_self(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [])
    user = _MockUser()
    assert perms.visible_students_scope(None, user) == "self:usr-test"


def test_scope_priority_admin_wins_over_coach(monkeypatch):
    monkeypatch.setattr(
        perms, "resolve_user_roles", lambda app, bid: [_ROLE_COACH, _ROLE_ADMIN]
    )
    user = _MockUser()
    assert perms.visible_students_scope(None, user) == "all"


# ---------------------------------------------------------------------------
# get_user_permissions (resolve_user_roles monkeypatched)
# ---------------------------------------------------------------------------


def test_get_permissions_admin_expands_to_full_set(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [_ROLE_ADMIN])
    keys = perms.get_user_permissions(None, _MockUser())
    assert "all" in keys
    for key in perms.ALL_PERMISSION_KEYS:
        assert key in keys


def test_get_permissions_operator_full_set(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [])
    keys = perms.get_user_permissions(None, _MockUser(is_operator=True))
    for key in perms.ALL_PERMISSION_KEYS:
        assert key in keys


def test_get_permissions_operator_ignored_when_roles_present(monkeypatch):
    """B6: is_operator=1 no longer bypasses when the user holds a role."""
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [_ROLE_LEARNER])
    keys = perms.get_user_permissions(None, _MockUser(is_operator=True))
    assert "all" not in keys
    assert keys == ["learner:read", "learner:write", "view_own_report"]


def test_get_permissions_learner_union(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [_ROLE_LEARNER])
    keys = perms.get_user_permissions(None, _MockUser())
    assert keys == ["learner:read", "learner:write", "view_own_report"]


def test_get_permissions_no_roles_empty(monkeypatch):
    monkeypatch.setattr(perms, "resolve_user_roles", lambda app, bid: [])
    assert perms.get_user_permissions(None, _MockUser()) == []


# ---------------------------------------------------------------------------
# resolve_user_roles — real SQLite schema (app fixture)
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_permission_db(app):
    """Create coach_roles + user_role_assignments and seed a few rows."""
    with app.app_context():
        db.session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS coach_roles ("
                " role_bid VARCHAR(32) PRIMARY KEY,"
                " name VARCHAR(50) NOT NULL UNIQUE,"
                " label VARCHAR(100) DEFAULT '',"
                " permissions TEXT,"
                " is_active INTEGER DEFAULT 1)"
            )
        )
        db.session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS user_role_assignments ("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " user_bid VARCHAR(32) NOT NULL,"
                " role_bid VARCHAR(32) NOT NULL,"
                " UNIQUE (user_bid, role_bid))"
            )
        )
        db.session.execute(
            text(
                "INSERT OR REPLACE INTO coach_roles "
                "(role_bid, name, permissions, is_active) VALUES "
                "('role-admin', 'admin', '[\"all\"]', 1),"
                "('role-learner', 'learner',"
                " '[\"learner:read\",\"learner:write\",\"view_own_report\"]', 1),"
                "('role-coach', 'coach', '[\"score\",\"view_own_report\"]', 1),"
                "('role-inactive', 'inactive', '[\"manage_users\"]', 0)"
            )
        )
        db.session.execute(
            text(
                "INSERT OR REPLACE INTO user_role_assignments "
                "(user_bid, role_bid) VALUES "
                "('usr-admin', 'role-admin'),"
                "('usr-learner', 'role-learner'),"
                "('usr-multi', 'role-learner'),"
                "('usr-multi', 'role-coach'),"
                "('usr-inactive', 'role-inactive')"
            )
        )
        db.session.commit()
        yield


def test_resolve_user_roles_real_db(app, seeded_permission_db):
    with app.app_context():
        roles = perms.resolve_user_roles(app, "usr-admin")
        assert [r["role_bid"] for r in roles] == ["role-admin"]
        assert roles[0]["permissions"] == ["all"]

        roles = perms.resolve_user_roles(app, "usr-learner")
        assert [r["role_bid"] for r in roles] == ["role-learner"]
        assert roles[0]["permissions"] == ["learner:read", "learner:write", "view_own_report"]

        # multi-role, ordered by ROLE_PRIORITY (coach < learner in priority)
        roles = perms.resolve_user_roles(app, "usr-multi")
        assert [r["role_bid"] for r in roles] == ["role-coach", "role-learner"]

        # is_active=0 roles are filtered out
        assert perms.resolve_user_roles(app, "usr-inactive") == []
        assert perms.resolve_user_roles(app, "no-such-user") == []
        assert perms.resolve_user_roles(app, "") == []


def test_has_permission_real_db(app, seeded_permission_db):
    with app.app_context():
        admin = _MockUser(user_bid="usr-admin")
        assert perms.has_permission(app, admin, "audit") is True

        learner = _MockUser(user_bid="usr-learner")
        assert perms.has_permission(app, learner, "score") is False
        assert perms.has_permission(app, learner, "view_own_report") is True

        multi = _MockUser(user_bid="usr-multi")
        assert perms.has_permission(app, multi, "score") is True  # via role-coach
        assert perms.has_permission(app, multi, "view_own_report") is True

        assert perms.has_permission(app, _MockUser(user_bid="usr-inactive"), "manage_users") is False


def test_visible_students_scope_real_db(app, seeded_permission_db):
    with app.app_context():
        assert (
            perms.visible_students_scope(app, _MockUser(user_bid="usr-admin")) == "all"
        )
        assert (
            perms.visible_students_scope(
                app, _MockUser(user_bid="usr-learner")
            )
            == "self:usr-learner"
        )
        assert (
            perms.visible_students_scope(
                app, _MockUser(user_bid="usr-multi")
            )
            == "mentored:usr-multi"
        )
