"""Search tenders tool — extracted from chat_service._search_tenders."""

from typing import Dict, List, Optional

from sqlalchemy import func, or_, and_, Integer

from core.database import (
    get_session, Tender, TenderDetail, TenderDocuments,
    TenderQualityScore,
)
from tools.registry import Tool, ToolResult, tool_registry
from core.url_utils import get_tendly_url


COUNTRY_FLAGS = {
    "EE": "\U0001f1ea\U0001f1ea", "GB": "\U0001f1ec\U0001f1e7",
    "LV": "\U0001f1f1\U0001f1fb", "PL": "\U0001f1f5\U0001f1f1",
    "LT": "\U0001f1f1\U0001f1f9", "FR": "\U0001f1eb\U0001f1f7",
}

CURRENCY_SYMBOLS = {"EUR": "\u20ac", "GBP": "\u00a3", "PLN": "z\u0142"}


def format_tender(tender, detail, quality=None, docs=None) -> Dict:
    """Format a tender row into a dict for UI card rendering."""
    formatted_docs = []
    for d in (docs or []):
        formatted_docs.append({
            "name": d.document_name or d.file_name,
            "summary": (d.ai_summary_en or d.ai_summary or "")[:200],
        })
    return {
        "id": tender.procurement_id,
        "name": tender.procurement_name_en or tender.procurement_name,
        "authority": tender.contracting_authority_name,
        "country": tender.country,
        "country_code": tender.country_code,
        "flag": COUNTRY_FLAGS.get(tender.country_code, ""),
        "currency": tender.currency,
        "currency_symbol": CURRENCY_SYMBOLS.get(tender.currency, tender.currency),
        "value": detail.estimated_cost if detail else None,
        "deadline": detail.submission_deadline.isoformat() if detail and detail.submission_deadline else None,
        "cpv_code": detail.primary_cpv_code if detail else "",
        "cpv_name": detail.primary_cpv_name if detail else "",
        "description": (tender.short_description_en or tender.short_description or "")[:200],
        "is_green": detail.is_green if detail else False,
        "is_eu_funded": detail.is_eu_financing if detail else False,
        "source_url": tender.source_portal_url or "",
        "quality_score": quality.overall_score if quality else None,
        "tendly_url": get_tendly_url(tender.procurement_id, tender.procurement_name_en or tender.procurement_name),
        "documents": formatted_docs,
    }


class SearchTendersTool(Tool):
    name = "search_tenders"
    description = "Search for active government tenders by country, CPV code, keywords, and value range"
    artifact_type = None  # Tenders render inline, not in canvas

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        tenders = _search_tenders(params)
        if tenders:
            summary = f"Found {len(tenders)} active tender(s) matching the search criteria."
        else:
            summary = "No active tenders matched the search criteria."
        return ToolResult(tenders=tenders, summary=summary)


