"""Deeper route-level tests for the chat-side fixes.

These tests exercise the SERVER-side contracts that the LLM-driven
behaviour rests on: the right primer is added on /chat?plan=, the
right primer is added on /chat?benchmark=, /api/chat/attach injects
the document text as a system primer, and the rfp_draft tool routes
correctly with a doc_type hint.

We can't drive real LLM responses (the dev env uses stub keys), but
we CAN assert that the inputs to the LLM (system_primers, query
analysis result, tool dispatch) are wired up correctly. That's the
class of bug the original tickets reported.
"""

import asyncio
import json
import os
import sys
import time
import uuid

from playwright.async_api import async_playwright

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:5002")
LOGIN_EMAIL = os.environ.get("TEST_USER", "buyer@tendly.local")
LOGIN_PASSWORD = os.environ.get("TEST_PASS", "buyer123")

PASSED = 0
FAILED = 0


def _log(name, ok, detail=""):
    global PASSED, FAILED
    status = "PASS" if ok else "FAIL"
    if ok:
        PASSED += 1
    else:
        FAILED += 1
    print(f"  [{status}] {name}{(' — ' + detail) if detail else ''}")


async def _login(context):
    page = await context.new_page()
    await page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    if await page.locator('input[name="email"]').count() == 0:
        await page.close()
        return
    await page.fill('input[name="email"]', LOGIN_EMAIL)
    await page.fill('input[name="password"]', LOGIN_PASSWORD)
    await page.click('button[type="submit"]')
    try:
        await page.wait_for_url(f"{BASE_URL}/", timeout=5000)
    except Exception:
        pass
    await page.close()


def _read_conversation_messages(conv_id):
    """Read messages directly from the DB so we can verify primer injection."""
    sys.path.insert(0, ".")
    from core.database import get_tendly_session, ChatContext
    s = get_tendly_session()
    try:
        ctx = s.query(ChatContext).filter(
            ChatContext.conversation_id == conv_id
        ).first()
        return list(ctx.messages or []) if ctx else []
    finally:
        s.close()


async def test_plan_primer_injection(context):
    print("\n[A] /chat?plan=… injects ACTIVE PLAN primer (#1180)")
    sys.path.insert(0, ".")
    from services.procurement_service import create_plan, list_plans
    plan = create_plan(
        title="Office IT support 2026",
        description="Tier-2 IT helpdesk for the city office, 250 endpoints.",
        category="IT",
        estimated_value=80000,
        cpv_code="72611000",
        fiscal_year=2026,
        procurement_method="open",
        created_by_email=LOGIN_EMAIL,
        organization_id=LOGIN_EMAIL,
        metadata_json={
            "evaluation_criteria": [
                {"name": "Price", "weight": 60, "description": "Total 24mo cost"},
                {"name": "Quality", "weight": 40, "description": "SLA + refs"},
            ],
            "requirements": [
                {"text": "ISO 27001", "type": "compliance", "priority": "must"},
            ],
        },
    )
    plan_id = plan.get("id")
    page = await context.new_page()
    await page.goto(f"{BASE_URL}/chat?plan={plan_id}", wait_until="domcontentloaded")
    cur = page.url
    _log("redirected to /chat/c/<uuid>", "/chat/c/" in cur, f"url={cur}")
    conv_id = cur.rsplit("/", 1)[-1]
    msgs = _read_conversation_messages(conv_id)
    sys_primers = [m for m in msgs if m.get("role") == "system"]
    ok_primer = any("ACTIVE PROCUREMENT PLAN" in (m.get("content") or "")
                    for m in sys_primers)
    ok_eval = any("Evaluation criteria" in (m.get("content") or "")
                  for m in sys_primers)
    ok_value = any("80,000" in (m.get("content") or "") or "80000" in (m.get("content") or "")
                   for m in sys_primers)
    _log("system primer recorded", ok_primer)
    _log("evaluation criteria included in primer", ok_eval)
    _log("estimated value included in primer", ok_value)
    await page.close()


async def test_benchmark_primer_injection(context):
    print("\n[B] /chat?benchmark=… injects BENCHMARK CONTEXT primer (#1190)")
    page = await context.new_page()
    await page.goto(f"{BASE_URL}/chat?benchmark=1001", wait_until="domcontentloaded")
    cur = page.url
    _log("redirected to /chat/c/<uuid>", "/chat/c/" in cur, f"url={cur}")
    conv_id = cur.rsplit("/", 1)[-1]
    msgs = _read_conversation_messages(conv_id)
    sys_primers = [m for m in msgs if m.get("role") == "system"]
    ok_primer = any("BENCHMARK CONTEXT" in (m.get("content") or "")
                    for m in sys_primers)
    has_assistant_intro = any(
        m.get("role") == "assistant" and "benchmark" in (m.get("content") or "").lower()
        for m in msgs
    )
    _log("benchmark primer recorded", ok_primer)
    _log("intro assistant message offering benchmark options", has_assistant_intro)
    await page.close()


