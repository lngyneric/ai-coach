"""
OpenRouter TTS Provider.

OpenRouter exposes an OpenAI-compatible speech endpoint at
``{OPENROUTER_API_URL}/audio/speech``. Unlike chat completions, TTS is a
dedicated endpoint (NOT served through the chat completions route), so it
requires its own provider alongside the OpenRouter LLM provider.

Endpoint contract (OpenAI-compatible):
- POST {base}/audio/speech
- body: {"model", "input", "voice", "response_format", "speed", "stream"}
- auth: Authorization: Bearer <OPENROUTER_API_KEY>

Free, Chinese-capable model used by default: ``fish-audio/s2.1-pro-free:free``.
"""

import logging
import requests
from dataclasses import dataclass, field
from typing import Iterator, Optional, Dict, Any, List

from flaskr.common.config import get_config
from flaskr.common.log import AppLoggerProxy
from flaskr.api.tts.base import (
    BaseTTSProvider,
    TTSResult,
    VoiceSettings,
    AudioSettings,
    ProviderConfig,
    ParamRange,
)
from flaskr.service.tts.rpm_gate import acquire_tts_rpm_slot


logger = AppLoggerProxy(logging.getLogger(__name__))

# OpenRouter base for the LLM provider; TTS lives under the same base path.
OPENROUTER_TTS_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

# Free, Chinese-capable speech model verified to work on OpenRouter.
OPENROUTER_TTS_DEFAULT_MODEL = "fish-audio/s2.1-pro-free:free"

# Models exposed to the frontend. Only the free fish-audio model is guaranteed
# to work without billing; others are listed for completeness.
OPENROUTER_TTS_MODELS = [
    {"value": "fish-audio/s2.1-pro-free:free", "label": "Fish Audio S2.1 Pro (Free)"},
]

# OpenRouter speech follows the OpenAI schema where `voice` is required.
# For ``fish-audio/s2.1-pro-free:free`` the only reliably accepted preset voice
# on OpenRouter is ``alloy`` (maps to the model's default multilingual speaker;
# other OpenAI preset names are rejected by the upstream provider). Kept minimal
# so strict validation does not lock out stored course voice_ids.
OPENROUTER_TTS_VOICES = [
    {"value": "alloy", "label": "Alloy（默认）"},
]

# Requests are read in fixed-size chunks when streaming.
_OPENROUTER_STREAM_CHUNK_SIZE = 4096


@dataclass
class OpenRouterHTTPStreamChunk:
    """One parsed OpenRouter HTTP streaming audio event (raw audio bytes)."""

    audio_data: bytes = b""
    is_final: bool = False
    duration_ms: int = 0
    sample_rate: int = 24000
    format: str = "mp3"
    word_count: int = 0
    extra_info: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""


def _resolve_openrouter_base_url() -> str:
    base = (get_config("OPENROUTER_API_URL") or OPENROUTER_TTS_DEFAULT_BASE_URL).strip()
    if not base:
        base = OPENROUTER_TTS_DEFAULT_BASE_URL
    return base.rstrip("/") + "/audio/speech"


def _resolve_openrouter_model(model: Optional[str]) -> str:
    requested = (model or "").strip()
    allowed = {m["value"] for m in OPENROUTER_TTS_MODELS}
    if requested and requested not in allowed:
        logger.warning(
            "Ignoring unsupported OpenRouter TTS model: %s (falling back to default)",
            requested,
        )
        requested = ""
    return requested or OPENROUTER_TTS_DEFAULT_MODEL


def _resolve_openrouter_voice(voice_settings: Optional[VoiceSettings]) -> str:
    voice_id = (voice_settings.voice_id if voice_settings else None) or ""
    voice_id = voice_id.strip()
    if not voice_id:
        return "alloy"
    allowed = {v["value"] for v in OPENROUTER_TTS_VOICES}
    if allowed and voice_id not in allowed:
        logger.warning(
            "OpenRouter TTS voice '%s' not in known set; sending as-is", voice_id
        )
    return voice_id


