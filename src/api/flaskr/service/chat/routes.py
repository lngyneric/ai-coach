"""Generic chat endpoint backed by the LLM gateway (W2, task 3).

``POST /api/chat`` exposes the verified LLM gateway (``flaskr.api.llm.chat_llm``)
to authenticated users:

- request  body: ``{"messages": [{"role": "user", "content": "..."}], "model"?: str,
  "temperature"?: number, "stream"?: bool}``
- ``stream: true``  → SSE ``text/event-stream`` (``data: {type: text_delta, text}``
  chunks, ``data: {type: done, final}`` then ``data: [DONE]``)
- ``stream: false`` → JSON ``{code:0, data:{answer, model}}``

Authentication is enforced by the global ``before_request`` auth middleware
(``flaskr.route.user``): this endpoint is not in the bypass list, so a valid
``Token`` header (or ``?token=`` / body ``token``) is required and
``request.user`` is populated.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from flask import Flask, Response, request, stream_with_context

from flaskr.api.langfuse import (
    create_trace_with_root_span,
    finalize_langfuse_trace,
    get_langfuse_client,
)
from flaskr.api.llm import chat_llm, get_allowed_models
from flaskr.framework.plugin.inject import inject
from flaskr.route.common import make_common_response
from flaskr.service.common.models import raise_param_error
from flaskr.service.metering import UsageContext
from flaskr.service.metering.consts import BILL_USAGE_SCENE_PROD

DEFAULT_TEMPERATURE = 0.3
MAX_TEMPERATURE = 2.0

_ALLOWED_ROLES = ("system", "user", "assistant")

TRACE_NAME = "chat_api"
SPAN_NAME = "chat_api_span"
GENERATION_NAME = "chat_api"


def _resolve_model(app: Flask, raw: Any) -> str:
    """Pick the requested model or fall back to ``DEFAULT_LLM_MODEL``.

    When ``LLM_ALLOWED_MODELS`` is configured the requested model must be in
    that allow-list (same guard as other LLM endpoints).
    """
    model = str(raw or "").strip()
    if not model:
        model = str(app.config.get("DEFAULT_LLM_MODEL", "") or "").strip()
    if not model:
        raise_param_error("chat: model is required and DEFAULT_LLM_MODEL is unset")
    allowed = get_allowed_models()
    if allowed and model not in allowed:
        raise_param_error(f"chat: model not allowed: {model}")
    return model


def _resolve_temperature(raw: Any) -> float:
    if raw is None:
        return DEFAULT_TEMPERATURE
    try:
        temperature = float(raw)
    except (TypeError, ValueError):
        raise_param_error("chat: temperature must be a number")
    if temperature < 0 or temperature > MAX_TEMPERATURE:
        raise_param_error("chat: temperature must be within [0, 2]")
    return temperature


def _validate_messages(raw: Any) -> list[dict[str, str]]:
    """Validate OpenAI-style ``messages``; normalize role/content to str."""
    if not isinstance(raw, list) or not raw:
        raise_param_error("chat: messages must be a non-empty array")
    messages: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise_param_error("chat: each message must be an object")
        role = str(item.get("role") or "").strip()
        content = str(item.get("content") or "").strip()
        if role not in _ALLOWED_ROLES or not content:
            raise_param_error(
                "chat: message must have role in system/user/assistant "
                "and non-empty content"
            )
        messages.append({"role": role, "content": content})
    return messages


def _current_user_id() -> str:
    user = getattr(request, "user", None)
    return str(getattr(user, "user_id", "") or "").strip()


def _build_usage_context(user_id: str) -> UsageContext:
    return UsageContext(
        user_bid=user_id,
        usage_scene=BILL_USAGE_SCENE_PROD,
        billable=0,
    )


def _stream_sse(
    app: Flask,
    user_id: str,
    trace: Any,
    span: Any,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
) -> Response:
    """SSE streaming response for ``stream: true``."""

    def event_stream():
        collected: list[str] = []
        try:
            yield (
                "data: "
                + json.dumps(
                    {"type": "init", "session_id": uuid.uuid4().hex},
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            resp = chat_llm(
                app,
                user_id,
                span,
                model=model,
                messages=messages,
                json=False,
                stream=True,
                generation_name=GENERATION_NAME,
                temperature=temperature,
                usage_context=_build_usage_context(user_id),
                usage_scene=BILL_USAGE_SCENE_PROD,
                billable=0,
            )
            for chunk in resp:
                if not chunk.result:
                    continue
                collected.append(chunk.result)
                yield (
                    "data: "
                    + json.dumps(
                        {"type": "text_delta", "text": chunk.result},
                        ensure_ascii=False,
                    )
                    + "\n\n"
                )
            yield (
                "data: "
                + json.dumps(
                    {"type": "done", "final": "".join(collected)},
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            yield "data: [DONE]\n\n"
        except Exception as exc:  # noqa: BLE001 - SSE stream must not die silently
            app.logger.error("chat_api SSE error: %s", exc)
            yield (
                "data: "
                + json.dumps({"type": "error", "error": str(exc)}, ensure_ascii=False)
                + "\n\n"
            )
            yield "data: [DONE]\n\n"
        finally:
            finalize_langfuse_trace(
                trace=trace,
                root_span=span,
                root_span_payload={"output": "".join(collected)},
            )

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@inject
def register_chat_routes(app: Flask, path_prefix: str = "/api") -> None:
    app.logger.info("register chat routes %s", path_prefix)

    @app.route(path_prefix + "/chat", methods=["POST"])
    def chat_api():
        """Generic AI chat.

        ---
        tags:
            - chat
        requestBody:
            required: true
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            messages:
                                type: array
                                items:
                                    type: object
                                    properties:
                                        role:
                                            type: string
                                            enum: [system, user, assistant]
                                        content:
                                            type: string
                            model:
                                type: string
                            temperature:
                                type: number
                            stream:
                                type: boolean
        responses:
            200:
                description: LLM answer (JSON when stream=false, SSE when stream=true)
        """
        payload = request.get_json(silent=True) or {}
        messages = _validate_messages(payload.get("messages"))
        model = _resolve_model(app, payload.get("model"))
        temperature = _resolve_temperature(payload.get("temperature"))
        stream = bool(payload.get("stream", True))

        user_id = _current_user_id()
        if not user_id:
            raise_param_error("chat: login required")

        trace, span = create_trace_with_root_span(
            client=get_langfuse_client(),
            trace_payload={
                "user_id": user_id,
                "input": messages,
                "name": TRACE_NAME,
                "metadata": {"scene": TRACE_NAME, "model": model},
            },
            root_span_payload={"name": SPAN_NAME, "input": messages},
        )

        if stream:
            return _stream_sse(app, user_id, trace, span, model, messages, temperature)

        # Non-streaming: collect the single chat_llm response.
        try:
            collected: list[str] = []
            resp = chat_llm(
                app,
                user_id,
                span,
                model=model,
                messages=messages,
                json=False,
                stream=False,
                generation_name=GENERATION_NAME,
                temperature=temperature,
                usage_context=_build_usage_context(user_id),
                usage_scene=BILL_USAGE_SCENE_PROD,
                billable=0,
            )
            for chunk in resp:
                if chunk.result:
                    collected.append(chunk.result)
            answer = "".join(collected)
            finalize_langfuse_trace(
                trace=trace,
                root_span=span,
                root_span_payload={"output": answer},
            )
            return make_common_response({"answer": answer, "model": model})
        except Exception:
            finalize_langfuse_trace(trace=trace, root_span=span)
            raise
