"""Employee AAD authentication provider.

Validates users against the internal enterprise AAD server using employee
number and password.
"""

from __future__ import annotations

import base64
import logging

import requests
from flask import Flask
from requests.exceptions import RequestException

from flaskr.service.user.auth.base import (
    AuthProvider,
    AuthResult,
    VerificationRequest,
)
from flaskr.service.user.auth.factory import (
    has_provider,
    register_provider,
)
from flaskr.service.user.repository import (
    build_user_info_from_aggregate,
    ensure_user_for_identifier,
    load_user_aggregate,
    upsert_credential,
)
from flaskr.service.user.utils import generate_token
from flaskr.service.common.dtos import UserToken
from flaskr.service.common.models import raise_error
from flaskr.service.user.consts import (
    CREDENTIAL_STATE_VERIFIED,
    USER_STATE_REGISTERED,
)

logger = logging.getLogger(__name__)


def _load_whitelist(app: Flask, key: str) -> set[str]:
    """Read a whitelist config value into a normalized, lowercased set.

    Accepts either a list of employee numbers or a comma/space-separated
    string. Each element is itself split on commas/whitespace so mixed
    separators work regardless of ``EnvVar(type=list)`` conversion.
    All items are lowercased so whitelist matching is case-insensitive
    (fixes R2; AAD employee numbers are case-insensitive).
    """
    raw = app.config.get(key, []) or []
    items: set[str] = set()
    if not isinstance(raw, (list, tuple, set)):
        raw = [raw]
    for item in raw:
        for part in str(item).replace(",", " ").split():
            part = part.strip().lower()
            if part:
                items.add(part)
    return items


def _resolve_role_grants(
    employee_no: str,
    *,
    operator_whitelist: set[str],
    creator_whitelist: set[str],
    revoke_others: bool,
    existing_is_operator: bool,
    existing_is_creator: bool,
) -> tuple[bool, bool]:
    """Decide which role flags to persist for an employee-login user.

    Rule (matches P0-DESIGN-CORRECTION.md D1):
      - whitelist hit -> always grant (explicit operator/creator approval);
      - otherwise keep the user's existing roles, unless ``revoke_others``
        is enabled, in which case a user in neither whitelist is treated as
        revoked (existing grants cleared, new grants denied).

    Returns ``(grant_operator, grant_creator)``.
    """
    employee_no = (employee_no or "").strip().lower()
    in_operator_whitelist = employee_no in operator_whitelist
    in_creator_whitelist = employee_no in creator_whitelist
    revoked = revoke_others and not (in_operator_whitelist or in_creator_whitelist)

    grant_operator = in_operator_whitelist or (existing_is_operator and not revoked)
    grant_creator = in_creator_whitelist or (existing_is_creator and not revoked)
    return grant_operator, grant_creator


