"""Create procurement plan tool — turns a natural-language description from
the buyer into a real persisted row in tendly.procurement_plans (with a
5-step workflow) and points the chat reply at the newly created plan.

This is the BUYER-side equivalent of the existing rfp_draft tool (which
only renders a canvas artifact). Where rfp_draft says "here is a draft
RFP for review", this tool says "I have created a procurement plan in
your workspace — open it in /procurements/{id}".
"""

import asyncio
import json
import re
from typing import Dict, Optional

from tools.registry import Tool, ToolResult, tool_registry


def _parse_value(raw) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).replace(" ", "").replace(",", "")
    m = re.search(r"-?\d+(\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


class CreatePlanTool(Tool):
    name = "create_plan"
    description = (
        "Create a new procurement plan in the buyer's workspace from a "
        "natural-language description. Persists the plan to the database "
        "with a 5-step workflow (need review, market research, plan review, "
        "budget approval, document preparation) and returns the new plan's "
        "ID and URL."
    )
    artifact_type = "create_plan"

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        # Multi-turn signals from the LLM analyzer
        plan_draft = params.get("plan_draft") or {}
        plan_ready = bool(params.get("plan_ready"))
        plan_question = params.get("plan_question") or ""
        plan_missing = params.get("plan_missing_field") or ""

        # Pull the user_email from chat_service context (set in
        # process_message). The plan must be scoped to the calling buyer.
        chat_service = context.get("chat_service")
        user_email = getattr(chat_service, "_current_user_email", None) if chat_service else None
        if not user_email:
            return ToolResult(error=(
                "You must be logged in to create a procurement plan. "
                "Please sign in and ask again."
            ))

        # If the analyzer says we're not ready yet, surface a "needs info"
        # ToolResult — no DB write, no artifact. The response generator
        # picks this up and asks the user the follow-up question.
        if not plan_ready:
            # Build a snapshot of what's been gathered so the response
            # generator can confirm it back to the user ("So far I have
            # 'IT support', 50,000 EUR — what category should I file it
            # under?").
            gathered = {k: v for k, v in plan_draft.items() if v not in (None, "", [], {}, 0)}
            return ToolResult(
                # No artifact_type — we don't open the canvas yet. Just
                # carry the draft in summary so _generate_response can
                # turn it into a friendly question.
                summary=json.dumps({
                    "phase": "gathering",
                    "missing": plan_missing,
                    "question": plan_question,
                    "gathered": gathered,
                }),
            )

        # READY: persist the plan
        from services.rfp_generator import RfpGeneratorService
        from services.procurement_service import create_plan

        # Prefer plan_draft fields, fall back to top-level params
        description = (
            plan_draft.get("description")
            or params.get("rfp_description")
            or " ".join(params.get("keywords", []))
            or ""
        ).strip()
        title = plan_draft.get("title") or ""
        category = plan_draft.get("category") or params.get("industry") or ""
        cpv_code = plan_draft.get("cpv_code") or ""
        estimated_value = (
            _parse_value(plan_draft.get("estimated_value"))
            or _parse_value(params.get("estimated_value"))
            or _parse_value(params.get("max_value"))
            or _parse_value(params.get("min_value"))
        )

        # If the LLM gave structured criteria/requirements directly in
        # plan_draft, use them; otherwise fall back to the RFP generator
        # to flesh them out.
        eval_criteria = plan_draft.get("evaluation_criteria") or []
        requirements = plan_draft.get("requirements") or []

        if not (eval_criteria and requirements):
            loop = asyncio.new_event_loop()
            try:
                rfp_result = loop.run_until_complete(
                    RfpGeneratorService().generate_rfp(
                        description=description or title,
                        category=category,
                        estimated_value=estimated_value,
                    )
                )
            finally:
                loop.close()

            if rfp_result.get("success"):
                rfp = rfp_result.get("rfp", {})
                if not eval_criteria and rfp.get("evaluation_criteria"):
                    eval_criteria = [
                        {
                            "name": c.get("criterion") or c.get("name") or "",
                            "weight": c.get("weight") or c.get("weight_percentage") or 0,
                            "description": c.get("description", ""),
                        }
                        for c in rfp["evaluation_criteria"]
                    ]
                if not requirements and rfp.get("qualification_requirements"):
                    requirements = [
                        {
                            "text": r.get("requirement") or r.get("text") or "",
                            "type": r.get("type") or "qualification",
                            "priority": r.get("priority") or "must",
                        }
                        for r in rfp["qualification_requirements"]
                    ]
                # Backfill missing structural fields from the generator
                if not title:
                    title = rfp.get("title", "")
                if not category:
                    category = rfp.get("category", "")
                if not cpv_code:
                    cpv_code = rfp.get("cpv_code", "")
                if not estimated_value:
                    estimated_value = _parse_value(rfp.get("estimated_value"))

        metadata = {}
        if eval_criteria:
            metadata["evaluation_criteria"] = eval_criteria
        if requirements:
            metadata["requirements"] = requirements

        try:
            plan = create_plan(
                title=title or (description[:80] if description else "New Procurement Plan"),
                description=description,
                category=category or "muu",
                estimated_value=estimated_value,
                cpv_code=cpv_code,
                fiscal_year=2026,
                procurement_method=plan_draft.get("procurement_method", "open"),
                created_by_email=user_email,
                organization_id=user_email,
                metadata_json=metadata or None,
            )
        except Exception as e:
            return ToolResult(error=f"Could not create plan: {e}")

        plan_id = plan.get("id")
        plan_url = f"/procurements/{plan_id}"

        ev = plan.get("estimated_value")
        try:
            ev = float(ev) if ev is not None else None
        except Exception:
            ev = None

        return ToolResult(
            artifact_type="create_plan",
            artifact_id=f"plan_{plan_id}",
            artifact_data={
                "plan_id": plan_id,
                "plan_url": plan_url,
                "title": plan.get("title"),
                "category": plan.get("category"),
                "estimated_value": ev,
                "cpv_code": plan.get("cpv_code"),
                "evaluation_criteria": metadata.get("evaluation_criteria", []),
                "requirements": metadata.get("requirements", []),
            },
            summary=(
                f"Created procurement plan '{plan.get('title')}' "
                f"(category: {plan.get('category')}, value: {ev} EUR). "
                f"Open it at {plan_url}."
            ),
        )


tool_registry.register(CreatePlanTool())
