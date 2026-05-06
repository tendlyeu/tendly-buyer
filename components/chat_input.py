"""Chat input component."""

from fasthtml.common import *
from config.icons import _ICON_SEND
from core.utils import _raw
from config.i18n import t


_ICON_PAPERCLIP = (
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round">'
    '<path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 '
    '015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/></svg>'
)


def chat_input_component(language="en"):
    return Div(
        # Hidden chip showing the currently-attached file (if any).
        Div(id="chat-attachment-chip", cls="chat-attachment-chip", style="display:none;"),
        Form(
            Div(
                # Hidden file input + paperclip button that opens it.
                Input(
                    type="file",
                    id="chat-file-input",
                    name="document",
                    accept=".pdf,.docx,.txt,.xlsx,.csv",
                    style="display:none;",
                ),
                Button(
                    _raw(_ICON_PAPERCLIP),
                    type="button",
                    id="chat-attach-btn",
                    cls="attach-btn",
                    title=t("chat.attach_file", language) or "Attach file",
                    onclick="document.getElementById('chat-file-input').click()",
                ),
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
