"""Price benchmarking tool — queries UK tender data to find comparable contracts and prices."""

from typing import Dict, List
from tools.registry import Tool, ToolResult, tool_registry


class PriceBenchmarkTool(Tool):
    name = "price_benchmark"
    description = "Search UK tender data for price benchmarks by category (services, goods, works), CPV code, or keywords. Shows price distributions, comparable contracts, and market averages."
    artifact_type = "price_benchmark"

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        keywords = params.get("keywords") or []
        cpv_divisions = params.get("cpv_divisions") or []
        main_category = params.get("main_category") or params.get("industry") or ""

        from services.price_benchmark import get_price_benchmarks
        result = get_price_benchmarks(
            keywords=keywords,
            cpv_divisions=cpv_divisions,
            main_category=main_category,
        )

        if not result.get("contracts"):
            return ToolResult(
                summary="No comparable UK contracts found for this search.",
            )

        search_desc = " ".join(keywords[:3]) or main_category or "general"
        artifact_id = f"benchmark_{search_desc.replace(' ', '_')[:30]}"

        stats = result.get("stats", {})
        return ToolResult(
            artifact_type="price_benchmark",
            artifact_id=artifact_id,
            artifact_data=result,
            summary=(
                f"Price benchmark for '{search_desc}': "
                f"{stats.get('count', 0)} comparable UK contracts found. "
                f"Average value: £{stats.get('avg', 0):,.0f}, "
                f"Median: £{stats.get('median', 0):,.0f}, "
                f"Range: £{stats.get('min', 0):,.0f} — £{stats.get('max', 0):,.0f}."
            ),
        )


tool_registry.register(PriceBenchmarkTool())
