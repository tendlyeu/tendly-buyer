"""URL utilities for generating tendly.eu tender links."""

import re
import unicodedata


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    if not text:
        return ""
    text = text.lower().strip()
    char_map = {
        'ä': 'a', 'ö': 'o', 'ü': 'u', 'õ': 'o', 'š': 's', 'ž': 'z',
        'ā': 'a', 'ē': 'e', 'ī': 'i', 'ū': 'u', 'č': 'c', 'ģ': 'g',
        'ķ': 'k', 'ļ': 'l', 'ņ': 'n', 'ŗ': 'r',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'ø': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u',
        'ñ': 'n', 'ç': 'c', 'ß': 'ss',
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
        'ś': 's', 'ź': 'z', 'ż': 'z',
        'ė': 'e', 'į': 'i', 'ų': 'u',
    }
    for original, replacement in char_map.items():
        text = text.replace(original, replacement)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text


def get_tendly_url(tender_id, tender_name, language="en"):
    """Generate full tendly.eu URL for a tender."""
    slug = slugify(tender_name)
    lang_prefix = language if language != "en" else "en"
    # Map language codes to URL prefixes used by tendly.eu
    lang_map = {"et": "ee", "en": "en", "lv": "lv", "lt": "lt", "pl": "pl", "fr": "fr"}
    prefix = lang_map.get(lang_prefix, "en")
    if slug:
        return f"https://tendly.eu/{prefix}/tender/{tender_id}-{slug}"
    return f"https://tendly.eu/{prefix}/tender/{tender_id}"
