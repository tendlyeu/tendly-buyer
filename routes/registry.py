"""RHR (Riigihangete Register) browser routes for Tendly Buyer."""

from fasthtml.common import *
from starlette.responses import HTMLResponse, RedirectResponse

from components.layout import buyer_page
from config.i18n import get_language_from_request, t
from routes.auth_utils import get_auth_from_request
from core.utils import _raw

COUNTRY_FLAGS = {"EE": "🇪🇪", "GB": "🇬🇧", "LV": "🇱🇻", "PL": "🇵🇱", "LT": "🇱🇹", "FR": "🇫🇷"}


def _tender_row(tender, detail, result, language):
    flag = COUNTRY_FLAGS.get(tender.country_code, "")
    name = getattr(tender, f"procurement_name_{language}", "") or tender.procurement_name or ""
    authority = tender.contracting_authority_name or ""
    value_str = ""
    if detail and detail.estimated_cost:
        value_str = f"€{detail.estimated_cost:,.0f}"
    elif result and result.contract_cost:
        value_str = f"€{result.contract_cost:,.0f}"
    winner = result.winner_name if result else ""
    status = tender.procurement_status or ""

    return A(
        Div(
            Span(flag, style="font-size:18px;flex-shrink:0;"),
            Div(
                Div(name[:80] + ("..." if len(name) > 80 else ""), style="font-size:13px;font-weight:600;color:#111827;line-height:1.3;"),
                Div(
                    Span(authority, style="font-size:12px;color:#6b7280;"),
                    style="margin-top:2px;",
                ),
                style="flex:1;min-width:0;",
            ),
            style="display:flex;align-items:flex-start;gap:10px;flex:1;min-width:0;",
        ),
        Div(
            Span(value_str, style="font-size:13px;font-weight:600;color:#111827;white-space:nowrap;") if value_str else "",
            Span(winner[:30] + ("..." if len(winner) > 30 else ""), style="font-size:11px;color:#059669;white-space:nowrap;") if winner else "",
            style="display:flex;flex-direction:column;align-items:flex-end;gap:2px;flex-shrink:0;",
        ),
        href=f"/registry/{tender.procurement_id}",
        style="display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 16px;background:white;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:6px;cursor:pointer;transition:border-color 0.15s;text-decoration:none;color:inherit;",
        onmouseover="this.style.borderColor='#93c5fd'",
        onmouseout="this.style.borderColor='#e5e7eb'",
    )


def _registry_page(tenders_data, query, country_filter, language="en"):
    country_options = [
        Option("All countries", value=""),
        Option("🇪🇪 Estonia", value="EE"),
        Option("🇬🇧 United Kingdom", value="GB"),
        Option("🇱🇻 Latvia", value="LV"),
        Option("🇵🇱 Poland", value="PL"),
        Option("🇱🇹 Lithuania", value="LT"),
        Option("🇫🇷 France", value="FR"),
    ]
    for opt in country_options:
        if opt.attrs.get("value") == country_filter:
            opt.attrs["selected"] = True

    search_bar = Form(
        Div(
            Input(
                name="q", type="text", value=query,
                placeholder=t("registry.search_placeholder", language),
                cls="form-input registry-search-input",
                style="padding:10px 14px;font-size:14px;height:42px;box-sizing:border-box;width:100%;min-width:0;",
            ),
            Select(
                *country_options, name="country",
                cls="form-select",
                style="padding:10px 14px;font-size:14px;height:42px;box-sizing:border-box;width:100%;",
            ),
            Button(
                t("registry.search", language), type="submit",
                cls="btn-primary",
                style="white-space:nowrap;height:42px;padding:0 22px;width:100%;justify-content:center;",
            ),
            style="display:grid;grid-template-columns:1fr 200px 120px;gap:10px;align-items:center;width:100%;",
        ),
        action="/registry",
        method="get",
        cls="dashboard-section",
    )

    if tenders_data:
        rows = [_tender_row(t_obj, d, r, language) for t_obj, d, r in tenders_data]
        results = Div(
            Div(
                Span(f"{len(tenders_data)} {t('registry.results_found', language)}", style="font-size:13px;color:#6b7280;"),
                style="margin-bottom:10px;",
            ),
            *rows,
            cls="dashboard-section",
        )
    else:
        results = Div(
            _raw('<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'),
            P(t("registry.no_results", language), style="color:#6b7280;font-size:14px;margin:12px 0;"),
            style="text-align:center;padding:32px 0;",
            cls="dashboard-section",
        )

    return Div(
        Div(
            H1(t("registry.title", language), style="font-size:22px;font-weight:700;color:#111827;margin:0;"),
            P(t("registry.subtitle", language), style="font-size:14px;color:#6b7280;margin:4px 0 0;"),
            cls="page-header",
        ),
        search_bar,
        results,
        cls="page-content",
    )


