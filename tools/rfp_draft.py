"""RFP drafting tool — generates structured RFP from natural language description."""

import asyncio
from typing import Dict, Optional
from tools.registry import Tool, ToolResult, tool_registry


def _description_from_chat_context(context: Dict) -> str:
    """Pull the buyer's plan description from a system primer message.

    When the chat was started via /chat?plan={id} or /chat?benchmark={id},
    the conversation has a system message with the full plan / tender
    facts. The buyer often follows up with terse asks like 'draft the
    technical specification' or 'tee tehniline kirjeldus' that omit the
    description. Without this fallback, rfp_draft errors out asking the
    user to repeat what they're procuring — even though the plan is
    already attached to the conversation.
    """
    chat_service = context.get("chat_service") if context else None
    if not chat_service:
        return ""
    cid = context.get("conversation_id") if context else None
    if not cid:
        cid = getattr(chat_service, "_current_conversation_id", None)
    if not cid:
        return ""
    try:
        conv = chat_service.get_conversation(cid)
    except Exception:
        return ""
    if not conv:
        return ""
    primers = [
        m.get("content", "")
        for m in (conv.get("messages") or [])
        if m.get("role") == "system" and m.get("content")
    ]
    return "\n\n".join(primers).strip()


_DOC_TYPE_HINTS = {
    "technical_specification": (
        "Focus the output on a TECHNICAL SPECIFICATION (tehniline "
        "kirjeldus) — emphasise scope, deliverables, quality / SLA, "
        "non-discriminatory functional requirements; keep contract "
        "and procedural sections short."
    ),
    "draft_contract": (
        "Focus the output on a DRAFT CONTRACT (lepingu kavand) — "
        "emphasise contract_terms (price, payment milestones, "
        "penalties, performance bonds, IP, termination); the scope "
        "section can be brief."
    ),
    "evaluation_methodology": (
        "Focus the output on an EVALUATION METHODOLOGY "
        "(hindamismetoodika) — emphasise evaluation_criteria with "
        "explicit weights (sum=100%), scoring formulas, and how "
        "each criterion is graded objectively per RHS §85."
    ),
    "espd": (
        "Focus the output on an ESPD / own-declaration form — "
        "emphasise qualification_requirements (no tax debt, "
        "references, certifications) per RHS §95–§101 and what "
        "evidence the bidder must submit."
    ),
}

_DOC_KEYWORD_PATTERNS = [
    ("technical_specification", (
        "technical specification", "technical_specification",
        "tech spec", "tehniline kirjeldus", "tehniline spec",
        "specification technique", "techniczna specyfikacja",
        "tehnine specifikacija", "tehniska specifikacija",
    )),
    ("draft_contract", (
        "draft contract", "lepingu kavand", "lepingu projekt",
        "contract draft", "draft of the contract",
        "projet de contrat", "kontrakta projekts",
    )),
    ("evaluation_methodology", (
        "evaluation methodology", "evaluation method",
        "hindamismetoodika", "hindamise metoodika",
        "méthodologie d'évaluation", "metoda oceny",
    )),
    ("espd", (
        "espd", "own-declaration", "self-declaration",
        "euroopa ühtne hankedokument",
        "european single procurement document",
    )),
]


def _detect_doc_type(params: Dict, description: str) -> Optional[str]:
    """Pick a standard-document type from explicit param or text hints."""
    explicit = (params.get("doc_type") or params.get("document_type") or "").strip().lower()
    if explicit in _DOC_TYPE_HINTS:
        return explicit
    blob = " ".join([
        params.get("rfp_description") or "",
        " ".join(params.get("keywords") or []),
        description or "",
    ]).lower()
    for doc_type, patterns in _DOC_KEYWORD_PATTERNS:
        if any(p in blob for p in patterns):
            return doc_type
    return None


class RfpDraftTool(Tool):
    name = "rfp_draft"
    description = "Generate a structured RFP (Request for Proposal) draft from a natural language description of the procurement need. Includes scope, evaluation criteria, qualification requirements, and timeline."
    artifact_type = "rfp_draft"

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        # Extract the procurement description from keywords or raw message
        description = params.get("rfp_description") or " ".join(params.get("keywords", []))
        # If the buyer was working on an attached plan and just typed
        # 'draft the technical specification', fall back to the plan
        # context primer so we don't bounce them with "please describe".
        if not description.strip():
            description = _description_from_chat_context(context)
        if not description.strip():
            return ToolResult(error="Please describe what you need to procure.")

        category = params.get("industry") or params.get("main_category") or ""
        estimated_value = params.get("max_value") or params.get("estimated_value")
        doc_type = _detect_doc_type(params, description)

        from services.rfp_generator import RfpGeneratorService
        service = RfpGeneratorService()

        # Pass a doc-type hint into the description so the generator
        # knows whether to focus on tech-spec, contract, methodology
        # or ESPD. Without this hint every "draft X" request produced
        # an identical full RFP, leaving the buyer feeling ignored.
        focus_hint = _DOC_TYPE_HINTS.get(doc_type or "", "")
        gen_description = description
        if focus_hint:
            gen_description = f"{description.strip()}\n\nDocument focus: {focus_hint}"

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                service.generate_rfp(
                    description=gen_description,
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
        if doc_type and not title.lower().startswith(doc_type.replace("_", " ")):
            title = f"{doc_type.replace('_', ' ').title()} — {title}"
        artifact_id = f"rfp_{title.replace(' ', '_')[:30]}"

        return ToolResult(
            artifact_type="rfp_draft",
            artifact_id=artifact_id,
            artifact_data={
                "rfp": rfp,
                "doc_type": doc_type,
                "processing_time_ms": result.get("processing_time_ms"),
            },
            summary=(
                f"Generated draft: '{title}'. "
                f"Category: {rfp.get('category', 'N/A')}, "
                f"CPV: {rfp.get('cpv_code', 'N/A')}, "
                f"Estimated value: {rfp.get('estimated_value', 'TBD')}."
                + (f" Document focus: {doc_type}." if doc_type else "")
            ),
        )


tool_registry.register(RfpDraftTool())
