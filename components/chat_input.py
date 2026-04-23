"""Chat input component."""

from fasthtml.common import *
from config.icons import _ICON_SEND
from core.utils import _raw
from config.i18n import t


def chat_input_component(language="en"):
    return Div(
        Form(
            Div(
                Textarea(
                    placeholder=t("chat.placeholder", language),
                    name="message",
                    id="chat-input",
                    rows="1",
                    cls="chat-textarea",
                    autofocus=True,
                ),
                Button(
                    _raw(_ICON_SEND),
                    type="submit",
                    cls="send-btn",
                    id="send-btn",
                ),
                cls="input-wrapper",
            ),
            id="chat-form",
            cls="chat-form",
        ),
        Div(
            Span(id="msg-counter", cls="msg-counter"),
            Span(t("chat.disclaimer", language), cls="input-disclaimer"),
            Span(
                _raw("<kbd>Enter</kbd>"),
                f" {t('chat.enter_to_send', language)}",
                cls="input-shortcut",
            ),
            cls="input-hint",
        ),
        cls="chat-input-area",
    )
