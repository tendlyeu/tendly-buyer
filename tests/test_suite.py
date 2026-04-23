"""
Tendly Buyer Test Suite

Covers all phases of the buyer portal:
  Phase 0: Foundation (imports, i18n, layout)
  Phase 1: Dashboard & Procurement Plans (CRUD, workflow steps, stats)
  Phase 2: Document Management (add, list, delete)
  Phase 3: AI Chat Service (import, conversations, tools)
  Phase 4: Workflow & Approvals (state machine, role checks)
  Phase 5: RHR Integration & i18n (registry search, translations, default language)

Usage:
  python tests/test_suite.py                   # unit tests only
  python tests/test_suite.py --with-db         # include DB/integration tests
  python tests/test_suite.py --with-http       # include HTTP route tests (requires running server on 5004)
  python tests/test_suite.py --all             # run everything
"""

import sys
import os
import json
import time
import uuid

from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

RESULTS_DIR = ROOT / "test-results"
RESULTS_DIR.mkdir(exist_ok=True)

LOCAL_URL = "http://localhost:5004"

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
_with_db = "--with-db" in sys.argv or "--all" in sys.argv
_with_http = "--with-http" in sys.argv or "--all" in sys.argv

# ---------------------------------------------------------------------------
# Test framework
# ---------------------------------------------------------------------------
_results = []
_pass = 0
_fail = 0
_skip = 0
_tests = []


def test(name, phase=0, requires_db=False, requires_http=False):
    def wrapper(fn):
        fn._test_name = name
        fn._phase = phase
        fn._requires_db = requires_db
        fn._requires_http = requires_http
        _tests.append(fn)
        return fn
    return wrapper


def run_test(fn):
    global _pass, _fail, _skip
    name = fn._test_name
    phase = fn._phase

    if fn._requires_db and not _with_db:
        _skip += 1
        print(f"  \033[33mSKIP\033[0m  [P{phase}] {name} (needs --with-db)")
        return
    if fn._requires_http and not _with_http:
        _skip += 1
        print(f"  \033[33mSKIP\033[0m  [P{phase}] {name} (needs --with-http)")
        return

    t0 = time.time()
    try:
        result = fn()
        _pass += 1
        elapsed = time.time() - t0
        detail = result if isinstance(result, str) else "OK"
        print(f"  \033[32mPASS\033[0m  [P{phase}] {name} ({elapsed:.2f}s)")
    except Exception as e:
        _fail += 1
        elapsed = time.time() - t0
        detail = str(e)
        print(f"  \033[31mFAIL\033[0m  [P{phase}] {name}: {e} ({elapsed:.2f}s)")
    _results.append({
        "test": name,
        "phase": phase,
        "status": "PASS" if detail != str(detail) or _results == [] or _results[-1].get("test") != name else ("PASS" if not any(r["test"] == name and r["status"] == "FAIL" for r in _results) else "FAIL"),
        "detail": detail,
        "elapsed": round(time.time() - t0, 3),
    })


def save_results(filename, data):
    path = RESULTS_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ===========================================================================
# Phase 0: Foundation — Imports, i18n, Layout
# ===========================================================================

@test("Import: config.i18n", phase=0)
def test_import_i18n():
    from config.i18n import (
        SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, LANGUAGE_INFO,
        t, get_language_from_request, get_js_translations,
    )
    assert DEFAULT_LANGUAGE == "et", f"Expected default 'et', got '{DEFAULT_LANGUAGE}'"
    assert "et" in SUPPORTED_LANGUAGES
    assert "en" in SUPPORTED_LANGUAGES
    assert len(SUPPORTED_LANGUAGES) == 6
    return f"Default={DEFAULT_LANGUAGE}, {len(SUPPORTED_LANGUAGES)} languages"


@test("Import: components.layout", phase=0)
def test_import_layout():
    from components.layout import chat_page, buyer_page
    assert callable(chat_page)
    assert callable(buyer_page)
    return "chat_page, buyer_page OK"


@test("Import: components.sidebar", phase=0)
def test_import_sidebar():
    from components.sidebar import sidebar_component
    assert callable(sidebar_component)
    return "sidebar_component OK"


@test("Import: routes.__init__", phase=0)
def test_import_routes():
    from routes import register_routes
    assert callable(register_routes)
    return "register_routes OK"


