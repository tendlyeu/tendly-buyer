"""
Chat service for Tendly Chat - orchestrates query understanding, tool dispatch,
and streaming response generation for a ChatGPT-like tender search interface.

Uses a tool-calling architecture where the LLM analyzes user queries and the
service dispatches to registered tools. Tools can produce canvas artifacts
(displayed in the right panel) and/or tender cards (displayed inline).
"""

import uuid
import json
import asyncio
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, AsyncGenerator
import logging

from core.llm_client import LLMClient, LLMProvider
from core.url_utils import get_tendly_url
from core.database import get_tendly_session, ChatContext
from sqlalchemy.orm.attributes import flag_modified

# Import tools to trigger registration with the global registry
import tools.search_tenders
import tools.search_companies
import tools.tender_detail
import tools.tender_compare
import tools.risk_analysis
import tools.gap_analysis
import tools.requirements_extraction
import tools.price_benchmark
import tools.rfp_draft
# Seller-side tools (winning_strategy, competitor_intel) are intentionally
# NOT imported — Tendly Buyer is a buyer-only product and bidding strategy /
# competitor analysis don't belong on this surface.

from tools.registry import tool_registry, ToolResult
from tools.search_tenders import COUNTRY_FLAGS, CURRENCY_SYMBOLS, format_tender


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

