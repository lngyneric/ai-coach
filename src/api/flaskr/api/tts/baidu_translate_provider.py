"""Baidu Translate TTS Provider (free, no registration).

Uses Baidu Translate's public TTS endpoint.
No API key required — works as long as ``fanyi.baidu.com`` is reachable.

Voices: zh (Chinese Mandarin), en (English), and many others.
Quality: Good neural-like quality for Chinese.

Rate limits: approximately 5-10 requests/second.
Text limit: ~200 characters per request.
"""
from __future__ import annotations

import base64
import logging
from typing import Optional
from urllib.parse import quote

import requests
from requests.exceptions import RequestException

from flaskr.api.tts.base import (
    BaseTTSProvider,
    TTSResult,
    VoiceSettings,
    AudioSettings,
    ProviderConfig,
    ParamRange,
)

logger = logging.getLogger(__name__)

BAIDU_TRANSLATE_TTS_URL = "https://fanyi.baidu.com/gettts"

BAIDU_VOICES = [
    {"value": "zh", "label": "Chinese Mandarin"},
    {"value": "en", "label": "English"},
    {"value": "yue", "label": "Cantonese"},
    {"value": "jp", "label": "Japanese"},
    {"value": "kor", "label": "Korean"},
]

BAIDU_SPEEDS = [
    {"value": 1, "label": "Slow"},
    {"value": 3, "label": "Normal"},
    {"value": 5, "label": "Fast"},
]

MAX_CHARS_PER_REQUEST = 200


class BaiduTranslateTTSProvider(BaseTTSProvider):
    """Baidu Translate public TTS provider (free, no key)."""

    provider_name = "baidu_translate"

    def is_configured(self) -> bool:
        """Always configured — no API key needed."""
        return True

    def synthesize(
        self,
        text: str,
        voice_settings: Optional[VoiceSettings] = None,
        audio_settings: Optional[AudioSettings] = None,
        model: str = "",
    ) -> TTSResult:
        lang = (voice_settings.voice_id if voice_settings else None) or "zh"
        speed = (voice_settings.speed if voice_settings else None) or 3
        text = text.strip()

        # Baidu TTS has a character limit — truncate if needed
        if len(text) > MAX_CHARS_PER_REQUEST:
            text = text[:MAX_CHARS_PER_REQUEST]

        try:
            resp = requests.get(
                BAIDU_TRANSLATE_TTS_URL,
                params={
                    "text": text,
                    "lan": lang,
                    "spd": int(speed),
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    " AppleWebKit/537.36 (KHTML, like Gecko)"
                    " Chrome/120.0.0.0 Safari/537.36",
                },
                timeout=15,
            )
        except RequestException as exc:
            logger.error("Baidu Translate TTS request failed: %s", exc)
            raise RuntimeError(f"Baidu TTS request failed: {exc}") from exc

        if resp.status_code != 200:
            raise RuntimeError(
                f"Baidu TTS returned {resp.status_code}"
            )

        content_type = resp.headers.get("Content-Type", "")
        if "audio" not in content_type and len(resp.content) < 500:
            # May be an error message in JSON
            raise RuntimeError(f"Baidu TTS error: {resp.text[:200]}")

        return TTSResult(
            audio_data=resp.content,
            duration_ms=0,
            sample_rate=24000,
            format="mp3",
            word_count=len(text),
        )

    def stream_synthesize(self, *args, **kwargs) -> TTSResult:
        return self.synthesize(*args, **kwargs)

    def get_default_voice_settings(self) -> VoiceSettings:
        return VoiceSettings(
            voice_id="zh",
            speed=3.0,
            pitch=1.0,
            emotion="neutral",
        )

    def get_default_audio_settings(self) -> AudioSettings:
        return AudioSettings(
            format="mp3",
            sample_rate=24000,
            bitrate=48000,
        )

    @classmethod
    def get_supported_voices(cls) -> list[dict]:
        return BAIDU_VOICES

    def get_provider_config(self) -> ProviderConfig:
        return ProviderConfig(
            name="baidu_translate",
            label="百度翻译（免费）",
            speed=ParamRange(min=1, max=5, step=1, default=3),
            pitch=ParamRange(min=1, max=5, step=1, default=3),
            supports_emotion=False,
            models=None,
            voices=BAIDU_VOICES,
        )
