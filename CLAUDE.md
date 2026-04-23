# CLAUDE.md

## Project Overview

**Tendly Buyer** is an AI-powered procurement buyer portal for public sector procurement officers. It provides a multi-page application with dashboard, procurement plan management, document management, registry browser, AI chat, and team management.

Built with FastHTML + HTMX, it connects to Tendly's production PostgreSQL database (read-only for tender data, read-write for buyer-specific tables) and uses Gemini AI for natural language query understanding and response generation.

### Target Users (Estonian public sector)
- **Valdkonna juht** (Domain Lead) — reviews procurement needs, market research
- **Hankejuht** (Procurement Manager) — reviews procurement plans
- **Juhatus** (Board) — approves budgets and plans
- **Valdkonna spetsialist** (Domain Specialist) — prepares base documents, technical descriptions

### Procurement Workflow (5 steps)
1. Vajaduse ülevaade (Need review) — Domain Lead
2. Turu-uuring (Market research) — Domain Lead + AI
3. Hankeplaani ülevaade (Plan review) — Procurement Manager
4. Eelarve kinnitamine (Budget approval) — Board
5. Dokumentide koostamine (Document preparation) — Domain Specialist + AI

---

## Quick Start

```bash
./run.sh    # Creates venv, installs deps, starts on http://localhost:5002
```

### Environment Variables (.env)

```
USE_GCP_CLOUD_SQL=true
CLOUD_SQL_INSTANCE=scenic-impact-476918-n6:europe-north1:tendly-prod
DB_NAME=tendly_prod
DB_USER=tendly_admin
DB_PASSWORD=<password>
GOOGLE_APPLICATION_CREDENTIALS_JSON=<service-account-json>
TOGETHER_API_KEY=<key>
GEMINI_API_KEY=<key>
```

---

## Architecture

```
app.py              → Main FastHTML app (CSS, JS, Python components, routes)
chat_service.py     → Query understanding, DB search, SSE streaming orchestration
database.py         → SQLAlchemy models, Cloud SQL connection (read-only)
llm_client.py       → Unified LLM client (Together AI/Kimi, Gemini, xAI Grok)
run.sh              → Dev server startup script
requirements.txt    → Python dependencies
```

### app.py Structure (~2076 lines, single-file)

The app is a monolithic single-file FastHTML application containing:

1. **CSS_STYLES** (~800 lines) — Complete CSS including layout, sidebar, messages, tender list, detail panel, welcome screen, suggestion chips, responsive breakpoints
2. **JS_CODE** (~500 lines) — Client-side JS for SSE streaming, DOM manipulation, tender card rendering, detail panel, suggestion chips, markdown rendering
3. **Python Components** (~400 lines) — FastHTML component functions (`welcome_screen()`, `chat_page()`, `message_component()`, `tender_cards_component()`, `tender_detail_panel()`)
4. **Routes** (~100 lines) — API endpoints

### Key Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Welcome/home page |
| `/c/{conversation_id}` | GET | Load existing conversation |
| `/api/chat` | POST | Send message, returns SSE stream |
| `/api/conversations` | GET | List all conversations |
| `/api/conversations/new` | POST | Create new conversation |
| `/api/conversations/{id}` | DELETE | Delete conversation |
| `/api/tender/{tender_id}` | GET | Get tender detail panel (HTML fragment) |

### SSE Event Types

The `/api/chat` endpoint streams these events:
- `status` — Thinking/searching indicators
- `chunk` — AI response text (streamed incrementally)
- `tenders` — JSON array of matching tender cards
- `done` — Stream complete, includes `conversation_id`
- `error` — Error message

### Data Flow

```
User query → /api/chat (POST)
  → chat_service.process_message()
    → LLM: Understand query (extract country, keywords, filters)
    → SQLAlchemy: Search tenders in PostgreSQL
    → LLM: Generate analytical summary
    → SSE stream: status → chunks → tenders → done
```

---

## Database

**Read-only access** to the shared Tendly production database via GCP Cloud SQL.

### Models (database.py)

- `Tender` — Core tender data (name, authority, status, type, CPV, country)
- `TenderDetail` — Extended info (value, deadline, description, AI requirements, NUTS)
- `TenderResult` — Winner info, contract cost, offer count
- `TenderDocuments` — Attached documents with AI summaries
- `TenderQualityScore` — AI quality scoring (overall + per-language analysis JSON)
- `TenderEvaluationCriteria` — Evaluation criteria with weights

### Critical Rules

- **NEVER write to the database** — read-only access
- **NEVER alter schema** — no CREATE/ALTER/DROP
- Models must match the actual prod schema exactly
- `submission_deadline` is the key column for active tenders (`> now()`)

### Multi-language Fields

Most models have language-suffixed columns: `_en`, `_et`, `_lv`, `_lt`, `_pl`, `_fr`. Always use `_en` as the primary fallback for display.

---

## UI/UX Design

The UI follows ChatGPT/Claude.ai-level design patterns:

### Key Design Decisions
- **Compact tender list** — Single-column rows (flag + title + org + value + deadline), not a card grid
- **Progressive disclosure** — Show 5 tenders initially, "View all X results" to expand
- **Suggestion chips** — "Try also:" from AI responses parsed into clickable pill buttons that auto-submit
- **Detail panel** — Fixed position slide-in from right with backdrop overlay, closeable via X or Escape
- **No emojis in UI components** — SVG icons only (country flags from data are OK)
- **Off-white background** (#f9fafb), white cards, subtle shadows

### CSS Conventions
- Primary blue: `#2563eb`, purple accent: `#7c3aed`
- System font stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, ...`
- Subtle shadows: `0 1px 3px rgba(0,0,0,0.06)`
- Smooth transitions on interactive elements

### JS Conventions
- All DOM manipulation via `document.createElement()` — no innerHTML with untrusted content
- Markdown rendered via `renderMarkdownToFragment()` (DOM-safe)
- `qs()` helper for `document.querySelector()`
- Global functions exposed via `window.showTenderDetail`, `window.closeDetailPanel`

---

## LLM Providers

Configured in `llm_client.py`:

| Provider | Model | Use Case |
|----------|-------|----------|
| Together AI | Kimi (moonshotai/kimi-k2-instruct) | Query understanding, response generation |
| Google Gemini | gemini-2.5-flash | Fallback / alternative |
| xAI Grok | grok-3-mini-fast | Fallback / alternative |

The chat service uses Together AI (Kimi) by default for both query parsing (structured JSON output) and response generation (analytical summaries).

---

## Development Notes

### Testing
- Server runs on port 5002 (avoids conflict with main Tendly app on 5001)
- Test with Playwright using Chrome debug profile on port 9222
- Delete screenshots after testing

### Common Pitfalls
- `/api/tender/{id}` must return HTML fragment (via `HTMLResponse(to_xml(panel))`), not a full page
- The `TenderQualityScore` model does NOT have a generic `analysis` column — only language-specific ones (`analysis_en`, `analysis_et`, etc.)
- `TenderEvaluationCriteria.id` is `String` (VARCHAR), not Integer
- `TenderEvaluationCriteria` uses `weight_percentage`, not `weight`

### GCP Infrastructure
- **Project ID**: `scenic-impact-476918-n6`
- **Cloud SQL Instance**: `scenic-impact-476918-n6:europe-north1:tendly-prod`
- **Region**: `europe-north1`
