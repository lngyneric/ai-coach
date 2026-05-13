"""WeCom (企业微信) OAuth authentication provider.

Supports silent OAuth login via WeCom's built-in browser for H5 pages.
Uses ``snsapi_base`` scope — no user consent dialog, returns UserId only.
"""

from __future__ import annotations

import logging
import secrets
import time
from typing import Any, Dict, Optional

import requests
from flask import Flask, request

from flaskr.service.common.models import raise_error
from flaskr.service.user.auth.base import (
    AuthProvider,
    AuthResult,
    OAuthCallbackRequest,
)
from flaskr.service.user.auth.factory import has_provider, register_provider
from flaskr.service.user.consts import USER_STATE_REGISTERED
from flaskr.service.user.repository import (
    build_user_info_from_aggregate,
    ensure_user_for_identifier,
    load_user_aggregate,
    upsert_credential,
)
from flaskr.service.user.utils import generate_token
from flaskr.service.common.dtos import UserToken

logger = logging.getLogger(__name__)

WECOM_AUTHORIZE_URL = (
    "https://open.weixin.qq.com/connect/oauth2/authorize"
)
WECOM_TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
WECOM_USERINFO_URL = "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo"

# Cache access token in memory with expiry (seconds)
ACCESS_TOKEN_TTL = 7000  # Slightly less than 7200 to allow refresh margin
_token_cache: Dict[str, Any] = {}


def _get_access_token(app: Flask) -> str:
    """Get a cached WeCom API access token, refreshing if expired."""
    now = time.time()
    corpid = app.config.get("WECOM_CORP_ID", "")
    secret = app.config.get("WECOM_SECRET", "")

    cache_key = f"{corpid}:{secret[:8]}" if secret else corpid
    entry = _token_cache.get(cache_key)
    if entry and entry.get("expires_at", 0) > now:
        return entry["token"]

    if not corpid or not secret:
        raise_error("server.common.unknownError")

    url = f"{WECOM_TOKEN_URL}?corpid={corpid}&corpsecret={secret}"
    resp = requests.get(url, timeout=10)
    data = resp.json()

    if data.get("errcode", -1) != 0:
        logger.error("WeCom gettoken failed: %s", data)
        raise_error("server.common.unknownError")

    token = data["access_token"]
    expires_in = data.get("expires_in", 7200)
    _token_cache[cache_key] = {
        "token": token,
        "expires_at": now + min(expires_in, ACCESS_TOKEN_TTL),
    }
    return token


def _build_wecom_oauth_url(app: Flask, state: str, redirect_uri: str) -> str:
    """Build the WeCom OAuth authorize URL."""
    corpid = app.config.get("WECOM_CORP_ID", "")
    from urllib.parse import quote

    encoded_redirect = quote(redirect_uri, safe="")
    return (
        f"{WECOM_AUTHORIZE_URL}"
        f"?appid={corpid}"
        f"&redirect_uri={encoded_redirect}"
        f"&response_type=code"
        f"&scope=snsapi_base"
        f"&state={state}"
        f"#wechat_redirect"
    )


def _build_callback_url(app: Flask, explicit_uri: Optional[str] = None) -> str:
    """Resolve the WeCom OAuth callback URL."""
    if explicit_uri:
        return explicit_uri

    # Build from the incoming request host
    host = str(request.host or "").strip()
    forwarded = str(request.headers.get("X-Forwarded-Host", "") or "").strip()
    effective_host = forwarded.split(",")[0].strip() if forwarded else host
    effective_host = effective_host.split(":")[0] if effective_host else ""

    scheme = "https" if request.headers.get("X-Forwarded-Proto") == "https" else "http"
    return f"{scheme}://{effective_host}/api/user/oauth/wecom/callback"


class WeComAuthProvider(AuthProvider):
    """Authenticate via 企业微信 OAuth (silent, snsapi_base scope)."""

    provider_name = "wecom"
    supports_oauth = True

    def verify(self, app, request):
        raise NotImplementedError("WeComAuthProvider only supports OAuth flows")

    def begin_oauth(self, app: Flask, metadata: Dict[str, Any]) -> Any:
        state = secrets.token_hex(16)
        redirect_uri = _build_callback_url(app, metadata.get("redirect_uri"))

        # Store state + redirect_uri mapping in app config temporarily
        # (stateless: encode redirect_uri in state or use a simple cache)
        authorize_url = _build_wecom_oauth_url(app, state, redirect_uri)

        return {
            "authorize_url": authorize_url,
            "state": state,
            "redirect_uri": redirect_uri,
        }

    def handle_oauth_callback(
        self, app: Flask, callback_req: OAuthCallbackRequest
    ) -> AuthResult:
        code = callback_req.code
        if not code:
            raise_error("server.user.invalidCredentials")

        # Exchange code for WeCom UserId
        access_token = _get_access_token(app)
        userinfo_url = (
            f"{WECOM_USERINFO_URL}"
            f"?access_token={access_token}"
            f"&code={code}"
        )
        resp = requests.get(userinfo_url, timeout=10)
        data = resp.json()

        if data.get("errcode", -1) != 0:
            logger.warning("WeCom userinfo failed: %s", data)
            raise_error("server.user.invalidCredentials")

        user_id = data.get("UserId", "")
        # OpenId is available for apps in WeChat ecosystem, UserId is internal
        subject_id = user_id or data.get("OpenId", "")
        if not subject_id:
            logger.error("WeCom OAuth returned no UserId or OpenId: %s", data)
            raise_error("server.user.invalidCredentials")

        # Map to local user — UserId is the canonical subject
        aggregate, created = ensure_user_for_identifier(
            app,
            provider=self.provider_name,
            identifier=subject_id,
            defaults={
                "identify": subject_id,
                "nickname": subject_id,
                "state": USER_STATE_REGISTERED,
            },
        )

        # Upsert the wecom credential
        credential = upsert_credential(
            app,
            user_bid=aggregate.user_bid,
            provider_name=self.provider_name,
            subject_id=subject_id,
            subject_format="wecom_userid",
            identifier=subject_id,
            metadata={
                "user_id": user_id,
                "open_id": data.get("OpenId", ""),
                "device_id": data.get("DeviceId", ""),
            },
            verified=True,
        )

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
                "wecom_user_id": user_id,
            },
        )


if not has_provider(WeComAuthProvider.provider_name):
    register_provider(WeComAuthProvider)
