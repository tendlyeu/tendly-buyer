"""
Winning Strategy Service — AI-powered bidding strategy generation.

Generates comprehensive winning strategies for tenders using Gemini,
analyzing tender requirements, evaluation criteria, and document contents.
"""

import json
import time
from typing import Dict, List, Optional
from datetime import datetime, timezone

from core.llm_client import LLMClient, LLMProvider
from services.document_reader import TenderDocumentReader

STRATEGY_MODEL = "gemini-2.5-flash-lite"


class WinningStrategyService:
    def __init__(self):
        self.llm = LLMClient(provider=LLMProvider.GEMINI, temperature=0.3)
        self.document_reader = TenderDocumentReader()

    async def generate_winning_strategy(self, tender_id: int,
                                        tender_data: Dict,
                                        language: str = "en") -> Dict:
        """Generate a winning strategy for a tender."""
        import asyncio
        start = time.time()

        # Check if strategy already exists in DB
        cached = self._check_cached_strategy(tender_id)
        if cached:
            return {
                "success": True,
                "strategy_data": cached,
                "win_probability": cached.get("win_probability", 50),
                "overall_readiness": cached.get("overall_readiness", "moderate_competition"),
                "executive_summary": cached.get("executive_summary", ""),
                "cached": True,
            }

        # Load documents
        all_docs = self.document_reader.get_all_documents_from_db(tender_id)
        loaded_docs = await asyncio.to_thread(
            self.document_reader.load_document_contents, tender_id, all_docs, 6
        )

        # Build strategy prompt
        prompt = self._build_strategy_prompt(tender_data, loaded_docs)

        result = await self.llm.chat_completion_async(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an expert bid strategist for government procurement. Respond with valid JSON only.",
            temperature=0.3,
        )

        strategy = None
        if result.get("success") and result.get("content"):
            strategy = LLMClient.extract_json(result["content"])

        if not strategy:
            return {
                "success": False,
                "error": "Failed to generate strategy.",
                "strategy_data": None,
            }

        elapsed = int((time.time() - start) * 1000)
        return {
            "success": True,
            "strategy_data": strategy,
            "win_probability": strategy.get("win_probability", 50),
            "overall_readiness": strategy.get("overall_readiness", "moderate_competition"),
            "executive_summary": strategy.get("executive_summary", ""),
            "processing_time_ms": elapsed,
            "model_used": STRATEGY_MODEL,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

    def _check_cached_strategy(self, tender_id: int) -> Optional[Dict]:
        """Check if a winning strategy already exists in the database."""
        try:
            from database import get_session
            from sqlalchemy import text
            session = get_session()
            try:
                row = session.execute(
                    text("SELECT strategy_data FROM tender_winning_strategies WHERE procurement_id = :tid"),
                    {"tid": tender_id},
                ).first()
                if row and row[0]:
                    data = row[0] if isinstance(row[0], dict) else json.loads(row[0])
                    return data
            finally:
                session.close()
        except Exception:
            pass
        return None

    def _build_strategy_prompt(self, tender_data: Dict,
                               documents: List[Dict]) -> str:
        """Build the strategy generation prompt."""
        criteria_text = ""
        for c in tender_data.get("evaluation_criteria", [])[:5]:
            criteria_text += f"\n  - {c.get('name', '')}: {c.get('weight', '')}% ({c.get('type', '')})"

        docs_text = ""
        for d in documents[:6]:
            content = d.get("content") or d.get("ai_summary", "")
            if content:
                docs_text += f"\n--- {d.get('name', 'Document')} ---\n{content[:2000]}\n"

        return f"""Generate a comprehensive winning strategy for this government tender.

Tender: {tender_data.get('name', '')}
Country: {tender_data.get('country', '')}
Authority: {tender_data.get('authority', '')}
Estimated value: {tender_data.get('value', 'Not specified')} {tender_data.get('currency', 'EUR')}
Deadline: {tender_data.get('deadline', 'Not specified')}
CPV: {tender_data.get('cpv_code', '')} {tender_data.get('cpv_name', '')}
Description: {tender_data.get('description', '')[:500]}
Requirements: {tender_data.get('ai_requirements', '')[:500]}

Evaluation criteria:{criteria_text or ' Not specified'}

Documents:{docs_text or ' No documents available'}

Return JSON:
{{
  "win_probability": 0-100,
  "overall_readiness": "<high_competition|moderate_competition|low_competition>",
  "executive_summary": "2-3 sentence strategy overview",
  "ideal_bidder_profile": "description of ideal bidder",
  "key_requirements": [
    {{"requirement": "text", "importance": "<critical|high|medium>"}}
  ],
  "key_opportunities": [
    {{"opportunity": "text", "evidence": "why this is an opportunity"}}
  ],
  "key_challenges": [
    {{"challenge": "text", "mitigation": "how to address"}}
  ],
  "bid_focus_areas": [
    {{"area": "text", "weight": "high|medium|low", "strategy": "approach"}}
  ],
  "recommendations": [
    {{
      "id": 1,
      "category": "<key_requirement|evaluation_strategy|differentiator|action_item|risk_mitigation>",
      "priority": "<critical|high|medium|low>",
      "title": "short title",
      "description": "detailed description",
      "impact": "expected impact",
      "effort": "<low|medium|high>"
    }}
  ]
}}

Return ONLY valid JSON."""