def _search_tenders(query_info: Dict) -> List[Dict]:
    """Execute a read-only database search based on extracted query parameters."""
    country_codes = query_info.get("country_codes") or []
    if not country_codes:
        legacy = query_info.get("country_code")
        if legacy:
            country_codes = [legacy]
    cpv_divisions = query_info.get("cpv_divisions") or []
    keywords = query_info.get("keywords") or []
    min_value = query_info.get("min_value")
    max_value = query_info.get("max_value")
    tender_id = query_info.get("tender_id")

    session = get_session()
    try:
        # Specific tender lookup by ID
        if tender_id:
            row = (
                session.query(Tender, TenderDetail, TenderQualityScore)
                .outerjoin(TenderDetail, Tender.procurement_id == TenderDetail.procurement_id)
                .outerjoin(TenderQualityScore, Tender.procurement_id == TenderQualityScore.procurement_id)
                .filter(Tender.procurement_id == int(tender_id))
                .first()
            )
            if row:
                return [format_tender(row[0], row[1], row[2])]
            return []

        # --- Base query: active, not suspended ---
        base_filters = [
            TenderDetail.submission_deadline > func.now(),
            Tender.is_suspended == False,
        ]
        if country_codes:
            base_filters.append(Tender.country_code.in_(country_codes))
        if min_value:
            base_filters.append(TenderDetail.estimated_cost >= min_value)
        if max_value:
            base_filters.append(TenderDetail.estimated_cost <= max_value)

        def _base_query():
            return (
                session.query(Tender, TenderDetail, TenderQualityScore)
                .outerjoin(TenderDetail, Tender.procurement_id == TenderDetail.procurement_id)
                .outerjoin(TenderQualityScore, Tender.procurement_id == TenderQualityScore.procurement_id)
                .filter(and_(*base_filters))
            )

        def _keyword_filters(kws):
            filters = []
            for kw in kws:
                if len(kw) <= 3:
                    for field in [Tender.procurement_name, Tender.procurement_name_en,
                                  Tender.short_description, Tender.short_description_en,
                                  TenderDetail.primary_cpv_name]:
                        padded = func.concat(' ', func.coalesce(field, ''), ' ')
                        filters.append(padded.ilike(f"% {kw} %"))
                else:
                    for field in [Tender.procurement_name, Tender.procurement_name_en,
                                  Tender.short_description, Tender.short_description_en,
                                  TenderDetail.primary_cpv_name]:
                        filters.append(field.ilike(f"%{kw}%"))
            return filters

        # --- Strategy: CPV-first, keyword-fallback ---
        if cpv_divisions:
            cpv_filters = [TenderDetail.primary_cpv_code.like(f"{div}%") for div in cpv_divisions]
            query = _base_query().filter(or_(*cpv_filters))

            if keywords:
                relevance_parts = []
                for kw in keywords:
                    if len(kw) <= 3:
                        padded = func.concat(' ', func.coalesce(Tender.procurement_name_en, ''), ' ')
                        relevance_parts.append(func.cast(padded.ilike(f"% {kw} %"), Integer))
                    else:
                        relevance_parts.append(func.cast(Tender.procurement_name_en.ilike(f"%{kw}%"), Integer))
                relevance_score = sum(relevance_parts)
                query = query.order_by(relevance_score.desc(), TenderDetail.submission_deadline.asc())
            else:
                query = query.order_by(TenderDetail.submission_deadline.asc())

            results = query.limit(20).all()

            if len(results) < 10 and keywords:
                existing_ids = {r[0].procurement_id for r in results}
                kw_filters = _keyword_filters(keywords)
                supplement = (
                    _base_query()
                    .filter(or_(*kw_filters))
                    .filter(~Tender.procurement_id.in_(existing_ids))
                    .order_by(TenderDetail.submission_deadline.asc())
                    .limit(20 - len(results))
                    .all()
                )
                results.extend(supplement)

        elif keywords:
            kw_filters = _keyword_filters(keywords)
            query = _base_query().filter(or_(*kw_filters))
            query = query.order_by(TenderDetail.submission_deadline.asc())
            results = query.limit(20).all()

        else:
            query = _base_query().order_by(TenderDetail.submission_deadline.asc())
            results = query.limit(20).all()

        # Fetch documents for all result tenders in one query
        tender_ids = [t.procurement_id for t, d, q in results]
        docs_by_tender: Dict[int, list] = {}
        if tender_ids:
            all_docs = (
                session.query(TenderDocuments)
                .filter(TenderDocuments.tender_id.in_(tender_ids))
                .all()
            )
            for doc in all_docs:
                docs_by_tender.setdefault(doc.tender_id, []).append(doc)

        return [format_tender(t, d, q, docs_by_tender.get(t.procurement_id, [])) for t, d, q in results]

    except Exception as e:
        print(f"Database search error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        session.close()


# Register with global registry
tool_registry.register(SearchTendersTool())
