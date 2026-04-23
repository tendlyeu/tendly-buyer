"""Dashboard routes for Tendly Buyer."""

from starlette.responses import RedirectResponse

from components.layout import buyer_page
from components.dashboard.overview import dashboard_page_content
from config.i18n import get_language_from_request
from routes.auth_utils import get_auth_from_request


def register_dashboard_routes(rt, chat_service):
    pass
