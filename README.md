# Tendly Buyer - AI-Powered Procurement Portal

Multi-page procurement buyer portal for public sector procurement officers. Features dashboard, procurement plan management with 5-step workflow, document management, AI chat assistant, procurement registry browser, and team management.

**Target users**: Estonian public sector — valdkonna juhid (domain leads), hankejuhid (procurement managers), juhatus (board), valdkonna spetsialistid (domain specialists).

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

## Architecture

```
app.py              -> Main FastHTML app (routes, middleware)
chat_service.py     -> Query understanding, DB search, SSE streaming
database.py         -> SQLAlchemy models, Cloud SQL connection (read-only)
llm_client.py       -> Unified LLM client (Together AI/Kimi, Gemini, Grok)
i18n.py             -> Internationalization (6 languages)
routes/             -> API and page routes
components/         -> UI components (tender detail panel, etc.)
static/             -> CSS, JS, guide screenshots
tests/              -> Test suite, video/screenshot capture
```

### SSE Streaming

The `/api/chat` endpoint streams Server-Sent Events:
- `status` - Thinking/searching indicators
- `chunk` - AI response text (streamed word-by-word)
- `tenders` - JSON array of matching tender cards
- `done` - Stream complete with conversation ID
- `error` - Error message

### Data Flow

```
User query -> /api/chat (POST)
  -> chat_service.process_message()
    -> LLM: Understand query (extract country, keywords, filters)
    -> SQLAlchemy: Search tenders in PostgreSQL
    -> LLM: Generate analytical summary
    -> SSE stream: status -> chunks -> tenders -> done
```

## Testing

### Run Test Suite

```bash
python tests/test_suite.py                # Full suite against chat.tendly.eu
python tests/test_suite.py --local        # Against localhost:5002
python tests/test_suite.py --skip-browser # Skip Playwright/HTTP tests
```

The test suite covers 27 tests across 8 categories:
- DB connection and schema validation
- Chat service (create, search, detail, delete)
- LLM client integration
- Database model field verification
- Search queries (by country, keyword, deadline)
- i18n language support
- API endpoint testing (HTTP)
- Full Playwright UI walkthrough with SSE streaming

Results are written to `test-results/*.json` with `test-results/test_summary.json` as the summary.

### Capture Guide Screenshots

```bash
python tests/capture_guide.py             # Against chat.tendly.eu
python tests/capture_guide.py --local     # Against localhost:5002
```

Saves 10 screenshots to `static/guide/` covering every key feature.

### Generate Demo Video & GIF

```bash
python tests/capture_video.py             # Against chat.tendly.eu
python tests/capture_video.py --local     # Against localhost:5002
```

Walks through the full product flow, captures frames, and generates:
- `docs/demo_video.mp4` - 30-second MP4 demo
- `docs/demo_video.gif` - Animated GIF for README

## Supported Countries

| Flag | Country | Currency |
|------|---------|----------|
| EE | Estonia | EUR |
| GB | United Kingdom | GBP |
| LV | Latvia | EUR |
| PL | Poland | PLN |
| LT | Lithuania | EUR |
| FR | France | EUR |

## LLM Providers

| Provider | Model | Use Case |
|----------|-------|----------|
| Together AI | Kimi (moonshotai/kimi-k2-instruct) | Query understanding, response generation |
| Google Gemini | gemini-2.5-flash | Fallback |
| xAI Grok | grok-3-mini-fast | Fallback |
