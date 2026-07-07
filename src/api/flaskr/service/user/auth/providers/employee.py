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


class EmployeeAuthProvider(AuthProvider):
    """Authenticate via employee number + password against the internal AAD server."""

    provider_name = "employee"
    supports_challenge = False

    def verify(self, app: Flask, request: VerificationRequest) -> AuthResult:
        employee_no = (request.identifier or "").strip()
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

        # Auto-grant creator + operator roles for all employee-login users.
        # Employees authenticate against enterprise AAD and are trusted.
        creator_granted_now = False
        from flaskr.service.user.repository import mark_user_roles
        from flaskr.dao import db

        needs_roles = not bool(aggregate.is_creator) or not bool(aggregate.is_operator)
        if needs_roles:
            mark_user_roles(aggregate.user_bid, is_creator=True, is_operator=True)
            db.session.flush()
            # Re-fetch after role update so user_info reflects the new roles
            aggregate = load_user_aggregate(aggregate.user_bid)
            creator_granted_now = True

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
