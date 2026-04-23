"""Tender detail panel component."""

from datetime import datetime
from fasthtml.common import *
from config.icons import _ICON_CLOSE, _ICON_DOWNLOAD, _ICON_EXTERNAL, _ICON_TROPHY
from core.utils import _raw, _get_file_type_info, _format_file_size
from components.requirements import format_requirements_component
from config.i18n import t


def tender_detail_panel(detail, language="en", auth=None, is_saved=False):
    """Build the right-hand detail panel as FastHTML components."""
    if not detail:
        return None

    country_flags = {"EE": "\U0001f1ea\U0001f1ea", "GB": "\U0001f1ec\U0001f1e7", "LV": "\U0001f1f1\U0001f1fb", "PL": "\U0001f1f5\U0001f1f1", "LT": "\U0001f1f1\U0001f1f9", "FR": "\U0001f1eb\U0001f1f7"}
    flag = country_flags.get(detail.get("country_code", ""), "")
    value = detail.get("value")
    currency = detail.get("currency", "EUR")
    value_str = f"{currency} {value:,.0f}" if value else t("tender.not_specified", language)

    deadline_str = ""
    if detail.get("deadline"):
        try:
            dt = datetime.fromisoformat(detail["deadline"].replace("Z", "+00:00"))
            deadline_str = dt.strftime("%d %b %Y, %H:%M")
        except Exception:
            deadline_str = detail["deadline"]

    badges = []
    if detail.get("is_green"):
        badges.append(Span(t("tender.green_procurement", language), cls="detail-badge detail-badge-green"))
    if detail.get("is_eu_funded"):
        badges.append(Span(t("tender.eu_funded", language), cls="detail-badge detail-badge-eu"))
    if detail.get("status"):
        status_val = str(detail["status"]).strip()
        # Only show status badge if it's a readable text label, not a numeric code
        if status_val and not status_val.isdigit():
            badges.append(Span(status_val, cls="detail-badge detail-badge-active"))

    # Build document items with file type detection
    doc_items = []
    for doc in detail.get("documents", []):
        display_name = doc.get("name") or doc.get("file_name", "Document")
        # Try file_name first for extension detection (more likely to have extensions)
        detect_name = doc.get("file_name") or doc.get("name", "")
        ext_label, icon_svg, icon_cls = _get_file_type_info(detect_name)
        # If still default, try using document type field as hint
        if icon_cls == "detail-doc-icon-default" and doc.get("type"):
            doc_type = str(doc["type"]).lower()
            type_map = {"pdf": ".pdf", "word": ".docx", "excel": ".xlsx", "zip": ".zip", "image": ".png"}
            for key, ext in type_map.items():
                if key in doc_type:
                    ext_label, icon_svg, icon_cls = _get_file_type_info(f"file{ext}")
                    break
        size_str = _format_file_size(doc.get("file_size") or doc.get("size"))
        meta_parts = [ext_label.upper()]
        if size_str:
            meta_parts.append(size_str)

        doc_items.append(
            Div(
                Div(_raw(icon_svg), cls=f"detail-doc-icon {icon_cls}"),
                Div(
                    Div(display_name, cls="detail-doc-name"),
                    Div(" / ".join(meta_parts), cls="detail-doc-meta"),
                    cls="detail-doc-info",
                ),
                Div(_raw(_ICON_DOWNLOAD), cls="detail-doc-action"),
                cls="detail-doc-item",
            )
        )

    # Quality score with ring indicator
    quality_section = []
    if detail.get("quality_score") is not None:
        score = detail["quality_score"]
        circumference = 138.23
        offset = circumference - (score / 100) * circumference
        if score >= 70:
            ring_color = "#16a34a"
            label = t("tender.good_quality", language)
        elif score >= 50:
            ring_color = "#d97706"
            label = t("tender.average_quality", language)
        else:
            ring_color = "#9ca3af"
            label = t("tender.below_average", language)

        ring_svg = f'<svg viewBox="0 0 52 52"><circle class="ring-bg" cx="26" cy="26" r="22"/><circle class="ring-fg" cx="26" cy="26" r="22" stroke="{ring_color}" stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"/></svg>'

        quality_section.append(
            Div(
                Div(t("tender.quality_score", language), cls="detail-section-title"),
                Div(
                    Div(
                        _raw(ring_svg),
                        Div(str(round(score)), cls="quality-score-number"),
                        cls="quality-score-ring",
                    ),
                    Div(label, cls="quality-score-label"),
                    cls="quality-score-display",
                ),
                cls="detail-section",
            )
        )

    # Evaluation criteria with progress bars
    criteria_items = []
    for c in detail.get("evaluation_criteria", []):
        weight = c.get("weight", 0)
        criteria_items.append(
            Div(
                Div(
                    Span(c.get("name", ""), cls="eval-criteria-name"),
                    Span(f"{weight}%", cls="eval-criteria-weight"),
                    cls="eval-criteria-header",
                ),
                Div(
                    Div(cls="eval-criteria-bar-fill", style=f"width:{min(weight, 100)}%;"),
                    cls="eval-criteria-bar",
                ),
                cls="eval-criteria-item",
            )
        )

    source_section = []
    if detail.get("tendly_url"):
        source_section.append(
            A(_raw(_ICON_EXTERNAL), f" {t('tender.view_on_tendly', language)}", href=detail["tendly_url"], target="_blank", rel="noopener", cls="detail-tendly-link")
        )
    if detail.get("source_url"):
        source_section.append(
            A(_raw(_ICON_EXTERNAL), f" {t('tender.view_source', language)}", href=detail["source_url"], target="_blank", rel="noopener", cls="detail-source-link")
        )

    sections = []

    # Main info
    main_children = [
        H3(detail.get("name", ""), style="font-size:16px;font-weight:600;color:#111827;line-height:1.4;margin-bottom:10px;"),
    ]
    if badges:
        main_children.append(Div(*badges, style="margin-bottom:10px;display:flex;gap:6px;flex-wrap:wrap;"))
    main_children.append(Div(Div(t("tender.contracting_authority", language), cls="detail-field-label"), Div(detail.get("authority", ""), cls="detail-field-value"), cls="detail-field"))
    if detail.get("reference"):
        main_children.append(Div(Div(t("tender.reference", language), cls="detail-field-label"), Div(str(detail.get("reference", "")), cls="detail-field-value"), cls="detail-field"))
    sections.append(Div(*main_children, cls="detail-section"))

    # Key information
    key_fields = [
        Div(Div(t("tender.estimated_value", language), cls="detail-field-label"), Div(value_str, cls="detail-field-value", style="font-weight:600;"), cls="detail-field"),
        Div(Div(t("tender.submission_deadline", language), cls="detail-field-label"), Div(deadline_str or t("tender.not_specified", language), cls="detail-field-value"), cls="detail-field"),
        Div(Div(t("tender.cpv_code", language), cls="detail-field-label"), Div(f"{detail.get('cpv_code', '')} {detail.get('cpv_name', '')}", cls="detail-field-value"), cls="detail-field"),
        Div(Div(t("tender.country", language), cls="detail-field-label"), Div(f"{flag} {detail.get('country', '')}", cls="detail-field-value"), cls="detail-field"),
    ]
    if detail.get("duration_months"):
        dm = detail['duration_months']
        month_word = t("tender.month", language) if dm == 1 else t("tender.months", language)
        key_fields.append(Div(Div(t("tender.duration", language), cls="detail-field-label"), Div(f"{dm} {month_word}", cls="detail-field-value"), cls="detail-field"))
    if detail.get("nuts_code"):
        key_fields.append(Div(Div(t("tender.nuts_code", language), cls="detail-field-label"), Div(detail["nuts_code"], cls="detail-field-value"), cls="detail-field"))
    sections.append(Div(Div(t("tender.key_info", language), cls="detail-section-title"), *key_fields, cls="detail-section"))

    if quality_section:
        sections.extend(quality_section)

    if detail.get("description"):
        sections.append(Div(Div(t("tender.description", language), cls="detail-section-title"), Div(detail["description"], cls="detail-field-value", style="font-size:13.5px;line-height:1.6;"), cls="detail-section"))

    if detail.get("ai_requirements"):
        req_component = format_requirements_component(detail["ai_requirements"])
        if req_component:
            sections.append(Div(Div(t("tender.ai_requirements", language), cls="detail-section-title"), req_component, cls="detail-section"))

    if criteria_items:
        sections.append(Div(Div(t("tender.evaluation_criteria", language), cls="detail-section-title"), *criteria_items, cls="detail-section"))

    # Winner & Results section
    result_data = detail.get("result")
    if result_data:
        result_children = []
        if result_data.get("winner"):
            winner_meta = []
            if result_data.get("contract_cost"):
                winner_meta.append(Span(f"{currency} {result_data['contract_cost']:,.0f}"))
            if result_data.get("offer_count"):
                winner_meta.append(Span(f"{result_data['offer_count']} {t('tender.offers', language)}"))
            if result_data.get("status"):
                winner_meta.append(Span(result_data["status"]))

            result_children.append(
                Div(
                    Div(_raw(_ICON_TROPHY), f" {t('tender.winner', language)}", cls="detail-winner-label"),
                    Div(result_data["winner"], cls="detail-winner-name"),
                    Div(*winner_meta, cls="detail-winner-meta") if winner_meta else None,
                    cls="detail-winner-card",
                )
            )
        else:
            result_fields = []
            if result_data.get("contract_cost"):
                cost_str = f"{currency} {result_data['contract_cost']:,.0f}"
                result_fields.append(
                    Div(Div(t("tender.contract_value", language), cls="detail-field-label"),
                        Div(cost_str, cls="detail-field-value", style="font-weight:600;"),
                        cls="detail-field")
                )
            if result_data.get("actual_cost"):
                actual_str = f"{currency} {result_data['actual_cost']:,.0f}"
                result_fields.append(
                    Div(Div(t("tender.actual_cost", language), cls="detail-field-label"),
                        Div(actual_str, cls="detail-field-value"),
                        cls="detail-field")
                )
            if result_data.get("offer_count"):
                result_fields.append(
                    Div(Div(t("tender.number_of_offers", language), cls="detail-field-label"),
                        Div(str(result_data["offer_count"]), cls="detail-field-value", style="font-weight:600;"),
                        cls="detail-field")
                )
            if result_data.get("status"):
                result_fields.append(
                    Div(Div(t("tender.contract_status", language), cls="detail-field-label"),
                        Div(result_data["status"], cls="detail-field-value"),
                        cls="detail-field")
                )
            result_children.extend(result_fields)

        if result_children:
            sections.append(Div(Div(t("tender.results_section", language), cls="detail-section-title"), *[c for c in result_children if c is not None], cls="detail-section"))

    if doc_items:
        sections.append(Div(Div(f"{t('tender.documents', language)} ({len(doc_items)})", cls="detail-section-title"), *doc_items, cls="detail-section"))

    if source_section:
        sections.append(Div(*source_section, cls="detail-section"))

    # Save to pipeline button
    tender_id = detail.get("id") or detail.get("procurement_id", "")
    save_icon = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>'
    save_icon_filled = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>'

    if auth and auth.get('email'):
        if is_saved:
            save_btn = Button(
                _raw(save_icon_filled),
                f" {t('tender.saved', language)}",
                cls="detail-save-btn saved",
                id=f"save-btn-{tender_id}",
                onclick=f"unsaveTender({tender_id})",
            )
        else:
            save_btn = Button(
                _raw(save_icon),
                f" {t('tender.save_to_pipeline', language)}",
                cls="detail-save-btn",
                id=f"save-btn-{tender_id}",
                onclick=f"saveTender({tender_id})",
            )
    else:
        save_btn = Button(
            _raw(save_icon),
            f" {t('tender.save_to_pipeline', language)}",
            cls="detail-save-btn",
            onclick="promptLogin()",
        )

    return Div(
        Div(
            Span(f"{flag} {t('tender.detail', language)}", cls="detail-header-title"),
            Div(
                save_btn,
                Button(_raw(_ICON_CLOSE), cls="detail-close-btn", onclick="closeDetailPanel()"),
                cls="detail-header-actions",
            ),
            cls="detail-header",
        ),
        Div(*sections, cls="detail-body"),
        cls="detail-panel",
    )
