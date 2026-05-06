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
                # Seed primer
                primer_lines = [
                    f"You are working on this plan:",
                    f"  Title: {plan.get('title', '')}",
                    f"  Category: {plan.get('category', '')}",
                    f"  Estimated value: €{plan.get('estimated_value', 0):,.0f}" if plan.get('estimated_value') else "",
                    f"  Procurement method: {plan.get('procurement_method', '')}",
                    f"  Status: {plan.get('status', '')}",
                    f"  Plan URL: /procurements/{plan_id}",
                ]
                meta = plan.get("metadata_json") or {}
                if isinstance(meta, dict):
                    crit = meta.get("evaluation_criteria") or []
                    if crit:
                        primer_lines.append("  Evaluation criteria: " +
                            ", ".join(f"{c.get('name','?')} ({c.get('weight','?')}%)" for c in crit[:5]))
                    reqs = meta.get("requirements") or []
                    if reqs:
                        primer_lines.append("  Requirements: " +
                            "; ".join(r.get("text","?") for r in reqs[:5]))
                primer = "\n".join(l for l in primer_lines if l)

                # Create a conversation with the primer + a friendly
                # opener so the messages history shows the context.
                cid = chat_service.create_conversation(
                    user_email=user_email,
                    title=f"Plan: {plan.get('title','')[:60]}",
                )
                chat_service._append_message(cid, {
                    "role": "system",
                    "content": primer,
                    "tenders": [],
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                })
                chat_service._append_message(cid, {
                    "role": "assistant",
                    "content": (
                        f"I've loaded your plan **\"{plan.get('title','')}\"** "
                        f"(category: {plan.get('category','—')}, "
                        f"estimated value: €{plan.get('estimated_value', 0):,.0f}).\n\n"
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