def _search_registry(query="", country="", limit=50):
    try:
        from core.database import get_session, Tender, TenderDetail, TenderResult
        from sqlalchemy import or_, func
        db = get_session()
        try:
            q = db.query(Tender, TenderDetail, TenderResult).outerjoin(
                TenderDetail, Tender.procurement_id == TenderDetail.procurement_id
            ).outerjoin(
                TenderResult, Tender.procurement_id == TenderResult.procurement_id
            )
            if country:
                q = q.filter(Tender.country_code == country)
            if query:
                like = f"%{query}%"
                q = q.filter(or_(
                    Tender.procurement_name.ilike(like),
                    Tender.procurement_name_en.ilike(like),
                    Tender.procurement_name_et.ilike(like),
                    Tender.contracting_authority_name.ilike(like),
                ))
            q = q.filter(Tender.is_suspended == False)
            q = q.order_by(Tender.created_at.desc())
            return q.limit(limit).all()
        finally:
            db.close()
    except Exception as e:
        print(f"Registry search error: {e}")
        return []


def register_registry_routes(rt, chat_service):
    @rt("/registry")
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        query = request.query_params.get("q", "")
        country = request.query_params.get("country", "")
        tenders_data = _search_registry(query=query, country=country)
        content = _registry_page(tenders_data, query, country, language)
        return buyer_page(content, language=language, auth=auth, active_page="registry", chat_service=chat_service, title_key="registry.page_title")

    @rt("/registry/{tender_id}")
    def get(request, tender_id: int):
        """Detail view for a single registry tender. Buyers use this to
        benchmark — see scope, deadline, evaluation criteria, winner."""
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        detail = chat_service.get_tender_detail(tender_id) if chat_service else None
        if not detail:
            return RedirectResponse("/registry", status_code=302)

        # Build a lightweight detail page using the data dict
        flag = COUNTRY_FLAGS.get(detail.get("country_code", ""), "")
        name = (detail.get("name_original")
                or detail.get(f"name_{language}")
                or detail.get("name") or "")
        authority = detail.get("authority", "")
        value = detail.get("value")
        currency = detail.get("currency", "EUR")
        deadline = detail.get("deadline", "")
        cpv_name = detail.get("cpv_name", "")
        description = (detail.get("description_original")
                       or detail.get("description") or "")
        source_url = detail.get("source_url", "") or ""
        tendly_url = detail.get("tendly_url", "") or ""

        info_cards = [
            Div(
                Div(t("registry.country", language) or "Country",
                    style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(f"{flag} {detail.get('country','')}",
                    style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
                cls="info-card",
            ),
            Div(
                Div(t("registry.estimated_value", language) or "Estimated value",
                    style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(f"{currency} {value:,.0f}" if value else "—",
                    style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
                cls="info-card",
            ),
            Div(
                Div(t("registry.deadline", language) or "Deadline",
                    style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(str(deadline)[:10] if deadline else "—",
                    style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
                cls="info-card",
            ),
            Div(
                Div("CPV", style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;"),
                Div(cpv_name or "—",
                    style="font-size:14px;color:#111827;font-weight:500;margin-top:2px;"),
                cls="info-card",
            ),
        ]

        action_row = Div(
            A(t("registry.benchmark_in_chat", language) or "Benchmark in chat",
              href=f"/chat?benchmark={tender_id}",
              cls="btn-primary",
              style="font-size:13px;padding:6px 14px;"),
            (A(t("registry.open_source", language) or "Open source",
               href=source_url, target="_blank", rel="noopener",
               cls="btn-secondary",
               style="font-size:13px;padding:6px 14px;") if source_url else ""),
            (A(t("registry.view_on_tendly", language) or "View on Tendly",
               href=tendly_url, target="_blank", rel="noopener",
               cls="btn-secondary",
               style="font-size:13px;padding:6px 14px;") if tendly_url else ""),
            style="display:flex;gap:8px;flex-wrap:wrap;",
        )

        content = Div(
            Div(
                A("← " + (t("registry.back_to_registry", language) or "Back to registry"),
                  href="/registry",
                  style="font-size:13px;color:#6b7280;text-decoration:none;"),
                style="margin-bottom:8px;",
            ),
            Div(
                Div(
                    H1(name or f"Tender {tender_id}",
                       style="font-size:22px;font-weight:700;color:#111827;margin:0;"),
                    P(authority,
                      style="font-size:14px;color:#6b7280;margin:4px 0 0;"),
                ),
                action_row,
                style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;",
                cls="page-header",
            ),
            Div(*info_cards, cls="info-grid"),
            (Div(
                H3(t("registry.description", language) or "Description",
                   style="font-size:15px;font-weight:600;color:#111827;margin:0 0 10px;"),
                P(description, style="font-size:14px;color:#374151;line-height:1.6;"),
                cls="dashboard-section",
            ) if description else ""),
            cls="page-content",
        )
        return buyer_page(content, language=language, auth=auth,
                          active_page="registry", chat_service=chat_service,
                          title_key="registry.page_title")
