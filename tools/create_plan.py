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
        description = (
            params.get("rfp_description")
            or params.get("plan_description")
            or " ".join(params.get("keywords", []))
            or ""
        ).strip()
        if not description:
            return ToolResult(error="Please describe what you want to procure.")

        # Pull the user_email from chat_service context (set in
        # process_message). The plan must be scoped to the calling buyer
        # so the tenant guard rails pick it up.
        chat_service = context.get("chat_service")
        user_email = getattr(chat_service, "_current_user_email", None) if chat_service else None
        if not user_email:
            return ToolResult(error=(
                "You must be logged in to create a procurement plan. "
                "Please sign in and ask again."
            ))

        # Use the existing RFP generator to convert the description into
        # structured fields (title, category, cpv, value, criteria,
        # requirements). Then persist via procurement_service.create_plan.
        from services.rfp_generator import RfpGeneratorService
        from services.procurement_service import create_plan

        category = params.get("industry") or ""
        estimated_value = (
            _parse_value(params.get("estimated_value"))
            or _parse_value(params.get("max_value"))
            or _parse_value(params.get("min_value"))
        )

        loop = asyncio.new_event_loop()
        try:
            rfp_result = loop.run_until_complete(
                RfpGeneratorService().generate_rfp(
                    description=description,
                    category=category,
                    estimated_value=estimated_value,
                )
            )
        finally:
            loop.close()

        # Default fields if the generator failed — still create *something*
        # so the user has a plan they can edit, rather than silent failure.
        if not rfp_result.get("success"):
            rfp = {
                "title": (description[:80] + "…") if len(description) > 80 else description,
                "category": category or "muu",
                "cpv_code": "",
                "estimated_value": estimated_value or 0,
                "evaluation_criteria": [],
                "qualification_requirements": [],
            }
        else:
            rfp = rfp_result.get("rfp", {})

        # Map RFP shape -> metadata_json (same shape as the create-form sends)
        metadata = {}
        if rfp.get("evaluation_criteria"):
            metadata["evaluation_criteria"] = [
                {
                    "name": c.get("criterion") or c.get("name") or "",
                    "weight": c.get("weight") or c.get("weight_percentage") or 0,
                    "description": c.get("description", ""),
                }
                for c in rfp["evaluation_criteria"]
            ]
        if rfp.get("qualification_requirements"):
            metadata["requirements"] = [
                {
                    "text": r.get("requirement") or r.get("text") or "",
                    "type": r.get("type") or "qualification",
                    "priority": r.get("priority") or "must",
                }
                for r in rfp["qualification_requirements"]
            ]

        try:
            plan = create_plan(
                title=rfp.get("title") or "New Procurement Plan",
                description=description,
                category=rfp.get("category") or category or "muu",
                estimated_value=rfp.get("estimated_value") or estimated_value,
                cpv_code=rfp.get("cpv_code", ""),
                fiscal_year=2026,
                procurement_method=rfp.get("procedure_type", "open"),
                created_by_email=user_email,
                organization_id=user_email,
                metadata_json=metadata or None,
            )
        except Exception as e:
            return ToolResult(error=f"Could not create plan: {e}")

        plan_id = plan.get("id")
        plan_url = f"/procurements/{plan_id}"

        # Coerce Decimal → float so the artifact survives JSONB serialisation
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
                f"(category: {plan.get('category')}, "
                f"value: {ev} EUR). "
                f"Open it at {plan_url}."
            ),
        )


tool_registry.register(CreatePlanTool())
