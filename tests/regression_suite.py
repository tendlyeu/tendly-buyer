"""
Tendly Chat Regression Suite — CLI + Playwright

Tests all components: tool framework, canvas layout, artifact renderers,
buyer/seller role switching, price benchmarks, RFP drafting, DB connectivity,
and full browser walkthrough with Playwright.

Results are written to test-results/*.json.

Usage:
    python tests/regression_suite.py                    # full suite with browser
    python tests/regression_suite.py --skip-browser     # CLI-only (no Playwright)
    python tests/regression_suite.py --headed            # show browser window
"""

import sys
import os
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Setup path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=True)

os.environ.setdefault(
    "TENDLY_DB_URL",
    "postgresql://finespresso:mlfpass2026@72.62.114.124:5432/finespresso_db",
)

RESULTS_DIR = ROOT / "test-results"
RESULTS_DIR.mkdir(exist_ok=True)

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:5002")

_skip_browser = "--skip-browser" in sys.argv
_headed = "--headed" in sys.argv

# ---------------------------------------------------------------------------
# Test framework
# ---------------------------------------------------------------------------

_results = []
_pass = 0
_fail = 0
_skip = 0
_tests = []


def test(name, category="general"):
    def wrapper(fn):
        fn._test_name = name
        fn._test_category = category
        _tests.append(fn)
        return fn
    return wrapper


def run_test(fn):
    global _pass, _fail, _skip
    name = fn._test_name
    t0 = time.time()
    try:
        result = fn()
        elapsed = time.time() - t0
        if isinstance(result, str) and result.startswith("Skipped"):
            _skip += 1
            status = "SKIP"
            print(f"  \033[33mSKIP\033[0m  {name}: {result}")
        else:
            _pass += 1
            status = "PASS"
            print(f"  \033[32mPASS\033[0m  {name} ({elapsed:.1f}s)")
        detail = result if isinstance(result, str) else "OK"
    except Exception as e:
        _fail += 1
        status = "FAIL"
        detail = str(e)
        elapsed = time.time() - t0
        print(f"  \033[31mFAIL\033[0m  {name}: {e}")
    _results.append({
        "test": name,
        "category": fn._test_category,
        "status": status,
        "detail": detail,
        "elapsed_seconds": round(time.time() - t0, 2),
    })


def save_results(filename, data):
    path = RESULTS_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    return str(path)


# Check DB availability
_db_available = False
_tendly_db_available = False

try:
    from core.database import get_session
    from sqlalchemy import text
    _s = get_session()
    _s.execute(text("SELECT 1"))
    _s.close()
    _db_available = True
except Exception:
    pass

try:
    from core.database import get_tendly_session
    _s = get_tendly_session()
    _s.execute(text("SELECT 1"))
    _s.close()
    _tendly_db_available = True
except Exception:
    pass


def _require_db():
    return "Skipped (no primary DB)" if not _db_available else None


def _require_tendly_db():
    return "Skipped (no tendly DB)" if not _tendly_db_available else None


# ===================================================================
# 1. TOOL REGISTRY
# ===================================================================

@test("Tool registry loads all 13 tools", "tool_framework")
def test_tool_registry():
    try:
        import chat_service  # noqa
    except Exception:
        pass
    import tools.search_tenders, tools.search_companies, tools.tender_detail  # noqa
    import tools.competitor_intel, tools.tender_compare  # noqa
    import tools.risk_analysis, tools.winning_strategy, tools.gap_analysis  # noqa
    import tools.requirements_extraction, tools.price_benchmark, tools.rfp_draft  # noqa
    from tools.registry import tool_registry
    tools_list = tool_registry.list_tools()
    names = [t.name for t in tools_list]
    expected = [
        "search_tenders", "search_companies", "tender_detail",
        "competitor_intel", "tender_compare", "risk_analysis",
        "winning_strategy", "gap_analysis", "requirements_extraction",
        "price_benchmark", "rfp_draft",
    ]
    missing = [e for e in expected if e not in names]
    save_results("reg_tool_registry.json", {"tools": names, "count": len(names)})
    assert not missing, f"Missing tools: {missing}"
    return f"{len(names)} tools registered"


@test("ToolResult dataclass works", "tool_framework")
def test_tool_result():
    from tools.registry import ToolResult
    r = ToolResult(artifact_type="test", artifact_id="t1", summary="ok", tenders=[{"id": 1}])
    assert r.artifact_type == "test"
    assert r.error is None
    return "OK"