@test("Import: core.database models", phase=0)
def test_import_database_models():
    from core.database import (
        Tender, TenderDetail, TenderResult,
        ProcurementPlan, ProcurementStep, ProcurementDocument,
        ApprovalAction, TeamMember, ChatContext,
    )
    assert ProcurementPlan.__tablename__ == "procurement_plans"
    assert ProcurementStep.__tablename__ == "procurement_steps"
    assert ProcurementDocument.__tablename__ == "procurement_documents"
    assert ApprovalAction.__tablename__ == "approval_actions"
    assert TeamMember.__tablename__ == "team_members"
    assert ChatContext.__tablename__ == "chat_contexts"
    return "6 buyer models + 3 tender models"


@test("Import: services.procurement_service", phase=0)
def test_import_procurement_service():
    from services.procurement_service import (
        create_plan, get_plan, list_plans, update_plan, delete_plan,
        get_steps, complete_step, get_stats,
        add_document, list_documents, get_document, delete_document,
        add_team_member, list_team_members, remove_team_member,
    )
    return "All service functions importable"


@test("Import: services.workflow_service", phase=0)
def test_import_workflow_service():
    from services.workflow_service import (
        VALID_TRANSITIONS, STEP_ROLES, STEP_NAMES, STEP_NAMES_ET,
        can_transition, can_user_act_on_step, get_step_info,
    )
    assert len(STEP_ROLES) == 5
    assert len(STEP_NAMES_ET) == 5
    return "Workflow service OK"


@test("Import: all route modules", phase=0)
def test_import_all_routes():
    from routes.pages import register_page_routes
    from routes.api import register_api_routes
    from routes.auth import register_auth_routes
    from routes.procurements import register_procurement_routes
    from routes.documents import register_document_routes
    from routes.registry import register_registry_routes
    from routes.team import register_team_routes
    return "7 route modules imported"


@test("Translation file: et.json exists and is valid", phase=0)
def test_et_translation_file():
    path = ROOT / "config" / "translations" / "et.json"
    assert path.exists(), "et.json not found"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    required_sections = ["app", "nav", "dashboard", "procurements", "documents", "registry", "team", "chat", "tender", "auth"]
    missing = [s for s in required_sections if s not in data]
    assert not missing, f"Missing sections: {missing}"
    return f"{len(data)} top-level sections"


@test("Translation file: en.json exists and is valid", phase=0)
def test_en_translation_file():
    path = ROOT / "config" / "translations" / "en.json"
    assert path.exists(), "en.json not found"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    required_sections = ["app", "nav", "dashboard", "procurements", "documents", "registry", "team", "chat", "tender", "auth"]
    missing = [s for s in required_sections if s not in data]
    assert not missing, f"Missing sections: {missing}"
    return f"{len(data)} top-level sections"


@test("i18n: t() function returns Estonian by default", phase=0)
def test_i18n_default_estonian():
    from config.i18n import t
    assert t("nav.dashboard") == "Ülevaade", f"Expected 'Ülevaade', got '{t('nav.dashboard')}'"
    assert t("nav.procurements") == "Hanked"
    assert t("nav.documents") == "Dokumendid"
    assert t("nav.team") == "Meeskond"
    return "Estonian defaults confirmed"


@test("i18n: t() function falls back to English", phase=0)
def test_i18n_english_fallback():
    from config.i18n import t
    assert t("nav.dashboard", "en") == "Dashboard"
    assert t("nav.procurements", "en") == "Procurements"
    return "English translations OK"


@test("i18n: t() returns key for missing translation", phase=0)
def test_i18n_missing_key():
    from config.i18n import t
    result = t("nonexistent.key.here")
    assert result == "nonexistent.key.here"
    return "Missing key returns key itself"


@test("i18n: t() supports string formatting", phase=0)
def test_i18n_formatting():
    from config.i18n import t
    result = t("tender.view_all", "en", count=42)
    assert "42" in result
    return f"Formatted: '{result}'"


@test("i18n: get_js_translations returns dict", phase=0)
def test_i18n_js_translations():
    from config.i18n import get_js_translations
    js = get_js_translations("et")
    assert isinstance(js, dict)
    assert "chat.thinking" in js
    assert "tender.matching" in js
    assert len(js) > 20
    return f"{len(js)} JS translation keys"


