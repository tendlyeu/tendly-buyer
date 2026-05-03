"""Multi-language support for Tendly Chat."""

import json
import os
from typing import Optional

SUPPORTED_LANGUAGES = ["et", "en", "lv", "lt", "pl", "fr"]
BETA_LANGUAGES = ["et", "en"]
DEFAULT_LANGUAGE = "et"
LANGUAGE_COOKIE = "tendly_chat_lang"

# Language display info (native name + flag emoji)
LANGUAGE_INFO = {
    "en": {"name": "English", "native": "English", "flag": "\U0001f1ec\U0001f1e7"},
    "et": {"name": "Estonian", "native": "Eesti", "flag": "\U0001f1ea\U0001f1ea"},
    "lv": {"name": "Latvian", "native": "Latvie\u0161u", "flag": "\U0001f1f1\U0001f1fb"},
    "lt": {"name": "Lithuanian", "native": "Lietuvi\u0173", "flag": "\U0001f1f1\U0001f1f9"},
    "pl": {"name": "Polish", "native": "Polski", "flag": "\U0001f1f5\U0001f1f1"},
    "fr": {"name": "French", "native": "Fran\u00e7ais", "flag": "\U0001f1eb\U0001f1f7"},
}

_translations = {}


def _load_translations():
    """Load all translation JSON files."""
    global _translations
    base_dir = os.path.join(os.path.dirname(__file__), "translations")
    for lang in SUPPORTED_LANGUAGES:
        filepath = os.path.join(base_dir, f"{lang}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                _translations[lang] = json.load(f)
        else:
            _translations[lang] = {}


def t(key: str, language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """Get translation by dot-notation key with fallback to English."""
    if not _translations:
        _load_translations()

    def _get(d, k):
        parts = k.split(".")
        for part in parts:
            if isinstance(d, dict):
                d = d.get(part)
            else:
                return None
        return d

    # Try requested language
    val = _get(_translations.get(language, {}), key)
    # Fallback to English
    if val is None and language != DEFAULT_LANGUAGE:
        val = _get(_translations.get(DEFAULT_LANGUAGE, {}), key)
    # Final fallback: return key
    if val is None:
        return key

    # String formatting with kwargs
    if kwargs and isinstance(val, str):
        try:
            return val.format(**kwargs)
        except (KeyError, IndexError):
            return val
    return val


def get_language_from_request(request) -> str:
    """Extract language from cookie or query param."""
    # Check query param first
    lang = request.query_params.get("lang")
    if lang and lang in BETA_LANGUAGES:
        return lang
    # Check cookie
    lang = request.cookies.get(LANGUAGE_COOKIE)
    if lang and lang in BETA_LANGUAGES:
        return lang
    return DEFAULT_LANGUAGE


def get_js_translations(language: str) -> dict:
    """Get subset of translations needed by JavaScript."""
    if not _translations:
        _load_translations()

    js_keys = {
        "chat.thinking": t("chat.thinking", language),
        "chat.searching": t("chat.searching", language),
        "chat.generating": t("chat.generating", language),
        "chat.error": t("chat.error", language),
        "chat.empty_error": t("chat.empty_error", language),
        "tender.matching": t("tender.matching", language),
        "tender.results": t("tender.results", language),
        "tender.result": t("tender.result", language),
        "tender.view_all": t("tender.view_all", language),
        "tender.show_less": t("tender.show_less", language),
        "tender.days_left": t("tender.days_left", language),
        "tender.expired": t("tender.expired", language),
        "tender.green": t("tender.green", language),
        "tender.eu": t("tender.eu", language),
        "chat.you": t("chat.you", language),
        "chat.tendly_ai": t("chat.tendly_ai", language),
        "chat.stream_error": t("chat.stream_error", language),
        "tender.view_on_tendly": t("tender.view_on_tendly", language),
        "chat.copy": t("chat.copy", language),
        "chat.copied": t("chat.copied", language),
        "chat.copy_link": t("chat.copy_link", language),
        "chat.link_copied": t("chat.link_copied", language),
        "tender.save_to_pipeline": t("tender.save_to_pipeline", language),
        "tender.saved": t("tender.saved", language),
        "tender.save": t("tender.save", language),
        "pipeline.saved": t("pipeline.saved", language),
        "pipeline.removed": t("pipeline.removed", language),
        "pipeline.save_error": t("pipeline.save_error", language),
        "auth.login_to_save": t("auth.login_to_save", language),
        "auth.login_prompt_title": t("auth.login_prompt_title", language),
        "auth.login_prompt_text": t("auth.login_prompt_text", language),
        "auth.login_button": t("auth.login_button", language),
        "auth.signup_button": t("auth.signup_button", language),
        # Rate limit / upgrade modal
        "chat.messages_remaining": t("chat.messages_remaining", language),
        "upgrade.anon_title": t("upgrade.anon_title", language),
        "upgrade.anon_text": t("upgrade.anon_text", language),
        "upgrade.free_title": t("upgrade.free_title", language),
        "upgrade.free_text": t("upgrade.free_text", language),
        "upgrade.feature_unlimited": t("upgrade.feature_unlimited", language),
        "upgrade.feature_matching": t("upgrade.feature_matching", language),
        "upgrade.feature_pipeline": t("upgrade.feature_pipeline", language),
        "upgrade.view_plans": t("upgrade.view_plans", language),
        "upgrade.dismiss": t("upgrade.dismiss", language),
    }
    return js_keys
