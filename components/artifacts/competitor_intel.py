"""Competitor intelligence artifact renderer for the canvas panel."""

from fasthtml.common import *
from core.utils import _raw


def competitor_intel_panel(data: dict, language: str = "en"):
    """Render competitor intelligence analysis as HTML for the canvas."""
    if not data:
        return Div(P("No data available.", cls="detail-field-value"), cls="detail-body")

    company = data.get("company") or {}
    total_wins = data.get("total_wins", 0)
    total_value = data.get("total_value", 0)
    insights = data.get("insights") or {}

    sections = []

    # Company header
    sections.append(
        Div(
            Div(company.get("name", "Unknown"), cls="detail-field-value", style="font-size:18px;font-weight:700;"),
            Div(
                _stat_badge(f"{total_wins} wins", "#2563eb", "#eff6ff"),
                _stat_badge(_format_value(total_value), "#16a34a", "#f0fdf4"),
                *(
                    [_stat_badge(f"Reg: {company['reg_code']}", "#6b7280", "#f3f4f6")]
                    if company.get("reg_code") else []
                ),
                style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;",
            ),
            cls="detail-section",
        )
    )

    # Pricing strategy
    pricing = insights.get("pricing_strategy", {})
    if pricing.get("has_data"):
        tendency = pricing.get("pricing_vs_estimate", {}).get("tendency", "unknown")
        tendency_labels = {
            "aggressive_underbidding": ("Aggressive Underbidder", "#dc2626"),
            "competitive": ("Competitive Pricer", "#d97706"),
            "market_rate": ("Market Rate", "#16a34a"),
            "premium": ("Premium Pricer", "#7c3aed"),
            "unknown": ("Unknown", "#6b7280"),
        }
        label, color = tendency_labels.get(tendency, ("Unknown", "#6b7280"))

        brackets = pricing.get("brackets", {})
        sections.append(
            Div(
                Div("Pricing Strategy", cls="detail-section-title"),
                Div(
                    _stat_badge(label, color, f"{color}15"),
                    style="margin-bottom:10px;",
                ),
                _field("Avg Contract Value", _format_value(pricing.get("avg_contract_value"))),
                _field("Median", _format_value(pricing.get("median_contract_value"))),
                _field("Range", f"{_format_value(pricing.get('min_value'))} — {_format_value(pricing.get('max_value'))}"),
                Div(
                    Div(
                        _bracket_bar("< 50K", brackets.get("small", 0), "#93c5fd"),
                        _bracket_bar("50K-500K", brackets.get("medium", 0), "#7c3aed"),
                        _bracket_bar("> 500K", brackets.get("large", 0), "#2563eb"),
                        style="display:flex;gap:6px;",
                    ),
                    style="margin-top:10px;",
                ),
                cls="detail-section",
            )
        )

    # Sector focus
    sector = insights.get("sector_focus", {})
    if sector.get("has_data"):
        top_sectors = sector.get("top_sectors", [])[:5]
        sector_items = []
        for s in top_sectors:
            pct = round(s["count"] / total_wins * 100) if total_wins > 0 else 0
            sector_items.append(
                Div(
                    Div(
                        Span(s.get("name", s.get("code", "")), style="font-size:13px;font-weight:500;color:#374151;"),
                        Span(f"{s['count']} wins", style="font-size:12px;color:#6b7280;"),
                        style="display:flex;justify-content:space-between;margin-bottom:4px;",
                    ),
                    Div(
                        Div(style=f"height:100%;width:{pct}%;background:linear-gradient(90deg,#2563eb,#7c3aed);border-radius:2px;"),
                        style="height:4px;background:#f3f4f6;border-radius:2px;overflow:hidden;",
                    ),
                    style="margin-bottom:10px;",
                )
            )
        specialization = "Specialist" if sector.get("is_specialized") else "Diversified"
        sections.append(
            Div(
                Div("Sector Focus", cls="detail-section-title"),
                _stat_badge(
                    f"{specialization} ({sector.get('sector_concentration', 0)}% top sector)",
                    "#7c3aed" if sector.get("is_specialized") else "#2563eb",
                    "#f5f3ff" if sector.get("is_specialized") else "#eff6ff",
                ),
                Div(*sector_items, style="margin-top:12px;"),
                cls="detail-section",
            )
        )

    # Buyer relationships
    buyers = insights.get("buyer_relationships", {})
    if buyers.get("has_data"):
        repeat = buyers.get("repeat_buyers", [])[:5]
        buyer_items = []
        for b in repeat:
            buyer_items.append(
                Div(
                    Div(b["authority_name"], style="font-size:13px;font-weight:500;color:#374151;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"),
                    Div(
                        Span(f"{b['win_count']} wins", style="font-size:11px;color:#2563eb;font-weight:600;"),
                        Span(f" · {_format_value(b['total_value'])}", style="font-size:11px;color:#6b7280;"),
                    ),
                    style="padding:8px 0;border-bottom:1px solid #f3f4f6;",
                )
            )
        sections.append(
            Div(
                Div("Buyer Relationships", cls="detail-section-title"),
                _field("Unique Buyers", str(buyers.get("total_unique_buyers", 0))),
                _field("Repeat Win %", f"{buyers.get('repeat_win_percentage', 0)}%"),
                *(buyer_items if buyer_items else [Div("No repeat buyers found", style="font-size:13px;color:#9ca3af;")]),
                cls="detail-section",
            )
        )

    # Competition levels
    competition = insights.get("competition_analysis", {})
    if competition.get("has_data"):
        sections.append(
            Div(
                Div("Competition Landscape", cls="detail-section-title"),
                _field("Avg Bidders", str(competition.get("avg_bidders", 0))),
                _field("Range", f"{competition.get('min_bidders', 0)} — {competition.get('max_bidders', 0)} bidders"),
                Div(
                    _pct_bar("Low competition (1-2)", competition.get("low_competition_pct", 0), "#16a34a"),
                    _pct_bar("High competition (5+)", competition.get("high_competition_pct", 0), "#dc2626"),
                    style="margin-top:8px;",
                ),
                cls="detail-section",
            )
        )

    # Timing patterns
    timing = insights.get("timing_patterns", {})
    if timing.get("has_data"):
        trend_colors = {"growing": "#16a34a", "declining": "#dc2626", "stable": "#6b7280"}
        trend = timing.get("trend", "stable")
        sections.append(
            Div(
                Div("Timing Patterns", cls="detail-section-title"),
                _field("Peak Quarter", timing.get("peak_quarter", "Unknown")),
                Div(
                    _stat_badge(f"Trend: {trend.capitalize()}", trend_colors.get(trend, "#6b7280"), "#f9fafb"),
                    style="margin-bottom:8px;",
                ),
                _quarterly_chart(timing.get("quarterly_distribution", {})),
                cls="detail-section",
            )
        )

    return Div(*sections, cls="detail-body", style="padding:20px;")