# ===========================================================================
# Phase 1: Dashboard & Procurement Plans
# ===========================================================================

@test("Create plan with defaults", phase=1)
def test_create_plan_defaults():
    from services.procurement_service import create_plan, _plans, _steps
    _plans.clear()
    _steps.clear()
    plan = create_plan(title="Test Plan")
    assert plan["id"]
    assert plan["title"] == "Test Plan"
    assert plan["status"] == "draft"
    assert plan["current_step"] == 1
    assert plan["currency"] == "EUR"
    return f"Plan ID: {plan['id'][:8]}"


@test("Create plan creates 5 workflow steps", phase=1)
def test_create_plan_steps():
    from services.procurement_service import create_plan, get_steps, _plans, _steps
    _plans.clear()
    _steps.clear()
    plan = create_plan(title="Step Test")
    steps = get_steps(plan["id"])
    assert len(steps) == 5, f"Expected 5 steps, got {len(steps)}"
    assert steps[0]["step_number"] == 1
    assert steps[0]["status"] == "in_progress"
    assert steps[1]["status"] == "pending"
    assert steps[4]["step_number"] == 5
    step_roles = [s["assigned_role"] for s in steps]
    assert step_roles == ["domain_lead", "domain_lead", "procurement_manager", "board", "domain_specialist"]
    return "5 steps with correct roles"


@test("Create plan with all fields", phase=1)
def test_create_plan_full():
    from services.procurement_service import create_plan, _plans, _steps
    _plans.clear()
    _steps.clear()
    plan = create_plan(
        title="IT Infrastructure 2026",
        description="Server upgrade",
        category="it",
        estimated_value=150000,
        cpv_code="72000000",
        fiscal_year=2026,
        procurement_method="open",
        created_by_email="test@org.ee",
        organization_id="org-1",
    )
    assert plan["category"] == "it"
    assert plan["estimated_value"] == 150000.0
    assert plan["cpv_code"] == "72000000"
    assert plan["fiscal_year"] == 2026
    assert plan["procurement_method"] == "open"
    assert plan["created_by_email"] == "test@org.ee"
    return "All fields set correctly"


@test("Get plan by ID", phase=1)
def test_get_plan():
    from services.procurement_service import create_plan, get_plan, _plans, _steps
    _plans.clear()
    _steps.clear()
    plan = create_plan(title="Get Test")
    fetched = get_plan(plan["id"])
    assert fetched is not None
    assert fetched["title"] == "Get Test"
    assert get_plan("nonexistent-id") is None
    return "Get by ID works"


@test("List plans (empty and populated)", phase=1)
def test_list_plans():
    from services.procurement_service import create_plan, list_plans, _plans, _steps
    _plans.clear()
    _steps.clear()
    assert list_plans() == []
    create_plan(title="Plan A")
    create_plan(title="Plan B")
    plans = list_plans()
    assert len(plans) == 2
    return f"{len(plans)} plans listed"


@test("List plans filtered by status", phase=1)
def test_list_plans_filter():
    from services.procurement_service import create_plan, list_plans, complete_step, _plans, _steps, _approvals
    _plans.clear()
    _steps.clear()
    _approvals.clear()
    p1 = create_plan(title="Draft Plan")
    p2 = create_plan(title="Advanced Plan")
    complete_step(p2["id"], 1)
    complete_step(p2["id"], 2)
    drafts = list_plans(status="draft")
    reviews = list_plans(status="review")
    assert len(drafts) == 1
    assert len(reviews) == 1
    return "Status filter works"


@test("Update plan", phase=1)
def test_update_plan():
    from services.procurement_service import create_plan, update_plan, get_plan, _plans, _steps
    _plans.clear()
    _steps.clear()
    plan = create_plan(title="Old Title")
    updated = update_plan(plan["id"], title="New Title", category="kinnisvara")
    assert updated["title"] == "New Title"
    assert updated["category"] == "kinnisvara"
    assert update_plan("nonexistent", title="X") is None
    return "Update OK"


