import os
from pathlib import Path

from flask import Flask

from flaskr.i18n import _translations, load_translations, set_language, _ as t


def _shared_i18n_root() -> Path:
    # Resolve repo/src/i18n relative to this test file
    return Path(__file__).resolve().parents[3] / "i18n"


def test_load_and_translate_basic():
    os.environ["SHARED_I18N_ROOT"] = str(_shared_i18n_root())
    app = Flask(__name__)

    # Load translations from shared JSON
    load_translations(app)

    # Default language is en-US
    set_language("en-US")
    assert t("module.chat.ask") == "Ask"

    # Switch language to zh-CN
    set_language("zh-CN")
    assert t("module.chat.ask") == "追问"


def test_language_fallback_to_default():
    os.environ["SHARED_I18N_ROOT"] = str(_shared_i18n_root())
    app = Flask(__name__)

    load_translations(app)

    # Set an unsupported language and verify fallback to en-US
    set_language("fr-FR")
    assert t("module.chat.ask") == "Ask"


def test_existing_language_missing_key_falls_back_to_default():
    os.environ["SHARED_I18N_ROOT"] = str(_shared_i18n_root())
    app = Flask(__name__)

    load_translations(app)

    # fr-FR 是精简语言包（仅 onboarding / backend.user），本就没有 module.chat.ask；
    # 对该语言取缺失 key 时应回退到默认语言（en-US）文案。
    fr_translations = _translations["fr-FR"]
    assert "module.chat.ask" not in fr_translations

    set_language("fr-FR")
    assert t("module.chat.ask") == "Ask"


def test_flat_section_namespace_loading():
    os.environ["SHARED_I18N_ROOT"] = str(_shared_i18n_root())
    app = Flask(__name__)

    load_translations(app)

    # __flat__ keys should be exposed under their declared namespace
    set_language("en-US")
    assert t("server.common.unknownError") == "Unknown Error"
