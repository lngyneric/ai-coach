"""Unit tests for employee-login whitelist role-grant logic.

Covers the pure helpers in
``flaskr.service.user.auth.providers.employee``:

- ``_load_whitelist``: config value normalization
  (str comma/space-separated, list, empty, case normalization) — R5/R2.
- ``_resolve_role_grants``: the grant decision matrix
  (whitelist hit, existing-grant preservation, REVOKE_OTHERS on/off) — D1/R1/R4.
"""

from __future__ import annotations

import pytest
from flask import Flask

from flaskr.service.user.auth.providers.employee import (
    _load_whitelist,
    _resolve_role_grants,
)


@pytest.fixture
def app() -> Flask:
    return Flask(__name__)


class TestLoadWhitelist:
    """R5: comma/space separation + R2: case normalization."""

    def test_comma_separated_string(self, app: Flask) -> None:
        app.config["EMPLOYEE_OPERATOR_WHITELIST"] = "sch11111,sch00068,admin"
        assert _load_whitelist(app, "EMPLOYEE_OPERATOR_WHITELIST") == {
            "sch11111",
            "sch00068",
            "admin",
        }

    def test_space_separated_string(self, app: Flask) -> None:
        app.config["EMPLOYEE_OPERATOR_WHITELIST"] = "sch11111 sch00068 admin"
        assert _load_whitelist(app, "EMPLOYEE_OPERATOR_WHITELIST") == {
            "sch11111",
            "sch00068",
            "admin",
        }

    def test_mixed_separators_and_extra_whitespace(self, app: Flask) -> None:
        app.config["EMPLOYEE_OPERATOR_WHITELIST"] = " sch11111, sch00068 admin "
        assert _load_whitelist(app, "EMPLOYEE_OPERATOR_WHITELIST") == {
            "sch11111",
            "sch00068",
            "admin",
        }

    def test_list_value(self, app: Flask) -> None:
        # Simulates EnvVar(type=list) converting "a b c" or "a,b,c" already.
        app.config["EMPLOYEE_OPERATOR_WHITELIST"] = ["sch11111", "sch00068"]
        assert _load_whitelist(app, "EMPLOYEE_OPERATOR_WHITELIST") == {
            "sch11111",
            "sch00068",
        }

    def test_empty_config_returns_empty_set(self, app: Flask) -> None:
        app.config["EMPLOYEE_OPERATOR_WHITELIST"] = ""
        assert _load_whitelist(app, "EMPLOYEE_OPERATOR_WHITELIST") == set()

    def test_missing_config_returns_empty_set(self, app: Flask) -> None:
        # Key absent from config entirely.
        assert _load_whitelist(app, "NOT_DEFINED_KEY") == set()

    def test_case_normalization(self, app: Flask) -> None:
        # R2: whitelist entries are lowercased; lookup lowercases too.
        app.config["EMPLOYEE_OPERATOR_WHITELIST"] = "SCH11111,Admin"
        result = _load_whitelist(app, "EMPLOYEE_OPERATOR_WHITELIST")
        assert result == {"sch11111", "admin"}
        assert "SCH11111" not in result


class TestResolveRoleGrants:
    """D1 decision matrix for operator/creator grants."""

    def test_whitelist_hit_grants_even_without_existing(self) -> None:
        # sch00068 has no existing flags but is whitelisted -> granted.
        grant_operator, grant_creator = _resolve_role_grants(
            "sch00068",
            operator_whitelist={"sch00068"},
            creator_whitelist={"sch00068"},
            revoke_others=False,
            existing_is_operator=False,
            existing_is_creator=False,
        )
        assert (grant_operator, grant_creator) == (True, True)

    def test_no_whitelist_preserves_existing_grants(self) -> None:
        # User has existing grants but is NOT in whitelist; REVOKE_OTHERS off
        # -> existing grants preserved.
        grant_operator, grant_creator = _resolve_role_grants(
            "sch22222",
            operator_whitelist=set(),
            creator_whitelist=set(),
            revoke_others=False,
            existing_is_operator=True,
            existing_is_creator=True,
        )
        assert (grant_operator, grant_creator) == (True, True)

    def test_no_whitelist_no_existing_grants(self) -> None:
        # New user, no whitelist, REVOKE_OTHERS off -> no grants (privilege
        # creep stopped).
        grant_operator, grant_creator = _resolve_role_grants(
            "sch99999",
            operator_whitelist=set(),
            creator_whitelist=set(),
            revoke_others=False,
            existing_is_operator=False,
            existing_is_creator=False,
        )
        assert (grant_operator, grant_creator) == (False, False)

    def test_revoke_others_clears_non_whitelisted(self) -> None:
        # REVOKE_OTHERS on + not in any whitelist -> grants cleared.
        grant_operator, grant_creator = _resolve_role_grants(
            "sch22222",
            operator_whitelist=set(),
            creator_whitelist=set(),
            revoke_others=True,
            existing_is_operator=True,
            existing_is_creator=True,
        )
        assert (grant_operator, grant_creator) == (False, False)

    def test_revoke_others_keeps_partial_whitelist_hit(self) -> None:
        # REVOKE_OTHERS on, user in operator whitelist only -> operator kept,
        # creator not granted from existing (revoked because not in creator
        # whitelist and not in operator? No: revoked requires outside BOTH).
        # User is inside operator whitelist -> not revoked at all, so existing
        # creator is preserved too. Conservative behavior, documented in R4.
        grant_operator, grant_creator = _resolve_role_grants(
            "sch00068",
            operator_whitelist={"sch00068"},
            creator_whitelist=set(),
            revoke_others=True,
            existing_is_operator=False,
            existing_is_creator=True,
        )
        assert (grant_operator, grant_creator) == (True, True)

    def test_case_insensitive_match(self) -> None:
        # R2: uppercase login input matches lowercase whitelist.
        grant_operator, grant_creator = _resolve_role_grants(
            "SCH11111",
            operator_whitelist={"sch11111"},
            creator_whitelist={"sch11111"},
            revoke_others=False,
            existing_is_operator=False,
            existing_is_creator=False,
        )
        assert (grant_operator, grant_creator) == (True, True)

    def test_whitelist_split_between_roles(self) -> None:
        # User in creator whitelist only -> creator granted, operator not.
        grant_operator, grant_creator = _resolve_role_grants(
            "sch33333",
            operator_whitelist=set(),
            creator_whitelist={"sch33333"},
            revoke_others=False,
            existing_is_operator=False,
            existing_is_creator=False,
        )
        assert (grant_operator, grant_creator) == (False, True)