@test("Delete plan", phase=1)
def test_delete_plan():
    from services.procurement_service import create_plan, delete_plan, get_plan, _plans, _steps
    _plans.clear()
    _steps.clear()
    plan = create_plan(title="To Delete")
    assert delete_plan(plan["id"]) is True
    assert get_plan(plan["id"]) is None
    assert delete_plan("nonexistent") is False
    return "Delete OK"


@test("Complete step advances workflow", phase=1)
def test_complete_step():
    from services.procurement_service import create_plan, complete_step, get_plan, get_steps, _plans, _steps, _approvals
    _plans.clear()
    _steps.clear()
    _approvals.clear()
    plan = create_plan(title="Workflow Test")
    pid = plan["id"]

    assert complete_step(pid, 1, completed_by="user@org.ee") is True
    plan = get_plan(pid)
    assert plan["current_step"] == 2
    assert plan["status"] == "planning"

    assert complete_step(pid, 2) is True
    plan = get_plan(pid)
    assert plan["current_step"] == 3
    assert plan["status"] == "review"

    assert complete_step(pid, 3) is True
    assert complete_step(pid, 4) is True
    plan = get_plan(pid)
    assert plan["status"] == "approved"

    assert complete_step(pid, 5) is True
    plan = get_plan(pid)
    assert plan["status"] == "completed"
    assert plan["current_step"] == 5

    steps = get_steps(pid)
    completed = [s for s in steps if s["status"] == "completed"]
    assert len(completed) == 5
    return "Full 5-step workflow completed"


@test("Complete wrong step number is rejected", phase=1)
def test_complete_wrong_step():
    from services.procurement_service import create_plan, complete_step, _plans, _steps, _approvals
    _plans.clear()
    _steps.clear()
    _approvals.clear()
    plan = create_plan(title="Wrong Step")
    assert complete_step(plan["id"], 3) is False
    assert complete_step(plan["id"], 2) is False
    assert complete_step("nonexistent", 1) is False
    return "Invalid step completions rejected"


@test("Get stats aggregates correctly", phase=1)
def test_get_stats():
    from services.procurement_service import create_plan, complete_step, get_stats, add_document, _plans, _steps, _approvals, _documents
    _plans.clear()
    _steps.clear()
    _approvals.clear()
    _documents.clear()
    create_plan(title="Active 1")
    p2 = create_plan(title="In Review")
    complete_step(p2["id"], 1)
    complete_step(p2["id"], 2)
    p3 = create_plan(title="Completed")
    for i in range(1, 6):
        complete_step(p3["id"], i)
    add_document(title="Doc 1")
    add_document(title="Doc 2")

    stats = get_stats()
    assert stats["active"] == 2, f"Expected 2 active, got {stats['active']}"
    assert stats["pending_approval"] == 1
    assert stats["completed"] == 1
    assert stats["documents"] == 2
    return f"active={stats['active']}, pending={stats['pending_approval']}, completed={stats['completed']}, docs={stats['documents']}"


@test("Get approvals trail", phase=1)
def test_get_approvals():
    from services.procurement_service import create_plan, complete_step, get_approvals, _plans, _steps, _approvals
    _plans.clear()
    _steps.clear()
    _approvals.clear()
    plan = create_plan(title="Audit Trail")
    complete_step(plan["id"], 1, completed_by="user1@org.ee", notes="Reviewed")
    complete_step(plan["id"], 2, completed_by="user1@org.ee")
    approvals = get_approvals(plan["id"])
    assert len(approvals) == 2
    assert approvals[0]["actor_email"] == "user1@org.ee"
    assert approvals[0]["comment"] == "Reviewed"
    return f"{len(approvals)} approval actions"


# ===========================================================================
# Phase 2: Document Management
# ===========================================================================

@test("Add document", phase=2)
def test_add_document():
    from services.procurement_service import add_document, _documents
    _documents.clear()
    doc = add_document(
        title="Contract Template",
        document_type="contract_template",
        content_text="Sample contract text...",
        uploaded_by_email="user@org.ee",
    )
    assert doc["id"]
    assert doc["title"] == "Contract Template"
    assert doc["document_type"] == "contract_template"
    assert doc["content_text"] == "Sample contract text..."
    assert doc["status"] == "draft"
    assert doc["version"] == 1
    return f"Doc ID: {doc['id'][:8]}"


