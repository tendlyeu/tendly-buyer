"""Page routes for Tendly Buyer."""

from starlette.responses import RedirectResponse

from components.layout import chat_page, buyer_page
from components.dashboard.overview import dashboard_page_content
from config.i18n import get_language_from_request
from routes.auth_utils import get_auth_from_request
from core.rate_limiter import get_usage_info
from services.procurement_service import list_plans, get_stats, get_plan


def register_page_routes(rt, chat_service):
    @rt("/")
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        # Dashboard stats and "recent plans" are always scoped to the
        # logged-in user. Anonymous landing on / sees zeroes.
        stats = get_stats(organization_id=user_email) if user_email else {}
        plans = list_plans(organization_id=user_email) if user_email else []
        content = dashboard_page_content(plans=plans, stats=stats, language=language)
        return buyer_page(content, language=language, auth=auth, active_page="dashboard", chat_service=chat_service, title_key="dashboard.page_title")

    @rt("/chat")
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        rate_info = get_usage_info(request, user_email)

        # When the buyer clicks "Ask AI" on a plan detail page, the link
        # is /chat?plan={id}. Pre-create a conversation seeded with a
        # primer message about that plan so the LLM has it as context
        # from the very first user turn (no need to re-explain the plan).
        plan_id = request.query_params.get("plan")
        if plan_id and user_email:
            plan = get_plan(plan_id)
            if plan and (plan.get("organization_id") == user_email or
                         plan.get("created_by_email") == user_email):
                # Build a rich primer with everything the buyer filled into
                # the plan form. The LLM uses this as the conversation's
                # opening system context, so when the user asks "what's
                # missing?" or "draft an RFP", it already knows the plan.
                meta = plan.get("metadata_json") or {}
                if isinstance(meta, str):
                    try:
                        import json as _json
                        meta = _json.loads(meta)
                    except Exception:
                        meta = {}
                if not isinstance(meta, dict):
                    meta = {}

                est_val = plan.get("estimated_value")
                primer_lines = [
                    "ACTIVE PROCUREMENT PLAN — the buyer is working on this plan and "
                    "expects every answer to be grounded in its details. Use these "
                    "fields directly, do not ask for them again.",
                    "",
                    f"Title: {plan.get('title') or '(no title)'}",
                ]
                if plan.get("description"):
                    primer_lines.append(f"Description: {plan.get('description')}")
                if plan.get("category"):
                    primer_lines.append(f"Category: {plan.get('category')}")
                if est_val:
                    try:
                        primer_lines.append(f"Estimated value: €{float(est_val):,.0f}")
                    except (TypeError, ValueError):
                        primer_lines.append(f"Estimated value: {est_val}")
                if plan.get("cpv_code"):
                    primer_lines.append(f"CPV code: {plan.get('cpv_code')}")
                if plan.get("fiscal_year"):
                    primer_lines.append(f"Fiscal year: {plan.get('fiscal_year')}")
                if plan.get("procurement_method"):
                    primer_lines.append(f"Procurement method: {plan.get('procurement_method')}")
                if plan.get("status"):
                    primer_lines.append(f"Status: {plan.get('status')}")
                if meta.get("submission_deadline"):
                    primer_lines.append(f"Submission deadline: {meta.get('submission_deadline')}")

                crit = meta.get("evaluation_criteria") or []
                if crit:
                    primer_lines.append("")
                    primer_lines.append("Evaluation criteria:")
                    for c in crit:
                        name = c.get("name") or c.get("criterion_name") or "(unnamed)"
                        weight = c.get("weight") or c.get("weight_percentage") or ""
                        desc = c.get("description") or ""
                        line = f"  - {name}"
                        if weight != "":
                            line += f" ({weight}%)"
                        if desc:
                            line += f" — {desc}"
                        primer_lines.append(line)

                reqs = meta.get("requirements") or []
                if reqs:
                    primer_lines.append("")
                    primer_lines.append("Requirements:")
                    for r in reqs:
                        text = r.get("text") or "(no text)"
                        rtype = r.get("type") or ""
                        prio = r.get("priority") or ""
                        suffix_bits = [b for b in (rtype, prio) if b]
                        suffix = f" [{', '.join(suffix_bits)}]" if suffix_bits else ""
                        primer_lines.append(f"  - {text}{suffix}")

                primer_lines.append("")
                primer_lines.append(f"Plan URL: /procurements/{plan_id}")
                primer = "\n".join(primer_lines)

                cid = chat_service.create_conversation(
                    user_email=user_email,
                    title=f"Plan: {plan.get('title','')[:60]}",
                )
                # Persist plan_id on the conversation so any later prompt
                # builders can re-inject the plan context if it falls out
                # of the recent-history window.
                try:
                    chat_service.set_conversation_metadata(cid, {"plan_id": plan_id})
                except AttributeError:
                    pass
                chat_service._append_message(cid, {
                    "role": "system",
                    "content": primer,
                    "tenders": [],
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                })
                est_str = ""
                if est_val:
                    try: est_str = f", estimated value €{float(est_val):,.0f}"
                    except (TypeError, ValueError): est_str = ""
                chat_service._append_message(cid, {
                    "role": "assistant",
                    "content": (
                        f"I've loaded your plan **\"{plan.get('title','')}\"** "
                        f"(category: {plan.get('category','—')}{est_str}).\n\n"
                        f"How can I help — review requirements, draft documents, "
                        f"benchmark against similar past tenders, or propose "
                        f"evaluation criteria?"
                    ),
                    "tenders": [],
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                })
                return RedirectResponse(f"/chat/c/{cid}", status_code=302)

        return chat_page(chat_service=chat_service, language=language, auth=auth, rate_info=rate_info)

    @rt("/chat/c/{conversation_id}")
    def get(request, conversation_id: str):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        rate_info = get_usage_info(request, user_email)
        conv = chat_service.get_conversation(conversation_id, user_email=user_email)
        if not conv:
            return chat_page(chat_service=chat_service, language=language, auth=auth, rate_info=rate_info)
        return chat_page(conversation_id=conversation_id, messages=conv.get("messages", []), chat_service=chat_service, language=language, auth=auth, rate_info=rate_info)
