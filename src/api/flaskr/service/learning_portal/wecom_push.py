"""Learning Portal — WeCom (企业微信) message push side-channel.

W1: the four Celery tasks in ``tasks.py`` keep writing ``TaskNotification``
rows exactly as before (in-app banner compatibility), and additionally push a
WeCom app message to the recipient when enabled.

Design constraints
------------------
- Purely additive / side-channel: a WeCom failure must NEVER break the
  notification pipeline. Every public function below degrades to ``False`` /
  ``""`` instead of raising, and callers additionally wrap the push in a
  try/except as a belt-and-suspenders guard.
- Driven by ``WECOM_NOTIFY_ENABLED`` (default ``False``). Dev and prod both
  default to off; only turn it on where a WeCom app with ``message.send``
  permission and a matching ``WECOM_AGENT_ID`` are configured.
- Recipient mapping: ``user_bid`` -> WeCom ``UserId`` via the
  ``user_auth_credentials`` table (``provider_name='wecom'``, verified,
  ``deleted=0``) — the same credential store the WeCom OAuth provider writes.
"""

from __future__ import annotations

import logging
import time
from typing import Iterable, Optional

import requests
from flask import current_app, has_app_context

from flaskr.service.user.consts import CREDENTIAL_STATE_VERIFIED
from flaskr.service.user.models import AuthCredential

logger = logging.getLogger(__name__)

WECOM_GETTOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
WECOM_MESSAGE_SEND_URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send"

# Slightly below the 7200s API TTL so the token refreshes before it expires.
ACCESS_TOKEN_TTL = 7000
_token_cache: dict = {}


def _has_config() -> bool:
    """True when running inside a Flask app context with a config to read."""
    return has_app_context()


def _enabled() -> bool:
    """Whether the W1 WeCom push switch is on."""
    if not _has_config():
        return False
    return bool(current_app.config.get("WECOM_NOTIFY_ENABLED", False))


def _agent_id() -> str:
    """WeCom app AgentId; empty means push is skipped."""
    if not _has_config():
        return ""
    return str(current_app.config.get("WECOM_AGENT_ID", "") or "").strip()


def _corp_config() -> tuple[str, str]:
    """Return (corpid, secret) from the current app config."""
    if not _has_config():
        return "", ""
    corpid = str(current_app.config.get("WECOM_CORP_ID", "") or "").strip()
    secret = str(current_app.config.get("WECOM_SECRET", "") or "").strip()
    return corpid, secret


def _get_access_token() -> str:
    """Return a cached WeCom access token, or ``""`` when unavailable/failed."""
    corpid, secret = _corp_config()
    if not corpid or not secret:
        logger.info("WECOM push skipped: WECOM_CORP_ID / WECOM_SECRET not set")
        return ""

    cache_key = f"{corpid}:{secret[:8]}"
    entry = _token_cache.get(cache_key)
    if entry and entry.get("expires_at", 0) > time.time():
        return entry["token"]

    try:
        resp = requests.get(
            WECOM_GETTOKEN_URL,
            params={"corpid": corpid, "corpsecret": secret},
            timeout=10,
        )
        data = resp.json()
    except Exception as exc:  # noqa: BLE001 - side channel must not raise
        logger.warning("WECOM gettoken request failed: %s", exc)
        return ""

    if data.get("errcode", -1) != 0:
        logger.warning("WECOM gettoken failed: %s", data)
        return ""

    token = data.get("access_token", "")
    expires_in = int(data.get("expires_in", 7200))
    _token_cache[cache_key] = {
        "token": token,
        "expires_at": time.time() + min(expires_in, ACCESS_TOKEN_TTL),
    }
    return token


def resolve_wecom_user_ids(user_bids: Iterable[str]) -> list[str]:
    """Map ``user_bid``(s) to WeCom ``UserId``(s) via verified wecom credentials.

    Unmapped bids are silently skipped — the WeCom message simply targets the
    users that actually bound a WeCom account.
    """
    bids = {b for b in user_bids if b}
    if not bids:
        return []
    rows = (
        AuthCredential.query.filter(
            AuthCredential.provider_name == "wecom",
            AuthCredential.deleted == 0,
            AuthCredential.state == CREDENTIAL_STATE_VERIFIED,
            AuthCredential.user_bid.in_(bids),
        )
        .with_entities(AuthCredential.subject_id)
        .all()
    )
    user_ids: list[str] = []
    seen: set[str] = set()
    for (subject_id,) in rows:
        uid = str(subject_id or "").strip()
        if uid and uid not in seen:
            seen.add(uid)
            user_ids.append(uid)
    return user_ids


def send_wecom_text(user_ids: Iterable[str], content: str) -> bool:
    """Send a plain-text WeCom app message to ``user_ids``.

    Never raises. Returns ``True`` only when the API acknowledged with
    ``errcode == 0``.
    """
    user_id_list = [u for u in user_ids if u]
    if not user_id_list:
        return False

    agent_id = _agent_id()
    if not agent_id:
        logger.info("WECOM push skipped: WECOM_AGENT_ID not set")
        return False

    token = _get_access_token()
    if not token:
        return False

    payload = {
        "touser": "|".join(user_id_list),
        "msgtype": "text",
        "agentid": int(agent_id),
        "text": {"content": content},
        "safe": 0,
    }
    try:
        resp = requests.post(
            WECOM_MESSAGE_SEND_URL,
            params={"access_token": token},
            json=payload,
            timeout=10,
        )
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("WECOM message/send request failed: %s", exc)
        return False

    if data.get("errcode", -1) != 0:
        logger.warning("WECOM message/send failed: %s", data)
        return False
    logger.info("WECOM push sent to %d user(s): %s", len(user_id_list), user_id_list)
    return True


def push_wecom_notification(
    *,
    user_bid: str,
    title: str,
    content: str,
    notif_type: str = "",  # noqa: ARG002 - reserved for future channel routing
) -> bool:
    """Side-channel push for one ``user_bid``.

    Returns ``True`` when the message was actually sent; ``False`` when
    disabled, unmapped, misconfigured, or failed. Never raises.
    """
    if not _enabled():
        return False
    user_ids = resolve_wecom_user_ids([user_bid])
    if not user_ids:
        logger.debug(
            "WECOM push skipped: no verified wecom credential for user %s", user_bid
        )
        return False
    body = f"【{title}】\n{content}" if title else content
    return send_wecom_text(user_ids, body)
