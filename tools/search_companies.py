"""Search companies tool — extracted from chat_service._search_companies."""

from typing import Dict, List

from sqlalchemy import func, or_

from core.database import (
    get_session, Tender, TenderDetail, TenderResult,
)
from tools.registry import Tool, ToolResult, tool_registry


class SearchCompaniesTool(Tool):
    name = "search_companies"
    description = "Search for companies that have won government tenders, with win counts, values, and industries"
    artifact_type = None  # Results go into LLM context, not canvas

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        companies = _search_companies(params)
        if companies:
            summary = f"Found {len(companies)} companies matching the search criteria."
        else:
            summary = "No companies found matching the search criteria."
        return ToolResult(companies=companies, summary=summary)


def _search_companies(query_info: Dict) -> List[Dict]:
    """Search for companies that have won tenders, aggregated by company name."""
    country_codes = query_info.get("country_codes") or []
    if not country_codes:
        legacy = query_info.get("country_code")
        if legacy:
            country_codes = [legacy]
    cpv_divisions = query_info.get("cpv_divisions") or []
    keywords = query_info.get("keywords") or []
    company_name = query_info.get("company_name")

    session = get_session()
    try:
        base = (
            session.query(
                TenderResult.winner_name,
                func.count(TenderResult.procurement_id).label("win_count"),
                func.sum(TenderResult.contract_cost).label("total_value"),
                func.avg(TenderResult.contract_cost).label("avg_value"),
                func.avg(TenderResult.offer_count).label("avg_competition"),
            )
            .join(Tender, Tender.procurement_id == TenderResult.procurement_id)
            .outerjoin(TenderDetail, Tender.procurement_id == TenderDetail.procurement_id)
            .filter(
                TenderResult.winner_name != None,
                TenderResult.winner_name != "",
            )
        )

        if country_codes:
            base = base.filter(Tender.country_code.in_(country_codes))
        if cpv_divisions:
            cpv_filters = [TenderDetail.primary_cpv_code.like(f"{div}%") for div in cpv_divisions]
            base = base.filter(or_(*cpv_filters))
        if company_name:
            base = base.filter(TenderResult.winner_name.ilike(f"%{company_name}%"))
        if keywords and not cpv_divisions:
            kw_filters = []
            for kw in keywords:
                if len(kw) > 3:
                    kw_filters.append(Tender.procurement_name_en.ilike(f"%{kw}%"))
                    kw_filters.append(Tender.short_description_en.ilike(f"%{kw}%"))
                    kw_filters.append(TenderDetail.primary_cpv_name.ilike(f"%{kw}%"))
            if kw_filters:
                base = base.filter(or_(*kw_filters))

        results = (
            base
            .group_by(TenderResult.winner_name)
            .order_by(func.count(TenderResult.procurement_id).desc())
            .limit(20)
            .all()
        )

        if not results:
            return []

        companies = []
        for winner_name, win_count, total_value, avg_value, avg_competition in results:
            detail_rows = (
                session.query(
                    Tender.country_code,
                    Tender.country,
                    TenderDetail.primary_cpv_name,
                )
                .join(TenderResult, Tender.procurement_id == TenderResult.procurement_id)
                .outerjoin(TenderDetail, Tender.procurement_id == TenderDetail.procurement_id)
                .filter(TenderResult.winner_name == winner_name)
                .all()
            )

            countries_active = list({r[1] for r in detail_rows if r[1]})
            country_codes_active = list({r[0] for r in detail_rows if r[0]})
            industries = list({r[2] for r in detail_rows if r[2]})[:5]

            companies.append({
                "name": winner_name,
                "win_count": win_count,
                "total_contract_value": float(total_value) if total_value else 0,
                "avg_contract_value": float(avg_value) if avg_value else 0,
                "avg_competition": float(avg_competition) if avg_competition else 0,
                "countries": countries_active,
                "country_codes": country_codes_active,
                "industries": industries,
            })

        return companies

    except Exception as e:
        print(f"Company search error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        session.close()


# Register with global registry
tool_registry.register(SearchCompaniesTool())
