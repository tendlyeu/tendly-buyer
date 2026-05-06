"""Message and tender card components."""

import json as _json
from datetime import datetime
from fasthtml.common import *
from config.icons import _ICON_COPY, _ICON_LINK
from core.utils import _raw
from config.i18n import t


# Artifact type → translation key + sensible English fallback for the
# "Reopen <kind>" button. Mirrors the dispatch in scripts.py SSE handler.
_ARTIFACT_LABELS = {
    "rfp_draft": ("canvas.rfp_draft", "RFP Draft"),
    "create_plan": ("canvas.create_plan", "New procurement plan"),
    "legal_lookup": ("canvas.legal_lookup", "Legal source"),
    "tender_comparison": ("canvas.tender_comparison", "Tender Comparison"),
    "risk_analysis": ("canvas.risk_analysis", "Risk Analysis"),
    "gap_analysis": ("canvas.gap_analysis", "Gap Analysis"),
    "requirements": ("canvas.requirements", "Requirements"),
    "price_benchmark": ("canvas.price_benchmark", "Price Benchmarks"),
    "tender_detail": ("canvas.tender_detail", "Tender Detail"),
}


def _reopen_artifact_button(artifact: dict, language: str):
    """Render a button that re-opens the artifact's canvas panel.

    Persisted assistant messages now include their `artifact` reference, so
    when the user reloads or revisits a past conversation we can offer them
    a way to bring the side panel back. Previously the canvas was only
    reachable during the original SSE stream — once dismissed, it was gone.
    """
    art_type = artifact.get("type") or ""
    art_id = artifact.get("id") or ""
    if not art_type:
        return None

    key, fallback = _ARTIFACT_LABELS.get(art_type, ("canvas.artifact", art_type.replace("_", " ").title()))
    label = t(key, language) or fallback
    button_label = (t("chat.reopen_artifact", language) or "Reopen") + " " + label

    if art_type == "tender_detail" and artifact.get("tender_id"):
        onclick = f"showTenderDetail({_json.dumps(int(artifact['tender_id']))})"
    elif art_id:
        onclick = (
            f"openArtifact({_json.dumps(art_type)},"
            f"{_json.dumps(art_id)},"
            f"{_json.dumps(label)})"
        )
    else:
        return None

    return Button(
        _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 18l6-6-6-6"/></svg>'),
        Span(button_label, cls="action-btn-label"),
        type="button",
        cls="msg-action-btn reopen-artifact-btn",
        onclick=onclick,
        title=button_label,
    )


def message_component(msg, language="en"):
    is_user = msg.get("role") == "user"
    avatar_letter = "Y" if is_user else "T"
    avatar_cls = "avatar user-avatar" if is_user else "avatar ai-avatar"
    sender = t("chat.you", language) if is_user else t("chat.tendly_ai", language)

    if is_user:
        text_content = Div(msg.get("content", ""), cls="message-text")
    else:
        import markdown as md
        rendered = md.markdown(msg.get("content", ""), extensions=["fenced_code", "tables"])
        text_content = Div(_raw(rendered), cls="message-text")

    tenders = msg.get("tenders", [])
    tender_section = []
    if tenders:
        tender_section.append(tender_cards_component(tenders, language=language))

    # Action buttons for AI messages (copy content, copy link, reopen artifact)
    action_bar = None
    if not is_user:
        action_buttons = [
            Button(
                _raw(_ICON_COPY),
                Span(t("chat.copy", language), cls="action-btn-label"),
                cls="msg-action-btn copy-msg-btn",
                onclick="copyMessageContent(this)",
                title=t("chat.copy", language),
            ),
            Button(
                _raw(_ICON_LINK),
                Span(t("chat.copy_link", language), cls="action-btn-label"),
                cls="msg-action-btn copy-link-btn",
                onclick="copyConversationLink()",
                title=t("chat.copy_link", language),
            ),
        ]
        artifact = msg.get("artifact")
        if isinstance(artifact, dict):
            reopen_btn = _reopen_artifact_button(artifact, language)
            if reopen_btn is not None:
                action_buttons.append(reopen_btn)
        action_bar = Div(*action_buttons, cls="message-actions")

    return Div(
        Div(
            Div(avatar_letter, cls=avatar_cls),
            Div(
                Div(sender, cls="message-sender"),
                text_content,
                *tender_section,
                action_bar,
                cls="message-content",
            ),
            cls="message-inner",
        ),
        cls=f"message {'user-message' if is_user else 'ai-message'}",
    )


