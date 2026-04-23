"""Procurement plan list and form components."""

from fasthtml.common import *
from core.utils import _raw
from config.i18n import t
from components.dashboard.overview import procurement_card


PROCUREMENT_CATEGORIES = [
    ("it", "IT & Technology"),
    ("kinnisvara", "Real Estate / Kinnisvara"),
    ("personal", "Personnel / Personal"),
    ("toitlustus", "Catering / Toitlustus"),
    ("ehitus", "Construction / Ehitus"),
    ("transport", "Transport"),
    ("meditsiiniline", "Medical / Meditsiiniline"),
    ("haridus", "Education / Haridus"),
    ("muu", "Other / Muu"),
]

WORKFLOW_STEPS = [
    (1, "domain_review", "Vajaduse ülevaade", "domain_lead"),
    (2, "market_research", "Turu-uuring", "domain_lead"),
    (3, "plan_review", "Hankeplaani ülevaade", "procurement_manager"),
    (4, "board_approval", "Eelarve kinnitamine", "board"),
    (5, "document_preparation", "Dokumentide koostamine", "domain_specialist"),
]


def procurement_list_page(plans=None, language="en"):
    plans = plans or []

    filter_bar = Div(
        Div(
            H1(t("procurements.title", language), style="font-size:22px;font-weight:700;color:#111827;margin:0;"),
            A(
                f"+ {t('procurements.new', language)}",
                href="/procurements/new",
                cls="btn-primary",
            ),
            style="display:flex;align-items:center;justify-content:space-between;",
        ),
        cls="page-header",
    )

    if plans:
        plan_cards = [procurement_card(p) for p in plans]
        content = Div(*plan_cards, cls="plans-list")
    else:
        content = Div(
            _raw('<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'),
            P(t("procurements.empty", language), style="color:#6b7280;font-size:14px;margin:12px 0 4px;"),
            A(
                f"+ {t('procurements.create_first', language)}",
                href="/procurements/new",
                style="color:#2563eb;font-size:14px;font-weight:500;text-decoration:none;",
            ),
            style="text-align:center;padding:48px 0;",
        )

    return Div(filter_bar, content, cls="page-content")


def procurement_new_page(language="en"):
    category_options = [Option(label, value=val) for val, label in PROCUREMENT_CATEGORIES]

    return Div(
        Div(
            H1(t("procurements.new_title", language), style="font-size:22px;font-weight:700;color:#111827;margin:0;"),
            cls="page-header",
        ),
        Form(
            Div(
                Label(t("procurements.field_title", language), fr="title", cls="form-label"),
                Input(name="title", id="title", type="text", placeholder=t("procurements.title_placeholder", language), cls="form-input", required=True),
                cls="form-group",
            ),
            Div(
                Label(t("procurements.field_description", language), fr="description", cls="form-label"),
                Textarea(name="description", id="description", placeholder=t("procurements.description_placeholder", language), cls="form-textarea", rows="4"),
                cls="form-group",
            ),
            Div(
                Div(
                    Label(t("procurements.field_category", language), fr="category", cls="form-label"),
                    Select(*category_options, name="category", id="category", cls="form-select"),
                    cls="form-group",
                ),
                Div(
                    Label(t("procurements.field_estimated_value", language), fr="estimated_value", cls="form-label"),
                    Input(name="estimated_value", id="estimated_value", type="number", step="0.01", placeholder="0.00", cls="form-input"),
                    cls="form-group",
                ),
                cls="form-row",
            ),
            Div(
                Div(
                    Label(t("procurements.field_cpv_code", language), fr="cpv_code", cls="form-label"),
                    Input(name="cpv_code", id="cpv_code", type="text", placeholder="e.g. 72000000", cls="form-input"),
                    cls="form-group",
                ),
                Div(
                    Label(t("procurements.field_fiscal_year", language), fr="fiscal_year", cls="form-label"),
                    Input(name="fiscal_year", id="fiscal_year", type="number", value="2026", cls="form-input"),
                    cls="form-group",
                ),
                cls="form-row",
            ),
            Div(
                Label(t("procurements.field_method", language), fr="procurement_method", cls="form-label"),
                Select(
                    Option("Open procedure / Avatud hange", value="open"),
                    Option("Restricted procedure / Piiratud hange", value="restricted"),
                    Option("Negotiated procedure / Väljakuulutamisega läbirääkimistega hange", value="negotiated"),
                    Option("Framework agreement / Raamleping", value="framework"),
                    Option("Simplified / Lihthange", value="simplified"),
                    name="procurement_method", id="procurement_method", cls="form-select",
                ),
                cls="form-group",
            ),
            Div(
                Button(t("procurements.cancel", language), type="button", cls="btn-secondary", onclick="window.location='/procurements'"),
                Button(t("procurements.create", language), type="submit", cls="btn-primary"),
                cls="form-actions",
            ),
            action="/procurements",
            method="post",
            cls="procurement-form",
        ),
        cls="page-content",
    )