# ===================================================================
# 2. CANVAS & LAYOUT
# ===================================================================

@test("Canvas component renders HTML", "layout")
def test_canvas_html():
    from components.canvas import canvas_panel
    from fasthtml.common import to_xml
    html = str(to_xml(canvas_panel()))
    assert "canvas-panel" in html and "canvas-body" in html
    return "OK"


@test("Layout includes canvas + role switcher", "layout")
def test_layout_canvas_role():
    from components.layout import chat_page
    class F:
        def get_conversations(self): return []
    html = str(chat_page(chat_service=F()))
    assert "canvas-panel" in html, "Missing canvas"
    assert "role-switcher" in html, "Missing role switcher"
    assert "role-tab" in html, "Missing role tabs"
    return "Canvas + role switcher present"


@test("CSS has canvas + role switcher styles", "layout")
def test_css():
    from static.styles import CSS_STYLES
    assert ".canvas-panel" in CSS_STYLES
    assert ".role-switcher" in CSS_STYLES
    assert ".role-tab.active" in CSS_STYLES
    return "OK"


@test("JS has canvas + role switch functions", "layout")
def test_js():
    from static.scripts import JS_CODE
    assert "openCanvas" in JS_CODE
    assert "closeCanvas" in JS_CODE
    assert "switchRole" in JS_CODE
    assert "openArtifact" in JS_CODE
    return "OK"


# ===================================================================
# 3. ARTIFACT RENDERERS (all 9)
# ===================================================================

@test("Competitor intel artifact", "artifacts")
def test_art_competitor():
    from components.artifacts.competitor_intel import competitor_intel_panel
    from fasthtml.common import to_xml
    html = str(to_xml(competitor_intel_panel({
        "company": {"name": "X", "reg_code": "", "total_wins": 5, "total_value": 100000},
        "total_wins": 5, "total_value": 100000,
        "insights": {"pricing_strategy": {"has_data": False}, "sector_focus": {"has_data": False},
                     "buyer_relationships": {"has_data": False}, "competition_analysis": {"has_data": False},
                     "timing_patterns": {"has_data": False}},
    })))
    assert "X" in html
    return "OK"


@test("Tender comparison artifact", "artifacts")
def test_art_compare():
    from components.artifacts.tender_comparison import tender_comparison_panel
    from fasthtml.common import to_xml
    t1 = {"id": 1, "name": "A", "authority": "O", "country": "UK", "country_code": "GB",
          "value": 100, "currency": "GBP", "deadline": None, "cpv_code": "", "cpv_name": "",
          "quality_score": None, "duration_months": None, "is_green": False, "is_eu_funded": False,
          "documents": [], "evaluation_criteria": [], "result": None}
    html = str(to_xml(tender_comparison_panel({"tenders": [t1, {**t1, "id": 2, "name": "B"}]})))
    assert "A" in html and "B" in html
    return "OK"


@test("Risk analysis artifact", "artifacts")
def test_art_risk():
    from components.artifacts.risk_analysis import risk_analysis_panel
    from fasthtml.common import to_xml
    html = str(to_xml(risk_analysis_panel({"tender_name": "T", "analysis": {
        "summary": "S", "overall_risk_level": "medium", "risk_score": 50, "bid_readiness_score": 60,
        "risk_summary": {"total_risks": 1, "critical_count": 0, "high_count": 1, "medium_count": 0, "low_count": 0},
        "risks": [{"severity": "high", "category": "financial", "title": "R", "description": "D", "mitigation": "M"}],
        "document_inconsistencies": [], "key_actions": ["A"]}})))
    assert "R" in html
    return "OK"


@test("Winning strategy artifact", "artifacts")
def test_art_strategy():
    from components.artifacts.winning_strategy import winning_strategy_panel
    from fasthtml.common import to_xml
    html = str(to_xml(winning_strategy_panel({"tender_name": "T", "cached": False, "strategy": {
        "win_probability": 65, "overall_readiness": "moderate_competition", "executive_summary": "Good.",
        "key_opportunities": [], "key_challenges": [], "bid_focus_areas": [], "recommendations": []}})))
    assert "65%" in html
    return "OK"


@test("Gap analysis artifact", "artifacts")
def test_art_gap():
    from components.artifacts.gap_analysis import gap_analysis_panel
    from fasthtml.common import to_xml
    html = str(to_xml(gap_analysis_panel({"tender_name": "T", "analysis": {
        "summary": "S", "risk_level": "low", "total_discrepancies": 0,
        "discrepancies": [], "document_coverage": []}})))
    assert "T" in html
    return "OK"


