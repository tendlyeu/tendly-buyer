"""Competitor intelligence tool — analyzes a company's winning history."""

from typing import Dict
from tools.registry import Tool, ToolResult, tool_registry


class CompetitorIntelTool(Tool):
    name = "competitor_intel"
    description = "Analyze a company's tender winning history: pricing strategy, sector focus, buyer relationships, competition levels, and timing patterns"
    artifact_type = "competitor_intel"

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        company_name = params.get("company_name")
        if not company_name:
            return ToolResult(error="No company name provided")

        country = None
        country_codes = params.get("country_codes") or []
        if country_codes:
            country = country_codes[0]

        from services.strategy_analytics import get_competitor_strategy_analysis
        analysis = get_competitor_strategy_analysis(company_name, country=country)

        if analysis.get("error") == "company_not_found":
            return ToolResult(
                summary=f"No tender wins found for company '{company_name}'."
                + (f" in {country}" if country else "")
            )
        if analysis.get("error"):
            return ToolResult(error=f"Analysis failed: {analysis['error']}")

        company = analysis.get("company", {})
        total_wins = analysis.get("total_wins", 0)

        artifact_id = f"competitor_{company_name.replace(' ', '_')[:30]}"
        return ToolResult(
            artifact_type="competitor_intel",
            artifact_id=artifact_id,
            artifact_data=analysis,
            summary=(
                f"Analyzed {company.get('name', company_name)}: "
                f"{total_wins} tender wins, "
                f"total value {analysis.get('total_value', 0):,.0f}."
            ),
        )


tool_registry.register(CompetitorIntelTool())
