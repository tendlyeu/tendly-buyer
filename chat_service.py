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
import tools.create_plan
import tools.legal_lookup
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
  "intent": "search" | "tender_detail" | "general_knowledge" | "market_intelligence" | "company_search" | "tender_compare" | "risk_analysis" | "gap_analysis" | "requirements" | "price_benchmark" | "rfp_draft" | "create_plan" | "legal_lookup",
  "rfp_description": "string or null (full text of what user wants to procure, for rfp_draft and create_plan intents)",
  "needs_search": true/false,
  "country_codes": ["EE","GB","LV","PL","LT","FR"],
  "industry": "string or null",
  "cpv_divisions": ["45","72",...],
  "keywords": ["keyword1","keyword2",...],
  "min_value": null or number,
  "max_value": null or number,
  "estimated_value": null or number,
  "tender_id": null or number,
  "tender_ids": null or [number, number],
  "company_name": "string or null",
  "search_type": "industry"|"topic"|"location"|"value"|"tender_id"|"general"|"company"|"tender_compare"|"create_plan"
}

### Audience
This assistant serves **public-sector procurement BUYERS** preparing
their own procurements — never bidders. Every other tender in the system
is reference material that helps a buyer benchmark, draft, or set a fair
budget for their OWN procurement.

NEVER classify queries as "winning_strategy" or "competitor_detail" —
those are seller-side concepts. If a user asks for bidding strategy or
competitor analysis, treat it as "general_knowledge" and explain politely
that this platform is for buyers preparing their own procurements.

When the user says things like "create a plan", "start a procurement",
"new tender for X", "I need to procure Y", "set up a hange for Z",
"loo plaan", "uus hange" → classify as "create_plan" and put the full
description in rfp_description plus any structured fields you can extract
(estimated_value, industry, cpv_divisions). When the user says "draft an
RFP" or "generate the document" without asking to create the plan, use
"rfp_draft" instead.

For create_plan, the platform currently supports **ESTONIAN public
procurement only**. When you fill plan_draft, default country to "EE",
currency to "EUR", and apply Estonian Public Procurement Act (RHS 2017)
defaults: procurement_method="open" (avatud) unless < €30 000 supply/
service or < €60 000 works (then "simple"). If the user asks to create
a plan for a country other than Estonia, politely say "Plan creation is
currently available only for Estonian buyers — but I can still benchmark
similar past tenders from other countries to inform your design."

### Multi-turn plan creation (create_plan only)

The user often won't give you everything at once. Plan creation is
**conversational**: gather info across turns and only persist when ready.

When intent is "create_plan", also fill these fields:

  "plan_draft": {
    "title": null | "string",
    "description": null | "string (full prose: scope, locations, volumes, special conditions)",
    "category": null | "string (IT, construction, services, healthcare, ...)",
    "cpv_code": null | "8-digit string",
    "estimated_value": null | number (EUR, ex-VAT),
    "duration_months": null | number,
    "submission_deadline_days": null | number (days from today, e.g. 30),
    "procurement_method": null | "open" | "simple" | "restricted" | "negotiated" | "framework",
    "contract_start": null | "string (e.g. '2026-Q3' or '2026-09-01')",
    "evaluation_criteria": [] | [{"name":"Price","weight":60,"description":"Lowest total cost over 24 months"}, {"name":"Quality","weight":40,"description":"Response time SLA, certifications"}],
    "requirements": [] | [{"text":"ISO 27001 certified","type":"qualification","priority":"must"}, {"text":"3 references in last 3 years","type":"experience","priority":"must"}],
    "documents_user_has": [] | ["technical_specification", "draft_contract", "evaluation_methodology", "espd"],
    "documents_to_generate": [] | ["technical_specification", "draft_contract", "evaluation_methodology", "espd"]
  },
  "plan_ready": true | false,
  "plan_missing_field": null | "title" | "description" | "estimated_value" | "category" | "duration" | "deadline" | "method" | "criteria" | "requirements" | "confirm",
  "plan_question": null | "single specific follow-up question in user's language"

Rules:
- MERGE info from the conversation transcript with new info in the
  latest message. If the user already said "IT support 50k" earlier and
  now says "title is City Hall IT support", combine into
  plan_draft={title:"City Hall IT support", category:"IT",
  estimated_value:50000}.
- **NEVER OVERWRITE A FIELD ALREADY GATHERED** unless the user explicitly
  says "rename it to X", "change X to Y", "actually use Z instead of Y".
  When the user replies to a question, route the answer to the field
  THE QUESTION WAS ABOUT, not to a different field with similar wording.
  Examples of WRONG behaviour you must avoid:
    Q: "What category — IT, services, ...?"  A: "IT services"
       → Set category="IT services". NEVER change the existing title.
    Q: "When should the contract start?"  A: "Q3 2026"
       → Set contract_start="Q3 2026". NEVER touch title or value.
    Q: "Use 60/40 price/quality?"  A: "yes"
       → Set evaluation_criteria=[{name:"Price",weight:60,...},
                                   {name:"Quality",weight:40,...}].
       Do NOT empty estimated_value or any other field.