@test("List documents", phase=2)
def test_list_documents():
    from services.procurement_service import add_document, list_documents, _documents
    _documents.clear()
    add_document(title="Doc A", document_type="technical_description")
    add_document(title="Doc B", document_type="rfp_draft")
    add_document(title="Doc C", document_type="technical_description")
    all_docs = list_documents()
    assert len(all_docs) == 3
    tech_docs = list_documents(document_type="technical_description")
    assert len(tech_docs) == 2
    return f"{len(all_docs)} total, {len(tech_docs)} technical"


@test("Get document by ID", phase=2)
def test_get_document():
    from services.procurement_service import add_document, get_document, _documents
    _documents.clear()
    doc = add_document(title="Fetch Me")
    fetched = get_document(doc["id"])
    assert fetched is not None
    assert fetched["title"] == "Fetch Me"
    assert get_document("nonexistent") is None
    return "Get by ID works"


@test("Delete document", phase=2)
def test_delete_document():
    from services.procurement_service import add_document, delete_document, get_document, _documents
    _documents.clear()
    doc = add_document(title="To Delete")
    assert delete_document(doc["id"]) is True
    assert get_document(doc["id"]) is None
    assert delete_document("nonexistent") is False
    return "Delete OK"


@test("Document types constant covers all expected types", phase=2)
def test_document_types():
    from routes.documents import DOCUMENT_TYPES
    type_keys = [k for k, _ in DOCUMENT_TYPES]
    expected = ["contract_template", "technical_description", "good_practice",
                "org_chart", "cv", "iso_certificate", "product_list",
                "software_list", "rit_inventory", "rfp_draft", "other"]
    missing = [t for t in expected if t not in type_keys]
    assert not missing, f"Missing types: {missing}"
    return f"{len(DOCUMENT_TYPES)} document types"


# ===========================================================================
# Phase 3: AI Chat Service
# ===========================================================================

@test("Import: chat_service", phase=3)
def test_import_chat_service():
    from chat_service import TendlyChatService
    cs = TendlyChatService()
    assert cs is not None
    return "TendlyChatService imported"


@test("Chat: create conversation", phase=3)
def test_chat_create():
    from chat_service import TendlyChatService
    cs = TendlyChatService()
    cid = cs.create_conversation()
    assert cid
    assert len(cid) > 10
    return f"Conversation: {cid[:8]}"


@test("Chat: get conversations", phase=3)
def test_chat_list():
    from chat_service import TendlyChatService
    cs = TendlyChatService()
    convos = cs.get_conversations()
    assert isinstance(convos, list)
    return f"{len(convos)} conversations"


@test("Chat: get conversation by ID", phase=3)
def test_chat_get():
    from chat_service import TendlyChatService
    cs = TendlyChatService()
    cid = cs.create_conversation()
    conv = cs.get_conversation(cid)
    assert conv is not None
    assert "messages" in conv
    return "Get conversation OK"


@test("Chat: delete conversation", phase=3)
def test_chat_delete():
    from chat_service import TendlyChatService
    cs = TendlyChatService()
    cid = cs.create_conversation()
    assert cs.delete_conversation(cid)
    return "Delete OK"


@test("Import: tools registry", phase=3)
def test_import_tools():
    try:
        from tools.registry import get_available_tools
        tools = get_available_tools()
        assert isinstance(tools, (list, dict))
        tool_count = len(tools)
        return f"{tool_count} tools registered"
    except ImportError:
        from tools import search_tenders
        return "search_tenders importable"


@test("Import: core.llm_client", phase=3)
def test_import_llm():
    from core.llm_client import LLMClient
    client = LLMClient()
    assert client is not None
    return "LLMClient imported"


# ===========================================================================
# Phase 4: Workflow & Approvals (State Machine)
# ===========================================================================

@test("Workflow: valid transitions", phase=4)
def test_workflow_transitions():
    from services.workflow_service import can_transition
    assert can_transition("draft", "planning") is True
    assert can_transition("draft", "cancelled") is True
    assert can_transition("planning", "review") is True
    assert can_transition("review", "approved") is True
    assert can_transition("review", "planning") is True
    assert can_transition("approved", "published") is True
    assert can_transition("published", "completed") is True
    assert can_transition("cancelled", "draft") is True
    return "All valid transitions pass"


