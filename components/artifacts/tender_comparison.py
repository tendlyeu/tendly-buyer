"""Tender comparison artifact renderer for the canvas panel."""

from fasthtml.common import *
from core.utils import _raw


CURRENCY_SYMBOLS = {"EUR": "\u20ac", "GBP": "\u00a3", "PLN": "z\u0142"}
COUNTRY_FLAGS = {
    "EE": "\U0001f1ea\U0001f1ea", "GB": "\U0001f1ec\U0001f1e7",
    "LV": "\U0001f1f1\U0001f1fb", "PL": "\U0001f1f5\U0001f1f1",
    "LT": "\U0001f1f1\U0001f1f9", "FR": "\U0001f1eb\U0001f1f7",
}


def tender_comparison_panel(data: dict, language: str = "en"):
    """Render tender comparison as HTML for the canvas."""
    tenders = data.get("tenders") or []
    if len(tenders) < 2:
        return Div(P("Not enough tenders to compare.", cls="detail-field-value"), cls="detail-body")

    # Comparison rows
    rows = []

    # Names
    rows.append(_comparison_row(
        "Tender",
        [Div(t.get("name", ""), style="font-size:13px;font-weight:600;color:#111827;line-height:1.4;") for t in tenders],
        header=True,
    ))

    # Authority
    rows.append(_comparison_row(
        "Authority",
        [t.get("authority", "N/A") for t in tenders],
    ))

    # Country
    rows.append(_comparison_row(
        "Country",
        [f"{COUNTRY_FLAGS.get(t.get('country_code', ''), '')} {t.get('country', '')}" for t in tenders],
    ))

    # Value
    rows.append(_comparison_row(
        "Estimated Value",
        [_format_value(t.get("value"), t.get("currency", "EUR")) for t in tenders],
        highlight_best=True,
        compare_values=[t.get("value") for t in tenders],
    ))

    # Deadline
    rows.append(_comparison_row(
        "Deadline",
        [_format_date(t.get("deadline")) for t in tenders],
    ))

    # CPV
    rows.append(_comparison_row(
        "CPV Code",
        [f"{t.get('cpv_code', '')} {t.get('cpv_name', '')}" for t in tenders],
    ))

    # Quality Score
    quality_scores = [t.get("quality_score") for t in tenders]
    rows.append(_comparison_row(
        "Quality Score",
        [_quality_badge(qs) for t, qs in zip(tenders, quality_scores)],
        highlight_best=True,
        compare_values=quality_scores,
    ))

    # Duration
    rows.append(_comparison_row(
        "Duration",
        [f"{t.get('duration_months', 'N/A')} months" if t.get("duration_months") else "N/A" for t in tenders],
    ))

    # Badges (green, EU)
    rows.append(_comparison_row(
        "Attributes",
        [_tender_badges(t) for t in tenders],
    ))

    # Documents count
    rows.append(_comparison_row(
        "Documents",
        [f"{len(t.get('documents', []))} documents" for t in tenders],
    ))

    # Evaluation criteria
    criteria_rows = _build_criteria_comparison(tenders)
    if criteria_rows:
        rows.extend(criteria_rows)

    # Result (if available)
    result_rows = _build_result_comparison(tenders)
    if result_rows:
        rows.extend(result_rows)

    return Div(
        Div(*rows),
        cls="detail-body",
        style="padding:12px;",
    )


def _comparison_row(label, values, header=False, highlight_best=False, compare_values=None):
    """Render a comparison row with label and value cells."""
    label_style = "font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;padding:10px 12px;background:#f9fafb;border-bottom:1px solid #f3f4f6;"
    if header:
        label_style += "border-top:none;"

    # Find best value for highlighting
    best_idx = None
    if highlight_best and compare_values:
        valid = [(i, v) for i, v in enumerate(compare_values) if v is not None]
        if valid:
            best_idx = max(valid, key=lambda x: x[1])[0]

    cells = []
    for i, val in enumerate(values):
        cell_style = "padding:10px 12px;border-bottom:1px solid #f3f4f6;font-size:13px;color:#374151;"
        if i < len(values) - 1:
            cell_style += "border-right:1px solid #f3f4f6;"
        if highlight_best and i == best_idx:
            cell_style += "background:#f0fdf4;"

        if isinstance(val, str):
            cells.append(Div(val, style=cell_style))
        else:
            cells.append(Div(val, style=cell_style))

    col_count = len(values)
    grid_cols = " ".join(["1fr"] * col_count)

    return Div(
        Div(label, style=label_style),
        Div(*cells, style=f"display:grid;grid-template-columns:{grid_cols};"),
    )


