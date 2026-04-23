"""Winning strategy tool — AI-powered bidding strategy generation."""

import asyncio
from typing import Dict
from tools.registry import Tool, ToolResult, tool_registry
from tools.tender_detail import get_tender_detail


class WinningStrategyTool(Tool):
    name = "winning_strategy"
    description = "Generate an AI-powered winning strategy for a tender: win probability, readiness assessment, key opportunities, challenges, and actionable recommendations"
    artifact_type = "winning_strategy"

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        tender_id = params.get("tender_id")
        if not tender_id:
            return ToolResult(error="No tender_id provided for strategy generation")

        tender_data = get_tender_detail(int(tender_id))
        if not tender_data:
            return ToolResult(error=f"Tender {tender_id} not found")

        from services.winning_strategy import WinningStrategyService
        service = WinningStrategyService()

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                service.generate_winning_strategy(int(tender_id), tender_data)
            )
        finally:
            loop.close()

        if not result.get("success"):
            return ToolResult(
                error=result.get("error", "Strategy generation failed"),
                summary=result.get("error", "Strategy generation failed"),
            )

        strategy = result.get("strategy_data", {})
        artifact_id = f"strategy_{tender_id}"

        return ToolResult(
            artifact_type="winning_strategy",
            artifact_id=artifact_id,
            artifact_data={
                "tender_id": tender_id,
                "tender_name": tender_data.get("name", ""),
                "strategy": strategy,
                "cached": result.get("cached", False),
                "processing_time_ms": result.get("processing_time_ms"),
            },
            summary=(
                f"Winning strategy for '{tender_data.get('name', '')}': "
                f"Win probability: {strategy.get('win_probability', 'N/A')}%, "
                f"Competition: {strategy.get('overall_readiness', 'unknown')}. "
                f"{strategy.get('executive_summary', '')}"
            ),
        )


tool_registry.register(WinningStrategyTool())
