"""Tender comparison tool — side-by-side comparison of 2-3 tenders."""

from typing import Dict, List
from tools.registry import Tool, ToolResult, tool_registry
from tools.tender_detail import get_tender_detail


class TenderCompareTool(Tool):
    name = "tender_compare"
    description = "Compare 2-3 tenders side by side: value, deadline, CPV, authority, evaluation criteria, documents, and quality scores"
    artifact_type = "tender_comparison"

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        tender_ids = params.get("tender_ids") or []
        if len(tender_ids) < 2:
            return ToolResult(error="Need at least 2 tender IDs to compare")
        if len(tender_ids) > 3:
            tender_ids = tender_ids[:3]

        tenders = []
        for tid in tender_ids:
            detail = get_tender_detail(int(tid))
            if detail:
                tenders.append(detail)

        if len(tenders) < 2:
            return ToolResult(error="Could not find enough tenders to compare")

        artifact_id = f"compare_{'_'.join(str(t['id']) for t in tenders)}"
        names = [t.get("name", "")[:40] for t in tenders]
        return ToolResult(
            artifact_type="tender_comparison",
            artifact_id=artifact_id,
            artifact_data={"tenders": tenders},
            summary=f"Comparing {len(tenders)} tenders: {' vs '.join(names)}",
        )


tool_registry.register(TenderCompareTool())
