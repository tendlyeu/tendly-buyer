"""Winning strategy artifact renderer for the canvas panel."""

from fasthtml.common import *


PRIORITY_COLORS = {
    "critical": ("#dc2626", "#fef2f2"),
    "high": ("#ea580c", "#fff7ed"),
    "medium": ("#d97706", "#fffbeb"),
    "low": ("#6b7280", "#f3f4f6"),
}

EFFORT_LABELS = {"low": "Low effort", "medium": "Medium effort", "high": "High effort"}


def winning_strategy_panel(data: dict, language: str = "en"):
    """Render winning strategy as HTML for the canvas."""
    if not data:
        return Div(P("No data available."), cls="detail-body")

    strategy = data.get("strategy") or {}
    tender_name = data.get("tender_name", "")
    sections = []

    # Header with win probability
    win_prob = strategy.get("win_probability", 50)
    readiness = strategy.get("overall_readiness", "moderate_competition")
    readiness_labels = {
        "high_competition": ("High Competition", "#dc2626"),
        "moderate_competition": ("Moderate Competition", "#d97706"),
        "low_competition": ("Low Competition", "#16a34a"),
    }
    r_label, r_color = readiness_labels.get(readiness, ("Unknown", "#6b7280"))

    sections.append(Div(
        Div(tender_name, style="font-size:14px;font-weight:600;color:#111827;margin-bottom:12px;"),
        Div(
            _probability_gauge(win_prob),
            Div(
                Span(
                    r_label,
                    style=f"font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;color:{r_color};background:{r_color}15;",
                ),
                *(
                    [Span(
                        "Cached",
                        style="font-size:10px;padding:2px 8px;border-radius:10px;color:#6b7280;background:#f3f4f6;",
                    )]
                    if data.get("cached") else []
                ),
                style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;",
            ),
            style="flex:1;",
        ),
        style="display:flex;gap:16px;align-items:flex-start;",
        cls="detail-section",
    ))

    # Executive summary
    exec_summary = strategy.get("executive_summary", "")
    if exec_summary:
        sections.append(Div(
            Div("Executive Summary", cls="detail-section-title"),
            P(exec_summary, style="font-size:13px;color:#374151;line-height:1.6;"),
            cls="detail-section",
        ))

    # Key opportunities
    opportunities = strategy.get("key_opportunities", [])
    if opportunities:
        opp_items = []
        for o in opportunities[:5]:
            opp_text = o.get("opportunity", o) if isinstance(o, dict) else str(o)
            evidence = o.get("evidence", "") if isinstance(o, dict) else ""
            opp_items.append(Div(
                Div(
                    Span(style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#16a34a;margin-top:5px;flex-shrink:0;"),
                    Div(
                        Div(opp_text, style="font-size:13px;color:#111827;font-weight:500;"),
                        *(
                            [Div(evidence, style="font-size:11px;color:#6b7280;margin-top:2px;")]
                            if evidence else []
                        ),
                    ),
                    style="display:flex;gap:8px;align-items:flex-start;",
                ),
                style="padding:6px 0;border-bottom:1px solid #f3f4f6;",
            ))
        sections.append(Div(
            Div("Key Opportunities", cls="detail-section-title"),
            *opp_items,
            cls="detail-section",
        ))

    # Key challenges
    challenges = strategy.get("key_challenges", [])
    if challenges:
        ch_items = []
        for c in challenges[:5]:
            ch_text = c.get("challenge", c) if isinstance(c, dict) else str(c)
            mitigation = c.get("mitigation", "") if isinstance(c, dict) else ""
            ch_items.append(Div(
                Div(
                    Span(style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#d97706;margin-top:5px;flex-shrink:0;"),
                    Div(
                        Div(ch_text, style="font-size:13px;color:#111827;font-weight:500;"),
                        *(
                            [Div(f"Mitigation: {mitigation}", style="font-size:11px;color:#6b7280;margin-top:2px;")]
                            if mitigation else []
                        ),
                    ),
                    style="display:flex;gap:8px;align-items:flex-start;",
                ),
                style="padding:6px 0;border-bottom:1px solid #f3f4f6;",
            ))
        sections.append(Div(
            Div("Key Challenges", cls="detail-section-title"),
            *ch_items,
            cls="detail-section",
        ))

    # Bid focus areas
    focus_areas = strategy.get("bid_focus_areas", [])
    if focus_areas:
        fa_items = []
        for fa in focus_areas[:5]:
            area = fa.get("area", fa) if isinstance(fa, dict) else str(fa)
            weight = fa.get("weight", "") if isinstance(fa, dict) else ""
            strat = fa.get("strategy", "") if isinstance(fa, dict) else ""
            weight_colors = {"high": "#dc2626", "medium": "#d97706", "low": "#6b7280"}
            w_color = weight_colors.get(weight, "#6b7280")
            fa_items.append(Div(
                Div(
                    Div(area, style="font-size:13px;font-weight:600;color:#111827;"),
                    *(
                        [Span(weight, style=f"font-size:9px;font-weight:700;padding:2px 6px;border-radius:10px;color:{w_color};background:{w_color}15;text-transform:uppercase;")]
                        if weight else []
                    ),
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;",
                ),
                *(
                    [P(strat, style="font-size:12px;color:#6b7280;line-height:1.4;")]
                    if strat else []
                ),
                style="padding:10px;border:1px solid #f3f4f6;border-radius:8px;margin-bottom:6px;",
            ))
        sections.append(Div(
            Div("Bid Focus Areas", cls="detail-section-title"),
            *fa_items,
            cls="detail-section",
        ))

    # Recommendations
    recs = strategy.get("recommendations", [])
    if recs:
        rec_items = []
        for r in recs[:8]:
            priority = r.get("priority", "medium")
            p_color, p_bg = PRIORITY_COLORS.get(priority, ("#6b7280", "#f3f4f6"))
            effort = r.get("effort", "")
            rec_items.append(Div(
                Div(
                    Span(priority.upper(), style=f"font-size:9px;font-weight:700;padding:2px 6px;border-radius:10px;color:{p_color};background:{p_bg};"),
                    *(
                        [Span(EFFORT_LABELS.get(effort, effort), style="font-size:10px;color:#9ca3af;")]
                        if effort else []
                    ),
                    style="display:flex;align-items:center;gap:6px;margin-bottom:4px;",
                ),
                Div(r.get("title", ""), style="font-size:13px;font-weight:600;color:#111827;margin-bottom:2px;"),
                P(r.get("description", ""), style="font-size:12px;color:#6b7280;line-height:1.4;"),
                style=f"padding:10px;border:1px solid #f3f4f6;border-radius:8px;border-left:3px solid {p_color};margin-bottom:6px;",
            ))
        sections.append(Div(
            Div(f"Recommendations ({len(recs)})", cls="detail-section-title"),
            *rec_items,
            cls="detail-section",
        ))

    return Div(*sections, cls="detail-body", style="padding:20px;")


def _probability_gauge(prob):
    """Render a win probability gauge."""
    if prob >= 70:
        color = "#16a34a"
    elif prob >= 40:
        color = "#d97706"
    else:
        color = "#dc2626"

    circumference = 2 * 3.14159 * 20
    offset = circumference * (1 - prob / 100)

    return Div(
        Div(
            NotStr(f"""<svg viewBox="0 0 52 52" style="width:56px;height:56px;transform:rotate(-90deg);">
                <circle cx="26" cy="26" r="20" fill="none" stroke="#f3f4f6" stroke-width="4"/>
                <circle cx="26" cy="26" r="20" fill="none" stroke="{color}" stroke-width="4"
                    stroke-linecap="round" stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"/>
            </svg>"""),
            Div(f"{prob}%", style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#111827;"),
            style="position:relative;width:56px;height:56px;",
        ),
        Div("Win Probability", style="font-size:10px;color:#6b7280;text-align:center;margin-top:4px;"),
        style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;",
    )