class OpenRouterTTSProvider(BaseTTSProvider):
    """TTS provider using OpenRouter's OpenAI-compatible speech endpoint."""

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def is_configured(self) -> bool:
        """OpenRouter TTS requires an API key."""
        return bool(get_config("OPENROUTER_API_KEY"))

    def get_default_voice_settings(self) -> VoiceSettings:
        return VoiceSettings(
            voice_id="alloy",
            speed=1.0,
            pitch=0,
            emotion="",
            volume=1.0,
        )

    def get_default_audio_settings(self) -> AudioSettings:
        return AudioSettings(
            format="mp3",
            sample_rate=24000,
            bitrate=128000,
            channel=1,
        )

    def get_supported_voices(self) -> List[Dict[str, str]]:
        return list(OPENROUTER_TTS_VOICES)

    def synthesize(
        self,
        text: str,
        voice_settings: Optional[VoiceSettings] = None,
        audio_settings: Optional[AudioSettings] = None,
        model: Optional[str] = None,
    ) -> TTSResult:
        """Synthesize text to speech (non-streaming)."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        api_key = get_config("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured")

        tts_model = _resolve_openrouter_model(model)
        voice_settings = voice_settings or self.get_default_voice_settings()
        audio_settings = audio_settings or self.get_default_audio_settings()
        voice = _resolve_openrouter_voice(voice_settings)

        payload = {
            "model": tts_model,
            "input": text,
            "voice": voice,
            "response_format": (audio_settings.format or "mp3"),
            "stream": False,
        }
        if voice_settings.speed is not None:
            payload["speed"] = float(voice_settings.speed)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept": "audio/mpeg",
        }

        logger.debug(
            "OpenRouter TTS synthesize: model=%s, voice=%s, text_length=%s",
            tts_model,
            voice,
            len(text),
        )

        response = requests.post(
            _resolve_openrouter_base_url(),
            json=payload,
            headers=headers,
            timeout=90,
        )
        if response.status_code != 200:
            raise ValueError(
                f"OpenRouter TTS API error: {response.status_code} - {response.text[:500]}"
            )

        audio_data = response.content
        if not audio_data:
            raise ValueError("No audio data returned from OpenRouter TTS")

        logger.info(
            "OpenRouter TTS synthesis completed: size=%s bytes, model=%s",
            len(audio_data),
            tts_model,
        )

        return TTSResult(
            audio_data=audio_data,
            duration_ms=0,
            sample_rate=int(audio_settings.sample_rate or 24000),
            format=str(audio_settings.format or "mp3"),
            word_count=len(text),
        )

    def stream_synthesize(
        self,
        text: str,
        voice_settings: Optional[VoiceSettings] = None,
        audio_settings: Optional[AudioSettings] = None,
        model: Optional[str] = None,
    ) -> Iterator[OpenRouterHTTPStreamChunk]:
        """
        Synthesize text with OpenRouter HTTP streaming.

        The endpoint returns raw audio bytes progressively (no SSE framing), so
        each yielded chunk carries incremental audio data and ``is_final`` marks
        the terminating chunk.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        api_key = get_config("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured")

        tts_model = _resolve_openrouter_model(model)
        voice_settings = voice_settings or self.get_default_voice_settings()
        audio_settings = audio_settings or self.get_default_audio_settings()
        voice = _resolve_openrouter_voice(voice_settings)

        payload = {
            "model": tts_model,
            "input": text,
            "voice": voice,
            "response_format": (audio_settings.format or "mp3"),
            "stream": True,
        }
        if voice_settings.speed is not None:
            payload["speed"] = float(voice_settings.speed)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept": "audio/mpeg",
        }

        acquire_tts_rpm_slot(
            provider="openrouter",
            api_key=api_key,
            rpm_limit=0,
            max_wait_seconds=10.0,
        )

        logger.debug(
            "OpenRouter TTS streaming: model=%s, voice=%s, text_length=%s",
            tts_model,
            voice,
            len(text),
        )

        response = requests.post(
            _resolve_openrouter_base_url(),
            json=payload,
            headers=headers,
            stream=True,
            timeout=(10, 120),
        )
        if response.status_code != 200:
            raise ValueError(
                f"OpenRouter TTS API error: {response.status_code} - {response.text[:500]}"
            )

        yielded_any = False
        for chunk in response.iter_content(chunk_size=_OPENROUTER_STREAM_CHUNK_SIZE):
            if not chunk:
                continue
            yielded_any = True
            yield OpenRouterHTTPStreamChunk(
                audio_data=chunk,
                is_final=False,
                duration_ms=0,
                sample_rate=int(audio_settings.sample_rate or 24000),
                format=str(audio_settings.format or "mp3"),
                word_count=0,
            )

        # Emit a final marker so consumers know the stream is complete.
        yield OpenRouterHTTPStreamChunk(
            audio_data=b"",
            is_final=True,
            duration_ms=0,
            sample_rate=int(audio_settings.sample_rate or 24000),
            format=str(audio_settings.format or "mp3"),
            word_count=len(text),
        )
        if not yielded_any:
            logger.warning("OpenRouter TTS stream returned no audio data")

    def get_provider_config(self) -> ProviderConfig:
        return ProviderConfig(
            name="openrouter",
            label="OpenRouter（免费 Fish Audio）",
            speed=ParamRange(min=0.5, max=2.0, step=0.1, default=1.0),
            pitch=ParamRange(min=0, max=0, step=1, default=0),
            supports_emotion=False,
            models=OPENROUTER_TTS_MODELS,
            voices=OPENROUTER_TTS_VOICES,
        )
