"""Page routes for Tendly Buyer."""

from components.layout import chat_page, buyer_page
from components.dashboard.overview import dashboard_page_content
from config.i18n import get_language_from_request
from routes.auth_utils import get_auth_from_request
from core.rate_limiter import get_usage_info
from services.procurement_service import list_plans, get_stats


def register_page_routes(rt, chat_service):
    @rt("/")
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        stats = get_stats()
        plans = list_plans()
        content = dashboard_page_content(plans=plans, stats=stats, language=language)
        return buyer_page(content, language=language, auth=auth, active_page="dashboard", chat_service=chat_service, title_key="dashboard.page_title")

    @rt("/chat")
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        rate_info = get_usage_info(request, user_email)
        return chat_page(chat_service=chat_service, language=language, auth=auth, rate_info=rate_info)

    @rt("/chat/c/{conversation_id}")
    def get(request, conversation_id: str):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        rate_info = get_usage_info(request, user_email)
        conv = chat_service.get_conversation(conversation_id)
        if not conv:
            return chat_page(chat_service=chat_service, language=language, auth=auth, rate_info=rate_info)
        return chat_page(conversation_id=conversation_id, messages=conv.get("messages", []), chat_service=chat_service, language=language, auth=auth, rate_info=rate_info)