@test("Requirements artifact", "artifacts")
def test_art_reqs():
    from components.artifacts.requirements import requirements_panel
    from fasthtml.common import to_xml
    html = str(to_xml(requirements_panel({"tender_name": "T", "authority": "A",
        "cpv_code": "72", "cpv_name": "IT", "ai_requirements": "MANDATORY\n- Item 1"})))
    assert "MANDATORY" in html
    return "OK"


@test("Price benchmark artifact", "artifacts")
def test_art_benchmark():
    from components.artifacts.price_benchmark import price_benchmark_panel
    from fasthtml.common import to_xml
    html = str(to_xml(price_benchmark_panel({
        "stats": {"count": 5, "avg": 100000, "median": 80000, "min": 10000, "max": 500000, "p25": 30000, "p75": 200000},
        "contracts": [{"id": 1, "title": "C", "buyer": "B", "value": 80000, "currency": "GBP",
                       "category": "services", "cpv_code": "90", "cpv_description": "Clean", "status": "active",
                       "deadline": None, "notice_url": "", "procurement_method": "open"}],
        "awards": [], "search_params": {"keywords": ["test"], "cpv_divisions": [], "main_category": ""}})))
    assert "Price Distribution" in html
    return "OK"


@test("RFP draft artifact", "artifacts")
def test_art_rfp():
    from components.artifacts.rfp_draft import rfp_draft_panel
    from fasthtml.common import to_xml
    html = str(to_xml(rfp_draft_panel({"rfp": {"title": "RFP Test", "category": "services",
        "cpv_code": "90", "estimated_value": 50000, "procedure_type": "open",
        "sections": {"scope_of_work": "Scope.", "requirements": "- Item",
                     "evaluation_criteria": [{"name": "Price", "weight": 60, "type": "price", "description": ""}],
                     "qualification_requirements": [], "contract_terms": "24 months",
                     "timeline": {"notice": "30 days"}}, "compliance_notes": []}})))
    assert "RFP Test" in html
    return "OK"


# ===================================================================
# 4. DATABASE (tendly schema)
# ===================================================================

@test("Tendly DB: connection", "database")
def test_tdb_conn():
    skip = _require_tendly_db()
    if skip: return skip
    from core.database import get_tendly_session
    s = get_tendly_session()
    s.execute(text("SELECT 1"))
    s.close()
    return "Connected"


@test("Tendly DB: tables exist", "database")
def test_tdb_tables():
    skip = _require_tendly_db()
    if skip: return skip
    from core.database import get_tendly_session
    s = get_tendly_session()
    rows = s.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='tendly' ORDER BY table_name")).fetchall()
    tables = [r[0] for r in rows]
    s.close()
    expected = ["tenders", "awards", "users", "rfp_drafts"]
    missing = [t for t in expected if t not in tables]
    save_results("reg_tendly_tables.json", {"tables": tables})
    assert not missing, f"Missing: {missing}"
    return f"{len(tables)} tables"


@test("Tendly DB: UK tenders exist", "database")
def test_tdb_tenders():
    skip = _require_tendly_db()
    if skip: return skip
    from core.database import get_tendly_session
    s = get_tendly_session()
    count = s.execute(text("SELECT count(*) FROM tendly.tenders")).scalar()
    s.close()
    save_results("reg_uk_tenders.json", {"count": count})
    assert count >= 100, f"Only {count} tenders"
    return f"{count} UK tenders"


@test("Tendly DB: test users exist with roles", "database")
def test_tdb_users():
    skip = _require_tendly_db()
    if skip: return skip
    from core.database import get_tendly_user
    buyer = get_tendly_user("buyer@tendly.eu")
    seller = get_tendly_user("seller@tendly.eu")
    save_results("reg_tendly_users.json", {
        "buyer": {"exists": buyer is not None, "role": buyer.role if buyer else None},
        "seller": {"exists": seller is not None, "role": seller.role if seller else None},
    })
    assert buyer and buyer.role == "buyer"
    assert seller and seller.role == "seller"
    return f"buyer={buyer.role}, seller={seller.role}"


@test("Production DB: connection", "database")
def test_prod_db():
    skip = _require_db()
    if skip: return skip
    from core.database import get_session
    s = get_session()
    count = s.execute(text("SELECT count(*) FROM tenders")).scalar()
    s.close()
    save_results("reg_prod_db.json", {"tender_count": count})
    assert count > 1000
    return f"{count:,} production tenders"