def tender_cards_component(tenders, language="en"):
    """Build a compact list of tender cards (server-rendered for page loads)."""
    country_flags = {"EE": "\U0001f1ea\U0001f1ea", "GB": "\U0001f1ec\U0001f1e7", "LV": "\U0001f1f1\U0001f1fb", "PL": "\U0001f1f5\U0001f1f1", "LT": "\U0001f1f1\U0001f1f9", "FR": "\U0001f1eb\U0001f1f7"}
    MAX_VISIBLE = 5
    items = []
    for idx, td in enumerate(tenders):
        flag = country_flags.get(td.get("country_code", ""), "")
        value = td.get("value")
        currency = td.get("currency", "EUR")
        value_str = f"{currency} {value:,.0f}" if value else ""
        deadline = td.get("deadline", "")
        badge_el = None
        if deadline:
            try:
                dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                days_left = (dt.replace(tzinfo=None) - datetime.utcnow()).days
                if days_left > 0:
                    badge_cls = "tender-list-badge tlb-urgent" if days_left < 7 else "tender-list-badge tlb-normal"
                    badge_el = Span(t("tender.days_left", language, days=days_left), cls=badge_cls)
                else:
                    badge_el = Span(t("tender.expired", language), cls="tender-list-badge tlb-expired")
            except Exception:
                pass

        tag_els = []
        if td.get("is_green"):
            tag_els.append(Span(t("tender.green", language), cls="tender-list-tag tlt-green"))
        if td.get("is_eu_funded"):
            tag_els.append(Span(t("tender.eu", language), cls="tender-list-tag tlt-eu"))

        quality_badge_el = None
        qs_val = td.get("quality_score")
        if qs_val is not None:
            qs_int = round(qs_val)
            if qs_int >= 70:
                quality_badge_el = Span(f"{qs_int}/100", cls="tender-list-badge tlb-quality-high")
            elif qs_int >= 50:
                quality_badge_el = Span(f"{qs_int}/100", cls="tender-list-badge tlb-quality-mid")
            else:
                quality_badge_el = Span(f"{qs_int}/100", cls="tender-list-badge tlb-quality-low")

        meta_children = []
        if value_str:
            meta_children.append(Span(value_str, cls="tender-list-value"))
        if quality_badge_el:
            meta_children.append(quality_badge_el)
        if badge_el:
            meta_children.append(badge_el)

        hidden_style = "display:none;" if idx >= MAX_VISIBLE else ""

        items.append(
            Div(
                Span(flag, cls="tender-list-flag"),
                Div(
                    Div(td.get("name", ""), cls="tender-list-name"),
                    Div(td.get("authority", ""), cls="tender-list-org"),
                    cls="tender-list-info",
                ),
                Div(*tag_els, cls="tender-list-tags") if tag_els else None,
                Div(*meta_children, cls="tender-list-meta") if meta_children else None,
                cls="tender-list-item",
                style=hidden_style if hidden_style else None,
                data_hidden="1" if idx >= MAX_VISIBLE else None,
                onclick=f"showTenderDetail({td.get('id', 0)})",
            )
        )

    show_more = None
    if len(tenders) > MAX_VISIBLE:
        view_all_text = t("tender.view_all", language, count=len(tenders))
        show_less_text = t("tender.show_less", language)
        show_more = Button(
            Span(view_all_text),
            _raw('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" style="width:14px;height:14px;"><polyline points="6 9 12 15 18 9"/></svg>'),
            cls="tender-show-more-btn",
            onclick=f"""
                var btn=this;var list=btn.parentElement;var hidden=list.querySelectorAll('[data-hidden]');
                var expanded=btn.dataset.expanded==='1';
                hidden.forEach(function(el){{el.style.display=expanded?'none':'';}});
                btn.dataset.expanded=expanded?'0':'1';
                btn.querySelector('span').textContent=expanded?'{view_all_text}':'{show_less_text}';
                btn.classList.toggle('expanded',!expanded);
            """,
            data_expanded="0",
        )

    result_count = len(tenders)
    result_word = t("tender.result", language) if result_count == 1 else t("tender.results", language)
    result_children = [
        Div(
            Span(t("tender.matching", language), cls="tender-results-title"),
            Span(f"{result_count} {result_word}", cls="tender-results-count"),
            cls="tender-results-header",
        ),
        Div(*[i for i in items if i is not None], show_more, cls="tender-list"),
    ]
    return Div(*result_children, cls="tender-results")
