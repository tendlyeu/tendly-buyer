"""Risk analysis artifact renderer for the canvas panel."""

from fasthtml.common import *


SEVERITY_COLORS = {
    "critical": ("#dc2626", "#fef2f2"),
    "high": ("#ea580c", "#fff7ed"),
    "medium": ("#d97706", "#fffbeb"),
    "low": ("#6b7280", "#f3f4f6"),
}

CATEGORY_ICONS = {
    "timeline": "clock", "financial": "dollar", "legal": "scale",
    "technical": "wrench", "operational": "cog", "compliance": "shield",
}


def risk_analysis_panel(data: dict, language: str = "en"):
    """Render risk analysis as HTML for the canvas."""
    if not data:
        return Div(P("No data available."), cls="detail-body")

    analysis = data.get("analysis") or {}
    tender_name = data.get("tender_name", "")
    sections = []

    # Header with scores
    risk_level = analysis.get("overall_risk_level", "unknown")
    risk_score = analysis.get("risk_score", 0)
    bid_readiness = analysis.get("bid_readiness_score", 0)
    level_color, level_bg = SEVERITY_COLORS.get(risk_level, ("#6b7280", "#f3f4f6"))

    sections.append(Div(
        Div(tender_name, style="font-size:14px;font-weight:600;color:#111827;margin-bottom:12px;"),
        Div(
            _score_circle(risk_score, "Risk Score", _risk_color(risk_score)),
            _score_circle(bid_readiness, "Bid Readiness", _readiness_color(bid_readiness)),
            style="display:flex;gap:20px;margin-bottom:12px;",
        ),
        Span(
            f"Overall: {risk_level.upper()}",
            style=f"font-size:12px;font-weight:700;padding:4px 12px;border-radius:20px;color:{level_color};background:{level_bg};",
        ),
        cls="detail-section",
    ))

    # Executive summary
    summary = analysis.get("summary", "")
    if summary:
        sections.append(Div(
            Div("Executive Summary", cls="detail-section-title"),
            P(summary, style="font-size:13px;color:#374151;line-height:1.6;"),
            cls="detail-section",
        ))

    # Risk summary counts
    risk_summary = analysis.get("risk_summary", {})
    if risk_summary:
        sections.append(Div(
            Div("Risk Breakdown", cls="detail-section-title"),
            Div(
                _count_badge(risk_summary.get("critical_count", 0), "Critical", "#dc2626", "#fef2f2"),
                _count_badge(risk_summary.get("high_count", 0), "High", "#ea580c", "#fff7ed"),
                _count_badge(risk_summary.get("medium_count", 0), "Medium", "#d97706", "#fffbeb"),
                _count_badge(risk_summary.get("low_count", 0), "Low", "#6b7280", "#f3f4f6"),
                style="display:flex;gap:6px;flex-wrap:wrap;",
            ),
            cls="detail-section",
        ))

    # Individual risks
    risks = analysis.get("risks", [])
    if risks:
        risk_items = []
        for r in risks[:12]:
            severity = r.get("severity", "medium")
            s_color, s_bg = SEVERITY_COLORS.get(severity, ("#6b7280", "#f3f4f6"))
            risk_items.append(Div(
                Div(
                    Span(
                        severity.upper(),
                        style=f"font-size:9px;font-weight:700;padding:2px 6px;border-radius:10px;color:{s_color};background:{s_bg};",
                    ),
                    Span(
                        r.get("category", ""),
                        style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.3px;",
                    ),
                    style="display:flex;align-items:center;gap:6px;margin-bottom:4px;",
                ),
                Div(r.get("title", ""), style="font-size:13px;font-weight:600;color:#111827;margin-bottom:4px;"),
                P(r.get("description", ""), style="font-size:12px;color:#6b7280;line-height:1.5;margin-bottom:4px;"),
                *(
                    [Div(
                        Span("Mitigation: ", style="font-weight:600;color:#374151;"),
                        r.get("mitigation", ""),
                        style="font-size:11px;color:#6b7280;line-height:1.4;padding:6px 8px;background:#f9fafb;border-radius:6px;",
                    )]
                    if r.get("mitigation") else []
                ),
                style=f"padding:12px;border:1px solid #f3f4f6;border-radius:8px;border-left:3px solid {s_color};margin-bottom:8px;",
            ))
        sections.append(Div(
            Div(f"Risks ({len(risks)})", cls="detail-section-title"),
            *risk_items,
            cls="detail-section",
        ))

    # Document inconsistencies
    inconsistencies = analysis.get("document_inconsistencies", [])
    if inconsistencies:
        incon_items = []
        for inc in inconsistencies[:6]:
            s_color, s_bg = SEVERITY_COLORS.get(inc.get("severity", "medium"), ("#d97706", "#fffbeb"))
            incon_items.append(Div(
                Div(
                    Span(inc.get("type", ""), style=f"font-size:9px;font-weight:700;padding:2px 6px;border-radius:10px;color:{s_color};background:{s_bg};text-transform:uppercase;"),
                    style="margin-bottom:4px;",
                ),
                Div(inc.get("title", ""), style="font-size:13px;font-weight:600;color:#111827;margin-bottom:2px;"),
                P(inc.get("description", ""), style="font-size:12px;color:#6b7280;line-height:1.4;margin-bottom:4px;"),
                Div(
                    Span(inc.get("document_a", ""), style="font-size:11px;color:#2563eb;"),
                    Span(" vs ", style="font-size:11px;color:#9ca3af;"),
                    Span(inc.get("document_b", ""), style="font-size:11px;color:#2563eb;"),
                    style="margin-bottom:4px;",
                ),
                style="padding:10px;border:1px solid #f3f4f6;border-radius:8px;margin-bottom:6px;",
            ))
        sections.append(Div(
            Div(f"Document Inconsistencies ({len(inconsistencies)})", cls="detail-section-title"),
            *incon_items,
            cls="detail-section",
        ))

    # Key actions
    actions = analysis.get("key_actions", [])
    if actions:
        action_items = [
            Li(a, style="font-size:13px;color:#374151;margin-bottom:6px;")
            for a in actions[:5]
        ]
        sections.append(Div(
            Div("Key Actions", cls="detail-section-title"),
            Ol(*action_items, style="padding-left:20px;"),
            cls="detail-section",
        ))

    return Div(*sections, cls="detail-body", style="padding:20px;")


