"""Dashboard overview components."""

from fasthtml.common import *
from core.utils import _raw
from config.i18n import t


_ICON_PLAN = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'
_ICON_CLOCK = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
_ICON_CHECK = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
_ICON_FOLDER = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>'


def stat_card(icon_svg, label, value, color="#2563eb"):
    return Div(
        Div(
            Div(_raw(icon_svg), cls="stat-icon", style=f"color:{color};"),
            cls="stat-icon-wrap",
        ),
        Div(
            Div(str(value), cls="stat-value"),
            Div(label, cls="stat-label"),
            cls="stat-text",
        ),
        cls="stat-card",
    )


def workflow_step_mini(step_num, step_name, status="pending"):
    status_colors = {
        "completed": ("#10b981", "#ecfdf5"),
        "in_progress": ("#2563eb", "#eff6ff"),
        "pending": ("#9ca3af", "#f9fafb"),
    }
    color, bg = status_colors.get(status, status_colors["pending"])
    return Div(
        Div(
            Span(str(step_num), style=f"display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:{color};color:white;font-size:11px;font-weight:600;"),
            Span(step_name, style="font-size:13px;color:#374151;"),
            style="display:flex;align-items:center;gap:8px;",
        ),
        style=f"padding:8px 12px;background:{bg};border-radius:8px;border:1px solid {color}20;",
    )


def procurement_card(plan):
    status_badge_colors = {
        "draft": "#6b7280",
        "planning": "#2563eb",
        "review": "#f59e0b",
        "approved": "#10b981",
        "published": "#7c3aed",
        "completed": "#059669",
    }
    status = plan.get("status", "draft")
    badge_color = status_badge_colors.get(status, "#6b7280")

    value_display = ""
    if plan.get("estimated_value"):
        value_display = f"€{plan['estimated_value']:,.0f}"

    return A(
        Div(
            Div(
                Span(plan.get("title", "Untitled"), style="font-size:14px;font-weight:600;color:#111827;"),
                Span(
                    status.capitalize(),
                    style=f"font-size:11px;font-weight:600;color:white;background:{badge_color};padding:2px 8px;border-radius:4px;",
                ),
                style="display:flex;align-items:center;justify-content:space-between;gap:8px;",
            ),
            Div(
                Span(plan.get("category", ""), style="font-size:12px;color:#6b7280;"),
                Span(value_display, style="font-size:12px;color:#374151;font-weight:500;") if value_display else "",
                style="display:flex;align-items:center;justify-content:space-between;margin-top:6px;",
            ),
            Div(
                Span(f"Step {plan.get('current_step', 1)}/5", style="font-size:11px;color:#9ca3af;"),
                Div(
                    Div(style=f"width:{plan.get('current_step', 1) * 20}%;height:100%;background:linear-gradient(90deg,#2563eb,#7c3aed);border-radius:4px;transition:width 0.3s;"),
                    style="flex:1;height:4px;background:#f3f4f6;border-radius:4px;",
                ),
                style="display:flex;align-items:center;gap:8px;margin-top:8px;",
            ),
            cls="procurement-card-inner",
        ),
        href=f"/procurements/{plan.get('id', '')}",
        cls="procurement-card",
    )


def dashboard_page_content(plans=None, stats=None, language="en"):
    plans = plans or []
    stats = stats or {"active": 0, "pending_approval": 0, "completed": 0, "documents": 0}

    stats_row = Div(
        stat_card(_ICON_PLAN, t("dashboard.active_plans", language), stats["active"], "#2563eb"),
        stat_card(_ICON_CLOCK, t("dashboard.pending_approval", language), stats["pending_approval"], "#f59e0b"),
        stat_card(_ICON_CHECK, t("dashboard.completed", language), stats["completed"], "#10b981"),
        stat_card(_ICON_FOLDER, t("dashboard.documents", language), stats["documents"], "#7c3aed"),
        cls="stats-grid",
    )

    if plans:
        plan_cards = [procurement_card(p) for p in plans[:5]]
        plans_section = Div(
            Div(
                H2(t("dashboard.recent_plans", language), style="font-size:16px;font-weight:600;color:#111827;margin:0;"),
                A(t("dashboard.view_all", language), href="/procurements", style="font-size:13px;color:#2563eb;text-decoration:none;font-weight:500;"),
                style="display:flex;align-items:center;justify-content:space-between;",
            ),
            Div(*plan_cards, cls="plans-list"),
            cls="dashboard-section",
        )
    else:
        plans_section = Div(
            H2(t("dashboard.recent_plans", language), style="font-size:16px;font-weight:600;color:#111827;margin:0 0 16px;"),
            Div(
                _raw('<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5" stroke-linecap="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'),
                P(t("dashboard.no_plans", language), style="color:#6b7280;font-size:14px;margin:12px 0 4px;"),
                A(
                    f"+ {t('dashboard.create_first', language)}",
                    href="/procurements/new",
                    style="color:#2563eb;font-size:13px;font-weight:500;text-decoration:none;",
                ),
                style="text-align:center;padding:32px 0;",
            ),
            cls="dashboard-section",
        )

    quick_actions = Div(
        H2(t("dashboard.quick_actions", language), style="font-size:16px;font-weight:600;color:#111827;margin:0 0 12px;"),
        Div(
            A(
                _raw(_ICON_PLAN),
                Span(t("dashboard.new_procurement", language)),
                href="/procurements/new",
                cls="quick-action-btn",
            ),
            A(
                _raw('<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>'),
                Span(t("dashboard.ask_ai", language)),
                href="/chat",
                cls="quick-action-btn",
            ),
            A(
                _raw('<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'),
                Span(t("dashboard.browse_registry", language)),
                href="/registry",
                cls="quick-action-btn",
            ),
            cls="quick-actions-grid",
        ),
        cls="dashboard-section",
    )

    return Div(
        Div(
            H1(t("dashboard.title", language), style="font-size:22px;font-weight:700;color:#111827;margin:0;"),
            P(t("dashboard.subtitle", language), style="font-size:14px;color:#6b7280;margin:4px 0 0;"),
            cls="page-header",
        ),
        stats_row,
        plans_section,
        quick_actions,
        cls="page-content dashboard-content",
    )