QUERY_ANALYSIS_SYSTEM_PROMPT = """You are an expert query analyzer for Tendly, a government tender/procurement search system.

Tendly has active tenders from these countries:
- Estonia (EE) — currency: EUR
- United Kingdom (GB) — currency: GBP
- Latvia (LV) — currency: EUR
- Poland (PL) — currency: PLN
- Lithuania (LT) — currency: EUR
- France (FR) — currency: EUR

## Your Task

Analyze the user's message step by step, then return ONLY valid JSON (no markdown, no extra text).

### Step-by-step analysis (Chain of Thought)

1. **Language Detection**: What language is the user writing in? (English, Estonian, Latvian, Lithuanian, Polish, French, or other)
2. **Location Extraction**: Does the message mention a country, city, or region? Map cities to countries:
   - Tallinn, Tartu, Pärnu → EE
   - London, Manchester, Birmingham, Edinburgh, Leeds, Bristol → GB
   - Riga, Liepāja, Daugavpils → LV
   - Warsaw, Kraków, Gdańsk, Wrocław, Poznań, Łódź → PL
   - Vilnius, Kaunas, Klaipėda, Šiauliai → LT
   - Paris, Lyon, Marseille, Toulouse, Nice, Bordeaux, Strasbourg → FR
3. **Industry/Category Extraction**: What industry or CPV category does the query relate to? (see CPV reference below)
4. **Specific Technology/Topic**: Is there a specific technology, product, or service mentioned?
5. **Value Constraints**: Does the user specify a budget, minimum value, or maximum value?
6. **Time Constraints**: Does the user mention urgency, deadlines, or timeframes?
7. **Tender ID Detection**: Does the message contain a numeric tender/procurement ID?

### Output JSON schema

{
  "intent": "search" | "tender_detail" | "general_knowledge" | "market_intelligence" | "company_search" | "tender_compare" | "risk_analysis" | "gap_analysis" | "requirements" | "price_benchmark" | "rfp_draft",
  "rfp_description": "string or null (full text of what user wants to procure, for rfp_draft intent)",
  "needs_search": true/false,
  "country_codes": ["EE","GB","LV","PL","LT","FR"],
  "industry": "string or null",
  "cpv_divisions": ["45","72",...],
  "keywords": ["keyword1","keyword2",...],
  "min_value": null or number,
  "max_value": null or number,
  "tender_id": null or number,
  "tender_ids": null or [number, number],
  "company_name": "string or null",
  "search_type": "industry"|"topic"|"location"|"value"|"tender_id"|"general"|"company"|"tender_compare"
}

### Audience
This assistant serves **public-sector procurement buyers** (not bidders).
NEVER classify queries as "winning_strategy" or "competitor_detail" — those
are seller-side concepts. If a user asks for bidding strategy or competitor
analysis, treat it as "general_knowledge" and explain politely that this
platform is for buyers preparing their own procurements.

### Intent rules

- "search": user wants to find tenders (keywords, industry, country, CPV, value)
- "tender_detail": user asks about a specific tender by ID or reference number
- "general_knowledge": user asks about procurement concepts, processes, regulations
- "market_intelligence": user asks about market trends, competition, pricing, win rates
- "company_search": user wants to discover suppliers/vendors — who has won similar tenders historically, who could be a candidate vendor for a buyer's upcoming procurement
- "tender_compare": user asks to compare two or more specific tenders side by side (requires 2+ tender IDs) — used as benchmarking when drafting a new procurement
- "risk_analysis": user asks about risks in a tender's documents — requires a tender_id. Buyers use this to study how peers framed similar procurements
- "gap_analysis": user asks about gaps or discrepancies in a tender's documents — requires a tender_id
- "requirements": user asks to see/extract requirements from a specific tender — requires a tender_id
- "price_benchmark": user asks about prices, costs, market rates, budgets, or "what is a fair price for X?" — triggers price benchmarking against UK tender data
- "rfp_draft": user asks to draft, create, or generate an RFP, tender document, or procurement notice — triggers AI-powered RFP generation. Set rfp_description to the user's procurement need description.

### CPV Division Reference (use first 2 digits)

Products (03-44):
03: Agricultural, farming, fishing
09: Petroleum, fuel, electricity, energy
14: Mining, basic metals
15: Food, beverages, tobacco
16: Agricultural machinery
18: Clothing, footwear, luggage
22: Printed matter
24: Chemical products
30: Office and computing machinery
31: Electrical machinery, lighting
32: Radio, TV, telecom equipment
33: Medical equipment, pharmaceuticals
34: Transport equipment
35: Security, defence equipment
37: Musical instruments, sports, toys
38: Laboratory, optical equipment
39: Furniture, domestic appliances
42: Industrial machinery
43: Mining, construction machinery
44: Construction materials

Construction (45):
45: Construction work

Software (48):
48: Software packages, information systems

Services (50-98):
50: Repair and maintenance
51: Installation services
55: Hotel, restaurant services
60: Transport services
63: Travel agencies
64: Postal, telecommunications
65: Public utilities
66: Financial, insurance services
70: Real estate services
71: Architectural, engineering
72: IT services, consulting
73: R&D services
75: Administration, defence
76: Oil and gas industry
77: Agricultural, forestry services
79: Business services (law, marketing)
80: Education, training
85: Health, social work
90: Environmental, cleaning
92: Recreational, cultural
98: Other community services

### Rules

- Set needs_search=false ONLY for general_knowledge intent
- Extract ALL mentioned countries from explicit mentions or city names (see city mapping above). country_codes is always an array, even for a single country. Use [] if no country is mentioned.
- Translate non-English terms to identify industry (ehitus→construction, informatique→IT, statyba→construction, budowlane→construction, būvniecība→construction)
- For tender_detail intent, extract the tender_id
- keywords should be in English for best database matching
- cpv_divisions should contain 2-digit strings matching the CPV reference above
- Return ONLY valid JSON

### Few-shot examples

User: "IT tenders in Latvia"
→ Step 1: English. Step 2: Latvia → LV. Step 3: IT → CPV 48, 72. Step 4: general IT. Step 5: none. Step 6: none. Step 7: none.
{"intent":"search","needs_search":true,"country_codes":["LV"],"industry":"information technology","cpv_divisions":["48","72"],"keywords":["IT","software","digital"],"min_value":null,"max_value":null,"tender_id":null,"search_type":"industry"}

User: "ehitushanked Tallinnas"
→ Step 1: Estonian. Step 2: Tallinn → EE. Step 3: ehitus = construction → CPV 45. Step 4: none. Step 5: none. Step 6: none. Step 7: none.
{"intent":"search","needs_search":true,"country_codes":["EE"],"industry":"construction","cpv_divisions":["45"],"keywords":["construction","building","works"],"min_value":null,"max_value":null,"tender_id":null,"search_type":"location"}

User: "AI and machine learning projects in UK"
→ Step 1: English. Step 2: UK → GB. Step 3: IT/software → CPV 72, 48. Step 4: AI, machine learning. Step 5: none. Step 6: none. Step 7: none.
{"intent":"search","needs_search":true,"country_codes":["GB"],"industry":"information technology","cpv_divisions":["72","48"],"keywords":["artificial intelligence","machine learning","AI","data science"],"min_value":null,"max_value":null,"tender_id":null,"search_type":"topic"}

User: "high value construction contracts over 1 million"
→ Step 1: English. Step 2: none. Step 3: construction → CPV 45. Step 4: none. Step 5: min_value 1000000. Step 6: none. Step 7: none.
{"intent":"search","needs_search":true,"country_codes":[],"industry":"construction","cpv_divisions":["45"],"keywords":["construction","contracts"],"min_value":1000000,"max_value":null,"tender_id":null,"search_type":"value"}

User: "271946"
→ Step 1: N/A. Step 2: none. Step 3: none. Step 4: none. Step 5: none. Step 6: none. Step 7: tender ID 271946.
{"intent":"tender_detail","needs_search":true,"country_codes":[],"industry":null,"cpv_divisions":[],"keywords":[],"min_value":null,"max_value":null,"tender_id":271946,"search_type":"tender_id"}

User: "medical equipment"
→ Step 1: English. Step 2: none. Step 3: medical → CPV 33, 85. Step 4: equipment. Step 5: none. Step 6: none. Step 7: none.
{"intent":"search","needs_search":true,"country_codes":[],"industry":"medical and healthcare","cpv_divisions":["33","85"],"keywords":["medical","equipment","hospital","pharmaceutical"],"min_value":null,"max_value":null,"tender_id":null,"search_type":"industry"}

User: "būvniecības iepirkumi Rīgā"
→ Step 1: Latvian. Step 2: Rīga → LV. Step 3: būvniecība = construction → CPV 45. Step 4: none. Step 5: none. Step 6: none. Step 7: none.
{"intent":"search","needs_search":true,"country_codes":["LV"],"industry":"construction","cpv_divisions":["45"],"keywords":["construction","building","works"],"min_value":null,"max_value":null,"tender_id":null,"search_type":"location"}

User: "marchés publics informatique à Paris"
→ Step 1: French. Step 2: Paris → FR. Step 3: informatique = IT → CPV 48, 72. Step 4: none. Step 5: none. Step 6: none. Step 7: none.
{"intent":"search","needs_search":true,"country_codes":["FR"],"industry":"information technology","cpv_divisions":["48","72"],"keywords":["IT","software","digital","computing"],"min_value":null,"max_value":null,"tender_id":null,"search_type":"location"}

User: "find tenders in Estonia, Latvia and Poland"
→ Step 1: English. Step 2: Estonia → EE, Latvia → LV, Poland → PL. Step 3: none. Step 4: none. Step 5: none. Step 6: none. Step 7: none.
{"intent":"search","needs_search":true,"country_codes":["EE","LV","PL"],"industry":null,"cpv_divisions":[],"keywords":[],"min_value":null,"max_value":null,"tender_id":null,"search_type":"location"}

User: "construction tenders in France and UK"
→ Step 1: English. Step 2: France → FR, UK → GB. Step 3: construction → CPV 45. Step 4: none. Step 5: none. Step 6: none. Step 7: none.
{"intent":"search","needs_search":true,"country_codes":["FR","GB"],"industry":"construction","cpv_divisions":["45"],"keywords":["construction","building","works"],"min_value":null,"max_value":null,"tender_id":null,"company_name":null,"search_type":"industry"}

User: "who are the top competitors in IT tenders in Estonia?"
→ Step 1: English. Step 2: Estonia → EE. Step 3: IT → CPV 48, 72. Step 4: competitors. Step 5: none. Step 6: none. Step 7: none.
{"intent":"company_search","needs_search":true,"country_codes":["EE"],"industry":"information technology","cpv_divisions":["48","72"],"keywords":["IT","software"],"min_value":null,"max_value":null,"tender_id":null,"company_name":null,"search_type":"company"}

User: "has Nortal won any tenders?"
→ Step 1: English. Step 2: none. Step 3: none. Step 4: Nortal (company). Step 5: none. Step 6: none. Step 7: none.
{"intent":"company_search","needs_search":true,"country_codes":[],"industry":null,"cpv_divisions":[],"keywords":[],"min_value":null,"max_value":null,"tender_id":null,"company_name":"Nortal","search_type":"company"}

User: "compare tenders 271946 and 268500"
→ Step 1: English. Step 2: none. Step 3: none. Step 4: none. Step 5: none. Step 6: none. Step 7: tender IDs 271946, 268500.
{"intent":"tender_compare","needs_search":true,"country_codes":[],"industry":null,"cpv_divisions":[],"keywords":[],"min_value":null,"max_value":null,"tender_id":null,"tender_ids":[271946,268500],"company_name":null,"search_type":"tender_compare"}

User: "what are the risks in tender 271946?"
→ Step 1: English. Step 2: none. Step 3: none. Step 4: none. Step 5: none. Step 6: none. Step 7: tender ID 271946.
{"intent":"risk_analysis","needs_search":true,"country_codes":[],"industry":null,"cpv_divisions":[],"keywords":[],"min_value":null,"max_value":null,"tender_id":271946,"company_name":null,"search_type":"tender_id"}

User: "show me the gaps in tender 271946 documents"
→ Step 1: English. Step 2: none. Step 3: none. Step 4: none. Step 5: none. Step 6: none. Step 7: tender ID 271946.
{"intent":"gap_analysis","needs_search":true,"country_codes":[],"industry":null,"cpv_divisions":[],"keywords":[],"min_value":null,"max_value":null,"tender_id":271946,"company_name":null,"search_type":"tender_id"}

User: "what are the requirements for tender 268500?"
→ Step 1: English. Step 2: none. Step 3: none. Step 4: none. Step 5: none. Step 6: none. Step 7: tender ID 268500.
{"intent":"requirements","needs_search":true,"country_codes":[],"industry":null,"cpv_divisions":[],"keywords":[],"min_value":null,"max_value":null,"tender_id":268500,"company_name":null,"search_type":"tender_id"}

User: "what is a fair price for cleaning services?"
→ Step 1: English. Step 2: none. Step 3: cleaning → CPV 90. Step 4: cleaning services. Step 5: none. Step 6: none. Step 7: none.
{"intent":"price_benchmark","needs_search":true,"country_codes":[],"industry":"cleaning","cpv_divisions":["90"],"keywords":["cleaning","services"],"min_value":null,"max_value":null,"tender_id":null,"company_name":null,"search_type":"topic"}

User: "how much does IT consulting cost in public sector?"
→ Step 1: English. Step 2: none. Step 3: IT consulting → CPV 72. Step 4: IT consulting. Step 5: none. Step 6: none. Step 7: none.
{"intent":"price_benchmark","needs_search":true,"country_codes":[],"industry":"IT consulting","cpv_divisions":["72"],"keywords":["IT","consulting"],"min_value":null,"max_value":null,"tender_id":null,"company_name":null,"search_type":"topic"}

User: "help me draft an RFP for office renovation for 200 people"
→ Step 1: English. Step 2: none. Step 3: construction/renovation → CPV 45. Step 4: office renovation. Step 5: none. Step 6: none. Step 7: none.
{"intent":"rfp_draft","needs_search":false,"country_codes":[],"industry":"construction","cpv_divisions":["45"],"keywords":["office","renovation"],"min_value":null,"max_value":null,"tender_id":null,"company_name":null,"search_type":"topic","rfp_description":"Office renovation for 200 people"}

User: "create a tender document for security guard services at 3 government buildings"
→ Step 1: English. Step 2: none. Step 3: security → CPV 79. Step 4: security guards. Step 5: none. Step 6: none. Step 7: none.
{"intent":"rfp_draft","needs_search":false,"country_codes":[],"industry":"security","cpv_divisions":["79"],"keywords":["security","guard"],"min_value":null,"max_value":null,"tender_id":null,"company_name":null,"search_type":"topic","rfp_description":"Security guard services at 3 government buildings"}"""