def _score_circle(score, label, color):
    pct = min(max(score or 0, 0), 100)
    circumference = 2 * 3.14159 * 20
    offset = circumference * (1 - pct / 100)
    return Div(
        Div(
            NotStr(f"""<svg viewBox="0 0 52 52" style="width:52px;height:52px;transform:rotate(-90deg);">
                <circle cx="26" cy="26" r="20" fill="none" stroke="#f3f4f6" stroke-width="4"/>
                <circle cx="26" cy="26" r="20" fill="none" stroke="{color}" stroke-width="4"
                    stroke-linecap="round" stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"/>
            </svg>"""),
            Div(str(pct), style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#111827;"),
            style="position:relative;width:52px;height:52px;",
        ),
        Div(label, style="font-size:11px;color:#6b7280;text-align:center;margin-top:4px;"),
        style="display:flex;flex-direction:column;align-items:center;",
    )


def _risk_color(score):
    if score >= 70: return "#dc2626"
    if score >= 40: return "#d97706"
    return "#16a34a"


def _readiness_color(score):
    if score >= 70: return "#16a34a"
    if score >= 40: return "#d97706"
    return "#dc2626"


def _count_badge(count, label, color, bg):
    return Div(
        Div(str(count), style=f"font-size:18px;font-weight:700;color:{color};"),
        Div(label, style="font-size:10px;color:#6b7280;"),
        style=f"flex:1;text-align:center;padding:8px 4px;background:{bg};border-radius:8px;border:1px solid #f3f4f6;min-width:60px;",
    )
