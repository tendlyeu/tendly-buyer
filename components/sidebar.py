"""Sidebar navigation for Tendly Buyer."""

from fasthtml.common import *
from config.icons import _ICON_PLUS, _ICON_DELETE, _ICON_MENU
from core.utils import _raw
from components.language_switcher import language_switcher
from config.i18n import t


_ICON_DASHBOARD = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>'
_ICON_PROCUREMENT = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>'
_ICON_DOCUMENTS = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>'
_ICON_REGISTRY = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
_ICON_CHAT = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>'
_ICON_TEAM = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>'


def _user_section(auth, language="en"):
    if auth and auth.get('email'):
        name = auth.get('name', auth['email'].split('@')[0])
        initial = name[0].upper() if name else 'U'
        return Div(
            Div(
                Div(initial, cls="user-avatar-small"),
                Div(
                    Div(name, cls="user-name-text"),
                    Div(auth['email'], cls="user-email-text"),
                    cls="user-info-text",
                ),
                A(
                    _raw('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>'),
                    href="/logout",
                    cls="sidebar-logout-btn",
                    title=t("auth.logout", language),
                ),
                cls="user-info-row",
            ),
            cls="sidebar-user-section",
        )
    else:
        return Div(
            A(
                Span(_raw('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>'), style="display:flex;"),
                f" {t('auth.login', language)}",
                href="/login",
                cls="sidebar-login-btn",
            ),
            cls="sidebar-user-section",
        )


def _nav_item(icon_svg, label, href, active_page, page_id):
    is_active = active_page == page_id
    return A(
        _raw(icon_svg),
        Span(label),
        href=href,
        cls=f"sidebar-nav-item{' active' if is_active else ''}",
    )


def sidebar_component(active_page="dashboard", chat_service=None, language="en", auth=None, active_conversation_id=None):
    nav_items = [
        _nav_item(_ICON_DASHBOARD, t("nav.dashboard", language), "/", active_page, "dashboard"),
        _nav_item(_ICON_PROCUREMENT, t("nav.procurements", language), "/procurements", active_page, "procurements"),
        _nav_item(_ICON_DOCUMENTS, t("nav.documents", language), "/documents", active_page, "documents"),
        _nav_item(_ICON_REGISTRY, t("nav.registry", language), "/registry", active_page, "registry"),
        _nav_item(_ICON_CHAT, t("nav.chat", language), "/chat", active_page, "chat"),
        _nav_item(_ICON_TEAM, t("nav.team", language), "/team", active_page, "team"),
    ]

    sections = [
        Div(
            A(
                Div("T", cls="logo-mark"),
                Span(t("app.name", language), cls="logo-text"),
                Span(t("app.buyer_badge", language), cls="logo-badge"),
                Span("BETA", cls="logo-badge-beta"),
                href="/",
                cls="logo",
            ),
            cls="sidebar-header",
        ),
        Div(*nav_items, cls="sidebar-nav-section", style="padding:8px 8px 4px;"),
    ]

    # Chat conversations section (only when on chat page)
    if active_page == "chat" and chat_service:
        conversations = chat_service.get_conversations()
        conv_items = []
        for c in conversations:
            is_active = c["id"] == active_conversation_id
            conv_items.append(
                A(
                    Span(c["title"], cls="conv-item-text"),
                    Button(
                        _raw(_ICON_DELETE),
                        cls="conv-delete",
                        onclick=f"event.stopPropagation();event.preventDefault();deleteConversation('{c['id']}')",
                    ),
                    href=f"/chat/c/{c['id']}",
                    cls=f"conv-item{' active' if is_active else ''}",
                    data_conv_id=c["id"],
                    onclick=f"return loadConversation(event,'{c['id']}')",
                )
            )
        if not conv_items:
            conv_items.append(
                Div(
                    Span(t("sidebar.no_conversations", language), style="font-size:12px;color:#9ca3af;"),
                    cls="conv-empty",
                    style="padding:16px 12px;text-align:center;",
                )
            )
        sections.append(
            Div(
                Div(style="border-top:1px solid #f3f4f6;margin:4px 12px;"),
                Button(
                    _raw(_ICON_PLUS),
                    f" {t('sidebar.new_chat', language)}",
                    cls="new-chat-btn",
                    onclick="newChat()",
                ),
                Div(*conv_items, cls="conversation-list"),
                cls="sidebar-chat-section",
            )
        )

    sections.append(
        Div(
            _user_section(auth, language),
            Div(language_switcher(language), cls="sidebar-footer-lang"),
            Span(t("app.powered_by", language), cls="sidebar-footer-text"),
            cls="sidebar-footer",
        ),
    )

    return Div(*sections, cls="sidebar")