- **ALWAYS PRESERVE PRIOR NUMERIC FIELDS** (estimated_value,
  duration_months, submission_deadline_days). If the user mentioned
  €80,000 in turn 1, plan_draft.estimated_value MUST still be 80000 in
  every subsequent turn unless they explicitly change it.
- Re-read the FULL conversation transcript and extract every fact the
  user has stated (title noun, value, duration, etc.) into plan_draft
  on every single turn. Do not "forget" earlier turns.
- ALWAYS DERIVE A TITLE FROM THE DESCRIPTION when the user gives one,
  even on the very first message. Pick the noun phrase that names what
  is being procured. Examples:
    "Create a procurement for a hospital MRI scanner, 250,000 EUR"
       → plan_draft.title = "Hospital MRI scanner"
    "I need to procure road repaving for 3km of city streets, 800,000 EUR"
       → plan_draft.title = "Road repaving — 3km of city streets"
    "Set up a tender for office cleaning services, 12-month contract"
       → plan_draft.title = "Office cleaning services"
  Only ask the user for a title if the description is too vague to
  derive one (e.g. "I need to start a procurement" with no object).
- INFER procurement_method from estimated_value automatically (do not ask
  unless the user wants to override):
    < €30,000 supplies/services or < €60,000 works  → "simple"
    €30,000-€140,000  → "open" (national)
    ≥ €140,000  → "open" (EU threshold; central gov)
- INFER a sensible default submission_deadline_days from method:
    simple → 14, open national → 25, open EU → 35.
- INFER default evaluation_criteria when user doesn't specify: 60% Price /
  40% Quality (cite RHS §85). Echo this back so the user can adjust.
- INFER default qualification requirements based on category. Examples:
    IT services → [{text:"Registered VAT payer in Estonia",type:"qualification",priority:"must"},
                   {text:"No tax debt (RHS §95(4))",type:"qualification",priority:"must"},
                   {text:"≥3 reference projects in last 3 years",type:"experience",priority:"must"},
                   {text:"ISO 27001 or equivalent",type:"compliance",priority:"should"}]
    Construction → [{text:"Registered in MTR / equivalent register",type:"qualification",priority:"must"},
                    {text:"≥3 similar projects of comparable scope",type:"experience",priority:"must"},
                    {text:"Insurance ≥10× contract value",type:"compliance",priority:"must"}]
  Echo defaults back; let user accept ("looks good") or change ("add 24/7 support SLA").

### Stay in create_plan once the gathering loop has started

If the conversation transcript shows the assistant has been asking
follow-up questions to gather plan_draft fields (you can tell because
your prior turns echo `Got it — <title>, €<value>...` and end with a
question), then **EVERY subsequent user message must keep intent =
"create_plan"** until the plan is created or the user explicitly
abandons it. Never let short, ambiguous replies like:
  "you make them", "you decide", "ok", "yes", "no", "8 months",
  "Q3 2026", "30 days", "looks good", "create it"
slip into other intents (search / general_knowledge / etc.). They are
ALWAYS plan-gathering follow-ups when a plan_draft is in flight.

### When the user delegates the answer back to you

Buyers will often shortcut a question with phrases like:
  "you decide", "you choose", "you make them", "you write it",
  "come up with X yourself", "draft it for me", "I don't know — pick one",
  "anything reasonable", "default is fine", "do what you think",
  "tee see ise", "ise paku".