# --- Helpers ---

def _field(label, value):
    return Div(
        Div(label, cls="detail-field-label"),
        Div(str(value), cls="detail-field-value"),
        cls="detail-field",
    )


def _format_value(val):
    if val is None:
        return "N/A"
    if isinstance(val, (int, float)):
        if val >= 1_000_000:
            return f"\u20ac{val / 1_000_000:,.1f}M"
        if val >= 1_000:
            return f"\u20ac{val / 1_000:,.0f}K"
        return f"\u20ac{val:,.0f}"
    return str(val)


def _stat_badge(text, color, bg_color=None):
    bg = bg_color or f"{color}20"
    return Span(
        text,
        style=f"display:inline-block;font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;color:{color};background:{bg};",
    )


def _bracket_bar(label, count, color):
    return Div(
        Div(str(count), style=f"font-size:16px;font-weight:700;color:{color};"),
        Div(label, style="font-size:10px;color:#6b7280;"),
        style=f"flex:1;text-align:center;padding:8px 4px;background:#f9fafb;border-radius:8px;border:1px solid #f3f4f6;",
    )


def _pct_bar(label, pct, color):
    return Div(
        Div(
            Span(label, style="font-size:12px;color:#6b7280;"),
            Span(f"{pct}%", style=f"font-size:12px;font-weight:600;color:{color};"),
            style="display:flex;justify-content:space-between;margin-bottom:4px;",
        ),
        Div(
            Div(style=f"height:100%;width:{min(pct, 100)}%;background:{color};border-radius:2px;"),
            style="height:4px;background:#f3f4f6;border-radius:2px;overflow:hidden;",
        ),
        style="margin-bottom:8px;",
    )


def _quarterly_chart(quarters):
    max_val = max(quarters.values()) if quarters else 1
    bars = []
    for q in range(1, 5):
        count = quarters.get(q, 0)
        h = round(count / max_val * 40) if max_val > 0 else 0
        bars.append(
            Div(
                Div(style=f"width:100%;height:{h}px;background:linear-gradient(180deg,#2563eb,#7c3aed);border-radius:3px 3px 0 0;"),
                Div(f"Q{q}", style="font-size:10px;color:#6b7280;text-align:center;margin-top:4px;"),
                Div(str(count), style="font-size:11px;font-weight:600;color:#374151;text-align:center;"),
                style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;",
            )
        )
    return Div(
        *bars,
        style="display:flex;gap:8px;align-items:flex-end;height:80px;margin-top:8px;",
    )
