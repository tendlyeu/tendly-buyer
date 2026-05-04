"""Canvas artifact for the 'create_plan' chat tool.

Renders confirmation that a new procurement plan was persisted, with a
prominent link to open it and a quick recap of the seeded fields."""

from fasthtml.common import Div, P, A, H2, H3, Span, Strong
from config.i18n import t
from core.utils import _raw


def create_plan_panel(data: dict, language: str = "en") -> Div:
    plan_id = data.get("plan_id", "")
    plan_url = data.get("plan_url") or f"/procurements/{plan_id}"
    title = data.get("title") or t("procurements.new_title", language)
    category = data.get("category") or "—"
    estimated = data.get("estimated_value")
    cpv = data.get("cpv_code") or "—"
    criteria = data.get("evaluation_criteria") or []
    requirements = data.get("requirements") or []

    value_str = "—"
    if isinstance(estimated, (int, float)) and estimated:
        value_str = f"€{estimated:,.0f}"

    crit_rows = [
        Div(
            Span(c.get("name", ""), style="font-size:13px;font-weight:500;color:#111827;flex:1;min-width:0;"),
            Span(
                f"{c.get('weight','')}%" if c.get("weight") not in (None, "") else "",
                style="font-size:13px;color:#6b7280;width:60px;text-align:right;",
            ),
            Span(c.get("description", ""), style="font-size:12px;color:#6b7280;flex:2;min-width:0;"),
            style="display:flex;align-items:center;gap:12px;padding:6px 0;border-bottom:1px solid #f3f4f6;",
        )
        for c in criteria
    ]

    req_rows = [
        Div(
            Span(r.get("text", ""), style="font-size:13px;color:#111827;flex:1;min-width:0;"),
            Span(
                (r.get("priority") or "should").upper(),
                style=(
                    "font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;"
                    + ("background:#fee2e2;color:#991b1b;" if r.get("priority") == "must"
                       else "background:#fef3c7;color:#92400e;")
                ),
            ),
            style="display:flex;align-items:center;gap:12px;padding:6px 0;border-bottom:1px solid #f3f4f6;",
        )
        for r in requirements
    ]

    return Div(
        # Success header
        Div(
            Div(
                _raw('<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'),
                style="display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;background:#ecfdf5;border-radius:50%;",
            ),
            Div(
                P(t("create_plan.created", language), style="font-size:11px;color:#065f46;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin:0;"),
                H2(title, style="font-size:18px;font-weight:700;color:#111827;margin:2px 0 0;"),
            ),
            style="display:flex;align-items:center;gap:12px;padding:12px 14px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;",
        ),

        # Plan summary
        Div(
            Div(
                Div(t("procurements.field_category", language), style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(category.replace("_", " ").title(), style="font-size:14px;color:#111827;font-weight:500;"),
                style="padding:10px 12px;background:#f9fafb;border-radius:8px;flex:1;min-width:120px;",
            ),
            Div(
                Div(t("procurements.field_estimated_value", language), style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(value_str, style="font-size:14px;color:#111827;font-weight:500;"),
                style="padding:10px 12px;background:#f9fafb;border-radius:8px;flex:1;min-width:120px;",
            ),
            Div(
                Div("CPV", style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(cpv, style="font-size:14px;color:#111827;font-weight:500;"),
                style="padding:10px 12px;background:#f9fafb;border-radius:8px;flex:1;min-width:120px;",
            ),
            style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px;",
        ),

        # Criteria block
        (Div(
            H3(t("procurements.evaluation_criteria", language), style="font-size:14px;font-weight:600;color:#111827;margin:0 0 8px;"),
            *crit_rows,
            style="margin-top:14px;",
        ) if crit_rows else Div()),

        # Requirements block
        (Div(
            H3(t("procurements.requirements", language), style="font-size:14px;font-weight:600;color:#111827;margin:0 0 8px;"),
            *req_rows,
            style="margin-top:14px;",
        ) if req_rows else Div()),

        # CTA
        Div(
            A(
                _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><polyline points="12 5 19 12 12 19"/></svg>'),
                Span(" ", style="display:inline-block;width:6px;"),
                t("create_plan.open_plan", language),
                href=plan_url,
                style="display:inline-flex;align-items:center;gap:6px;background:linear-gradient(135deg,#2563eb,#7c3aed);color:white;padding:10px 18px;border-radius:8px;font-size:14px;font-weight:600;text-decoration:none;",
            ),
            style="margin-top:18px;text-align:right;",
        ),

        cls="detail-body",
        style="padding:14px;",
    )