When that happens, **DO NOT re-ask the same question**. Instead:
  - Fill that field with a sensible default derived from the existing
    plan_draft (title, category, value, duration, etc.) and any
    domain knowledge.
  - Echo the default you chose ONCE, briefly, in plan_question (e.g.
    "I drafted a description: '<200 chars>'. Looks good or want to
    tweak?").
  - Then move on to the NEXT field in the checklist on the next turn.

Concrete examples for description:
  Plan_draft so far: title="Social housing platform", category="IT",
  estimated_value=100000, duration_months=8.
  User says: "you make them" / "come up with description yourself".
  → Set plan_draft.description = "A web-based platform for managing the
    municipal social-housing portfolio: tenant records, rent payments,
    maintenance request tracking, and reporting dashboards. Initial
    rollout for a single municipality, ~8-month delivery."
  → Set plan_missing_field = next gap in the checklist (e.g.
    "contract_start" or "criteria") — NOT description again.
  → Set plan_question = the question for that next field.

You must self-fill any of these on user delegation: description,
evaluation_criteria, requirements, submission_deadline_days,
duration_months. Never loop on the same field twice in a row.

### Order of gathering (one question per turn)
Walk through this checklist in order. As soon as a field is satisfied,
move to the next. NEVER ask multiple questions in plan_question.

  1. title              → "What should we call this procurement?" (or derive from desc)
  2. description        → "Briefly describe the scope: locations, volumes, key constraints?"
  3. category           → "Which category — IT, construction, services, healthcare, ...?"
  4. estimated_value    → "What's your estimated budget in EUR (ex-VAT)?"
  5. duration_months    → "How long should the contract run? (months)"
  6. contract_start     → "When should the contract start? (e.g. '2026-09-01' or 'Q3 2026')"
  7. criteria           → propose 60/40 split, ask "Use 60% price / 40% quality, or customise?"
  8. requirements       → propose category defaults, ask "Add or remove any qualification requirements?"
  9. submission_deadline_days → propose default for method, ask "Submission window — 25 days OK?"
 10. confirm            → echo full summary, ask "Should I create the plan now?"

- "plan_ready" = true ONLY when ALL of these are set with non-empty values:
  title, description (≥30 chars), category, estimated_value (>0),
  duration_months, evaluation_criteria (sum of weights = 100),
  requirements (≥1), AND the user has explicitly confirmed
  ("yes" / "go ahead" / "create it" / "loo see ära" / "tee see").
  Otherwise plan_ready=false.
- When asking for confirmation, ECHO BACK a structured summary so the
  user can spot misreadings before committing:
    "Here's what I'll create:
       • Title: Hospital MRI scanner
       • Category: healthcare, CPV 33
       • Budget: €250,000 ex-VAT
       • Duration: 60 months
       • Procedure: open (EU threshold)
       • Criteria: Price 60% / Quality 40%
       • Requirements: 4 (no tax debt, ≥3 refs, ISO 13485, ...)
       • Submission deadline: 35 days
     Should I create the plan now?"
- When plan_ready=false, set plan_missing_field to the single next thing
  to ask (per the order above), and write plan_question as a friendly
  one-line question **IN THE SAME LANGUAGE AS THE LATEST USER MESSAGE**.
- If the user later says "go ahead" / "yes" / "create it" /
  "tee see ära" / "loo plaan ära" — set plan_ready=true.
- NEVER ask multiple questions in plan_question; one focused question
  per turn.

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
- "rfp_draft": user asks to DRAFT a tender / RFP document for review (no DB persistence yet) — triggers AI-powered RFP generation as a canvas artifact only. Set rfp_description to the user's procurement need description.
- "create_plan": user asks to CREATE / START / SET UP a procurement plan in the buyer's workspace ("create a tender for...", "new procurement for...", "start a hange for..."). Persists the plan into /procurements with a 5-step workflow. Set rfp_description to the user's procurement need description and extract estimated_value if mentioned.
- "legal_lookup": user asks for the exact text of an act, a current threshold value, or an authoritative procedural rule ("what does RHS §85 say?", "what's the EU threshold for 2026?", "is open procedure mandatory below 30k?", "tsiteer mulle riigihangete seaduse"). Triggers a fetch from riigiteataja.ee / EUR-Lex / fin.ee and returns a cited excerpt. Optional fields: `topic` (one of: rhs, thresholds, register), `url` (full URL on the allow-list), `question` (what to extract).

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
{"intent":"rfp_draft","needs_search":false,"country_codes":[],"industry":"security","cpv_divisions":["79"],"keywords":["security","guard"],"min_value":null,"max_value":null,"tender_id":null,"company_name":null,"search_type":"topic","rfp_description":"Security guard services at 3 government buildings"}

User: "create a procurement plan for IT support, 50,000 EUR, 2-year contract"
→ Step 1: English. Step 2: none. Step 3: IT → CPV 72. Step 4: IT support. Step 5: 50,000. Step 6: 2-year. Step 7: none.
{"intent":"create_plan","needs_search":false,"country_codes":[],"industry":"information technology","cpv_divisions":["72"],"keywords":["IT","support"],"min_value":null,"max_value":null,"estimated_value":50000,"tender_id":null,"company_name":null,"search_type":"create_plan","rfp_description":"IT support, 2-year contract, 50,000 EUR"}

User: "Start a new procurement for office cleaning, 30k for 12 months"
→ Step 1: English. Step 2: none. Step 3: cleaning → CPV 90. Step 4: cleaning. Step 5: 30,000. Step 6: 12 months. Step 7: none.
{"intent":"create_plan","needs_search":false,"country_codes":[],"industry":"cleaning","cpv_divisions":["90"],"keywords":["cleaning","office"],"min_value":null,"max_value":null,"estimated_value":30000,"tender_id":null,"company_name":null,"search_type":"create_plan","rfp_description":"Office cleaning services, 12-month contract, 30,000 EUR"}

User: "Loo uus hankeplaan IT-süsteemi hoolduseks 120 000 eurot"
→ Step 1: Estonian. Step 2: none. Step 3: IT → CPV 72. Step 4: IT system maintenance. Step 5: 120,000. Step 6: none. Step 7: none.
{"intent":"create_plan","needs_search":false,"country_codes":[],"industry":"information technology","cpv_divisions":["72"],"keywords":["IT","hooldus","süsteem"],"min_value":null,"max_value":null,"estimated_value":120000,"tender_id":null,"company_name":null,"search_type":"create_plan","rfp_description":"IT-süsteemi hooldus, 120 000 EUR"}"""

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


RESPONSE_SYSTEM_PROMPT = """You are Tendly Buyer AI, an assistant for **Estonian public-sector procurement BUYERS** (not bidders).

Your job is to help procurement officers PREPARE THEIR OWN procurements
under the Estonian Public Procurement Act (Riigihangete seadus, RHS 2017,
https://www.riigiteataja.ee/en/eli/505092017003/consolide). You help
them: draft RFPs, set fair budgets, choose the right procedure, define
evaluation criteria and qualification requirements, and benchmark
against similar past tenders.

Audience guard rails — you serve BUYERS only:
- NEVER offer "winning strategies", "competitor analysis", "win
  probabilities", or any other bidder-side framing. The user is the
  BUYER who issues tenders; they do not bid on them. If the user asks
  for bidding advice, gently redirect: "this platform is for buyers
  preparing procurements — seller-side tooling lives elsewhere".

# Estonian Public Procurement Act — quick reference (use when relevant)

## Procedure choice (by estimated value, supplies & services, EUR, ex-VAT)
- < €30,000   → simple procurement (lihthange) for SUPPLIES (and < €60,000 for WORKS)
                — minimum 10 days for tender submission, simplified rules
- < €140,000  → national open / restricted procedure (RHS §48–§55)
- ≥ €140,000  → EU-threshold procedure for central government (RHS §14)
                — supplies & services. ≥ €216,000 for sub-central
                contracting authorities. Works EU threshold: €5,538,000.
- Always justify the procedure choice in writing.

## Procedure types (always recommend OPEN unless restriction is justified)
- Open (avatud) — RHS §48 — default for transparency. Use when no
  pre-qualification needed.
- Restricted (piiratud) — RHS §50 — when bidder universe is very large;
  pre-qualifies a shortlist of ≥5 candidates.
- Competitive negotiation (konkurentsipõhine läbirääkimistega menetlus)
  — RHS §52 — only when open/restricted unsuitable (complex, innovation,
  cannot specify upfront).
- Competitive dialogue — RHS §54 — for complex contracts where the
  authority can't define a solution.
- Innovation partnership — RHS §57.

## Minimum deadlines (RHS §93 and EU directives)
- Open procedure (national): ≥ 20 days for tender submission
- Open procedure (EU): ≥ 35 days, can drop to 30 with electronic submission
- Restricted procedure: ≥ 30 days for requests to participate, then
  ≥ 30 days (national) / 25 days (EU) for tenders
- Simple procurement: ≥ 10 days
- Always extend if the documents are amended materially.

## Evaluation criteria (RHS §85)
- "Most economically advantageous tender" (MEAT) is the default.
- Allowed criteria: price, quality, technical merit, environmental
  impact, social criteria, life-cycle cost, post-sale support,
  delivery time, organisation/qualifications/experience of personnel
  assigned (only when staff matter to performance).
- Each non-price criterion needs a stated weight in % and an
  objective scoring rule — DO NOT use vague language ("better is
  better"). Recommend explicit weights summing to 100%.
- Pure lowest-price is allowed but not encouraged: requires that all
  other terms are exhaustively specified.

## Mandatory exclusion grounds (RHS §95)
- Convictions for corruption, fraud, money laundering, terrorism,
  trafficking, child labour
- Tax / social-security debt > €1,500 outstanding
- Bankruptcy / liquidation / insolvency
- Misrepresentation in earlier procurements
The buyer MUST require a sworn statement and check the registry
(äriregister, EMTA tax debt) before contract signature.

## Qualification criteria (RHS §98–§101) — must be PROPORTIONATE
- Economic standing: turnover requirement ≤ 2× contract value
- Technical capacity: similar reference contracts (typically 2–3 in
  past 3 years for services, 5 years for works) — relevance > volume
- Avoid over-specifying: a small municipal cleaning contract should
  not require €10M turnover

## Tender documents that MUST be attached
- Contract notice (hanketeade)
- Technical specification / scope (tehniline kirjeldus)
- Draft contract (lepingu projekt)
- Form for tender submission (pakkumuse vorm)
- Evaluation methodology
- ESPD form for self-declaration
- Submission via riigihanked.riik.ee (mandatory e-procurement above
  certain thresholds)

## Strategic principles (Government 2023 declaration)
Recommend buyers consider: green/sustainable criteria, innovation,
SME-friendly lot sizes, social responsibility, security risks,
proportionality.

# Language rules
- Respond in the same language the user writes in. Estonian → Estonian,
  French → French, Latvian → Latvian, Lithuanian → Lithuanian, Polish
  → Polish. Default to English if unclear.

# Response guidelines
- Use markdown formatting. Be concise but insightful.
- When tender results are shown, treat them as REFERENCE MATERIAL the
  buyer can learn from when drafting their own. Highlight: how many
  comparable past tenders found, value ranges, common CPV codes, what
  evaluation criteria peers used, typical contract durations, useful
  patterns for the user's own draft (price/quality weighting,
  qualification thresholds).
- When you give legal/procedural advice, cite the relevant RHS section
  number (e.g. "per RHS §85 you must state explicit weights"). When
  the user asks for the exact text of a section, use the legal_lookup
  tool to fetch from riigiteataja.ee and quote it accurately.
- Do NOT list individual tenders in the text — the UI renders them as
  cards separately.
- If no tenders found, explain possible reasons and suggest 2-3
  alternative benchmarking searches.
- End with a "**Try also:**" section with 2-3 contextually relevant
  follow-up actions, EXCEPT in multi-turn plan creation gathering mode.
- Do NOT fabricate tender data. Only reference tenders from the
  provided search results.
- Format currency with symbols (€ for EUR). Highlight deadlines."""

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

    def create_conversation(self, user_email=None, title=None) -> str:
        cid = str(uuid.uuid4())
        session = get_tendly_session()
        try:
            ctx = ChatContext(
                id=str(uuid.uuid4()),
                conversation_id=cid,
                user_email=user_email,
                title=title or "New conversation",
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

    def get_conversation_artifacts(self, conversation_id: str) -> list:
        """Return all artifacts for a conversation, oldest first."""
        session = get_tendly_session()
        try:
            ctx = session.query(ChatContext).filter(
                ChatContext.conversation_id == conversation_id
            ).first()
            return list(ctx.artifacts or []) if ctx else []
        finally:
            session.close()

    # ======================================================================
    # Tool dispatch
    # ======================================================================

    def _is_plan_gathering_in_progress(self, conv_messages: List[Dict]) -> bool:
        """Detect whether the assistant is currently mid-way through a
        plan-creation gathering conversation.

        Heuristic: look at the most recent assistant turn. If it reads
        like a "Got it — <fields>... <question>?" gathering reply
        (no plan was persisted yet), we are still gathering. We also
        accept the explicit `[GATHERING]` marker the response generator
        adds. Returns False once the create_plan artifact has shipped
        because then we move into the documents phase, not gathering."""
        if not conv_messages:
            return False
        # Walk back from the most recent message, skipping the user turn
        # that just landed (the one we're about to analyze).
        for m in reversed(conv_messages):
            role = m.get("role")
            if role != "assistant":
                continue
            content = (m.get("content") or "").strip()
            if not content:
                return False
            # If the assistant already told the user the plan was created,
            # we are NOT gathering anymore (we moved to docs phase).
            lower = content.lower()
            if "/procurements/" in lower and (
                "has been created" in lower
                or "i created" in lower
                or "is now in your workspace" in lower
                or "open it at /procurements/" in lower
            ):
                return False
            # Gathering signals: the prompt template makes the assistant
            # start with "Got it" or echo plan fields, and end with a
            # follow-up question. We just need to know it ended with a
            # question and was a single-turn confirmation of fields.
            ends_with_question = content.rstrip().endswith("?")
            looks_like_gathering = (
                content.lower().startswith("got it")
                or "estimated value" in lower
                or "duration of" in lower and "months" in lower
                or "submission deadline" in lower
            )
            return bool(ends_with_question and looks_like_gathering)
        return False

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

        # Create procurement plan — persists a row in tendly.procurement_plans
        if intent == "create_plan":
            tool = tool_registry.get("create_plan")
            if tool:
                return tool.execute(query_info, {"chat_service": self})

        # Legal lookup — fetch an excerpt from riigiteataja.ee / EUR-Lex /
        # fin.ee and quote it back with a citation
        if intent == "legal_lookup":
            tool = tool_registry.get("legal_lookup")
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
        self, conversation_id: str, user_message: str,
        user_email: Optional[str] = None,
        ui_language: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Process a user message and yield SSE-formatted chunks.

        ui_language is the authoritative UI-picker / cookie language code
        (en/et/lv/lt/pl/fr). When set, _generate_response uses it as a hard
        constraint so a single ambiguous word like "Hi" doesn't drift to
        whatever language the LLM defaults to."""
        # Stash for tools that need to know who's logged in (e.g. create_plan
        # which writes to procurement_plans scoped by org_id = user_email).
        self._current_user_email = user_email
        self._current_ui_language = ui_language
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
                    user_email=user_email or "",
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
            # Pass conversation history so multi-turn plan creation works:
            # the user can give title/budget/category across separate turns.
            query_info = await self._analyze_query(user_message, history=conv_messages[:-1])
            intent = query_info.get("intent", "search")

            # Defensive guard: if a plan-creation gathering loop is active
            # (the previous assistant message asked a follow-up question
            # for plan_draft), force intent back to create_plan even if
            # the LLM analyzer drifted to search/general_knowledge on a
            # short reply like "yes use the standards" / "you make them".
            # This prevents the gathering thread from being abandoned mid-way.
            if intent != "create_plan" and self._is_plan_gathering_in_progress(conv_messages):
                intent = "create_plan"
                query_info["intent"] = "create_plan"
                query_info["needs_search"] = False
                # plan_ready stays whatever the analyzer decided so we don't
                # accidentally force-persist a half-finished plan.

            # --- Stage 2: Tool dispatch ---
            tool_result = ToolResult()
            # Intents that always need a tool to run, even when no DB search
            # is required (the LLM sets needs_search=false for these because
            # they don't filter the tenders table).
            artifact_intents = {
                "rfp_draft", "create_plan", "tender_compare",
                "risk_analysis", "gap_analysis", "requirements",
                "price_benchmark", "legal_lookup",
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
                ui_language=ui_language,
            )

            # Emit response text
            yield _sse_event("text", {"content": response_text})

            # Store assistant message — also include the artifact reference
            # (type + id + tender_id) so when the page is reloaded later, we
            # can render a "Reopen ..." button that brings the canvas back.
            # Without this the artifact is unreachable after navigation.
            assistant_msg = {
                "role": "assistant",
                "content": response_text,
                "tenders": tool_result.tenders,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if tool_result.artifact_type and tool_result.artifact_id:
                assistant_msg["artifact"] = {
                    "type": tool_result.artifact_type,
                    "id": tool_result.artifact_id,
                    "tender_id": (tool_result.artifact_data or {}).get("id") if tool_result.artifact_data else None,
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
    async def process_message_sync(self, conversation_id: str, user_message: str,
                                    user_email: Optional[str] = None,
                                    ui_language: Optional[str] = None) -> Dict:
        """Non-streaming variant that collects the full response."""
        response_text = ""
        tenders = []
        artifact = None
        event_type = None
        async for chunk in self.process_message(conversation_id, user_message,
                                                 user_email=user_email,
                                                 ui_language=ui_language):
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

    async def _analyze_query(self, user_message: str, history: Optional[List[Dict]] = None) -> Dict:
        """Use Gemini to extract structured search parameters from the user query.

        When `history` is provided (recent conversation messages), the analyzer
        can stitch together info across turns — important for multi-turn
        plan creation where the user may give the title, value, and category
        in separate messages."""
        # If we have history, prepend a compact transcript to the user message
        # so Gemini sees prior context. Cap to last 6 messages to keep prompts
        # cheap.
        if history:
            recent = history[-6:]
            transcript = "\n".join(
                f"{m.get('role','user').upper()}: {m.get('content','')[:400]}"
                for m in recent if m.get("content")
            )
            framed = (
                "Recent conversation transcript (most recent last):\n"
                f"{transcript}\n\n"
                f"Latest user message: {user_message}\n\n"
                "When classifying, consider the transcript: e.g. if the user "
                "earlier asked to create a plan and is now answering your "
                "follow-up question (giving a title or budget), still classify "
                "as `create_plan` and merge the new field into plan_draft."
            )
        else:
            framed = user_message

        cache_name = _get_or_create_query_cache(self.llm)
        if cache_name:
            result = await self.llm.chat_completion_async(
                messages=[{"role": "user", "content": framed}],
                system_prompt=None,
                cached_content=cache_name,
                temperature=0.1,
            )
        else:
            result = await self.llm.chat_completion_async(
                messages=[{"role": "user", "content": framed}],
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
        ui_language: Optional[str] = None,
    ) -> str:
        """Generate a natural-language response using Gemini.

        ui_language is the UI-picker code (en/et/lv/lt/pl/fr). When the
        user's message is too short to confidently detect a language
        (e.g. "Hi", "ok", "yes"), we use ui_language as the authoritative
        signal instead of letting the LLM drift toward whatever language
        appears in the system prompt's RHS terminology."""

        # Map picker code → human-readable name for the prompt
        _LANG_NAME = {
            "en": "English", "et": "Estonian", "lv": "Latvian",
            "lt": "Lithuanian", "pl": "Polish", "fr": "French",
        }
        ui_lang_name = _LANG_NAME.get((ui_language or "").lower(), None)

        if intent == "company_search":
            sys_prompt = COMPANY_INTELLIGENCE_PROMPT
        elif intent == "market_intelligence":
            sys_prompt = MARKET_INTELLIGENCE_PROMPT
        else:
            sys_prompt = RESPONSE_SYSTEM_PROMPT

        # Hard language directive at the TOP of the prompt — overrides any
        # language inference from the user message or RHS terminology in
        # later sections. Without this, a one-word "Hi" with the picker on
        # English drifted to Estonian because the prompt is full of
        # Estonian legal terms.
        if ui_lang_name:
            sys_prompt = (
                f"=== ABSOLUTE LANGUAGE RULE ===\n"
                f"YOU MUST WRITE YOUR ENTIRE REPLY IN {ui_lang_name.upper()}.\n"
                f"The user has set their interface language to "
                f"{ui_lang_name}. Reply in {ui_lang_name} regardless of "
                f"what language Estonian legal terms (RHS, Riigihangete "
                f"seadus, hange, hankemenetlus) appear in this prompt — "
                f"those are reference vocabulary you may CITE in "
                f"{ui_lang_name} prose, NOT a directive to switch language. "
                f"If the user's message is in a clearly different language, "
                f"prefer that language; otherwise default to "
                f"{ui_lang_name}. NEVER answer a short ambiguous greeting "
                f"like 'Hi' / 'Hello' / 'Tere' / 'Salut' in a language "
                f"other than {ui_lang_name}.\n"
                f"===\n\n"
            ) + sys_prompt

        # Detect "gathering" phase: create_plan didn't yet have enough info
        # and is asking the user a follow-up question.
        gathering_state = None
        if intent == "create_plan" and not artifact_type and artifact_summary:
            try:
                parsed = json.loads(artifact_summary)
                if isinstance(parsed, dict) and parsed.get("phase") == "gathering":
                    gathering_state = parsed
            except Exception:
                pass

        # When an analytical tool produced an artifact, tell the model so it
        # writes a short pointer to the canvas instead of generic deflection
        # text like "I cannot draft an RFP". The canvas already holds the
        # full result; the chat reply just needs to summarise + redirect.
        if artifact_type == "create_plan":
            # Post-creation: shift the agent into "documents preparation"
            # phase. Don't open canvas talk — give a clear next-steps
            # checklist focused on the 4 standard RHS docs and offer to
            # generate any the user doesn't have.
            sys_prompt = sys_prompt + (
                "\n\n=== PLAN CREATED — DOCUMENTS PHASE ===\n"
                "The procurement plan has just been persisted to the user's "
                "workspace. Your job NOW is to walk the buyer through "
                "preparing the four standard RHS 2017 tender documents. "
                "DO NOT add a 'Try also' section in this turn.\n\n"
                "**LANGUAGE:** match the user's latest message language.\n\n"
                "**OUTPUT FORMAT (must follow exactly):**\n"
                "1) One sentence confirming the plan was created, including "
                "the title, value (€), duration and procurement method "
                "(from the artifact data below). End with a link to the "
                "plan: 'Open it at /procurements/{plan_id}'.\n"
                "2) A blank line.\n"
                "3) A heading 'Next: prepare the 4 tender documents' (or "
                "the equivalent in the user's language) followed by a "
                "bulleted checklist of EXACTLY these four items, each on "
                "its own line, in this order:\n"
                "   • Technical specification (tehniline kirjeldus) — "
                "   describes what is being procured, scope, performance "
                "   requirements.\n"
                "   • Draft contract (lepingu kavand) — payment terms, "
                "   penalties, performance guarantees.\n"
                "   • Evaluation methodology (hindamismetoodika) — how "
                "   each evaluation criterion is scored.\n"
                "   • ESPD form / own-declaration (Euroopa ühtne "
                "   hankedokument) — qualification self-declaration.\n"
                "4) A blank line.\n"
                "5) A short paragraph telling the user they have two "
                "options for each document:\n"
                "   - Upload an existing file via the paperclip icon "
                "   below, or open the plan and use 'Upload Document'.\n"
                "   - Ask me here to generate it (e.g. 'draft the "
                "   technical specification', 'generate the contract', "
                "   'propose evaluation methodology').\n"
                "6) End with exactly ONE focused question: 'Which would "
                "you like to start with?' (or the equivalent in the user's "
                "language).\n\n"
                "**HARD RULES:**\n"
                " - Use the artifact data below for the title / value / "
                "method — never invent values.\n"
                " - Keep it under ~180 words total.\n"
                " - Do NOT mention 'canvas panel' here — the artifact for "
                "create_plan does not open a canvas.\n"
                " - Do NOT add a 'Try also' section.\n"
            )
        elif artifact_type:
            sys_prompt = sys_prompt + (
                f"\n\nIMPORTANT: A specialised '{artifact_type}' tool has "
                "already run successfully and the full result is rendered in "
                "the canvas panel on the right (which has Copy and Download "
                "buttons). You MUST NOT say you cannot perform this task or "
                "that you lack this capability — the tool already did it.\n\n"
                "**Reply structure (consistent across all languages):**\n"
                "1) ONE short opening sentence confirming what was produced "
                "and naming it (use the artifact summary below).\n"
                "2) A brief inline preview — for an RFP/document draft this "
                "means the title plus 3-6 of the most important bullet points "
                "(scope highlights, top evaluation criteria, key qualification "
                "requirements). Use compact bullet lists, not full prose. The "
                "user must be able to see the substance directly in chat, not "
                "just a pointer to the canvas.\n"
                "3) ONE short line telling them the full document is open in "
                "the canvas with Copy and Download buttons.\n"
                "4) A 'Try also:' section with 2-3 contextually relevant "
                "follow-ups (e.g. 'tighten the scope', 'add an SLA clause', "
                "'benchmark this budget').\n\n"
                "**This format is identical regardless of UI language — only "
                "the words are translated.** Keep total length 120-200 words."
            )
        elif gathering_state:
            # Multi-turn plan creation: agent is in info-gathering mode.
            sys_prompt = sys_prompt + (
                "\n\n=== MULTI-TURN PLAN CREATION MODE ===\n"
                "You are gathering details for a procurement plan. The user "
                "has not yet given enough info to create it.\n\n"
                "**LANGUAGE: REPLY IN THE EXACT LANGUAGE OF THE LATEST USER "
                "MESSAGE.** If the latest user message is in English, reply "
                "in English. If Estonian, reply in Estonian. Do NOT default "
                "to Estonian just because earlier messages were Estonian. "
                "Detect language from THIS message only.\n\n"
                "**OUTPUT FORMAT (must follow exactly):**\n"
                "1) One short conversational sentence acknowledging what "
                "you have so far (e.g. 'Got it — IT support, €50,000.'). "
                "Write this naturally in the user's language. DO NOT include "
                "raw JSON, the literal words 'Gathered so far', "
                "'Missing field', 'plan_draft', or 'Question to ask' — those "
                "are internal labels for you only.\n"
                "2) A blank line.\n"
                "3) Exactly ONE follow-up question, written naturally as a "
                "human would phrase it (the `Question to ask` below is just "
                "a hint — rewrite it in the user's language and tone).\n\n"
                "**HARD RULES:**\n"
                " - NEVER paste the JSON or label strings into the chat.\n"
                " - NEVER claim the plan has been created — it hasn't yet.\n"
                " - NEVER add a 'Try also' section in this mode.\n"
                " - NEVER ask multiple questions in one turn.\n\n"
                "GOOD example reply (English user):\n"
                "  Got it — IT support, €50,000 for 2 years.\n\n"
                "  What category does this fall under (IT, services, ...)?\n\n"
                "BAD example reply (don't do this):\n"
                "  Käesolev tehing on planeerimisel.\n"
                "  Senini kogutud info: {\"description\": \"...\"}\n"
                "  Vajalik väli: title\n"
                "  Küsimus: ..."
            )

        context_parts = [f"User query: {user_message}"]
        context_parts.append(f"Detected intent: {intent}")
        if gathering_state:
            # Internal hints — the LLM must NOT echo these labels verbatim.
            context_parts.append(
                f"\n[INTERNAL — do not paste this text into the reply.]\n"
                f"  Plan-draft so far: {json.dumps(gathering_state.get('gathered', {}), default=str)}\n"
                f"  Missing field hint: {gathering_state.get('missing','?')}\n"
                f"  Suggested question (rewrite in user's language): {gathering_state.get('question','?')}"
            )
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

        # Pull out any system primer messages from the conversation history
        # and inject them in full into sys_prompt. We do this because:
        #   1) System primers contain the linked plan context (when the user
        #      clicked "Ask AI" on a procurement plan), which must remain in
        #      view for the entire conversation, not just the first 6 turns.
        #   2) The recent-history block truncates each message to 300 chars,
        #      which would drop most of a plan primer (criteria, requirements).
        system_primers = [
            m.get("content", "") for m in conversation_history
            if m.get("role") == "system" and m.get("content")
        ]
        if system_primers:
            sys_prompt = (
                sys_prompt
                + "\n\n=== ACTIVE PLAN CONTEXT (always honor this) ===\n"
                + "\n\n".join(system_primers)
            )

        # Build the rolling recent-history block from user/assistant turns
        # only. System primers were already injected above.
        recent = [
            m for m in conversation_history[-7:-1]
            if m.get("role") in ("user", "assistant")
        ]
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
