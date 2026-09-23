import os

import flaskr.api.tts.volcengine_provider as volcengine_provider


def _drive_config_from_env(monkeypatch):
    """
    provider 通过 `get_config(...)` 读取凭证。为避免依赖全局 config 实例
    （用例间可能互相污染），这里让 provider 直接以环境变量为配置来源。
    """
    monkeypatch.setattr(
        volcengine_provider,
        "get_config",
        lambda key, default=None: os.environ.get(key, default),
    )


def test_volcengine_ws_get_credentials_uses_tts_api_key(monkeypatch):
    """当前 provider 使用单一 VOLCENGINE_TTS_API_KEY（X-Api-Key 模式）。"""
    _drive_config_from_env(monkeypatch)
    monkeypatch.setenv("VOLCENGINE_TTS_API_KEY", "test-api-key")

    provider = volcengine_provider.VolcengineTTSProvider()
    api_key, resource_id, resource_id_dup = provider._get_credentials("seed-tts-2.0")

    assert api_key == "test-api-key"
    assert resource_id == "seed-tts-2.0"
    assert resource_id_dup == "seed-tts-2.0"


def test_volcengine_ws_get_credentials_defaults_resource_id(monkeypatch):
    """未传 resource_id 时回退到默认 seed-tts-2.0。"""
    _drive_config_from_env(monkeypatch)
    monkeypatch.setenv("VOLCENGINE_TTS_API_KEY", "test-api-key")

    provider = volcengine_provider.VolcengineTTSProvider()
    api_key, resource_id, _ = provider._get_credentials("")

    assert api_key == "test-api-key"
    assert resource_id == "seed-tts-2.0"


def test_volcengine_ws_get_credentials_empty_when_key_absent(monkeypatch):
    """未配置 API key 时返回空凭证（不再回退到 legacy app/access key）。"""
    _drive_config_from_env(monkeypatch)
    monkeypatch.delenv("VOLCENGINE_TTS_API_KEY", raising=False)

    provider = volcengine_provider.VolcengineTTSProvider()
    api_key, _resource_id, _ = provider._get_credentials("seed-tts-2.0")

    assert api_key == ""


def test_volcengine_ws_is_configured_uses_tts_api_key(monkeypatch):
    _drive_config_from_env(monkeypatch)
    monkeypatch.setenv("VOLCENGINE_TTS_API_KEY", "test-api-key")
    monkeypatch.setattr(volcengine_provider, "WEBSOCKET_AVAILABLE", True)

    provider = volcengine_provider.VolcengineTTSProvider()
    assert provider.is_configured() is True


def test_volcengine_ws_is_configured_false_without_key(monkeypatch):
    _drive_config_from_env(monkeypatch)
    monkeypatch.delenv("VOLCENGINE_TTS_API_KEY", raising=False)
    monkeypatch.setattr(volcengine_provider, "WEBSOCKET_AVAILABLE", True)

    provider = volcengine_provider.VolcengineTTSProvider()
    assert provider.is_configured() is False
