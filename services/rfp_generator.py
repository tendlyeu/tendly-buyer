"""RFP Generator Service — AI-powered Request for Proposal drafting."""

import json
import time
from typing import Dict, Optional
from datetime import datetime, timezone

from core.llm_client import LLMClient, LLMProvider


class RfpGeneratorService:
    def __init__(self):
        self.llm = LLMClient(provider=LLMProvider.GEMINI, temperature=0.4)

    # Map language codes to names for prompt injection
    _LANG_NAMES = {
        "en": "English", "et": "Estonian", "lv": "Latvian",
        "lt": "Lithuanian", "pl": "Polish", "fr": "French",
    }

    async def generate_rfp(self, description: str, category: str = "",
                           estimated_value: float = None,
                           procedure_type: str = "open",
                           language: str = "en") -> Dict:
        """Generate a structured RFP draft from a natural language description."""
        start = time.time()

        lang_name = self._LANG_NAMES.get(language, "English")
        prompt = self._build_prompt(description, category, estimated_value, procedure_type, language=language)

        lang_directive = ""
        if language and language != "en":
            lang_directive = (
                f" You MUST write ALL content — titles, section text, "
                f"criterion names, requirement descriptions, contract terms, "
                f"compliance notes — in {lang_name}. The JSON keys must stay "
                f"in English, but ALL string VALUES must be in {lang_name}. "
                f"For example, evaluation criteria names must be in "
                f"{lang_name} (e.g. 'Hind' not 'Price' for Estonian)."
            )

        result = await self.llm.chat_completion_async(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=(
                "You are an expert public procurement officer and RFP writer. "
                "You draft clear, compliant, and professional Requests for Proposal "
                "for government procurement." + lang_directive +
                " Respond with valid JSON only."
            ),
            temperature=0.4,
        )

        rfp = None
        if result.get("success") and result.get("content"):
            rfp = LLMClient.extract_json(result["content"])

        if not rfp:
            return {"success": False, "error": "Failed to generate RFP."}

        elapsed = int((time.time() - start) * 1000)
        return {
            "success": True,
            "rfp": rfp,
            "processing_time_ms": elapsed,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _build_prompt(self, description: str, category: str,
                      estimated_value: float, procedure_type: str,
                      language: str = "en") -> str:
        value_str = f"€{estimated_value:,.0f}" if estimated_value else "Not yet determined"
        lang_name = self._LANG_NAMES.get(language, "English")

        # Determine regulation context based on language/country
        if language == "et":
            regulation_context = (
                "- Compliant with Estonian public procurement law (Riigihangete seadus, RHS 2017)\n"
                "- Follow Estonian procurement thresholds and procedures\n"
                "- Use EUR as currency"
            )
        else:
            regulation_context = (
                "- Compliant with EU public procurement directives\n"
                "- Non-discriminatory (no brand-specific references)\n"
                "- Use EUR as currency"
            )

        language_instruction = ""
        if language and language != "en":
            language_instruction = (
                f"\n\nCRITICAL LANGUAGE REQUIREMENT: ALL text content in the JSON "
                f"values MUST be written in {lang_name}. This includes the title, "
                f"scope_of_work, requirements, evaluation criteria names and "
                f"descriptions, qualification requirement texts, contract terms, "
                f"submission instructions, compliance notes — EVERYTHING. "
                f"Only the JSON keys stay in English. "
                f"For example, if {lang_name} is Estonian:\n"
                f'  - criterion name: "Hind" not "Price"\n'
                f'  - criterion name: "Kvaliteet" not "Quality"\n'
                f'  - requirement: "Pakkuja peab omama..." not "The bidder must..."\n'
                f'  - title: "IT-seadmete ost" not "Procurement of IT Equipment"'
            )

        return f"""Generate a complete RFP (Request for Proposal) draft based on this description.

Procurement Need: {description}
Category: {category or "To be determined based on the description"}
Estimated Value: {value_str}
Procedure Type: {procedure_type or "open"}

Generate a structured RFP with all necessary sections. Return JSON:
{{
  "title": "formal tender title",
  "category": "services|goods|works",
  "cpv_code": "suggested CPV code (8 digits)",
  "cpv_description": "CPV description",
  "estimated_value": number or null,
  "currency": "EUR",
  "procedure_type": "{procedure_type}",
  "sections": {{
    "scope_of_work": "Detailed scope of work / technical specifications (3-5 paragraphs)",
    "requirements": "Key requirements and deliverables (bulleted list as text)",
    "evaluation_criteria": [
      {{"name": "criterion name", "weight": percentage_number, "type": "quality|price|other", "description": "what is evaluated"}}
    ],
    "qualification_requirements": [
      {{"requirement": "text", "type": "mandatory|eligibility|technical|financial", "evidence": "what to submit"}}
    ],
    "contract_terms": "Key contract terms (duration, payment terms, penalties)",
    "submission_instructions": "How to submit the bid (format, deadline, contacts)",
    "timeline": {{
      "notice_period": "X days",
      "question_deadline": "date description",
      "submission_deadline": "date description",
      "evaluation_period": "X days",
      "contract_award": "date description",
      "contract_start": "date description"
    }}
  }},
  "compliance_notes": ["list of compliance considerations"],
  "suggested_duration_months": number
}}

Make the RFP:
{regulation_context}
- Proportionate to the estimated value
- Clear and specific in requirements
- Include realistic evaluation criteria weights (totaling 100%)
{language_instruction}

Return ONLY valid JSON."""