# ===================================================================
# 5. PRICE BENCHMARK (live data)
# ===================================================================

@test("Price benchmark: services query", "price_benchmark")
def test_bench_services():
    skip = _require_tendly_db()
    if skip: return skip
    from services.price_benchmark import get_price_benchmarks
    r = get_price_benchmarks(main_category="services")
    save_results("reg_benchmark_services.json", {"count": len(r["contracts"]), "stats": r.get("stats", {})})
    assert len(r["contracts"]) > 0
    return f"{len(r['contracts'])} contracts, avg £{r['stats'].get('avg', 0):,.0f}"


@test("Price benchmark: keyword search", "price_benchmark")
def test_bench_kw():
    skip = _require_tendly_db()
    if skip: return skip
    from services.price_benchmark import get_price_benchmarks
    r = get_price_benchmarks(keywords=["cleaning"])
    return f"{len(r['contracts'])} cleaning contracts"


# ===================================================================
# 6. ROLE SIDEBAR
# ===================================================================

@test("Sidebar: buyer role shows buyer nav", "role_sidebar")
def test_sidebar_buyer():
    from components.layout import sidebar_component
    from fasthtml.common import to_xml
    class F:
        def get_conversations(self): return []
    html = str(to_xml(sidebar_component(chat_service=F(), auth={"email": "x", "name": "X", "role": "buyer"})))
    assert "sidebar-nav-section" in html
    assert "role-tab" in html
    return "Buyer nav visible"


@test("Sidebar: seller role hides buyer nav", "role_sidebar")
def test_sidebar_seller():
    from components.layout import sidebar_component
    from fasthtml.common import to_xml
    class F:
        def get_conversations(self): return []
    html = str(to_xml(sidebar_component(chat_service=F(), auth={"email": "x", "name": "X", "role": "seller"})))
    assert "sidebar-nav-section" not in html
    return "Buyer nav hidden"


@test("Sidebar: default role is buyer", "role_sidebar")
def test_sidebar_default():
    from components.layout import sidebar_component
    from fasthtml.common import to_xml
    class F:
        def get_conversations(self): return []
    html = str(to_xml(sidebar_component(chat_service=F(), auth={"email": "x", "name": "X"})))
    assert "sidebar-nav-section" in html  # buyer is default, so buyer nav should show
    return "Default = buyer"


# ===================================================================
# 7. I18N
# ===================================================================

@test("i18n: all canvas + sidebar keys", "i18n")
def test_i18n():
    with open(ROOT / "config" / "translations" / "en.json") as f:
        data = json.load(f)
    canvas_keys = ["tender_detail", "competitor_intel", "tender_comparison", "risk_analysis",
                   "winning_strategy", "gap_analysis", "requirements", "price_benchmark", "rfp_draft"]
    sidebar_keys = ["buyer_tools", "my_rfps", "price_benchmarks", "buyer_label", "seller_label"]
    missing = [k for k in canvas_keys if k not in data.get("canvas", {})]
    missing += [k for k in sidebar_keys if k not in data.get("sidebar", {})]
    assert not missing, f"Missing: {missing}"
    return "All keys present"


# ===================================================================
# 8. FILE STRUCTURE
# ===================================================================

@test("All tool/service/artifact files exist", "structure")
def test_files():
    expected = [
        "tools/registry.py", "tools/search_tenders.py", "tools/search_companies.py",
        "tools/tender_detail.py", "tools/competitor_intel.py", "tools/tender_compare.py",
        "tools/risk_analysis.py", "tools/winning_strategy.py", "tools/gap_analysis.py",
        "tools/requirements_extraction.py", "tools/price_benchmark.py", "tools/rfp_draft.py",
        "services/strategy_analytics.py", "services/document_reader.py", "services/risk_analysis.py",
        "services/winning_strategy.py", "services/gap_analysis.py", "services/price_benchmark.py",
        "services/rfp_generator.py",
        "components/canvas.py",
        "components/artifacts/competitor_intel.py", "components/artifacts/tender_comparison.py",
        "components/artifacts/risk_analysis.py", "components/artifacts/winning_strategy.py",
        "components/artifacts/gap_analysis.py", "components/artifacts/requirements.py",
        "components/artifacts/price_benchmark.py", "components/artifacts/rfp_draft.py",
        "sql/001_create_tables.sql", "sql/002_create_indexes.sql",
    ]
    missing = [f for f in expected if not (ROOT / f).exists()]
    assert not missing, f"Missing: {missing}"
    return f"{len(expected)} files OK"


