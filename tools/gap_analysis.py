"""Gap analysis tool — identifies discrepancies between requirements and documents."""

import asyncio
from typing import Dict
from tools.registry import Tool, ToolResult, tool_registry
from tools.tender_detail import get_tender_detail


class GapAnalysisTool(Tool):
    name = "gap_analysis"
    description = "Analyze gaps between tender requirements and what's documented: missing fields, contradictions, incomplete information, and document coverage scores"
    artifact_type = "gap_analysis"

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        tender_id = params.get("tender_id")
        if not tender_id:
            return ToolResult(error="No tender_id provided for gap analysis")

        tender_data = get_tender_detail(int(tender_id))
        if not tender_data:
            return ToolResult(error=f"Tender {tender_id} not found")

        from services.gap_analysis import GapAnalysisService
        service = GapAnalysisService()

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                service.analyze_gaps(int(tender_id), tender_data)
            )
        finally:
            loop.close()

        if not result.get("success"):
            return ToolResult(
                error=result.get("error", "Gap analysis failed"),
                summary=result.get("error", "Gap analysis failed"),
            )

        analysis = result.get("analysis", {})
        artifact_id = f"gaps_{tender_id}"

        return ToolResult(
            artifact_type="gap_analysis",
            artifact_id=artifact_id,
            artifact_data={
                "tender_id": tender_id,
                "tender_name": tender_data.get("name", ""),
                "analysis": analysis,
                "processing_time_ms": result.get("processing_time_ms"),
            },
            summary=(
                f"Gap analysis for '{tender_data.get('name', '')}': "
                f"Risk level: {analysis.get('risk_level', 'unknown')}, "
                f"{analysis.get('total_discrepancies', 0)} discrepancies found. "
                f"{analysis.get('summary', '')}"
            ),
        )


tool_registry.register(GapAnalysisTool())