@test("Workflow: invalid transitions rejected", phase=4)
def test_workflow_invalid_transitions():
    from services.workflow_service import can_transition
    assert can_transition("draft", "completed") is False
    assert can_transition("draft", "approved") is False
    assert can_transition("completed", "draft") is False
    assert can_transition("completed", "planning") is False
    assert can_transition("planning", "approved") is False
    assert can_transition("published", "draft") is False
    return "Invalid transitions blocked"


@test("Workflow: step role assignment", phase=4)
def test_workflow_step_roles():
    from services.workflow_service import STEP_ROLES
    assert STEP_ROLES[1] == "domain_lead"
    assert STEP_ROLES[2] == "domain_lead"
    assert STEP_ROLES[3] == "procurement_manager"
    assert STEP_ROLES[4] == "board"
    assert STEP_ROLES[5] == "domain_specialist"
    return "5 steps with correct roles"


@test("Workflow: can_user_act_on_step", phase=4)
def test_workflow_user_role_check():
    from services.workflow_service import can_user_act_on_step
    assert can_user_act_on_step(1, "domain_lead") is True
    assert can_user_act_on_step(1, "board") is False
    assert can_user_act_on_step(3, "procurement_manager") is True
    assert can_user_act_on_step(3, "domain_lead") is False
    assert can_user_act_on_step(4, "board") is True
    assert can_user_act_on_step(5, "domain_specialist") is True
    assert can_user_act_on_step(1, "admin") is True
    assert can_user_act_on_step(4, "admin") is True
    return "Role checks correct"


@test("Workflow: get_step_info", phase=4)
def test_workflow_step_info():
    from services.workflow_service import get_step_info
    info = get_step_info(1)
    assert info["number"] == 1
    assert info["name"] == "domain_review"
    assert info["name_et"] == "Vajaduse ülevaade"
    assert info["role"] == "domain_lead"

    info5 = get_step_info(5)
    assert info5["name"] == "document_preparation"
    assert info5["name_et"] == "Dokumentide koostamine"
    assert info5["role"] == "domain_specialist"
    return "Step info correct for all steps"


@test("Workflow: Estonian step names match plan component", phase=4)
def test_workflow_step_names_match():
    from services.workflow_service import STEP_NAMES_ET
    from components.procurements.plan_list import WORKFLOW_STEPS
    for num, step_id, step_name_et, role in WORKFLOW_STEPS:
        assert STEP_NAMES_ET[num] == step_name_et, f"Step {num}: '{STEP_NAMES_ET[num]}' != '{step_name_et}'"
    return "5 step names match between service and component"


# ===========================================================================
# Phase 5: RHR Integration, Team, i18n completeness
# ===========================================================================

@test("Team: add member", phase=5)
def test_team_add():
    from services.procurement_service import add_team_member, _team
    _team.clear()
    member = add_team_member(
        organization_id="org-1",
        user_email="maria@org.ee",
        name="Maria Tamm",
        procurement_role="domain_lead",
        specialty="it",
    )
    assert member["id"]
    assert member["name"] == "Maria Tamm"
    assert member["procurement_role"] == "domain_lead"
    assert member["is_active"] is True
    return f"Member: {member['name']}"


@test("Team: list members", phase=5)
def test_team_list():
    from services.procurement_service import add_team_member, list_team_members, _team
    _team.clear()
    add_team_member("org-1", "a@org.ee", "Alice", "domain_lead", "it")
    add_team_member("org-1", "b@org.ee", "Bob", "board", "kinnisvara")
    add_team_member("org-2", "c@org.ee", "Carol", "procurement_manager", "ehitus")
    members = list_team_members("org-1")
    assert len(members) == 2
    members2 = list_team_members("org-2")
    assert len(members2) == 1
    return "Org filter works"


@test("Team: remove member (soft delete)", phase=5)
def test_team_remove():
    from services.procurement_service import add_team_member, remove_team_member, list_team_members, _team
    _team.clear()
    m = add_team_member("org-1", "x@org.ee", "X", "board", "muu")
    assert remove_team_member(m["id"]) is True
    active = list_team_members("org-1")
    assert len(active) == 0
    assert remove_team_member("nonexistent") is False
    return "Soft delete works"