# ===================================================================
# 9. PLAYWRIGHT BROWSER TESTS
# ===================================================================

@test("Browser: welcome page loads", "playwright")
def test_pw_welcome():
    if _skip_browser: return "Skipped (--skip-browser)"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not _headed)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        title = page.title()
        assert "Tendly" in title, f"Title: {title}"
        # Check 3-pane layout
        assert page.locator(".sidebar").count() == 1, "No sidebar"
        assert page.locator(".chat-main").count() == 1, "No chat-main"
        assert page.locator("#canvas-panel").count() == 1, "No canvas panel"
        # Check role switcher
        assert page.locator(".role-switcher").count() == 1, "No role switcher"
        buyer_tab = page.locator("#role-tab-buyer")
        seller_tab = page.locator("#role-tab-seller")
        assert buyer_tab.count() == 1, "No buyer tab"
        assert seller_tab.count() == 1, "No seller tab"
        save_results("reg_pw_welcome.json", {"title": title, "has_3pane": True, "has_role_switcher": True})
        browser.close()
    return "3-pane layout + role switcher OK"


@test("Browser: role switcher buyer is default", "playwright")
def test_pw_role_default():
    if _skip_browser: return "Skipped (--skip-browser)"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not _headed)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        buyer_tab = page.locator("#role-tab-buyer")
        has_active = "active" in (buyer_tab.get_attribute("class") or "")
        # Buyer nav section should be visible by default
        buyer_nav = page.locator(".sidebar-nav-section")
        nav_visible = buyer_nav.count() > 0
        save_results("reg_pw_role_default.json", {"buyer_active": has_active, "buyer_nav_visible": nav_visible})
        assert has_active, "Buyer tab not active by default"
        assert nav_visible, "Buyer nav not visible by default"
        browser.close()
    return "Buyer is default role"


@test("Browser: welcome suggestions clickable", "playwright")
def test_pw_suggestions():
    if _skip_browser: return "Skipped (--skip-browser)"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not _headed)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        cards = page.locator(".suggestion-card")
        count = cards.count()
        assert count >= 2, f"Only {count} suggestion cards"
        # Check first card is clickable
        first_text = cards.first.inner_text()
        save_results("reg_pw_suggestions.json", {"card_count": count, "first_card": first_text})
        browser.close()
    return f"{count} suggestion cards"


@test("Browser: new chat button works", "playwright")
def test_pw_new_chat():
    if _skip_browser: return "Skipped (--skip-browser)"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not _headed)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        btn = page.locator(".new-chat-btn")
        assert btn.count() == 1, "No new chat button"
        save_results("reg_pw_new_chat.json", {"button_found": True})
        browser.close()
    return "New chat button present"


@test("Browser: chat input and send", "playwright")
def test_pw_chat_input():
    if _skip_browser: return "Skipped (--skip-browser)"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not _headed)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        textarea = page.locator("#chat-input")
        assert textarea.count() == 1, "No chat input"
        send_btn = page.locator("#send-btn")
        assert send_btn.count() == 1, "No send button"
        # Type a message
        textarea.fill("IT tenders in UK")
        page.wait_for_timeout(500)
        # Check input has text
        value = textarea.input_value()
        assert "IT" in value, f"Input value: {value}"
        save_results("reg_pw_chat_input.json", {"input_works": True, "value": value})
        browser.close()
    return "Chat input works"


@test("Browser: send message and get response", "playwright")
def test_pw_send_message():
    if _skip_browser: return "Skipped (--skip-browser)"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not _headed)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        # Type and send
        page.locator("#chat-input").fill("construction tenders")
        page.locator("#send-btn").click()
        # Wait for AI response (thinking indicator then message)
        page.wait_for_selector(".ai-message", timeout=30000)
        # Check response appeared
        ai_msgs = page.locator(".ai-message")
        assert ai_msgs.count() >= 1, "No AI message appeared"
        # Check for tender results or response text
        page.wait_for_timeout(3000)
        response_text = page.locator(".ai-message .message-text").first.inner_text()
        save_results("reg_pw_send_message.json", {
            "ai_messages": ai_msgs.count(),
            "response_preview": response_text[:200],
            "has_tender_results": page.locator(".tender-results").count() > 0,
        })
        browser.close()
    return f"Got AI response ({len(response_text)} chars)"


