"""Price benchmark artifact renderer for the canvas panel."""

from fasthtml.common import *


def price_benchmark_panel(data: dict, language: str = "en"):
    """Render price benchmark analysis as HTML for the canvas."""
    if not data:
        return Div(P("No data available."), cls="detail-body")

    stats = data.get("stats", {})
    contracts = data.get("contracts", [])
    awards = data.get("awards", [])
    search = data.get("search_params", {})
    sections = []

    # Search context
    search_desc = " ".join(search.get("keywords", [])) or search.get("main_category", "") or "All categories"
    sections.append(Div(
        Div(f"Price Benchmarks: {search_desc}", style="font-size:16px;font-weight:700;color:#111827;margin-bottom:8px;"),
        Div(f"Based on {stats.get('count', 0)} UK public sector contracts", style="font-size:12px;color:#6b7280;"),
        cls="detail-section",
    ))

    # Stats overview
    if stats:
        sections.append(Div(
            Div("Price Distribution", cls="detail-section-title"),
            Div(
                _stat_card("Average", stats.get("avg"), "#2563eb"),
                _stat_card("Median", stats.get("median"), "#7c3aed"),
                _stat_card("Min", stats.get("min"), "#16a34a"),
                _stat_card("Max", stats.get("max"), "#dc2626"),
                style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;",
            ),
            # Percentile range
            Div(
                Div(
                    Span("25th %ile", style="font-size:10px;color:#6b7280;"),
                    Span(f"£{stats.get('p25', 0):,.0f}", style="font-size:12px;font-weight:600;color:#374151;"),
                    style="display:flex;justify-content:space-between;",
                ),
                Div(
                    Span("75th %ile", style="font-size:10px;color:#6b7280;"),
                    Span(f"£{stats.get('p75', 0):,.0f}", style="font-size:12px;font-weight:600;color:#374151;"),
                    style="display:flex;justify-content:space-between;",
                ),
                style="padding:8px 12px;background:#f9fafb;border-radius:8px;border:1px solid #f3f4f6;",
            ),
            cls="detail-section",
        ))

    # Top awarded contracts
    if awards:
        award_items = []
        for a in awards[:10]:
            val_str = f"£{a['value']:,.0f}" if a.get("value") else "N/A"
            award_items.append(Div(
                Div(a.get("supplier", "Unknown"), style="font-size:13px;font-weight:500;color:#111827;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"),
                Div(val_str, style="font-size:12px;font-weight:600;color:#16a34a;"),
                style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #f3f4f6;",
            ))
        sections.append(Div(
            Div("Recent Awards", cls="detail-section-title"),
            *award_items,
            cls="detail-section",
        ))

    # Comparable contracts list
    if contracts:
        contract_items = []
        for c in contracts[:15]:
            val_str = f"£{c['value']:,.0f}" if c.get("value") else "N/A"
            contract_items.append(Div(
                Div(
                    Div(c.get("title", "")[:80], style="font-size:12px;font-weight:500;color:#111827;line-height:1.3;"),
                    Div(c.get("buyer", ""), style="font-size:11px;color:#6b7280;margin-top:2px;"),
                    style="flex:1;min-width:0;",
                ),
                Div(
                    Div(val_str, style="font-size:12px;font-weight:600;color:#374151;text-align:right;"),
                    Div(c.get("cpv_description", "")[:30], style="font-size:10px;color:#9ca3af;text-align:right;"),
                    style="flex-shrink:0;",
                ),
                style="display:flex;gap:8px;padding:8px 0;border-bottom:1px solid #f3f4f6;",
            ))
        sections.append(Div(
            Div(f"Comparable Contracts ({len(contracts)})", cls="detail-section-title"),
            *contract_items,
            cls="detail-section",
        ))

    return Div(*sections, cls="detail-body", style="padding:20px;")


def _stat_card(label, value, color):
    val_str = f"£{value:,.0f}" if value else "N/A"
    return Div(
        Div(val_str, style=f"font-size:16px;font-weight:700;color:{color};"),
        Div(label, style="font-size:10px;color:#6b7280;font-weight:500;"),
        style=f"padding:10px;background:#f9fafb;border-radius:8px;border:1px solid #f3f4f6;text-align:center;",
    )
