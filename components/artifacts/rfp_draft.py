"""RFP draft artifact renderer for the canvas panel."""

from fasthtml.common import *


PRIORITY_COLORS = {
    "mandatory": ("#dc2626", "#fef2f2"),
    "eligibility": ("#7c3aed", "#f5f3ff"),
    "technical": ("#2563eb", "#eff6ff"),
    "financial": ("#16a34a", "#f0fdf4"),
}


def rfp_draft_panel(data: dict, language: str = "en"):
    """Render RFP draft as HTML for the canvas."""
    if not data:
        return Div(P("No data available."), cls="detail-body")

    rfp = data.get("rfp") or {}
    sections = []

    # Title and metadata
    title = rfp.get("title", "RFP Draft")
    sections.append(Div(
        Div(title, style="font-size:16px;font-weight:700;color:#111827;margin-bottom:8px;"),
        Div(
            _badge(rfp.get("category", ""), "#2563eb", "#eff6ff"),
            _badge(f"CPV: {rfp.get('cpv_code', '')}", "#7c3aed", "#f5f3ff") if rfp.get("cpv_code") else None,
            _badge(rfp.get("procedure_type", ""), "#6b7280", "#f3f4f6") if rfp.get("procedure_type") else None,
            style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;",
        ),
        *(
            [Div(f"Estimated: £{rfp['estimated_value']:,.0f}", style="font-size:13px;font-weight:600;color:#16a34a;")]
            if rfp.get("estimated_value") else []
        ),
        cls="detail-section",
    ))

    rfp_sections = rfp.get("sections", {})

    # Scope of work
    scope = rfp_sections.get("scope_of_work", "")
    if scope:
        sections.append(Div(
            Div("Scope of Work", cls="detail-section-title"),
            P(scope, style="font-size:13px;color:#374151;line-height:1.6;white-space:pre-wrap;"),
            cls="detail-section",
        ))

    # Requirements
    requirements = rfp_sections.get("requirements", "")
    if requirements:
        sections.append(Div(
            Div("Requirements & Deliverables", cls="detail-section-title"),
            P(requirements, style="font-size:13px;color:#374151;line-height:1.6;white-space:pre-wrap;"),
            cls="detail-section",
        ))

    # Evaluation criteria
    criteria = rfp_sections.get("evaluation_criteria", [])
    if criteria:
        crit_items = []
        for c in criteria:
            weight = c.get("weight", 0)
            crit_items.append(Div(
                Div(
                    Span(c.get("name", ""), style="font-size:13px;font-weight:500;color:#374151;"),
                    Span(f"{weight}%", style="font-size:13px;font-weight:600;color:#111827;"),
                    style="display:flex;justify-content:space-between;margin-bottom:4px;",
                ),
                Div(
                    Div(style=f"height:100%;width:{min(weight, 100)}%;background:linear-gradient(90deg,#2563eb,#7c3aed);border-radius:2px;"),
                    style="height:4px;background:#f3f4f6;border-radius:2px;overflow:hidden;margin-bottom:4px;",
                ),
                *(
                    [Div(c.get("description", ""), style="font-size:11px;color:#6b7280;")]
                    if c.get("description") else []
                ),
                style="margin-bottom:10px;",
            ))
        sections.append(Div(
            Div("Evaluation Criteria", cls="detail-section-title"),
            *crit_items,
            cls="detail-section",
        ))

    # Qualification requirements
    quals = rfp_sections.get("qualification_requirements", [])
    if quals:
        qual_items = []
        for q in quals:
            req_type = q.get("type", "eligibility")
            color, bg = PRIORITY_COLORS.get(req_type, ("#6b7280", "#f3f4f6"))
            qual_items.append(Div(
                Div(
                    Span(req_type.upper(), style=f"font-size:9px;font-weight:700;padding:2px 6px;border-radius:10px;color:{color};background:{bg};"),
                    style="margin-bottom:4px;",
                ),
                Div(q.get("requirement", ""), style="font-size:13px;color:#111827;margin-bottom:2px;"),
                *(
                    [Div(f"Evidence: {q.get('evidence', '')}", style="font-size:11px;color:#6b7280;")]
                    if q.get("evidence") else []
                ),
                style="padding:8px;border:1px solid #f3f4f6;border-radius:8px;margin-bottom:6px;",
            ))
        sections.append(Div(
            Div("Qualification Requirements", cls="detail-section-title"),
            *qual_items,
            cls="detail-section",
        ))

    # Contract terms
    terms = rfp_sections.get("contract_terms", "")
    if terms:
        sections.append(Div(
            Div("Contract Terms", cls="detail-section-title"),
            P(terms, style="font-size:13px;color:#374151;line-height:1.6;white-space:pre-wrap;"),
            cls="detail-section",
        ))

    # Timeline
    timeline = rfp_sections.get("timeline", {})
    if timeline:
        tl_items = []
        for key, val in timeline.items():
            label = key.replace("_", " ").title()
            tl_items.append(Div(
                Span(label, style="font-size:12px;color:#6b7280;min-width:120px;"),
                Span(str(val), style="font-size:12px;font-weight:500;color:#374151;"),
                style="display:flex;gap:8px;padding:4px 0;border-bottom:1px solid #f3f4f6;",
            ))
        sections.append(Div(
            Div("Timeline", cls="detail-section-title"),
            *tl_items,
            cls="detail-section",
        ))

    # Compliance notes
    notes = rfp.get("compliance_notes", [])
    if notes:
        note_items = [
            Li(n, style="font-size:12px;color:#6b7280;margin-bottom:4px;")
            for n in notes[:6]
        ]
        sections.append(Div(
            Div("Compliance Notes", cls="detail-section-title"),
            Ul(*note_items, style="padding-left:16px;"),
            cls="detail-section",
        ))

    return Div(*sections, cls="detail-body", style="padding:20px;")


def _badge(text, color, bg):
    if not text:
        return None
    return Span(
        text,
        style=f"font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;color:{color};background:{bg};",
    )
