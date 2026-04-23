"""
Gap Analysis Service — identifies discrepancies between tender requirements
and what's documented in tender documents.
"""

import json
import time
from typing import Dict, List, Optional
from datetime import datetime, timezone

from core.llm_client import LLMClient, LLMProvider
from services.document_reader import TenderDocumentReader


class GapAnalysisService:
    def __init__(self):
        self.llm = LLMClient(provider=LLMProvider.GEMINI, temperature=0.2)
        self.document_reader = TenderDocumentReader()

    async def analyze_gaps(self, tender_id: int, tender_data: Dict) -> Dict:
        """Analyze gaps between requirements and documents."""
        import asyncio
        start = time.time()

        all_docs = self.document_reader.get_all_documents_from_db(tender_id)
        if not all_docs:
            return {"success": False, "error": "No documents found.", "analysis": None}

        loaded_docs = await asyncio.to_thread(
            self.document_reader.load_document_contents, tender_id, all_docs, 6
        )

        docs_with_content = [d for d in loaded_docs if d.get("content") or d.get("ai_summary")]
        if not docs_with_content:
            return {"success": False, "error": "Could not read document content.", "analysis": None}

        prompt = self._build_prompt(tender_data, docs_with_content)

        result = await self.llm.chat_completion_async(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a procurement gap analysis expert. Respond with valid JSON only.",
            temperature=0.2,
        )

        analysis = None
        if result.get("success") and result.get("content"):
            analysis = LLMClient.extract_json(result["content"])

        if not analysis:
            return {"success": False, "error": "Analysis failed.", "analysis": None}

        elapsed = int((time.time() - start) * 1000)
        return {
            "success": True,
            "analysis": analysis,
            "has_full_content": any(d.get("content") for d in docs_with_content),
            "processing_time_ms": elapsed,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _build_prompt(self, tender_data: Dict, documents: List[Dict]) -> str:
        ai_requirements = tender_data.get("ai_requirements", "")
        docs_text = ""
        for d in documents[:6]:
            content = d.get("content") or d.get("ai_summary", "")
            if content:
                docs_text += f"\n--- {d.get('name', 'Document')} ---\n{content[:2000]}\n"

        return f"""Analyze the gap between requirements and documentation for this tender.

Tender: {tender_data.get('name', '')}
Description: {tender_data.get('description', '')[:500]}
Requirements: {ai_requirements[:1000]}

Tender documents:{docs_text}

Identify discrepancies: missing fields, contradictions, incomplete information, and format issues.

Return JSON:
{{
  "summary": "2-3 sentence executive summary",
  "risk_level": "<high|medium|low>",
  "total_discrepancies": integer,
  "discrepancies": [
    {{
      "id": 1,
      "type": "<missing_field|extra_field|conflict|incomplete|format_issue>",
      "severity": "<critical|high|medium|low>",
      "title": "short title",
      "description": "what the issue is",
      "source_document": "document name",
      "recommendation": "how to address"
    }}
  ],
  "document_coverage": [
    {{
      "document_name": "name",
      "coverage_score": 0-100,
      "status": "<complete|partial|poor>",
      "notes": "brief notes"
    }}
  ]
}}

Return ONLY valid JSON."""
