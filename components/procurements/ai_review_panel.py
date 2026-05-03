"""AI Document Review panel component for procurement detail page."""

from fasthtml.common import *
from core.utils import _raw
from config.i18n import t


SEVERITY_COLORS = {
    "critical": ("#dc2626", "#fef2f2"),
    "high": ("#ea580c", "#fff7ed"),
    "medium": ("#d97706", "#fffbeb"),
    "low": ("#6b7280", "#f3f4f6"),
}

IMPORTANCE_COLORS = {
    "critical": ("#dc2626", "#fef2f2"),
    "important": ("#ea580c", "#fff7ed"),
    "recommended": ("#2563eb", "#eff6ff"),
}


def _score_color(score):
    """Return color based on score value."""
    if score >= 80:
        return "#10b981"
    if score >= 60:
        return "#d97706"
    return "#dc2626"


def _score_circle(score, label, color):
    """Render an SVG score circle with label (reuses risk_analysis pattern)."""
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
            Div(
                str(pct),
                style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#111827;",
            ),
            style="position:relative;width:52px;height:52px;",
        ),
        Div(label, style="font-size:11px;color:#6b7280;text-align:center;margin-top:4px;"),
        style="display:flex;flex-direction:column;align-items:center;",
    )


def ai_review_panel(analysis: dict, language: str = "en"):
    """Render the full AI review results panel."""
    if not analysis:
        return Div(P("No review data available.", style="color:#6b7280;font-size:13px;"), cls="review-panel")

    sections = []

    # --- Score header ---
    quality = analysis.get("quality_score", 0)
    completeness = analysis.get("completeness_score", 0)
    compliance = analysis.get("compliance_score", 0)
    clarity = analysis.get("clarity_score", 0)

    sections.append(
        Div(
            Div(
                _score_circle(quality, t("review.quality_score", language), _score_color(quality)),
                _score_circle(completeness, t("review.completeness", language), _score_color(completeness)),
                _score_circle(compliance, t("review.compliance", language), _score_color(compliance)),
                _score_circle(clarity, t("review.clarity", language), _score_color(clarity)),
                style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap;",
            ),
            cls="review-scores",
            style="padding:20px 0;",
        )
    )

    # --- Executive summary ---
    summary = analysis.get("summary", "")
    if summary:
        sections.append(
            Div(
                Div(t("review.summary", language), cls="review-section-title"),
                P(summary, style="font-size:13px;color:#374151;line-height:1.6;margin:0;"),
                cls="review-section",
            )
        )

    # --- Issues ---
    issues = analysis.get("issues", [])
    if issues:
        # Group by severity for display order
        severity_order = ["critical", "high", "medium", "low"]
        sorted_issues = sorted(issues, key=lambda i: severity_order.index(i.get("severity", "medium")) if i.get("severity", "medium") in severity_order else 99)

        issue_cards = []
        for issue in sorted_issues[:12]:
            severity = issue.get("severity", "medium")
            s_color, s_bg = SEVERITY_COLORS.get(severity, ("#6b7280", "#f3f4f6"))
            category = issue.get("category", "")

            issue_cards.append(
                Div(
                    Div(
                        Span(
                            severity.upper(),
                            style=f"font-size:9px;font-weight:700;padding:2px 6px;border-radius:10px;color:{s_color};background:{s_bg};",
                        ),
                        Span(
                            category,
                            style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.3px;",
                        ) if category else "",
                        style="display:flex;align-items:center;gap:6px;margin-bottom:4px;",
                    ),
                    Div(issue.get("title", ""), style="font-size:13px;font-weight:600;color:#111827;margin-bottom:4px;"),
                    P(issue.get("description", ""), style="font-size:12px;color:#6b7280;line-height:1.5;margin:0 0 4px;"),
                    *(
                        [Div(
                            Span("Suggestion: ", style="font-weight:600;color:#374151;"),
                            issue.get("suggestion", ""),
                            style="font-size:11px;color:#6b7280;line-height:1.4;padding:6px 8px;background:#f9fafb;border-radius:6px;",
                        )]
                        if issue.get("suggestion") else []
                    ),
                    style=f"padding:12px;border:1px solid #f3f4f6;border-radius:8px;border-left:3px solid {s_color};margin-bottom:8px;",
                )
            )

        sections.append(
            Div(
                Div(
                    f"{t('review.issues', language)} ({len(issues)})",
                    cls="review-section-title",
                ),
                *issue_cards,
                cls="review-section",
            )
        )

    # --- Missing sections ---
    missing = analysis.get("missing_sections", [])
    if missing:
        missing_items = []
        for ms in missing[:8]:
            importance = ms.get("importance", "recommended")
            i_color, i_bg = IMPORTANCE_COLORS.get(importance, ("#2563eb", "#eff6ff"))

            missing_items.append(
                Div(
                    Div(
                        _raw(f'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{i_color}" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'),
                        Span(
                            ms.get("section", ""),
                            style="font-size:13px;font-weight:600;color:#111827;",
                        ),
                        Span(
                            importance.upper(),
                            style=f"font-size:9px;font-weight:700;padding:2px 6px;border-radius:10px;color:{i_color};background:{i_bg};margin-left:auto;",
                        ),
                        style="display:flex;align-items:center;gap:8px;margin-bottom:4px;",
                    ),
                    P(
                        ms.get("recommendation", ""),
                        style="font-size:12px;color:#6b7280;line-height:1.5;margin:0;padding-left:22px;",
                    ),
                    style="padding:10px 12px;border:1px solid #f3f4f6;border-radius:8px;margin-bottom:6px;",
                )
            )

        sections.append(
            Div(
                Div(
                    f"{t('review.missing', language)} ({len(missing)})",
                    cls="review-section-title",
                ),
                *missing_items,
                cls="review-section",
            )
        )

    # --- Improvement suggestions ---
    suggestions = analysis.get("improvement_suggestions", [])
    if suggestions:
        suggestion_items = []
        for s in suggestions[:8]:
            suggestion_items.append(
                Div(
                    Div(
                        _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>'),
                        Span(
                            s.get("area", ""),
                            style="font-size:13px;font-weight:600;color:#111827;",
                        ),
                        style="display:flex;align-items:center;gap:8px;margin-bottom:8px;",
                    ),
                    Div(
                        Div(
                            Span("Current: ", style="font-weight:600;color:#9ca3af;font-size:11px;text-transform:uppercase;"),
                            style="margin-bottom:2px;",
                        ),
                        P(s.get("current", ""), style="font-size:12px;color:#6b7280;line-height:1.4;margin:0 0 8px;"),
                        Div(
                            Span("Suggested: ", style="font-weight:600;color:#10b981;font-size:11px;text-transform:uppercase;"),
                            style="margin-bottom:2px;",
                        ),
                        P(s.get("suggested", ""), style="font-size:12px;color:#374151;line-height:1.4;margin:0;padding:6px 8px;background:#f0fdf4;border-radius:6px;border-left:2px solid #10b981;"),
                        style="padding-left:22px;",
                    ),
                    style="padding:12px;border:1px solid #f3f4f6;border-radius:8px;margin-bottom:8px;",
                )
            )

        sections.append(
            Div(
                Div(
                    f"{t('review.suggestions', language)} ({len(suggestions)})",
                    cls="review-section-title",
                ),
                *suggestion_items,
                cls="review-section",
            )
        )

    return Div(*sections, cls="review-panel")


