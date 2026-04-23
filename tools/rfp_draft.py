"""RFP drafting tool — generates structured RFP from natural language description."""

import asyncio
from typing import Dict
from tools.registry import Tool, ToolResult, tool_registry


class RfpDraftTool(Tool):
    name = "rfp_draft"
    description = "Generate a structured RFP (Request for Proposal) draft from a natural language description of the procurement need. Includes scope, evaluation criteria, qualification requirements, and timeline."
    artifact_type = "rfp_draft"

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        # Extract the procurement description from keywords or raw message
        description = params.get("rfp_description") or " ".join(params.get("keywords", []))
        if not description:
            return ToolResult(error="Please describe what you need to procure.")

        category = params.get("industry") or params.get("main_category") or ""
        estimated_value = params.get("max_value") or params.get("estimated_value")

        from services.rfp_generator import RfpGeneratorService
        service = RfpGeneratorService()

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                service.generate_rfp(
                    description=description,
                    category=category,
                    estimated_value=estimated_value,
                )
            )
        finally:
            loop.close()

        if not result.get("success"):
            return ToolResult(
                error=result.get("error", "RFP generation failed"),
                summary=result.get("error", "RFP generation failed"),
            )

        rfp = result.get("rfp", {})
        title = rfp.get("title", "RFP Draft")
        artifact_id = f"rfp_{title.replace(' ', '_')[:30]}"

        return ToolResult(
            artifact_type="rfp_draft",
            artifact_id=artifact_id,
            artifact_data={
                "rfp": rfp,
                "processing_time_ms": result.get("processing_time_ms"),
            },
            summary=(
                f"Generated RFP draft: '{title}'. "
                f"Category: {rfp.get('category', 'N/A')}, "
                f"CPV: {rfp.get('cpv_code', 'N/A')}, "
                f"Estimated value: {rfp.get('estimated_value', 'TBD')}."
            ),
        )


tool_registry.register(RfpDraftTool())