def _format_value(val, currency="EUR"):
    if val is None:
        return "Not specified"
    sym = CURRENCY_SYMBOLS.get(currency, currency)
    return f"{sym}{val:,.0f}"


def _format_date(deadline):
    if not deadline:
        return "N/A"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        days = (dt.replace(tzinfo=None) - datetime.utcnow()).days
        date_str = dt.strftime("%d %b %Y")
        if days > 0:
            return f"{date_str} ({days}d left)"
        return f"{date_str} (expired)"
    except Exception:
        return deadline[:10]


def _quality_badge(score):
    if score is None:
        return Span("N/A", style="font-size:12px;color:#9ca3af;")
    score = round(score)
    if score >= 70:
        color, bg = "#16a34a", "#f0fdf4"
    elif score >= 50:
        color, bg = "#d97706", "#fffbeb"
    else:
        color, bg = "#9ca3af", "#f3f4f6"
    return Span(
        f"{score}/100",
        style=f"font-size:12px;font-weight:600;padding:2px 8px;border-radius:20px;color:{color};background:{bg};",
    )


def _tender_badges(t):
    badges = []
    if t.get("is_green"):
        badges.append(Span("Green", cls="detail-badge detail-badge-green", style="font-size:10px;margin-right:4px;"))
    if t.get("is_eu_funded"):
        badges.append(Span("EU Funded", cls="detail-badge detail-badge-eu", style="font-size:10px;margin-right:4px;"))
    return Div(*badges) if badges else Span("—", style="color:#9ca3af;")


def _build_criteria_comparison(tenders):
    """Build evaluation criteria comparison rows."""
    # Collect all unique criteria names
    all_criteria = {}
    for t in tenders:
        for c in t.get("evaluation_criteria", []):
            name = c.get("name", "")
            if name and name not in all_criteria:
                all_criteria[name] = c.get("type", "")

    if not all_criteria:
        return []

    rows = [
        _comparison_row("Evaluation Criteria", ["" for _ in tenders], header=True),
    ]

    for crit_name, crit_type in list(all_criteria.items())[:6]:
        weights = []
        for t in tenders:
            w = None
            for c in t.get("evaluation_criteria", []):
                if c.get("name") == crit_name:
                    w = c.get("weight")
                    break
            if w is not None:
                weights.append(Div(
                    Div(
                        Div(style=f"height:100%;width:{min(w, 100)}%;background:linear-gradient(90deg,#2563eb,#7c3aed);border-radius:2px;"),
                        style="height:4px;background:#f3f4f6;border-radius:2px;overflow:hidden;margin-bottom:2px;",
                    ),
                    Span(f"{w}%", style="font-size:11px;font-weight:600;color:#374151;"),
                ))
            else:
                weights.append("—")
        rows.append(_comparison_row(crit_name, weights))

    return rows


def _build_result_comparison(tenders):
    """Build result/winner comparison rows."""
    has_results = any(t.get("result") for t in tenders)
    if not has_results:
        return []

    rows = [
        _comparison_row("Results", ["" for _ in tenders], header=True),
    ]

    rows.append(_comparison_row(
        "Winner",
        [t.get("result", {}).get("winner", "N/A") if t.get("result") else "Pending" for t in tenders],
    ))
    rows.append(_comparison_row(
        "Contract Value",
        [
            _format_value(t["result"].get("contract_cost"), t.get("currency", "EUR"))
            if t.get("result") and t["result"].get("contract_cost") else "N/A"
            for t in tenders
        ],
    ))
    rows.append(_comparison_row(
        "Offers",
        [
            f"{t['result'].get('offer_count', 'N/A')} offers"
            if t.get("result") and t["result"].get("offer_count") else "N/A"
            for t in tenders
        ],
    ))

    return rows
