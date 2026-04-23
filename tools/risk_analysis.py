"""Risk analysis tool — two-stage LLM risk assessment producing a canvas artifact."""

import asyncio
from typing import Dict
from tools.registry import Tool, ToolResult, tool_registry
from tools.tender_detail import get_tender_detail


class RiskAnalysisTool(Tool):
    name = "risk_analysis"
    description = "Perform AI-powered risk analysis on a tender's documents: identifies risks by severity, cross-document inconsistencies, and bid readiness score"
    artifact_type = "risk_analysis"

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        tender_id = params.get("tender_id")
        if not tender_id:
            return ToolResult(error="No tender_id provided for risk analysis")

        tender_data = get_tender_detail(int(tender_id))
        if not tender_data:
            return ToolResult(error=f"Tender {tender_id} not found")

        from services.risk_analysis import RiskAnalysisService
        service = RiskAnalysisService()

        # Run async analysis in sync context
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                service.analyze_risks(int(tender_id), tender_data)
            )
        finally:
            loop.close()

        if not result.get("success"):
            return ToolResult(
                error=result.get("error", "Risk analysis failed"),
                summary=result.get("error", "Risk analysis failed"),
            )

        analysis = result.get("analysis", {})
        risk_summary = analysis.get("risk_summary", {})
        artifact_id = f"risk_{tender_id}"

        return ToolResult(
            artifact_type="risk_analysis",
            artifact_id=artifact_id,
            artifact_data={
                "tender_id": tender_id,
                "tender_name": tender_data.get("name", ""),
                "analysis": analysis,
                "processing_time_ms": result.get("processing_time_ms"),
                "has_full_content": result.get("has_full_content", False),
            },
            summary=(
                f"Risk analysis for '{tender_data.get('name', '')}': "
                f"Overall risk level: {analysis.get('overall_risk_level', 'unknown')}, "
                f"Score: {analysis.get('risk_score', 'N/A')}/100, "
                f"{risk_summary.get('total_risks', 0)} risks identified "
                f"({risk_summary.get('critical_count', 0)} critical, "
                f"{risk_summary.get('high_count', 0)} high). "
                f"Bid readiness: {analysis.get('bid_readiness_score', 'N/A')}/100."
            ),
        )


tool_registry.register(RiskAnalysisTool())