class EmployeeAuthProvider(AuthProvider):
    """Authenticate via employee number + password against the internal AAD server."""

    provider_name = "employee"
    supports_challenge = False

    def verify(self, app: Flask, request: VerificationRequest) -> AuthResult:
        employee_no = (request.identifier or "").strip().lower()
        password = request.code or ""

        if not employee_no or not password:
            raise_error("server.user.invalidCredentials")

        # Testing bypass: if AAD_BYPASS is set, skip the AAD call
        aad_bypass = app.config.get("AAD_BYPASS", "")
        if not aad_bypass:
            # Validate credentials against the AAD server
            aad_url = app.config.get("AAD_AUTH_URL", "")
            if not aad_url:
                logger.error("AAD_AUTH_URL is not configured")
                raise_error("server.user.invalidCredentials")

            aad_timeout = app.config.get("AAD_AUTH_TIMEOUT", 10)
            encoded_password = base64.b64encode(password.encode("utf-8")).decode("ascii")

            auth_url = (
                f"{aad_url.rstrip('/')}/getAccessTokenByEmployeeNo"
                f"?employeeNo={employee_no}&password={encoded_password}"
            )

            try:
                response = requests.get(auth_url, timeout=aad_timeout)
            except RequestException as exc:
                logger.error("AAD server unreachable: %s", exc)
                raise_error("server.user.invalidCredentials")

            if response.status_code != 200:
                logger.warning(
                    "AAD auth failed for employee %s: HTTP %s",
                    employee_no,
                    response.status_code,
                )
                raise_error("server.user.invalidCredentials")

            # AAD returns HTTP 200 even on auth failure; check JSON body
            try:
                aad_body = response.json()
            except Exception:
                aad_body = {}
            if aad_body.get("statusCode") != "200" and aad_body.get("message") != "success":
                logger.warning(
                    "AAD auth failed for employee %s: %s",
                    employee_no,
                    aad_body.get("message", "unknown"),
                )
                raise_error("server.user.invalidCredentials")

        # AAD verified — find or create the local user
        # Use a synthetic email so the frontend auth check passes
        # (the frontend determines isAuthenticated by mobile || email)
        synthetic_email = f"{employee_no}@sysmex.internal"
        aggregate, created = ensure_user_for_identifier(
            app,
            provider=self.provider_name,
            identifier=employee_no,
            defaults={
                "identify": employee_no,
                "nickname": employee_no,
                "state": USER_STATE_REGISTERED,
            },
        )

        # Ensure an email credential exists for the employee
        # (the frontend initUser() checks mobile || email for auth status)
        upsert_credential(
            app,
            user_bid=aggregate.user_bid,
            provider_name="email",
            subject_id=synthetic_email,
            subject_format="email",
            identifier=synthetic_email,
            metadata={"source": "employee_aad"},
            verified=True,
        )

        # Upsert the employee credential
        credential = upsert_credential(
            app,
            user_bid=aggregate.user_bid,
            provider_name=self.provider_name,
            subject_id=employee_no,
            subject_format="employee_no",
            identifier=employee_no,
            metadata={},
            verified=True,
        )

        # Whitelist-gated role grants for employee-login users:
        #   - whitelist hit always grants (explicit operator/creator approval);
        #   - otherwise keep the user's existing roles unless REVOKE_OTHERS is on.
        # REVOKE_OTHERS defaults to False so existing grants are preserved.
        from flaskr.service.user.repository import mark_user_roles
        from flaskr.dao import db

        operator_whitelist = _load_whitelist(app, "EMPLOYEE_OPERATOR_WHITELIST")
        creator_whitelist = _load_whitelist(app, "EMPLOYEE_CREATOR_WHITELIST")
        revoke_others = bool(app.config.get("EMPLOYEE_ROLE_REVOKE_OTHERS", False))
        grant_operator, grant_creator = _resolve_role_grants(
            employee_no,
            operator_whitelist=operator_whitelist,
            creator_whitelist=creator_whitelist,
            revoke_others=revoke_others,
            existing_is_operator=bool(aggregate.is_operator),
            existing_is_creator=bool(aggregate.is_creator),
        )

        creator_granted_now = False
        needs_roles = (
            grant_creator != bool(aggregate.is_creator)
            or grant_operator != bool(aggregate.is_operator)
        )
        if needs_roles:
            mark_user_roles(
                aggregate.user_bid,
                is_creator=grant_creator,
                is_operator=grant_operator,
            )
            db.session.flush()
            # Re-fetch after role update so user_info reflects the new roles
            aggregate = load_user_aggregate(aggregate.user_bid)
            creator_granted_now = grant_creator

        # Build the login token
        user_info = build_user_info_from_aggregate(aggregate)
        token = generate_token(app, aggregate.user_bid)
        user_token = UserToken(user_info, token)

        return AuthResult(
            user=user_info,
            token=user_token,
            credential=credential,
            is_new_user=created,
            metadata={
                "user_bid": aggregate.user_bid,
                "employee_no": employee_no,
                "creator_granted_now": creator_granted_now,
            },
        )


if not has_provider(EmployeeAuthProvider.provider_name):
    register_provider(EmployeeAuthProvider)