# ---------------------------------------------------------------------------
# Gemini context cache for QUERY_ANALYSIS_SYSTEM_PROMPT
# ---------------------------------------------------------------------------

_query_cache_lock = threading.Lock()
_query_cache_name = None
_query_cache_expiry = None
_CACHE_TTL_SECONDS = 3600
_CACHE_REFRESH_MARGIN = 300

logger = logging.getLogger(__name__)


def _get_or_create_query_cache(client):
    """Get or create Gemini cache for QUERY_ANALYSIS_SYSTEM_PROMPT."""
    global _query_cache_name, _query_cache_expiry

    now = datetime.now(timezone.utc)

    with _query_cache_lock:
        if _query_cache_name and _query_cache_expiry and now < _query_cache_expiry:
            return _query_cache_name

        cache_name = client.create_cache(
            system_instruction=QUERY_ANALYSIS_SYSTEM_PROMPT,
            display_name="tendly-chat-query-analysis",
            ttl_seconds=_CACHE_TTL_SECONDS,
        )

        if cache_name:
            _query_cache_name = cache_name
            _query_cache_expiry = now + timedelta(seconds=_CACHE_TTL_SECONDS - _CACHE_REFRESH_MARGIN)
            logger.info(f"Query analysis cache active: {cache_name}")
            return cache_name
        return None


