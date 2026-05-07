"""Tender detail tool — fetches comprehensive detail and produces a canvas artifact."""

import uuid
from typing import Dict, Optional

from core.database import (
    get_session, Tender, TenderDetail, TenderDocuments,
    TenderResult, TenderQualityScore, TenderEvaluationCriteria,
)
from tools.registry import Tool, ToolResult, tool_registry
from tools.search_tenders import COUNTRY_FLAGS, CURRENCY_SYMBOLS
from core.url_utils import get_tendly_url, get_source_portal_url


class TenderDetailTool(Tool):
    name = "tender_detail"
    description = "Fetch comprehensive detail for a single tender including documents, quality scores, evaluation criteria, and results"
    artifact_type = "tender_detail"

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        tender_id = params.get("tender_id")
        if not tender_id:
            return ToolResult(error="No tender_id provided")

        detail = get_tender_detail(int(tender_id))
        if not detail:
            return ToolResult(error=f"Tender {tender_id} not found")

        artifact_id = f"tender_{tender_id}"
        return ToolResult(
            artifact_type="tender_detail",
            artifact_id=artifact_id,
            artifact_data=detail,
            summary=f"Loaded detail for tender: {detail.get('name', '')}",
        )


def get_tender_detail(tender_id: int) -> Optional[Dict]:
    """Fetch comprehensive detail for a single tender."""
    session = get_session()
    try:
        row = (
            session.query(Tender, TenderDetail)
            .outerjoin(TenderDetail, Tender.procurement_id == TenderDetail.procurement_id)
            .filter(Tender.procurement_id == tender_id)
            .first()
        )
        if not row:
            return None

        tender, detail = row

        docs = (
            session.query(TenderDocuments)
            .filter(TenderDocuments.tender_id == tender_id)
            .all()
        )
        quality = (
            session.query(TenderQualityScore)
            .filter(TenderQualityScore.procurement_id == tender_id)
            .first()
        )
        criteria = (
            session.query(TenderEvaluationCriteria)
            .filter(TenderEvaluationCriteria.procurement_id == tender_id)
            .all()
        )
        result = (
            session.query(TenderResult)
            .filter(TenderResult.procurement_id == tender_id)
            .first()
        )

        return {
            "id": tender.procurement_id,
            "reference": tender.procurement_reference_nr,
            "name": tender.procurement_name_en or tender.procurement_name,
            "name_original": tender.procurement_name,
            "authority": tender.contracting_authority_name,
            "status": tender.procurement_status,
            "type": tender.procurement_type,
            "process_type": tender.procurement_process_type,
            "country": tender.country,
            "country_code": tender.country_code,
            "flag": COUNTRY_FLAGS.get(tender.country_code, ""),
            "currency": tender.currency,
            "currency_symbol": CURRENCY_SYMBOLS.get(tender.currency, tender.currency),
            "description": tender.short_description_en or tender.short_description or "",
            "description_original": tender.short_description or "",
            "is_e_procurement": tender.is_e_procurement,
            "is_green": tender.is_green_procurement,
            "buyer_email": tender.buyer_email or "",
            "source_url": get_source_portal_url(
                tender.procurement_id,
                tender.country_code,
                tender.source_portal_url or "",
            ),
            "tendly_url": get_tendly_url(tender.procurement_id, tender.procurement_name_en or tender.procurement_name),
            "value": detail.estimated_cost if detail else None,
            "duration_months": detail.duration_in_months if detail else None,
            "deadline": detail.submission_deadline.isoformat() if detail and detail.submission_deadline else None,
            "is_eu_funded": detail.is_eu_financing if detail else False,
            "has_innovative_aspects": detail.has_innovative_aspects if detail else False,
            "cpv_code": detail.primary_cpv_code if detail else "",
            "cpv_name": detail.primary_cpv_name if detail else "",
            "nuts_code": detail.nuts_code if detail else "",
            "ai_requirements": (detail.ai_requirements_en or detail.ai_requirements or "") if detail else "",
            "document_url": detail.document_url if detail else "",
            "documents": [
                {
                    "id": d.procurement_doc_old_id,
                    "name": d.document_name,
                    "file_name": d.file_name,
                    "file_size": d.file_size,
                    "type": d.document_type,
                    "summary": d.ai_summary_en or d.ai_summary or "",
                    "web_url": d.web_url or "",
                }
                for d in docs
            ],
            "quality_score": quality.overall_score if quality else None,
            "quality_analysis": quality.analysis_en if quality else None,
            "evaluation_criteria": [
                {
                    "name": c.criterion_name_en or c.criterion_name,
                    "weight": c.weight_percentage,
                    "description": c.description_en or c.description or "",
                    "type": c.criterion_type,
                }
                for c in criteria
            ],
            "result": {
                "winner": result.winner_name,
                "contract_cost": result.contract_cost,
                "actual_cost": result.contract_actual_cost,
                "status": result.contract_status,
                "offer_count": result.offer_count,
            } if result else None,
        }

    except Exception as e:
        print(f"Error fetching tender detail: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        session.close()


# Register with global registry
tool_registry.register(TenderDetailTool())
