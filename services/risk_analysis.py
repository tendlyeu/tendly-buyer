"""
AI Risk Analysis Service — two-stage LLM-powered risk assessment.

Stage 1: Each document is analyzed individually for risks
Stage 2: Per-document results are compiled into a final risk report
         with cross-document inconsistency detection
"""

import json
import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime, timezone

from core.llm_client import LLMClient, LLMProvider
from services.document_reader import TenderDocumentReader

RISK_MODEL = "gemini-2.5-flash-lite"


class RiskAnalysisService:
    def __init__(self):
        self.llm = LLMClient(provider=LLMProvider.GEMINI, temperature=0.2)
        self.document_reader = TenderDocumentReader()

    async def analyze_risks(self, tender_id: int, tender_data: Dict,
                            language: str = "en") -> Dict:
        """Run two-stage risk analysis on a tender's documents."""
        start = time.time()

        # Load documents
        all_docs = self.document_reader.get_all_documents_from_db(tender_id)
        if not all_docs:
            return {
                "success": False,
                "error": "No documents found for this tender.",
                "analysis": None,
            }

        loaded_docs = await asyncio.to_thread(
            self.document_reader.load_document_contents, tender_id, all_docs, 8
        )

        docs_with_content = [d for d in loaded_docs if d.get("content") or d.get("ai_summary")]
        if not docs_with_content:
            return {
                "success": False,
                "error": "Could not read any document content.",
                "analysis": None,
            }

        tender_title = tender_data.get("name", "")
        tender_desc = tender_data.get("description", "")
        ai_requirements = tender_data.get("ai_requirements", "")

        # --- Stage 1: Per-document analysis ---
        per_doc_results = []
        for i, doc in enumerate(docs_with_content):
            result = await self._analyze_single_document(
                doc, tender_title, tender_desc, ai_requirements, i, len(docs_with_content)
            )
            if result:
                per_doc_results.append(result)

        if not per_doc_results:
            return {
                "success": False,
                "error": "Document analysis produced no results.",
                "analysis": None,
            }

        # --- Stage 2: Compilation with cross-document analysis ---
        compilation_prompt = self._build_compilation_prompt(
            ai_requirements, per_doc_results, tender_title, tender_desc,
            tender_data.get("value"), tender_data.get("deadline"),
            tender_data.get("evaluation_criteria", []),
        )

        result = await self.llm.chat_completion_async(
            messages=[{"role": "user", "content": compilation_prompt}],
            system_prompt="You are a procurement risk analyst. Respond with valid JSON only.",
            temperature=0.2,
        )

        analysis = None
        if result.get("success") and result.get("content"):
            analysis = LLMClient.extract_json(result["content"])

        if not analysis:
            # Build from per-doc results as fallback
            all_risks = []
            for pdr in per_doc_results:
                for r in pdr.get("risks", []):
                    all_risks.append(r)
            analysis = {
                "summary": f"Identified {len(all_risks)} potential risks across {len(per_doc_results)} documents.",
                "overall_risk_level": "medium",
                "risk_score": 50,
                "risks": all_risks[:15],
                "document_inconsistencies": [],
                "risk_summary": {
                    "total_risks": len(all_risks),
                    "critical_count": sum(1 for r in all_risks if r.get("severity") == "critical"),
                    "high_count": sum(1 for r in all_risks if r.get("severity") == "high"),
                    "medium_count": sum(1 for r in all_risks if r.get("severity") == "medium"),
                    "low_count": sum(1 for r in all_risks if r.get("severity") == "low"),
                },
                "bid_readiness_score": 60,
                "key_actions": ["Review all identified risks", "Address critical issues first", "Verify document consistency"],
            }

        elapsed = int((time.time() - start) * 1000)
        return {
            "success": True,
            "analysis": analysis,
            "has_full_content": any(d.get("content") for d in docs_with_content),
            "model_used": RISK_MODEL,
            "processing_time_ms": elapsed,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _analyze_single_document(self, doc: Dict, tender_title: str,
                                       tender_desc: str, ai_requirements: str,
                                       doc_index: int, total_docs: int) -> Optional[Dict]:
        """Stage 1: Analyze a single document for risks."""
        content = doc.get("content") or doc.get("ai_summary", "")
        if not content:
            return None

        prompt = f"""Analyze this tender document for risks and key findings.

Tender: {tender_title}
Description: {tender_desc[:500]}
Requirements: {ai_requirements[:500]}

Document ({doc_index + 1}/{total_docs}): {doc.get('name', 'Unknown')}
Content:
{content[:4000]}

Return JSON with:
{{
  "document_name": "{doc.get('name', '')}",
  "risks": [
    {{
      "category": "<timeline|financial|legal|technical|operational|compliance>",
      "severity": "<critical|high|medium|low>",
      "title": "short title",
      "description": "what the risk is",
      "impact": "potential impact",
      "mitigation": "suggested mitigation"
    }}
  ],
  "key_clauses": [
    {{
      "clause_type": "type",
      "summary": "summary",
      "concern_level": "<high|medium|low>"
    }}
  ],
  "missing_information": ["list of missing items"]
}}

Return ONLY valid JSON."""

        result = await self.llm.chat_completion_async(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a procurement risk analyst. Respond with valid JSON only.",
            temperature=0.2,
        )

        if result.get("success") and result.get("content"):
            return LLMClient.extract_json(result["content"])
        return None

    def _build_compilation_prompt(self, ai_requirements: str,
                                  per_doc_analyses: List[Dict],
                                  tender_title: str, tender_desc: str,
                                  tender_value: float, tender_deadline: str,
                                  evaluation_criteria: List[Dict]) -> str:
        """Build the Stage 2 compilation prompt."""
        docs_summary = ""
        for i, analysis in enumerate(per_doc_analyses, 1):
            doc_name = analysis.get("document_name", f"Document {i}")
            risks = analysis.get("risks", [])
            missing = analysis.get("missing_information", [])
            docs_summary += f"\n--- {doc_name} ---\n"
            docs_summary += f"Risks found: {len(risks)}\n"
            for r in risks:
                docs_summary += f"  - [{r.get('severity', '?')}] {r.get('title', '')}: {r.get('description', '')}\n"
            if missing:
                docs_summary += f"Missing info: {', '.join(missing[:5])}\n"

        criteria_text = ""
        if evaluation_criteria:
            criteria_text = "\nEvaluation criteria:\n"
            for c in evaluation_criteria[:5]:
                criteria_text += f"  - {c.get('name', '')}: {c.get('weight', '')}%\n"

        return f"""Compile a comprehensive risk assessment from these per-document analyses.

Tender: {tender_title}
Description: {tender_desc[:300]}
Estimated value: {tender_value or 'Not specified'}
Deadline: {tender_deadline or 'Not specified'}
{criteria_text}
Requirements summary: {ai_requirements[:500]}

Per-document analysis results:
{docs_summary}

IMPORTANT: Also check for cross-document inconsistencies (contradictions, ambiguities, missing info between documents).

Return JSON:
{{
  "summary": "2-3 sentence executive summary",
  "overall_risk_level": "<critical|high|medium|low>",
  "risk_score": 0-100,
  "risks": [
    {{
      "id": 1,
      "category": "<timeline|financial|legal|technical|operational|compliance>",
      "severity": "<critical|high|medium|low>",
      "title": "short title",
      "description": "full description",
      "impact": "potential impact",
      "mitigation": "suggested mitigation",
      "source_document": "document name"
    }}
  ],
  "document_inconsistencies": [
    {{
      "id": 1,
      "type": "<contradiction|ambiguity|missing_info|outdated>",
      "severity": "<critical|high|medium|low>",
      "title": "short title",
      "description": "what the inconsistency is",
      "document_a": "first document",
      "document_b": "second document",
      "recommendation": "how to resolve"
    }}
  ],
  "risk_summary": {{
    "total_risks": integer,
    "critical_count": integer,
    "high_count": integer,
    "medium_count": integer,
    "low_count": integer
  }},
  "bid_readiness_score": 0-100,
  "key_actions": ["action 1", "action 2", "action 3"]
}}

Return ONLY valid JSON."""