RESPONSE_SYSTEM_PROMPT = """You are Tendly AI, an expert assistant for government procurement and tender search.
You help users find and analyze government tenders from Estonia, UK, Latvia, Poland, Lithuania, and France.

Language rules:
- Respond in the same language the user writes in. If the user writes in Estonian, respond in Estonian. If in French, respond in French. If in Latvian, respond in Latvian. If in Lithuanian, respond in Lithuanian. If in Polish, respond in Polish. Default to English if unclear.

Response guidelines:
- Use markdown formatting. Be concise but insightful.
- When tender results are provided, write a brief analytical summary (3-5 sentences) highlighting:
  * How many results found and key patterns (countries, industries, value ranges)
  * Notable opportunities (high value, approaching deadlines, EU funded, high quality score)
  * If quality scores are available, mention the average quality and highlight top-scoring opportunities
  * If competition data is available (offer counts from past similar tenders), mention competition levels
  * Brief advice relevant to the search
- When a quick stats summary is provided, incorporate those insights naturally into your response.
- Do NOT list individual tenders in the text - the UI renders them as cards separately.
- If no tenders found, explain possible reasons and suggest 2-3 alternative searches.
- For general knowledge questions, give accurate procurement/tendering answers.
- For market intelligence, provide data-driven insights when context is available.
- End with a "**Try also:**" section with 2-3 related search suggestions that are contextually relevant to what the user searched for. Make them specific and actionable (e.g., if searching IT in Estonia, suggest "IT tenders in Latvia" or "Software development tenders" or "IT consulting above 50,000 EUR").
- Do NOT fabricate tender data. Only reference tenders from the provided search results.
- Format currency with symbols. Highlight deadlines."""

MARKET_INTELLIGENCE_PROMPT = """You are Tendly AI, specializing in government procurement market intelligence.
Provide data-driven analysis based on the tender data and market context provided.
Focus on: competition levels, pricing trends, success strategies, and market opportunities.
Use markdown formatting. Be analytical and actionable."""

COMPANY_INTELLIGENCE_PROMPT = """You are Tendly AI, specializing in government procurement competitor intelligence.
You help users understand the competitive landscape by analyzing companies that have won government tenders.

Language rules:
- Respond in the same language the user writes in. Default to English if unclear.

Response guidelines:
- Use markdown formatting. Be analytical and data-driven.
- When company data is provided, create a clear competitive analysis including:
  * Overview of the competitive landscape (how many companies found, total contracts)
  * Top competitors ranked by wins and contract value
  * Industry focus areas for each company
  * Countries where each company is active
  * Average contract values and competition intensity
- Provide actionable insights: which companies to watch, potential partnership opportunities, market gaps
- End with a "**Try also:**" section with 2-3 related searches (e.g., "IT tenders in Estonia" or "competitors in construction UK")
- Do NOT fabricate data. Only reference companies from the provided search results.
- Format currency with symbols."""


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _sse_event(event: str, data: Any) -> str:
    """Format a server-sent event string."""
    payload = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {payload}\n\n"


# ---------------------------------------------------------------------------
# Main service class
# ---------------------------------------------------------------------------

