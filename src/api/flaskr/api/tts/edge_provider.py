"""Microsoft Edge TTS Provider (free, no API key required).

Uses the same WebSocket endpoint as Microsoft Edge's Read Aloud feature.
No authentication needed — works with any internet connection that can reach
``speech.platform.bing.com``.

Voices: 322 neural voices including zh-CN-XiaoxiaoNeural.

Protocol: WebSocket → send config + SSML → receive binary audio frames.

Rate limits: approximately 1 request/second for the free endpoint.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import ssl
import struct
import time
import uuid
from typing import Optional

from flaskr.api.tts.base import (
    BaseTTSProvider,
    TTSResult,
    VoiceSettings,
    AudioSettings,
    ProviderConfig,
    ParamRange,
)
from flaskr.common.config import get_config

logger = logging.getLogger(__name__)

EDGE_WS_URL = "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1"
TRUSTED_CLIENT_TOKEN = "6A5AA1D4EAFF4E9FB37E23D68491D6F4"

EDGE_VOICES = [
    {"value": "zh-CN-XiaoxiaoNeural", "label": "Xiaoxiao (Female, Natural)"},
    {"value": "zh-CN-XiaoyiNeural", "label": "Xiaoyi (Female)"},
    {"value": "zh-CN-YunjianNeural", "label": "Yunjian (Male)"},
    {"value": "zh-CN-YunxiNeural", "label": "Yunxi (Male)"},
    {"value": "zh-CN-YunxiaNeural", "label": "Yunxia (Male)"},
]

EDGE_SAMPLE_RATES = {16000, 24000, 48000}
EDGE_AUDIO_FORMATS = {
    "mp3": "audio-24khz-48kbitrate-mono-mp3",
    "aac": "audio-24khz-48kbitrate-mono-aac",
    "opus": "audio-24khz-48kbitrate-mono-opus",
}


SYNTHESIS_HEADER = (
    "GET /consumer/speech/synthesize/readaloud/edge/v1"
    "?TrustedClientToken={token} HTTP/1.1\r\n"
    "Host: speech.platform.bing.com\r\n"
    "Pragma: no-cache\r\n"
    "Cache-Control: no-cache\r\n"
    "Connection: Upgrade\r\n"
    "Upgrade: websocket\r\n"
    "Sec-WebSocket-Key: {key}\r\n"
    "Sec-WebSocket-Version: 13\r\n"
    "Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits\r\n"
    "Origin: chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold\r\n"
    "Accept-Encoding: gzip, deflate, br\r\n"
    "Accept-Language: en-US,en;q=0.9\r\n"
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    " AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0\r\n"
    "\r\n"
)


class EdgeTTSProvider(BaseTTSProvider):
    """Microsoft Edge Read Aloud TTS provider."""

    provider_name = "edge"  # type: ignore[assignment]

    def is_configured(self) -> bool:
        """Edge TTS is always configured (no API key required)."""
        return True

    def synthesize(
        self,
        text: str,
        voice_settings: Optional[VoiceSettings] = None,
        audio_settings: Optional[AudioSettings] = None,
        model: str = "",
    ) -> TTSResult:
        voice = (voice_settings.voice_id if voice_settings else None) or "zh-CN-XiaoxiaoNeural"
        try:
            audio = asyncio.run(
                _edge_synthesize(text=text, voice=voice)
            )
        except Exception as exc:
            logger.error("Edge TTS synthesis failed: %s", exc)
            raise RuntimeError(f"Edge TTS synthesis failed: {exc}") from exc

        return TTSResult(
            audio_data=audio,
            duration_ms=0,
            sample_rate=24000,
            format="mp3",
            word_count=len(text),
        )

    def stream_synthesize(self, *args, **kwargs) -> TTSResult:
        return self.synthesize(*args, **kwargs)

    def get_default_voice_settings(self) -> VoiceSettings:
        return VoiceSettings(
            voice_id="zh-CN-XiaoxiaoNeural",
            speed=1.0,
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
        return EDGE_VOICES

    def get_provider_config(self) -> ProviderConfig:
        return ProviderConfig(
            name="edge",
            label="Microsoft Edge（免费）",
            speed=ParamRange(min=0.5, max=2.0, step=0.1, default=1.0),
            pitch=ParamRange(min=0.5, max=2.0, step=0.1, default=1.0),
            supports_emotion=False,
            models=None,
            voices=EDGE_VOICES,
        )


async def _edge_synthesize(text: str, voice: str) -> bytes:
    """Connect to Edge TTS WebSocket and synthesize a single text."""
    host = "speech.platform.bing.com"
    path = f"/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken={TRUSTED_CLIENT_TOKEN}"

    ssl_ctx = ssl.create_default_context()
    reader, writer = await asyncio.open_connection(host, 443, ssl=ssl_ctx)

    key = base64.b64encode(uuid.uuid4().bytes).decode()
    upgrade = SYNTHESIS_HEADER.format(token=TRUSTED_CLIENT_TOKEN, key=key)
    writer.write(upgrade.encode())
    await writer.drain()

    response = b""
    while b"\r\n\r\n" not in response:
        chunk = await reader.read(4096)
        if not chunk:
            break
        response += chunk

    if b"101" not in response:
        code_line = response.split(b"\r\n")[0].decode()
        raise RuntimeError(f"WebSocket upgrade failed: {code_line}")

    async def read_exact(n: int) -> bytes:
        data = b""
        while len(data) < n:
            chunk = await reader.read(n - len(data))
            if not chunk:
                raise EOFError()
            data += chunk
        return data

    async def recv_frame() -> tuple[bytes, int]:
        hdr = await read_exact(2)
        opcode = hdr[0] & 0x0F
        length = hdr[1] & 0x7F
        if length == 126:
            length = struct.unpack('>H', await read_exact(2))[0]
        elif length == 127:
            length = struct.unpack('>Q', await read_exact(8))[0]
        return await read_exact(length), opcode

    def ws_send(data: str | bytes) -> None:
        payload = data if isinstance(data, bytes) else data.encode()
        length = len(payload)
        frame = bytearray([0x82])
        if length < 126:
            frame.append(length | 0x80)
        elif length < 65536:
            frame.append(126 | 0x80)
            frame.extend(struct.pack('>H', length))
        else:
            frame.append(127 | 0x80)
            frame.extend(struct.pack('>Q', length))
        mask = uuid.uuid4().bytes[:4]
        frame.extend(mask)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        frame.extend(masked)
        writer.write(bytes(frame))

    # Send config message
    config = {
        "context": {
            "synthesis": {
                "audio": {
                    "metadataoptions": {
                        "sentenceBoundaryEnabled": "false",
                        "wordBoundaryEnabled": "false",
                    },
                    "outputFormat": "audio-24khz-48kbitrate-mono-mp3",
                }
            }
        }
    }
    rid = uuid.uuid4().hex
    ws_send(
        f"X-RequestId:{rid}\r\n"
        f"Content-Type:application/json; charset=utf-8\r\n"
        f"\r\n"
        f"Path:speech.config\r\n"
        f"\r\n"
        f"{json.dumps(config)}"
    )
    await writer.drain()

    # Send SSML
    ssml = (
        f'<speak version="1.0"'
        f' xmlns="http://www.w3.org/2001/10/synthesis"'
        f' xmlns:mstts="http://www.w3.org/2001/mstts"'
        f' xml:lang="zh-CN">'
        f'<voice name="{voice}">{text}</voice>'
        f'</speak>'
    )
    rid2 = uuid.uuid4().hex
    ws_send(
        f"X-RequestId:{rid2}\r\n"
        f"Content-Type:application/ssml+xml\r\n"
        f"\r\n"
        f"Path:ssml\r\n"
        f"\r\n"
        f"{ssml}"
    )
    await writer.drain()

    # Collect audio frames
    audio = b""
    start = time.monotonic()
    while time.monotonic() - start < 30:  # safety timeout
        try:
            data, opcode = await asyncio.wait_for(recv_frame(), timeout=15)
            if opcode == 0x8:
                break
            if opcode == 0x2 and len(data) > 2:
                header_len = struct.unpack('>H', data[:2])[0]
                audio += data[2 + header_len:]
            elif opcode == 0x1:
                msg = data.decode(errors="replace")
                if "Path:turn.end" in msg:
                    break
        except (asyncio.TimeoutError, EOFError):
            break

    writer.close()
