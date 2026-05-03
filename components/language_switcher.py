"""Language switcher component."""

from fasthtml.common import *
from config.i18n import BETA_LANGUAGES, LANGUAGE_INFO


def language_switcher(current_language="en"):
    """Compact language switcher dropdown for sidebar footer."""
    current = LANGUAGE_INFO.get(current_language, LANGUAGE_INFO["en"])

    options = []
    for lang_code in BETA_LANGUAGES:
        info = LANGUAGE_INFO[lang_code]
        options.append(
            Option(
                f"{info['flag']} {info['native']}",
                value=lang_code,
                selected=(lang_code == current_language),
            )
        )

    return Select(
        *options,
        cls="language-switcher",
        onchange="window.location.href='/set-language/'+this.value",
    )
