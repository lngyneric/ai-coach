from flask import Flask, request, has_request_context
import os
import importlib.util
from collections import defaultdict


# init translations
_translations = defaultdict(lambda: defaultdict(dict))


_lang_equals = {"Zh_cn": "zh"}


def load_translations(app: Flask):
    translations_dir = os.path.join(os.path.dirname(__file__))
    for lang in os.listdir(translations_dir):
        lang_dir = os.path.join(translations_dir, lang)
        if os.path.isdir(lang_dir):
            app.logger.info("load translations of lang: " + lang)
            for module_name in os.listdir(lang_dir):
                module_path = os.path.join(lang_dir, module_name)
                if os.path.isdir(module_path):
                    for file_name in os.listdir(module_path):
                        if file_name.endswith(".py"):
                            file_path = os.path.join(module_path, file_name)
                            spec = importlib.util.spec_from_file_location(
                                module_name, file_path
                            )
                            module = importlib.util.module_from_spec(spec)
                            app.logger.info(
                                "load translations of module: " + module_name
                            )
                            spec.loader.exec_module(module)
                            for var_name in dir(module):
                                if not var_name.startswith("__"):
                                    app.logger.info(
                                        "load translations: "
                                        + module_name.upper()
                                        + "."
                                        + var_name
                                    )
                                    _translations[lang][
                                        module_name.upper() + "." + var_name
                                    ] = getattr(module, var_name)


def _(text):
    if has_request_context() and hasattr(request, "user") and request.user.language:
        return _translations.get(request.user.language, {}).get(text, text)
    else:
        return _translations.get("en", {}).get(text, text)


__all__ = ["_"]