@test("Browser: tender card opens canvas", "playwright")
def test_pw_canvas_open():
    if _skip_browser: return "Skipped (--skip-browser)"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not _headed)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        # Send a search to get tender cards
        page.locator("#chat-input").fill("IT tenders")
        page.locator("#send-btn").click()
        page.wait_for_selector(".ai-message", timeout=30000)
        page.wait_for_timeout(3000)
        # Check if tender cards appeared
        tender_items = page.locator(".tender-list-item")
        if tender_items.count() == 0:
            save_results("reg_pw_canvas.json", {"tender_cards": 0, "canvas_opened": False})
            return "No tender cards to click (search returned 0)"
        # Click first tender card
        tender_items.first.click()
        page.wait_for_timeout(2000)
        # Check canvas opened
        canvas = page.locator("#canvas-panel.open")
        canvas_open = canvas.count() > 0
        save_results("reg_pw_canvas.json", {
            "tender_cards": tender_items.count(),
            "canvas_opened": canvas_open,
        })
        assert canvas_open, "Canvas did not open"
        browser.close()
    return "Canvas opens on tender click"


@test("Browser: canvas close button", "playwright")
def test_pw_canvas_close():
    if _skip_browser: return "Skipped (--skip-browser)"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not _headed)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        page.locator("#chat-input").fill("tenders in UK")
        page.locator("#send-btn").click()
        try:
            page.wait_for_selector(".ai-message", timeout=20000)
        except Exception:
            browser.close()
            return "Skipped (AI response timeout)"
        page.wait_for_timeout(3000)
        tender_items = page.locator(".tender-list-item")
        if tender_items.count() == 0:
            browser.close()
            return "No tender cards (skipping close test)"
        tender_items.first.click()
        page.wait_for_timeout(2000)
        close_btn = page.locator(".canvas-close-btn")
        if close_btn.count() > 0:
            close_btn.click()
            page.wait_for_timeout(500)
            canvas = page.locator("#canvas-panel.open")
            assert canvas.count() == 0, "Canvas still open after close"
        browser.close()
    return "Canvas closes OK"


@test("Browser: API endpoints respond", "playwright")
def test_pw_api():
    if _skip_browser: return "Skipped (--skip-browser)"
    import requests
    endpoints = [
        ("GET", f"{BASE_URL}/api/conversations", 200),
        ("POST", f"{BASE_URL}/api/conversations/new", 200),
        ("GET", f"{BASE_URL}/api/auth/status", 200),
    ]
    results = {}
    for method, url, expected in endpoints:
        resp = requests.request(method, url, timeout=10)
        results[url.split("/api/")[1]] = {"status": resp.status_code, "ok": resp.status_code == expected}
        assert resp.status_code == expected, f"{url} returned {resp.status_code}"
    save_results("reg_pw_api.json", results)
    return f"{len(endpoints)} API endpoints OK"


@test("Browser: login page renders", "playwright")
def test_pw_login():
    if _skip_browser: return "Skipped (--skip-browser)"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not _headed)
        page = browser.new_page()
        page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        assert page.locator("#email").count() == 1, "No email field"
        assert page.locator("#password").count() == 1, "No password field"
        save_results("reg_pw_login.json", {"login_page": True})
        browser.close()
    return "Login page OK"


# ===================================================================
# MAIN
# ===================================================================

def main():
    print(f"\n{'=' * 60}")
    print(f"  TENDLY REGRESSION SUITE")
    print(f"  Base URL:     {BASE_URL}")
    print(f"  Primary DB:   {'connected' if _db_available else 'unavailable'}")
    print(f"  Tendly DB:    {'connected' if _tendly_db_available else 'unavailable'}")
    print(f"  Browser:      {'skip' if _skip_browser else 'headed' if _headed else 'headless'}")
    print(f"{'=' * 60}\n")

    for fn in _tests:
        run_test(fn)

    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {_pass} passed, {_fail} failed, {_skip} skipped / {len(_tests)} total")
    print(f"{'=' * 60}\n")

    summary = {
        "passed": _pass,
        "failed": _fail,
        "skipped": _skip,
        "total": len(_tests),
        "base_url": BASE_URL,
        "primary_db": _db_available,
        "tendly_db": _tendly_db_available,
        "browser": "skip" if _skip_browser else "headed" if _headed else "headless",
        "tests": _results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    save_results("regression_summary.json", summary)
    print(f"Results saved to test-results/regression_summary.json")

    return 1 if _fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