def procurement_detail_page(plan, steps=None, language="en"):
    steps = steps or []
    status = plan.get("status", "draft")
    current_step = plan.get("current_step", 1)

    step_indicators = []
    for i, (num, step_id, step_name_et, role) in enumerate(WORKFLOW_STEPS):
        if num < current_step:
            step_status = "completed"
        elif num == current_step:
            step_status = "in_progress"
        else:
            step_status = "pending"

        step_colors = {
            "completed": ("#10b981", "#ecfdf5", "#065f46"),
            "in_progress": ("#2563eb", "#eff6ff", "#1e40af"),
            "pending": ("#d1d5db", "#f9fafb", "#9ca3af"),
        }
        dot_color, bg_color, text_color = step_colors[step_status]

        step_indicators.append(
            Div(
                Div(
                    Span(
                        "✓" if step_status == "completed" else str(num),
                        style=f"display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;background:{dot_color};color:white;font-size:12px;font-weight:600;",
                    ),
                    style="flex-shrink:0;",
                ),
                Div(
                    Div(step_name_et, style=f"font-size:13px;font-weight:600;color:{text_color};"),
                    Div(role.replace("_", " ").title(), style="font-size:11px;color:#9ca3af;"),
                    style="min-width:0;",
                ),
                style=f"display:flex;align-items:center;gap:10px;padding:10px 14px;background:{bg_color};border-radius:10px;border:1px solid {dot_color}20;cursor:pointer;",
                onclick=f"window.location='/procurements/{plan['id']}/steps/{num}'",
            )
        )

    value_display = f"€{plan['estimated_value']:,.0f}" if plan.get("estimated_value") else "—"

    return Div(
        Div(
            Div(
                A("← " + t("procurements.back", language), href="/procurements", style="font-size:13px;color:#6b7280;text-decoration:none;"),
                style="margin-bottom:8px;",
            ),
            Div(
                H1(plan.get("title", ""), style="font-size:22px;font-weight:700;color:#111827;margin:0;"),
                Div(
                    A(t("procurements.edit", language), href=f"/procurements/{plan['id']}/edit", cls="btn-secondary", style="font-size:13px;padding:6px 14px;"),
                    A(f"💬 {t('procurements.ask_ai', language)}", href=f"/chat?plan={plan['id']}", cls="btn-primary", style="font-size:13px;padding:6px 14px;"),
                    style="display:flex;gap:8px;",
                ),
                style="display:flex;align-items:center;justify-content:space-between;",
            ),
            cls="page-header",
        ),
        # Info cards
        Div(
            Div(
                Div(t("procurements.field_category", language), style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(plan.get("category", "—").replace("_", " ").title(), style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
                cls="info-card",
            ),
            Div(
                Div(t("procurements.field_estimated_value", language), style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(value_display, style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
                cls="info-card",
            ),
            Div(
                Div(t("procurements.status", language), style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(status.capitalize(), style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
                cls="info-card",
            ),
            Div(
                Div(t("procurements.field_method", language), style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(plan.get("procurement_method", "—").replace("_", " ").title(), style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
                cls="info-card",
            ),
            cls="info-grid",
        ),
        # Workflow stepper
        Div(
            H2(t("procurements.workflow", language), style="font-size:16px;font-weight:600;color:#111827;margin:0 0 12px;"),
            Div(*step_indicators, cls="workflow-steps"),
            cls="dashboard-section",
        ),
        cls="page-content",
    )
