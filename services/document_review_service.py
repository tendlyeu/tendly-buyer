"""AI Document Review Service — evaluates procurement document quality."""

import json
import time
from typing import Dict, List
from datetime import datetime, timezone

from core.llm_client import LLMClient, LLMProvider
from core.database import get_tendly_session, ProcurementPlan, ProcurementDocument
from sqlalchemy.orm.attributes import flag_modified


class DocumentReviewService:
    def __init__(self):
        self.llm = LLMClient(provider=LLMProvider.GEMINI, temperature=0.2)

    async def review_documents(self, plan_id: str) -> Dict:
        """Review all documents attached to a procurement plan."""
        start = time.time()

        session = get_tendly_session()
        try:
            plan = session.query(ProcurementPlan).filter(ProcurementPlan.id == plan_id).first()
            if not plan:
                return {"success": False, "error": "Plan not found.", "analysis": None}

            docs = (
                session.query(ProcurementDocument)
                .filter(ProcurementDocument.procurement_plan_id == plan_id)
                .all()
            )
            if not docs:
                return {"success": False, "error": "no_documents", "analysis": None}

            # Gather documents with extractable content
            docs_with_content = []
            for doc in docs:
                content = (doc.content_text or "").strip()
                if content:
                    docs_with_content.append({
                        "title": doc.title or doc.file_name or "Document",
                        "document_type": doc.document_type or "other",
                        "content": content,
                    })

            if not docs_with_content:
                return {"success": False, "error": "no_content", "analysis": None}

            # Build plan context from metadata
            metadata = {}
            if plan.metadata_json and isinstance(plan.metadata_json, dict):
                metadata = plan.metadata_json

            plan_context = {
                "title": plan.title or "",
                "description": plan.description or "",
                "category": plan.category or "",
                "cpv_code": plan.cpv_code or "",
                "procurement_method": plan.procurement_method or "",
                "estimated_value": str(plan.estimated_value) if plan.estimated_value else "",
                "evaluation_criteria": metadata.get("evaluation_criteria", []),
                "requirements": metadata.get("requirements", []),
                "submission_deadline": metadata.get("submission_deadline", ""),
            }

            prompt = self._build_prompt(plan_context, docs_with_content)

            result = await self.llm.chat_completion_async(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a public procurement document quality expert specializing in Estonian and EU procurement law. Respond with valid JSON only.",
                temperature=0.2,
            )

            analysis = None
            if result.get("success") and result.get("content"):
                analysis = LLMClient.extract_json(result["content"])

            if not analysis:
                return {"success": False, "error": "Analysis failed — could not parse LLM response.", "analysis": None}

            # Store results in plan metadata
            plan_meta = plan.metadata_json or {}
            plan_meta["ai_review"] = {
                "results": analysis,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "document_count": len(docs_with_content),
            }
            plan.metadata_json = plan_meta
            flag_modified(plan, "metadata_json")
            session.commit()

            elapsed = int((time.time() - start) * 1000)
            return {
                "success": True,
                "analysis": analysis,
                "document_count": len(docs_with_content),
                "processing_time_ms": elapsed,
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e), "analysis": None}
        finally:
            session.close()

    def _build_prompt(self, plan_context: Dict, documents: List[Dict]) -> str:
        # Assemble document texts
        docs_text = ""
        for d in documents[:8]:
            content = d.get("content", "")[:3000]
            docs_text += f"\n--- {d['title']} (type: {d['document_type']}) ---\n{content}\n"

        # Assemble plan metadata
        criteria_text = ""
        for c in plan_context.get("evaluation_criteria", []):
            criteria_text += f"  - {c.get('criterion_name', '')}: weight {c.get('weight_percentage', '')}%, {c.get('description', '')}\n"

        requirements_text = ""
        for r in plan_context.get("requirements", []):
            requirements_text += f"  - [{r.get('requirement_type', '')}] {r.get('requirement_text', '')} (priority: {r.get('priority', '')})\n"

        return f"""Review the following procurement documents for quality, completeness, and legal compliance.

PROCUREMENT PLAN:
- Title: {plan_context.get('title', '')}
- Description: {plan_context.get('description', '')[:500]}
- Category: {plan_context.get('category', '')}
- CPV Code: {plan_context.get('cpv_code', '')}
- Method: {plan_context.get('procurement_method', '')}
- Estimated Value: {plan_context.get('estimated_value', '')} EUR
- Submission Deadline: {plan_context.get('submission_deadline', '')}

EVALUATION CRITERIA:
{criteria_text if criteria_text else '  (none specified)'}

REQUIREMENTS:
{requirements_text if requirements_text else '  (none specified)'}

UPLOADED DOCUMENTS:
{docs_text}

Evaluate these documents on the following dimensions:

1. COMPLETENESS (0-100): Are standard procurement sections present?
   Check for: introduction/scope, requirements/specifications, evaluation criteria, submission instructions, timeline, terms & conditions, data protection/GDPR.

2. LEGAL COMPLIANCE (0-100): Does it meet Estonian/EU public procurement law?
   Check for: equal treatment, transparency, proportionality, non-discrimination, PPL (Riigihangete seadus) alignment.

3. CLARITY (0-100): Are requirements unambiguous and measurable?
   Check for: measurable evaluation criteria, clear deadlines, specific technical requirements, unambiguous language.

4. ISSUES: List of problems found, each with severity, category, title, description, and suggestion.

5. MISSING SECTIONS: What standard sections are absent.

6. IMPROVEMENT SUGGESTIONS: Actionable suggestions comparing current state vs. what should be done.

Return ONLY valid JSON matching this schema:
{{
  "quality_score": 0-100,
  "completeness_score": 0-100,
  "compliance_score": 0-100,
  "clarity_score": 0-100,
  "summary": "2-3 sentence executive summary",
  "issues": [
    {{
      "severity": "critical|high|medium|low",
      "category": "completeness|compliance|clarity|formatting|legal",
      "title": "short title",
      "description": "what the issue is",
      "suggestion": "how to fix it"
    }}
  ],
  "missing_sections": [
    {{
      "section": "section name",
      "importance": "critical|important|recommended",
      "recommendation": "what to add"
    }}
  ],
  "improvement_suggestions": [
    {{
      "area": "area name",
      "current": "what currently exists",
      "suggested": "what should be done"
    }}
  ]
}}

Return ONLY valid JSON."""