class TendlyChatService:
    """Orchestrates conversations, query understanding, tool dispatch, and streaming responses."""

    def __init__(self):
        self.llm = LLMClient(provider=LLMProvider.GEMINI, temperature=0.3)

    # ======================================================================
    # Conversation management (persisted to PostgreSQL via ChatContext model)
    # ======================================================================

    def create_conversation(self, user_email=None) -> str:
        cid = str(uuid.uuid4())
        session = get_tendly_session()
        try:
            ctx = ChatContext(
                id=str(uuid.uuid4()),
                conversation_id=cid,
                user_email=user_email,
                title="New conversation",
                messages=[],
                artifacts=[],
            )
            session.add(ctx)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        return cid

    def get_conversations(self, user_email=None) -> List[Dict]:
        session = get_tendly_session()
        try:
            q = session.query(ChatContext)
            if user_email:
                q = q.filter(ChatContext.user_email == user_email)
            q = q.order_by(ChatContext.created_at.desc())
            result = []
            for ctx in q.all():
                msgs = ctx.messages or []
                result.append({
                    "id": ctx.conversation_id,
                    "title": ctx.title or "New conversation",
                    "created_at": ctx.created_at.isoformat() if ctx.created_at else "",
                    "message_count": len(msgs),
                })
            return result
        finally:
            session.close()

    def get_conversation(self, conversation_id: str, user_email: Optional[str] = None) -> Optional[Dict]:
        """Fetch a conversation. If user_email is given, returns None unless
        the conversation belongs to that user OR has no owner (anonymous)."""
        session = get_tendly_session()
        try:
            ctx = session.query(ChatContext).filter(
                ChatContext.conversation_id == conversation_id
            ).first()
            if ctx is None:
                return None
            # Tenant check: a logged-in caller can only read their own
            # conversations. Anonymous (orphan) conversations have user_email
            # blank/null and are accessible to whoever knows the UUID.
            if user_email and ctx.user_email and ctx.user_email != user_email:
                return None
            return {
                "id": ctx.conversation_id,
                "title": ctx.title or "New conversation",
                "created_at": ctx.created_at.isoformat() if ctx.created_at else "",
                "messages": ctx.messages or [],
            }
        finally:
            session.close()

    def delete_conversation(self, conversation_id: str, user_email: Optional[str] = None) -> bool:
        """Delete a conversation. With user_email, only deletes when owned
        by that user (or unowned)."""
        session = get_tendly_session()
        try:
            q = session.query(ChatContext).filter(
                ChatContext.conversation_id == conversation_id
            )
            if user_email:
                # Owner OR unowned (legacy / anonymous)
                from sqlalchemy import or_
                q = q.filter(or_(
                    ChatContext.user_email == user_email,
                    ChatContext.user_email == None,
                    ChatContext.user_email == "",
                ))
            deleted = q.delete(synchronize_session='fetch')
            session.commit()
            return deleted > 0
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ======================================================================
    # Artifact management
    # ======================================================================

    def store_artifact(self, conversation_id: str, artifact_type: str,
                       artifact_id: str, artifact_data: Dict):
        """Store an artifact in the conversation for later retrieval."""
        session = get_tendly_session()
        try:
            ctx = session.query(ChatContext).filter(
                ChatContext.conversation_id == conversation_id
            ).first()
            if not ctx:
                return
            artifacts = list(ctx.artifacts or [])
            artifacts.append({
                "type": artifact_type,
                "id": artifact_id,
                "data": artifact_data,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            ctx.artifacts = artifacts
            flag_modified(ctx, 'artifacts')
            ctx.updated_at = datetime.utcnow()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_artifact(self, conversation_id: str, artifact_id: str) -> Optional[Dict]:
        """Retrieve a stored artifact."""
        session = get_tendly_session()
        try:
            ctx = session.query(ChatContext).filter(
                ChatContext.conversation_id == conversation_id
            ).first()
            if not ctx:
                return None
            for art in (ctx.artifacts or []):
                if art["id"] == artifact_id:
                    return art
            return None
        finally:
            session.close()

    # ======================================================================
    # Tool dispatch
    # ======================================================================

    def _dispatch_tools(self, query_info: Dict) -> ToolResult:
        """Dispatch to the appropriate tool based on query analysis."""
        intent = query_info.get("intent", "search")

        # Tender comparison — opens canvas artifact
        if intent == "tender_compare" and query_info.get("tender_ids"):
            tool = tool_registry.get("tender_compare")
            if tool:
                return tool.execute(query_info, {"chat_service": self})

        # Risk analysis — assess risks in a tender's documents (used by buyers
        # to study how peers framed similar procurements before drafting their
        # own).
        if intent == "risk_analysis" and query_info.get("tender_id"):
            tool = tool_registry.get("risk_analysis")
            if tool:
                return tool.execute({"tender_id": query_info["tender_id"]}, {"chat_service": self})

        # Gap analysis — document discrepancy detection
        if intent == "gap_analysis" and query_info.get("tender_id"):
            tool = tool_registry.get("gap_analysis")
            if tool:
                return tool.execute({"tender_id": query_info["tender_id"]}, {"chat_service": self})

        # Requirements extraction
        if intent == "requirements" and query_info.get("tender_id"):
            tool = tool_registry.get("requirements_extraction")
            if tool:
                return tool.execute({"tender_id": query_info["tender_id"]}, {"chat_service": self})

        # Price benchmarking — search UK tender data for market prices
        if intent == "price_benchmark":
            tool = tool_registry.get("price_benchmark")
            if tool:
                return tool.execute(query_info, {"chat_service": self})

        # RFP drafting — generate structured RFP from description
        if intent == "rfp_draft":
            tool = tool_registry.get("rfp_draft")
            if tool:
                return tool.execute(query_info, {"chat_service": self})

        # Company search (list view, no canvas artifact)
        if intent == "company_search" and query_info.get("needs_search", False):
            tool = tool_registry.get("search_companies")
            if tool:
                return tool.execute(query_info, {"chat_service": self})

        # Tender detail — opens canvas artifact
        if intent == "tender_detail" and query_info.get("tender_id"):
            search_tool = tool_registry.get("search_tenders")
            detail_tool = tool_registry.get("tender_detail")
            search_result = search_tool.execute(query_info, {"chat_service": self}) if search_tool else ToolResult()
            detail_result = detail_tool.execute(
                {"tender_id": query_info["tender_id"]},
                {"chat_service": self},
            ) if detail_tool else ToolResult()

            return ToolResult(
                tenders=search_result.tenders,
                artifact_type=detail_result.artifact_type,
                artifact_id=detail_result.artifact_id,
                artifact_data=detail_result.artifact_data,
                summary=detail_result.summary or search_result.summary,
            )

        # Standard tender search
        if query_info.get("needs_search", False):
            tool = tool_registry.get("search_tenders")
            if tool:
                return tool.execute(query_info, {"chat_service": self})

        # No tool needed (general_knowledge, etc.)
        return ToolResult(summary="No search needed — answering from knowledge.")

    # ======================================================================
    # Streaming message processing (main entry point)
    # ======================================================================

    def _load_conversation(self, conversation_id: str):
        """Load a ChatContext row, returning (session, ctx).

        Caller is responsible for closing the session.
        """
        session = get_tendly_session()
        ctx = session.query(ChatContext).filter(
            ChatContext.conversation_id == conversation_id
        ).first()
        return session, ctx

    def _append_message(self, conversation_id: str, message_dict: Dict):
        """Append a message dict to the ChatContext.messages JSONB column."""
        session = get_tendly_session()
        try:
            ctx = session.query(ChatContext).filter(
                ChatContext.conversation_id == conversation_id
            ).first()
            if not ctx:
                return
            messages = list(ctx.messages or [])
            messages.append(message_dict)
            ctx.messages = messages
            flag_modified(ctx, 'messages')
            ctx.updated_at = datetime.utcnow()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def process_message(
        self, conversation_id: str, user_message: str
    ) -> AsyncGenerator[str, None]:
        """Process a user message and yield SSE-formatted chunks."""
        # Ensure conversation exists in DB
        session = get_tendly_session()
        try:
            ctx = session.query(ChatContext).filter(
                ChatContext.conversation_id == conversation_id
            ).first()
            if not ctx:
                ctx = ChatContext(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    title="New conversation",
                    messages=[],
                    artifacts=[],
                )
                session.add(ctx)
                session.commit()

            conv_title = ctx.title or "New conversation"
            conv_messages = list(ctx.messages or [])

            # Auto-title from first user message
            if conv_title == "New conversation" and not conv_messages:
                conv_title = (user_message[:80] + "...") if len(user_message) > 80 else user_message
                ctx.title = conv_title
                session.commit()
                yield _sse_event("title", {"title": conv_title})
        finally:
            session.close()

        # Store user message
        user_msg_dict = {
            "role": "user",
            "content": user_message,
            "tenders": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._append_message(conversation_id, user_msg_dict)
        conv_messages.append(user_msg_dict)

        try:
            # --- Stage 1: Query understanding ---
            yield _sse_event("status", {"status": "thinking", "message": "Understanding your query..."})
            query_info = await self._analyze_query(user_message)
            intent = query_info.get("intent", "search")

            # --- Stage 2: Tool dispatch ---
            tool_result = ToolResult()
            # Intents that always need a tool to run, even when no DB search
            # is required (the LLM sets needs_search=false for these because
            # they don't filter the tenders table).
            artifact_intents = {
                "rfp_draft", "tender_compare", "risk_analysis",
                "gap_analysis", "requirements", "price_benchmark",
            }
            if (query_info.get("needs_search", False)
                    or intent in ("company_search", "tender_detail")
                    or intent in artifact_intents):
                status_msg = "Searching companies..." if intent == "company_search" else "Searching tenders..."
                yield _sse_event("status", {"status": "searching", "message": status_msg})
                tool_result = await asyncio.to_thread(self._dispatch_tools, query_info)

            # Emit tender cards
            if tool_result.tenders:
                yield _sse_event("tenders", {"tenders": tool_result.tenders})

            # Emit artifact event for canvas panel
            if tool_result.artifact_type and tool_result.artifact_id:
                self.store_artifact(
                    conversation_id,
                    tool_result.artifact_type,
                    tool_result.artifact_id,
                    tool_result.artifact_data or {},
                )
                yield _sse_event("artifact", {
                    "type": tool_result.artifact_type,
                    "id": tool_result.artifact_id,
                    "tender_id": tool_result.artifact_data.get("id") if tool_result.artifact_data else None,
                })

            # --- Stage 3: Generate AI response ---
            yield _sse_event("status", {"status": "generating", "message": "Generating response..."})
            response_text = await self._generate_response(
                user_message, query_info, tool_result.tenders,
                conv_messages, intent,
                companies=tool_result.companies,
                artifact_type=tool_result.artifact_type,
                artifact_summary=tool_result.summary,
                artifact_data=tool_result.artifact_data,
            )

            # Emit response text
            yield _sse_event("text", {"content": response_text})

            # Store assistant message
            assistant_msg = {
                "role": "assistant",
                "content": response_text,
                "tenders": tool_result.tenders,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._append_message(conversation_id, assistant_msg)

            yield _sse_event("done", {})

        except Exception as e:
            print(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
            error_msg = (
                "I'm sorry, I encountered an error while processing your request. "
                "Please try rephrasing your question or try again later."
            )
            yield _sse_event("error", {"message": error_msg})

            error_msg_dict = {
                "role": "assistant",
                "content": error_msg,
                "tenders": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._append_message(conversation_id, error_msg_dict)

    # Non-streaming convenience method (for API/testing)
    async def process_message_sync(self, conversation_id: str, user_message: str) -> Dict:
        """Non-streaming variant that collects the full response."""
        response_text = ""
        tenders = []
        artifact = None
        event_type = None
        async for chunk in self.process_message(conversation_id, user_message):
            for line in chunk.strip().split("\n"):
                if line.startswith("event: "):
                    event_type = line[7:]
                elif line.startswith("data: "):
                    data = json.loads(line[6:])
                    if event_type == "text":
                        response_text += data.get("content", "")
                    elif event_type == "tenders":
                        tenders = data.get("tenders", [])
                    elif event_type == "artifact":
                        artifact = data

        conv = self.get_conversation(conversation_id) or {}
        return {
            "response": response_text,
            "tenders": tenders,
            "artifact": artifact,
            "conversation_id": conversation_id,
            "title": conv.get("title", ""),
        }

    # ======================================================================
    # Query analysis
    # ======================================================================

    async def _analyze_query(self, user_message: str) -> Dict:
        """Use Gemini to extract structured search parameters from the user query."""
        cache_name = _get_or_create_query_cache(self.llm)
        if cache_name:
            result = await self.llm.chat_completion_async(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=None,
                cached_content=cache_name,
                temperature=0.1,
            )
        else:
            result = await self.llm.chat_completion_async(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=QUERY_ANALYSIS_SYSTEM_PROMPT,
                temperature=0.1,
            )

        if result.get("success") and result.get("content"):
            parsed = LLMClient.extract_json(result["content"])
            if parsed:
                return parsed

        return self._fallback_query_analysis(user_message)

    def _fallback_query_analysis(self, user_message: str) -> Dict:
        """Heuristic fallback when LLM query understanding fails."""
        msg = user_message.lower()

        country_codes = []
        country_hints = {
            "EE": ["estonia", "estonian", "tallinn", "tartu", "eesti", "pärnu"],
            "GB": ["uk", "united kingdom", "britain", "british", "london", "england", "manchester", "birmingham", "edinburgh", "leeds", "bristol"],
            "LV": ["latvia", "latvian", "riga", "liepāja", "daugavpils"],
            "PL": ["poland", "polish", "warsaw", "polska", "kraków", "gdańsk", "wrocław", "poznań", "łódź"],
            "LT": ["lithuania", "lithuanian", "vilnius", "kaunas", "lietuvos", "klaipeda", "klaipėda", "šiauliai"],
            "FR": ["france", "french", "paris", "français", "lyon", "marseille", "toulouse", "marchés", "nice", "bordeaux", "strasbourg"],
        }
        for code, hints in country_hints.items():
            if any(h in msg for h in hints):
                country_codes.append(code)

        cpv_divisions = []
        industry = None
        industry_map = {
            ("it", "software", "digital", "technology", "computer"): (["48", "72"], "information technology"),
            ("construction", "building", "works"): (["45"], "construction"),
            ("medical", "health", "hospital", "pharmaceutical"): (["33", "85"], "medical and healthcare"),
            ("transport", "logistics", "vehicle"): (["34", "60"], "transport"),
            ("consulting", "business service"): (["79"], "business services"),
            ("engineering", "architecture"): (["71"], "engineering"),
            ("education", "training"): (["80"], "education"),
            ("environmental", "cleaning", "waste"): (["90"], "environmental"),
            ("energy", "electricity", "renewable", "solar", "wind"): (["09", "65"], "energy and utilities"),
            ("security", "defence", "defense", "military"): (["35", "75"], "security and defence"),
            ("financial", "insurance", "banking", "finance"): (["66"], "financial services"),
            ("agriculture", "farming", "forestry", "agricultural"): (["03", "77"], "agriculture and forestry"),
            ("food", "catering", "restaurant", "canteen"): (["15", "55"], "food and catering"),
            ("furniture", "office furniture", "interior"): (["39"], "furniture and furnishings"),
            ("research", "development", "r&d", "innovation", "laboratory"): (["73", "38"], "research and development"),
            ("telecom", "telecommunications", "network", "fiber"): (["32", "64"], "telecommunications"),
        }
        for keywords, (divs, ind) in industry_map.items():
            if any(kw in msg for kw in keywords):
                cpv_divisions = divs
                industry = ind
                break

        # Non-English keyword detection
        if any(kw in msg for kw in ["ehitus", "ehitustööd", "hanked", "tarkvara"]):
            if not industry:
                if "ehitus" in msg or "ehitustööd" in msg:
                    cpv_divisions = ["45"]
                    industry = "construction"
                elif "tarkvara" in msg:
                    cpv_divisions = ["48", "72"]
                    industry = "information technology"

        if any(kw in msg for kw in ["būvniecība", "būvniecības", "iepirkumi", "pakalpojumi"]):
            if not industry:
                if "būvniecība" in msg or "būvniecības" in msg:
                    cpv_divisions = ["45"]
                    industry = "construction"

        if any(kw in msg for kw in ["statyba", "statybos", "viešieji pirkimai", "paslaugos"]):
            if not industry:
                if "statyba" in msg or "statybos" in msg:
                    cpv_divisions = ["45"]
                    industry = "construction"

        if any(kw in msg for kw in ["marchés publics", "travaux", "informatique", "bâtiment"]):
            if not industry:
                if "travaux" in msg or "bâtiment" in msg:
                    cpv_divisions = ["45"]
                    industry = "construction"
                elif "informatique" in msg:
                    cpv_divisions = ["48", "72"]
                    industry = "information technology"

        if any(kw in msg for kw in ["zamówienia", "budowlane", "informatyczne", "przetarg"]):
            if not industry:
                if "budowlane" in msg:
                    cpv_divisions = ["45"]
                    industry = "construction"
                elif "informatyczne" in msg:
                    cpv_divisions = ["48", "72"]
                    industry = "information technology"

        tender_id = None
        intent = "search"
        stripped = user_message.strip()
        if stripped.isdigit():
            tender_id = int(stripped)
            intent = "tender_detail"

        return {
            "intent": intent,
            "needs_search": True,
            "country_codes": country_codes,
            "industry": industry,
            "cpv_divisions": cpv_divisions,
            "keywords": user_message.split()[:5],
            "min_value": None,
            "max_value": None,
            "tender_id": tender_id,
            "search_type": "tender_id" if tender_id else "topic",
        }

    # ======================================================================
    # Tender detail (kept for backward compatibility with /api/tender/{id})
    # ======================================================================

    def get_tender_detail(self, tender_id: int) -> Optional[Dict]:
        """Fetch comprehensive detail for a single tender."""
        from tools.tender_detail import get_tender_detail
        return get_tender_detail(tender_id)

    # ======================================================================
    # Response generation
    # ======================================================================

    def _compute_quick_stats(self, tenders: List[Dict]) -> str:
        """Compute quick stats summary from search results for LLM context."""
        if not tenders:
            return ""

        from datetime import datetime as _dt

        stats_parts = []

        values = [t["value"] for t in tenders if t.get("value")]
        if values:
            avg_val = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            stats_parts.append(
                f"Value range: {min_val:,.0f} - {max_val:,.0f} (avg {avg_val:,.0f}). "
                f"{len(values)} of {len(tenders)} have disclosed values."
            )

        scores = [t["quality_score"] for t in tenders if t.get("quality_score") is not None]
        if scores:
            avg_score = sum(scores) / len(scores)
            high_quality = sum(1 for s in scores if s >= 70)
            stats_parts.append(
                f"Quality scores: avg {avg_score:.0f}/100, {high_quality} rated high quality (>=70). "
                f"{len(scores)} of {len(tenders)} have quality data."
            )

        country_counts = {}
        for t in tenders:
            cc = t.get("country", "Unknown")
            country_counts[cc] = country_counts.get(cc, 0) + 1
        if len(country_counts) > 1:
            dist = ", ".join(f"{c}: {n}" for c, n in sorted(country_counts.items(), key=lambda x: -x[1]))
            stats_parts.append(f"Country distribution: {dist}")

        now = _dt.utcnow()
        urgent_7d = 0
        within_30d = 0
        for t in tenders:
            dl = t.get("deadline")
            if dl:
                try:
                    dt = _dt.fromisoformat(dl.replace("Z", "+00:00")).replace(tzinfo=None)
                    days = (dt - now).days
                    if 0 < days <= 7:
                        urgent_7d += 1
                    if 0 < days <= 30:
                        within_30d += 1
                except Exception:
                    pass
        if urgent_7d or within_30d:
            stats_parts.append(
                f"Deadlines: {urgent_7d} closing within 7 days, {within_30d} within 30 days."
            )

        if stats_parts:
            return "\nQuick stats summary:\n" + "\n".join(f"- {s}" for s in stats_parts)
        return ""

    async def _generate_response(
        self,
        user_message: str,
        query_info: Dict,
        tenders: List[Dict],
        conversation_history: List[Dict],
        intent: str,
        companies: Optional[List[Dict]] = None,
        artifact_type: Optional[str] = None,
        artifact_summary: Optional[str] = None,
        artifact_data: Optional[Dict] = None,
    ) -> str:
        """Generate a natural-language response using Gemini."""

        if intent == "company_search":
            sys_prompt = COMPANY_INTELLIGENCE_PROMPT
        elif intent == "market_intelligence":
            sys_prompt = MARKET_INTELLIGENCE_PROMPT
        else:
            sys_prompt = RESPONSE_SYSTEM_PROMPT

        # When an analytical tool produced an artifact, tell the model so it
        # writes a short pointer to the canvas instead of generic deflection
        # text like "I cannot draft an RFP". The canvas already holds the
        # full result; the chat reply just needs to summarise + redirect.
        if artifact_type:
            sys_prompt = sys_prompt + (
                f"\n\nIMPORTANT: A specialised '{artifact_type}' tool has "
                "already run successfully and the full result is rendered in "
                "the canvas panel on the right. You MUST NOT say you cannot "
                "perform this task or that you lack this capability — the "
                "tool already did it. Acknowledge what was produced in 2-4 "
                "sentences (using the artifact summary/data below if helpful) "
                "and direct the user to the canvas panel for the complete "
                "output. End with a 'Try also:' section with 2-3 contextually "
                "relevant follow-ups."
            )

        context_parts = [f"User query: {user_message}"]
        context_parts.append(f"Detected intent: {intent}")
        if artifact_type:
            context_parts.append(f"\nArtifact produced ({artifact_type}):")
            if artifact_summary:
                context_parts.append(f"  Summary: {artifact_summary}")
            if artifact_data:
                # Include only the most informative top-level keys to keep
                # the prompt small but grounded.
                keys = list(artifact_data.keys())[:8]
                snippet = {k: artifact_data[k] for k in keys}
                try:
                    context_parts.append(f"  Data preview: {json.dumps(snippet, default=str)[:1500]}")
                except Exception:
                    pass

        if intent == "company_search" and companies:
            context_parts.append(f"\nFound {len(companies)} companies matching the search:\n")
            for i, c in enumerate(companies[:15], 1):
                val_str = f"{c['total_contract_value']:,.0f}" if c.get("total_contract_value") else "N/A"
                avg_str = f"{c['avg_contract_value']:,.0f}" if c.get("avg_contract_value") else "N/A"
                countries_str = ", ".join(c.get("countries", [])[:3])
                industries_str = ", ".join(c.get("industries", [])[:3])
                competition_str = f"{c['avg_competition']:.1f}" if c.get("avg_competition") else "N/A"
                context_parts.append(
                    f"{i}. **{c['name']}** - "
                    f"Wins: {c['win_count']} - "
                    f"Total value: {val_str} - "
                    f"Avg contract: {avg_str} - "
                    f"Avg competition: {competition_str} bidders - "
                    f"Countries: {countries_str or 'N/A'} - "
                    f"Industries: {industries_str or 'N/A'}"
                )
        elif intent == "company_search" and not companies:
            context_parts.append("\nNo companies found matching the search criteria.")
            context_parts.append(f"Search parameters: countries={query_info.get('country_codes', [])}, "
                                 f"cpv={query_info.get('cpv_divisions', [])}, "
                                 f"keywords={query_info.get('keywords', [])}")

        if query_info.get("needs_search"):
            if tenders:
                context_parts.append(f"\nFound {len(tenders)} active tender(s):\n")
                for i, t in enumerate(tenders[:15], 1):
                    sym = CURRENCY_SYMBOLS.get(t.get("currency", ""), "")
                    val = f"{sym}{t['value']:,.2f}" if t.get("value") else "Not disclosed"
                    qs_str = f" - Quality: {t['quality_score']:.0f}/100" if t.get("quality_score") is not None else ""
                    docs_str = ""
                    if t.get("documents"):
                        doc_parts = []
                        for doc in t["documents"][:3]:
                            if doc.get("summary"):
                                doc_parts.append(f"{doc['name']} ({doc['summary'][:80]})")
                            else:
                                doc_parts.append(doc["name"])
                        docs_str = f" - Documents: {', '.join(doc_parts)}"
                    context_parts.append(
                        f"{i}. {t['name']} ({t.get('country', '')}) - "
                        f"Value: {val} - Deadline: {t.get('deadline', 'N/A')} - "
                        f"CPV: {t.get('cpv_code', '')} {t.get('cpv_name', '')} - "
                        f"Authority: {t.get('authority', 'N/A')}{qs_str}{docs_str}"
                    )
                stats = self._compute_quick_stats(tenders)
                if stats:
                    context_parts.append(stats)
            else:
                context_parts.append("\nNo active tenders matched the search criteria.")
                context_parts.append(f"Search parameters: countries={query_info.get('country_codes', []) or query_info.get('country_code', 'all')}, "
                                     f"cpv={query_info.get('cpv_divisions', [])}, "
                                     f"keywords={query_info.get('keywords', [])}")

        recent = conversation_history[-7:-1]
        if recent:
            history_lines = []
            for msg in recent:
                role = "User" if msg["role"] == "user" else "Assistant"
                content = msg["content"][:300] + "..." if len(msg["content"]) > 300 else msg["content"]
                history_lines.append(f"{role}: {content}")
            context_parts.insert(0, "Recent conversation:\n" + "\n".join(history_lines) + "\n---")

        prompt = "\n".join(context_parts)

        result = await self.llm.chat_completion_async(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=sys_prompt,
            temperature=0.5,
        )

        if result.get("success") and result.get("content"):
            return result["content"]

        if tenders:
            return (
                f"I found **{len(tenders)} active tender(s)** matching your search. "
                "Browse the results in the panel.\n\n"
                "**Try also:**\n"
                "- Narrow by country (e.g. \"IT tenders in Estonia\")\n"
                "- Filter by value (e.g. \"tenders above 100,000 EUR\")\n"
                "- Search by industry (e.g. \"construction tenders\")"
            )
        return (
            "I couldn't find any active tenders matching your criteria. "
            "Try broadening your search or using different keywords.\n\n"
            "**Try also:**\n"
            "- Search by industry (e.g. \"construction\", \"IT services\")\n"
            "- Search by country (e.g. \"tenders in France\")\n"
            "- Ask about procurement processes or tendering concepts"
        )


# Module-level singleton
chat_service = TendlyChatService()