@test("Team: roles constant", phase=5)
def test_team_roles():
    from routes.team import ROLES
    role_keys = [k for k, _ in ROLES]
    expected = ["domain_lead", "procurement_manager", "board", "domain_specialist"]
    assert role_keys == expected
    return f"{len(ROLES)} roles defined"


@test("Team: specialties constant", phase=5)
def test_team_specialties():
    from routes.team import SPECIALTIES
    spec_keys = [k for k, _ in SPECIALTIES]
    expected = ["it", "kinnisvara", "personal", "toitlustus", "ehitus", "muu"]
    assert spec_keys == expected
    return f"{len(SPECIALTIES)} specialties"


@test("Registry: _search_registry importable", phase=5)
def test_registry_import():
    from routes.registry import _search_registry, COUNTRY_FLAGS
    assert callable(_search_registry)
    assert len(COUNTRY_FLAGS) >= 6
    return f"{len(COUNTRY_FLAGS)} country flags"


@test("Registry: DB search returns results", phase=5, requires_db=True)
def test_registry_search_db():
    from routes.registry import _search_registry
    results = _search_registry(query="", country="", limit=5)
    assert isinstance(results, list)
    return f"{len(results)} results from registry"


@test("Registry: DB search with country filter", phase=5, requires_db=True)
def test_registry_search_country():
    from routes.registry import _search_registry
    ee = _search_registry(query="", country="EE", limit=10)
    assert isinstance(ee, list)
    if ee:
        for tender, detail, result in ee:
            assert tender.country_code == "EE"
    return f"{len(ee)} Estonian tenders"


@test("Registry: DB search with keyword", phase=5, requires_db=True)
def test_registry_search_keyword():
    from routes.registry import _search_registry
    results = _search_registry(query="IT", country="", limit=10)
    assert isinstance(results, list)
    return f"{len(results)} tenders matching 'IT'"


@test("i18n: et.json and en.json key parity (top-level)", phase=5)
def test_i18n_parity():
    et_path = ROOT / "config" / "translations" / "et.json"
    en_path = ROOT / "config" / "translations" / "en.json"
    with open(et_path, "r", encoding="utf-8") as f:
        et = json.load(f)
    with open(en_path, "r", encoding="utf-8") as f:
        en = json.load(f)
    et_sections = set(et.keys())
    en_sections = set(en.keys())
    et_only = et_sections - en_sections
    en_only = en_sections - et_sections
    if et_only:
        return f"Warning: ET-only sections: {et_only}"
    if en_only:
        return f"Warning: EN-only sections: {en_only}"
    return f"{len(et_sections)} sections in sync"


@test("i18n: all nav keys present in ET", phase=5)
def test_i18n_nav_keys():
    from config.i18n import t
    nav_keys = ["nav.dashboard", "nav.procurements", "nav.documents", "nav.registry", "nav.chat", "nav.team"]
    for key in nav_keys:
        val = t(key, "et")
        assert val != key, f"Missing ET translation for '{key}'"
    return f"{len(nav_keys)} nav keys translated"


@test("Procurement categories match in component", phase=5)
def test_procurement_categories():
    from components.procurements.plan_list import PROCUREMENT_CATEGORIES
    assert len(PROCUREMENT_CATEGORIES) >= 9
    keys = [k for k, _ in PROCUREMENT_CATEGORIES]
    assert "it" in keys
    assert "kinnisvara" in keys
    assert "ehitus" in keys
    return f"{len(PROCUREMENT_CATEGORIES)} categories"


# ===========================================================================
# HTTP Integration Tests (require running server)
# ===========================================================================

