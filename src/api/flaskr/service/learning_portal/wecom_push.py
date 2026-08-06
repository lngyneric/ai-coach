"""Learning Portal — WeCom (企业微信) message push side-channel.

W1: the four Celery tasks in ``tasks.py`` keep writing ``TaskNotification``
rows exactly as before (in-app banner compatibility), and additionally push a
WeCom app message to the recipient when enabled.

W2: adds ``textcard`` messages (course link built from ``WECOM_NOTIFY_BASE_URL``
+ ``related_bid``) and department broadcast via ``toparty``
(``WECOM_DEFAULT_PARTY`` / ``party_id``).

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


def _base_url() -> str:
    """Base URL for WeCom textcard course links; empty disables textcard (W2)."""
    if not _has_config():
        return ""
    return str(current_app.config.get("WECOM_NOTIFY_BASE_URL", "") or "").strip().rstrip("/")


def _default_party() -> str:
    """WeCom department id(s) to broadcast to; empty keeps per-user push (W2).

    Accepts comma-separated ids; ``toparty`` is used instead of per-user
    ``touser`` mapping when non-empty.
    """
    if not _has_config():
        return ""
    return str(current_app.config.get("WECOM_DEFAULT_PARTY", "") or "").strip()


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


def _post_message(payload: dict) -> bool:
    """POST message/send with the configured agentid; True only on errcode==0.

    Never raises; network / API failures degrade to ``False``.
    """
    agent_id = _agent_id()
    if not agent_id:
        logger.info("WECOM push skipped: WECOM_AGENT_ID not set")
        return False
    token = _get_access_token()
    if not token:
        return False
    body = dict(payload)
    body["agentid"] = int(agent_id)
    try:
        resp = requests.post(
            WECOM_MESSAGE_SEND_URL,
            params={"access_token": token},
            json=body,
            timeout=10,
        )
        data = resp.json()
    except Exception as exc:  # noqa: BLE001 - side channel must not raise
        logger.warning("WECOM message/send request failed: %s", exc)
        return False

    if data.get("errcode", -1) != 0:
        logger.warning("WECOM message/send failed: %s", data)
        return False
    logger.info(
        "WECOM push sent: touser=%s toparty=%s",
        body.get("touser", ""),
        body.get("toparty", ""),
    )
    return True


def _recipient_fields(
    user_ids: Iterable[str], party_ids: Optional[Iterable[str]] = None
) -> dict:
    """Build ``touser`` / ``toparty`` request fields (union when both given)."""
    fields: dict = {}
    users = [str(u).strip() for u in user_ids if str(u).strip()]
    if users:
        fields["touser"] = "|".join(users)
    if party_ids:
        parties = [str(p).strip() for p in party_ids if str(p).strip()]
        if parties:
            fields["toparty"] = ",".join(parties)
    return fields


def send_wecom_text(
    user_ids: Iterable[str],
    content: str,
    *,
    party_ids: Optional[Iterable[str]] = None,
) -> bool:
    """Send a plain-text WeCom app message to ``user_ids`` and/or ``party_ids``.

    ``touser`` and ``toparty`` combine as a union when both are given (WeCom
    message/send semantics). Never raises; ``True`` only when the API
    acknowledged with ``errcode == 0``.
    """
    fields = _recipient_fields(user_ids, party_ids)
    if not fields:
        return False
    return _post_message(
        {
            "msgtype": "text",
            "text": {"content": content},
            "safe": 0,
            **fields,
        }
    )



def send_wecom_textcard(
    user_ids: Iterable[str],
    title: str,
    content: str,
    url: str,
    *,
    party_ids: Optional[Iterable[str]] = None,
    btntxt: str = "查看详情",
) -> bool:
    """Send a WeCom textcard app message to ``user_ids`` and/or ``party_ids`` (W2).

    ``btntxt`` is the button label rendered in the card footer. Never raises;
    returns ``True`` only when the API acknowledged with ``errcode == 0``.
    """
    fields = _recipient_fields(user_ids, party_ids)
    if not fields or not url:
        return False
    return _post_message(
        {
            "msgtype": "textcard",
            "textcard": {
                "title": title,
                "description": content,
                "url": url,
                "btntxt": btntxt,
            },
            "safe": 0,
            **fields,
        }
    )



def push_wecom_notification(
    *,
    user_bid: str,
    title: str,
    content: str,
    notif_type: str = "",  # noqa: ARG002 - reserved for future channel routing
    related_bid: str = "",
    msgtype: str = "",  # "text" forces text; "textcard" forces a card; "" = auto
    party_id: str = "",  # explicit department id(s); falls back to WECOM_DEFAULT_PARTY
) -> bool:
    """Side-channel push for one ``user_bid`` (or a department broadcast).

    Message shape (W2):
    - textcard when ``msgtype='textcard'``, or when ``msgtype`` is empty and
      ``related_bid`` plus ``WECOM_NOTIFY_BASE_URL`` are both configured.
      Card ``url`` is ``{base}/c/{related_bid}`` (course learning page).
    - otherwise a plain-text ``【title】\ncontent`` message (unchanged from W1).

    Recipient (W2 toparty):
    - ``party_id`` (explicit) or ``WECOM_DEFAULT_PARTY`` configured -> send to
      those department(s) via ``toparty`` (per-user mapping skipped entirely,
      ``user_bid`` need not resolve).
    - otherwise ``user_bid`` -> WeCom ``UserId`` via verified credentials.

    Returns ``True`` when the message was actually sent; ``False`` when
    disabled, unmapped, misconfigured, or failed. Never raises.
    """
    if not _enabled():
        return False

    base_url = _base_url()
    party = (party_id or _default_party()).strip()
    party_list = [p for p in party.split(",") if p.strip()] if party else []

    use_card = msgtype == "textcard"
    if not use_card and msgtype != "text":
        use_card = bool(related_bid and base_url)

    card_url = ""
    if use_card and related_bid and base_url:
        card_url = f"{base_url}/c/{related_bid}"

    if party_list:
        if card_url:
            return send_wecom_textcard([], title, content, card_url, party_ids=party_list)
        body = f"【{title}】\n{content}" if title else content
        return send_wecom_text([], body, party_ids=party_list)

    user_ids = resolve_wecom_user_ids([user_bid])
    if not user_ids:
        logger.debug(
            "WECOM push skipped: no verified wecom credential for user %s", user_bid
        )
        return False

    if card_url:
        return send_wecom_textcard(user_ids, title, content, card_url)
    body = f"【{title}】\n{content}" if title else content
    return send_wecom_text(user_ids, body)