def ai_review_section(plan, language="en"):
    """Render the AI Document Review section for the procurement detail page.

    Shows existing results or a 'Run AI Review' button.
    """
    plan_id = plan.get("id", "")
    metadata = plan.get("metadata_json") or {}
    existing_review = metadata.get("ai_review")

    header = Div(
        H2(
            _raw('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:6px;"><path d="M12 2a4 4 0 014 4c0 1.95-1.4 3.57-3.25 3.92A2 2 0 0011 12v1"/><circle cx="12" cy="17" r="1"/><circle cx="12" cy="12" r="10"/></svg>'),
            t("review.title", language),
            style="font-size:16px;font-weight:600;color:#111827;margin:0;display:flex;align-items:center;",
        ),
        style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;",
    )

    loading = Div(
        Div(
            _raw('<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" style="animation:spin 1s linear infinite;"><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>'),
            Span(
                t("review.analyzing", language),
                style="font-size:13px;color:#6b7280;margin-left:8px;",
            ),
            style="display:flex;align-items:center;justify-content:center;",
        ),
        id="review-loading",
        cls="htmx-indicator",
        style="display:none;text-align:center;padding:20px;",
    )

    if existing_review:
        results = existing_review.get("results", {})
        reviewed_at = existing_review.get("reviewed_at", "")
        doc_count = existing_review.get("document_count", 0)

        # Format reviewed_at for display
        reviewed_display = reviewed_at[:16].replace("T", " ") if reviewed_at else ""

        panel = ai_review_panel(results, language)

        footer = Div(
            Div(
                Span(
                    f"{t('review.reviewed_at', language)}: {reviewed_display}",
                    style="font-size:11px;color:#9ca3af;",
                ),
                Span(" | ", style="font-size:11px;color:#d1d5db;"),
                Span(
                    f"{doc_count} {t('review.documents_analyzed', language)}",
                    style="font-size:11px;color:#9ca3af;",
                ),
                style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;",
            ),
            Button(
                _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>'),
                f" {t('review.rerun_review', language)}",
                hx_post=f"/api/procurements/{plan_id}/ai-review",
                hx_target="#ai-review-results",
                hx_indicator="#review-loading",
                cls="btn-secondary",
                style="font-size:12px;padding:6px 12px;",
            ),
            style="display:flex;align-items:center;justify-content:space-between;margin-top:14px;padding-top:12px;border-top:1px solid #f3f4f6;flex-wrap:wrap;gap:8px;",
        )

        results_div = Div(panel, footer, id="ai-review-results")
    else:
        results_div = Div(id="ai-review-results")

    # Build the run button (shown when no review exists, hidden when results present)
    if not existing_review:
        run_button = Button(
            _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 014 4c0 1.95-1.4 3.57-3.25 3.92A2 2 0 0011 12v1"/><circle cx="12" cy="17" r="1"/><circle cx="12" cy="12" r="10"/></svg>'),
            f" {t('review.run_review', language)}",
            hx_post=f"/api/procurements/{plan_id}/ai-review",
            hx_target="#ai-review-results",
            hx_indicator="#review-loading",
            cls="btn-primary",
            style="font-size:13px;padding:8px 16px;",
        )
    else:
        run_button = ""

    return Div(
        header,
        run_button,
        loading,
        results_div,
        cls="dashboard-section",
    )