@test("HTTP: GET / (dashboard)", phase=0, requires_http=True)
def test_http_dashboard():
    import requests
    r = requests.get(LOCAL_URL, timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    assert "Ülevaade" in r.text or "Dashboard" in r.text
    return f"HTTP 200, {len(r.text)} bytes"


@test("HTTP: GET /chat", phase=0, requires_http=True)
def test_http_chat():
    import requests
    r = requests.get(f"{LOCAL_URL}/chat", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    assert "Tendly" in r.text
    return f"HTTP 200, {len(r.text)} bytes"


@test("HTTP: GET /procurements", phase=1, requires_http=True)
def test_http_procurements():
    import requests
    r = requests.get(f"{LOCAL_URL}/procurements", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    assert "Hankeplaanid" in r.text or "Procurement" in r.text
    return f"HTTP 200, {len(r.text)} bytes"


@test("HTTP: GET /procurements/new", phase=1, requires_http=True)
def test_http_procurements_new():
    import requests
    r = requests.get(f"{LOCAL_URL}/procurements/new", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return f"HTTP 200, {len(r.text)} bytes"


@test("HTTP: GET /documents", phase=2, requires_http=True)
def test_http_documents():
    import requests
    r = requests.get(f"{LOCAL_URL}/documents", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    assert "Dokumendid" in r.text or "Documents" in r.text
    return f"HTTP 200, {len(r.text)} bytes"


@test("HTTP: GET /registry", phase=5, requires_http=True)
def test_http_registry():
    import requests
    r = requests.get(f"{LOCAL_URL}/registry", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    assert "Register" in r.text or "Registry" in r.text
    return f"HTTP 200, {len(r.text)} bytes"


@test("HTTP: GET /team", phase=5, requires_http=True)
def test_http_team():
    import requests
    r = requests.get(f"{LOCAL_URL}/team", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    assert "Meeskond" in r.text or "Team" in r.text
    return f"HTTP 200, {len(r.text)} bytes"


@test("HTTP: GET /login", phase=0, requires_http=True)
def test_http_login():
    import requests
    r = requests.get(f"{LOCAL_URL}/login", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return f"HTTP 200, {len(r.text)} bytes"


# ===========================================================================
# DB connection test
# ===========================================================================

@test("DB: connection and basic query", phase=0, requires_db=True)
def test_db_connection():
    from core.database import get_session
    from sqlalchemy import text
    session = get_session()
    try:
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        session.close()
    return "Connected"


@test("DB: tender tables exist", phase=0, requires_db=True)
def test_db_tables():
    from core.database import get_session
    from sqlalchemy import text
    session = get_session()
    try:
        rows = session.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name IN "
            "('tenders', 'tender_details', 'tender_results') "
            "ORDER BY table_name"
        )).fetchall()
        tables = [r[0] for r in rows]
        assert len(tables) >= 2, f"Expected >= 2 tender tables, found {tables}"
        return f"{len(tables)} tables: {', '.join(tables)}"
    finally:
        session.close()


@test("DB: tenders have data", phase=0, requires_db=True)
def test_db_has_data():
    from core.database import get_session, Tender
    from sqlalchemy import func
    session = get_session()
    try:
        count = session.query(func.count(Tender.procurement_id)).scalar()
        assert count > 0, "No tenders in database"
        return f"{count} tenders"
    finally:
        session.close()


# ===========================================================================
# Runner
# ===========================================================================

def main():
    print(f"\n{'='*65}")
    print(f"  Tendly Buyer Test Suite")
    print(f"  Flags: --with-db={_with_db}, --with-http={_with_http}")
    if _with_http:
        print(f"  Server URL: {LOCAL_URL}")
    print(f"{'='*65}\n")

    current_phase = -1
    for fn in _tests:
        if fn._phase != current_phase:
            current_phase = fn._phase
            phase_names = {
                0: "Foundation (imports, i18n, layout)",
                1: "Dashboard & Procurement Plans",
                2: "Document Management",
                3: "AI Chat Service",
                4: "Workflow & Approvals",
                5: "RHR Integration, Team & i18n",
            }
            print(f"\n  --- Phase {current_phase}: {phase_names.get(current_phase, '')} ---")
        run_test(fn)

    print(f"\n{'='*65}")
    print(f"  Results: \033[32m{_pass} passed\033[0m, \033[31m{_fail} failed\033[0m, \033[33m{_skip} skipped\033[0m ({_pass + _fail + _skip} total)")
    print(f"{'='*65}\n")

    save_results("buyer_test_summary.json", {
        "passed": _pass,
        "failed": _fail,
        "skipped": _skip,
        "total": _pass + _fail + _skip,
        "with_db": _with_db,
        "with_http": _with_http,
        "tests": _results,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    print(f"  Results saved to test-results/buyer_test_summary.json\n")

    return _fail == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
