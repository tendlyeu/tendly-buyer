"""Layout components for Tendly Buyer — multi-page layout with sidebar navigation."""

import json

from fasthtml.common import *
from config.icons import _ICON_MENU
from core.utils import _raw
from components.welcome import welcome_screen
from components.messages import message_component
from components.chat_input import chat_input_component
from components.canvas import canvas_panel
from components.sidebar import sidebar_component
from config.i18n import t, get_js_translations


def _page_shell(title_key, language, auth, body_content, active_page="dashboard", chat_service=None, active_conversation_id=None, body_attrs=None, include_canvas=False, rate_info=None):
    """Shared page shell: sidebar + main content area."""
    body_attrs = body_attrs or {}

    js_translations = get_js_translations(language)
    lang_script = Script(f"window.__LANG__ = {json.dumps(js_translations, ensure_ascii=False)};")

    is_authenticated = bool(auth and auth.get('email'))
    auth_script = Script(f"window.__AUTH__ = {json.dumps(is_authenticated)};")
    user_role = auth.get('role', 'buyer') if auth else 'buyer'
    role_script = Script(f"window.__ROLE__ = {json.dumps(user_role)};")

    rate_data = rate_info or {"remaining": -1, "limit": -1, "tier": "anonymous"}
    rate_script = Script(f"window.__RATE__ = {json.dumps(rate_data)};")

    page_script = Script(f"window.__PAGE__ = {json.dumps(active_page)};")

    layout_children = [
        sidebar_component(
            active_page=active_page,
            chat_service=chat_service,
            language=language,
            auth=auth,
            active_conversation_id=active_conversation_id,
        ),
        body_content,
    ]
    if include_canvas:
        layout_children.append(canvas_panel())

    return (
        Title(t(title_key, language)),
        lang_script,
        auth_script,
        role_script,
        rate_script,
        page_script,
        Body(
            Div(
                Button(_raw(_ICON_MENU), cls="hamburger-btn", onclick="toggleSidebar()"),
                Span(
                    f"{t('app.name', language)} {t('app.buyer_badge', language)} ",
                    Span("BETA", cls="logo-badge-beta"),
                    style="font-size:15px;font-weight:600;color:#111827;display:flex;align-items:center;gap:6px;",
                ),
                cls="mobile-header",
            ),
            Div(cls="mobile-overlay", onclick="closeSidebar()"),
            Div(
                *layout_children,
                cls="app-layout",
                id="app",
            ),
            **body_attrs,
        ),
    )


def buyer_page(content, language="en", auth=None, active_page="dashboard", chat_service=None, title_key="app.title"):
    """Render a standard buyer page (dashboard, procurements, documents, etc.)."""
    main_area = Div(content, cls="main-content")
    return _page_shell(
        title_key=title_key,
        language=language,
        auth=auth,
        body_content=main_area,
        active_page=active_page,
        chat_service=chat_service,
    )


def chat_page(conversation_id=None, messages=None, chat_service=None, language="en", auth=None, rate_info=None):
    """Full chat page layout (preserved from original)."""
    body_attrs = {}
    if conversation_id:
        body_attrs["data_conversation_id"] = conversation_id

    if messages:
        # Hide internal "system" primer messages from the UI — they only
        # exist so the LLM has plan context on follow-up turns.
        visible = [m for m in messages if m.get("role") != "system"]
        main_area = Div(
            Div(
                *[message_component(m, language=language) for m in visible],
                id="messages",
                cls="messages-container",
            ),
            chat_input_component(language=language),
            cls="chat-main",
        )
    else:
        main_area = Div(
            welcome_screen(language=language),
            chat_input_component(language=language),
            cls="chat-main",
        )

    return _page_shell(
        title_key="app.title",
        language=language,
        auth=auth,
        body_content=main_area,
        active_page="chat",
        chat_service=chat_service,
        active_conversation_id=conversation_id,
        body_attrs=body_attrs,
        include_canvas=True,
        rate_info=rate_info,
    )
