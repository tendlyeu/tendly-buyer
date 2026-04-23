"""Requirements extraction tool — extracts/returns tender requirements for the canvas."""

from typing import Dict
from tools.registry import Tool, ToolResult, tool_registry
from tools.tender_detail import get_tender_detail


class RequirementsExtractionTool(Tool):
    name = "requirements_extraction"
    description = "Extract and display structured requirements from a tender: mandatory, eligibility, technical, financial, and submission requirements"
    artifact_type = "requirements"

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        tender_id = params.get("tender_id")
        if not tender_id:
            return ToolResult(error="No tender_id provided")

        tender_data = get_tender_detail(int(tender_id))
        if not tender_data:
            return ToolResult(error=f"Tender {tender_id} not found")

        ai_requirements = tender_data.get("ai_requirements", "")
        if not ai_requirements:
            return ToolResult(
                summary=f"No AI-extracted requirements available for tender {tender_id}.",
            )

        artifact_id = f"reqs_{tender_id}"
        return ToolResult(
            artifact_type="requirements",
            artifact_id=artifact_id,
            artifact_data={
                "tender_id": tender_id,
                "tender_name": tender_data.get("name", ""),
                "ai_requirements": ai_requirements,
                "authority": tender_data.get("authority", ""),
                "cpv_code": tender_data.get("cpv_code", ""),
                "cpv_name": tender_data.get("cpv_name", ""),
            },
            summary=f"Requirements extracted for '{tender_data.get('name', '')}'.",
        )


tool_registry.register(RequirementsExtractionTool())
