"""Gap analysis artifact renderer for the canvas panel."""

from fasthtml.common import *


SEVERITY_COLORS = {
    "critical": ("#dc2626", "#fef2f2"),
    "high": ("#ea580c", "#fff7ed"),
    "medium": ("#d97706", "#fffbeb"),
    "low": ("#6b7280", "#f3f4f6"),
}

COVERAGE_COLORS = {
    "complete": ("#16a34a", "#f0fdf4"),
    "partial": ("#d97706", "#fffbeb"),
    "poor": ("#dc2626", "#fef2f2"),
}


def gap_analysis_panel(data: dict, language: str = "en"):
    """Render gap analysis as HTML for the canvas."""
    if not data:
        return Div(P("No data available."), cls="detail-body")

    analysis = data.get("analysis") or {}
    tender_name = data.get("tender_name", "")
    sections = []

    # Header
    risk_level = analysis.get("risk_level", "unknown")
    total_gaps = analysis.get("total_discrepancies", 0)
    level_color, level_bg = SEVERITY_COLORS.get(risk_level, ("#6b7280", "#f3f4f6"))

    sections.append(Div(
        Div(tender_name, style="font-size:14px;font-weight:600;color:#111827;margin-bottom:8px;"),
        Div(
            Span(f"Risk: {risk_level.upper()}", style=f"font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;color:{level_color};background:{level_bg};"),
            Span(f"{total_gaps} discrepancies", style="font-size:12px;color:#6b7280;font-weight:500;"),
            style="display:flex;align-items:center;gap:8px;",
        ),
        cls="detail-section",
    ))

    # Summary
    summary = analysis.get("summary", "")
    if summary:
        sections.append(Div(
            Div("Summary", cls="detail-section-title"),
            P(summary, style="font-size:13px;color:#374151;line-height:1.6;"),
            cls="detail-section",
        ))

    # Document coverage
    coverage = analysis.get("document_coverage", [])
    if coverage:
        cov_items = []
        for c in coverage[:8]:
            status = c.get("status", "partial")
            score = c.get("coverage_score", 0)
            c_color, c_bg = COVERAGE_COLORS.get(status, ("#6b7280", "#f3f4f6"))
            cov_items.append(Div(
                Div(
                    Div(c.get("document_name", ""), style="font-size:13px;font-weight:500;color:#374151;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"),
                    Span(f"{score}%", style=f"font-size:12px;font-weight:600;color:{c_color};flex-shrink:0;"),
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;",
                ),
                Div(
                    Div(style=f"height:100%;width:{min(score, 100)}%;background:{c_color};border-radius:2px;"),
                    style="height:4px;background:#f3f4f6;border-radius:2px;overflow:hidden;margin-bottom:4px;",
                ),
                *(
                    [Div(c.get("notes", ""), style="font-size:11px;color:#9ca3af;")]
                    if c.get("notes") else []
                ),
                style="padding:8px 0;border-bottom:1px solid #f3f4f6;",
            ))
        sections.append(Div(
            Div("Document Coverage", cls="detail-section-title"),
            *cov_items,
            cls="detail-section",
        ))

    # Discrepancies
    discrepancies = analysis.get("discrepancies", [])
    if discrepancies:
        disc_items = []
        for d in discrepancies[:10]:
            severity = d.get("severity", "medium")
            disc_type = d.get("type", "")
            s_color, s_bg = SEVERITY_COLORS.get(severity, ("#6b7280", "#f3f4f6"))
            disc_items.append(Div(
                Div(
                    Span(severity.upper(), style=f"font-size:9px;font-weight:700;padding:2px 6px;border-radius:10px;color:{s_color};background:{s_bg};"),
                    Span(disc_type.replace("_", " "), style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.3px;"),
                    style="display:flex;align-items:center;gap:6px;margin-bottom:4px;",
                ),
                Div(d.get("title", ""), style="font-size:13px;font-weight:600;color:#111827;margin-bottom:2px;"),
                P(d.get("description", ""), style="font-size:12px;color:#6b7280;line-height:1.4;margin-bottom:4px;"),
                *(
                    [Div(
                        Span("Recommendation: ", style="font-weight:600;color:#374151;"),
                        d.get("recommendation", ""),
                        style="font-size:11px;color:#6b7280;line-height:1.4;padding:6px 8px;background:#f9fafb;border-radius:6px;",
                    )]
                    if d.get("recommendation") else []
                ),
                style=f"padding:10px;border:1px solid #f3f4f6;border-radius:8px;border-left:3px solid {s_color};margin-bottom:6px;",
            ))
        sections.append(Div(
            Div(f"Discrepancies ({len(discrepancies)})", cls="detail-section-title"),
            *disc_items,
            cls="detail-section",
        ))

    return Div(*sections, cls="detail-body", style="padding:20px;")
