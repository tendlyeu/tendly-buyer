"""Welcome screen component."""

from fasthtml.common import *
from config.icons import _ICON_SEARCH, _ICON_BUILDING, _ICON_LEAF, _ICON_CLOCK, _ICON_WELCOME
from core.utils import _raw
from config.i18n import t


def welcome_screen(language="en"):
    suggestions = [
        (t("welcome.suggestion_1_title", language), t("welcome.suggestion_1_text", language), "suggestion-icon-blue", _ICON_SEARCH),
        (t("welcome.suggestion_2_title", language), t("welcome.suggestion_2_text", language), "suggestion-icon-purple", _ICON_BUILDING),
        (t("welcome.suggestion_3_title", language), t("welcome.suggestion_3_text", language), "suggestion-icon-green", _ICON_LEAF),
        (t("welcome.suggestion_4_title", language), t("welcome.suggestion_4_text", language), "suggestion-icon-amber", _ICON_CLOCK),
    ]
    cards = [
        Div(
            Div(_raw(icon_svg), cls=f"suggestion-icon {icon_cls}"),
            Div(
                Div(title, cls="suggestion-title"),
                Div(desc, cls="suggestion-desc"),
                cls="suggestion-text-wrap",
            ),
            cls="suggestion-card",
            onclick=f"useSuggestion('{title}')",
        )
        for title, desc, icon_cls, icon_svg in suggestions
    ]
    return Div(
        Div(
            Div(_raw(_ICON_WELCOME), cls="welcome-icon"),
            H1(
                Span(t("welcome.title", language)),
                cls="welcome-title",
            ),
            P(t("welcome.subtitle", language), cls="welcome-subtitle"),
            Div(*cards, cls="suggestions-grid"),
            cls="welcome-content",
        ),
        cls="welcome-wrapper",
    )
