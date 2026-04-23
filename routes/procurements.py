"""Procurement plan routes for Tendly Buyer."""

from starlette.responses import RedirectResponse

from components.layout import buyer_page
from components.procurements.plan_list import (
    procurement_list_page,
    procurement_new_page,
    procurement_detail_page,
)
from config.i18n import get_language_from_request
from routes.auth_utils import get_auth_from_request
from services.procurement_service import (
    create_plan, get_plan, list_plans, get_steps, complete_step, get_stats,
)


def register_procurement_routes(rt, chat_service):
    @rt("/procurements")
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        plans = list_plans()
        content = procurement_list_page(plans=plans, language=language)
        return buyer_page(content, language=language, auth=auth, active_page="procurements", chat_service=chat_service, title_key="procurements.page_title")

    @rt("/procurements/new")
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        content = procurement_new_page(language=language)
        return buyer_page(content, language=language, auth=auth, active_page="procurements", chat_service=chat_service, title_key="procurements.new_title")

    @rt("/procurements")
    async def post(request):
        form = await request.form()
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        plan = create_plan(
            title=form.get("title", "Untitled"),
            description=form.get("description", ""),
            category=form.get("category", "muu"),
            estimated_value=form.get("estimated_value") or None,
            cpv_code=form.get("cpv_code", ""),
            fiscal_year=int(form.get("fiscal_year") or 2026),
            procurement_method=form.get("procurement_method", "open"),
            created_by_email=user_email,
        )
        return RedirectResponse(f"/procurements/{plan['id']}", status_code=303)

    @rt("/procurements/{plan_id}")
    def get(request, plan_id: str):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        plan = get_plan(plan_id)
        if not plan:
            return RedirectResponse("/procurements", status_code=302)
        steps = get_steps(plan_id)
        content = procurement_detail_page(plan=plan, steps=steps, language=language)
        return buyer_page(content, language=language, auth=auth, active_page="procurements", chat_service=chat_service, title_key="procurements.page_title")

    @rt("/procurements/{plan_id}/steps/{step_num}/complete")
    async def post(request, plan_id: str, step_num: int):
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        complete_step(plan_id, step_num, completed_by=user_email)
        return RedirectResponse(f"/procurements/{plan_id}", status_code=303)