async def test_attached_doc_primer(context):
    print("\n[C] /api/chat/attach injects ATTACHED DOCUMENT primer (#1181)")
    sys.path.insert(0, ".")
    from services.procurement_service import create_plan
    plan = create_plan(
        title="Cleaning services",
        description="3 government buildings, 12 months",
        category="services",
        estimated_value=30000,
        cpv_code="90910000",
        fiscal_year=2026,
        procurement_method="simple",
        created_by_email=LOGIN_EMAIL,
        organization_id=LOGIN_EMAIL,
    )
    plan_id = plan.get("id")
    page = await context.new_page()

    # Build a small TXT file
    txt = (
        "Past procurement reference: cleaning service contract 2024.\n"
        "Total value: 28,500 EUR. Duration: 12 months. Vendor: ACME Cleaning.\n"
        "Performance: 5 incidents reported, all resolved within SLA.\n"
    )
    multipart = {
        "conversation_id": "",
        "file": {
            "name": "past-cleaning.txt",
            "mimeType": "text/plain",
            "buffer": txt.encode("utf-8"),
        },
    }
    resp = await page.request.post(
        f"{BASE_URL}/api/chat/attach", multipart=multipart,
    )
    body = await resp.json()
    _log("attach succeeded", body.get("ok") is True, json.dumps(body)[:200])
    if not body.get("ok"):
        await page.close()
        return
    conv_id = body.get("conversation_id")
    msgs = _read_conversation_messages(conv_id)
    sys_primers = [m for m in msgs if m.get("role") == "system"]
    has_doc_primer = any("ATTACHED DOCUMENT" in (m.get("content") or "")
                         for m in sys_primers)
    has_doc_text = any("ACME Cleaning" in (m.get("content") or "")
                       for m in sys_primers)
    _log("ATTACHED DOCUMENT primer present", has_doc_primer)
    _log("document text reaches LLM context", has_doc_text)
    await page.close()


async def test_rfp_draft_doc_type_routing(context):
    print("\n[D] rfp_draft tool resolves description from chat context (#1189)")
    sys.path.insert(0, ".")
    from chat_service import chat_service
    from tools.rfp_draft import _detect_doc_type, _description_from_chat_context

    # Detection on text alone
    cases = [
        ({}, "draft the technical specification", "technical_specification"),
        ({"doc_type": "draft_contract"}, "", "draft_contract"),
        ({}, "tee mulle tehniline kirjeldus", "technical_specification"),
        ({}, "propose evaluation methodology", "evaluation_methodology"),
        ({}, "make me an espd form", "espd"),
        ({}, "just chatting", None),
    ]
    for params, desc, expected in cases:
        got = _detect_doc_type(params, desc)
        _log(f"detect_doc_type({params}, {desc!r}) → {got}", got == expected,
             f"expected {expected}")

    # Description fallback from system primer
    cid = chat_service.create_conversation(user_email=LOGIN_EMAIL, title="t")
    chat_service._append_message(cid, {
        "role": "system",
        "content": "ACTIVE PROCUREMENT PLAN — IT support, value €80,000",
        "tenders": [],
        "timestamp": "2026-01-01",
    })
    description = _description_from_chat_context({
        "chat_service": chat_service,
        "conversation_id": cid,
    })
    _log("primer pulled into rfp_draft description fallback",
         "ACTIVE PROCUREMENT PLAN" in description, description[:100])


async def test_chat_search_intent_rerouted(context):
    print("\n[E] chat reroutes search intent away from registry browsing (#1179)")
    sys.path.insert(0, ".")
    # We can't run the full LLM, but we can sanity-check the
    # fallback / heuristic path: process_message_sync with a stub
    # provider should not return tender cards.
    import asyncio as _aio
    from chat_service import chat_service

    async def _run():
        cid = chat_service.create_conversation(user_email=LOGIN_EMAIL, title="t")
        # The sync wrapper accumulates the streamed events. Under stub
        # credentials the LLM call fails gracefully and the heuristic
        # fallback takes over — we just need to confirm `tenders`
        # comes back empty.
        try:
            result = await _aio.wait_for(
                chat_service.process_message_sync(
                    conversation_id=cid,
                    user_message="show me IT tenders in Estonia",
                    user_email=LOGIN_EMAIL,
                    ui_language="en",
                ),
                timeout=20,
            )
        except _aio.TimeoutError:
            return None
        return result

    result = await _run()
    if result is None:
        _log("process_message_sync ran under stub keys",
             False, "timeout / LLM unreachable — skipping inline assertion")
    else:
        _log("no tender cards returned to UI",
             not result.get("tenders"),
             f"tenders={len(result.get('tenders') or [])}")


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context()
        await _login(context)

        await test_plan_primer_injection(context)
        await test_benchmark_primer_injection(context)
        await test_attached_doc_primer(context)
        await test_rfp_draft_doc_type_routing(context)
        await test_chat_search_intent_rerouted(context)

        await context.close()
        await browser.close()

    print(f"\n=== {PASSED} passed, {FAILED} failed ===")
    sys.exit(0 if FAILED == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
