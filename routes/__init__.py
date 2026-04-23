"""Route registration for Tendly Buyer."""

from routes.pages import register_page_routes
from routes.api import register_api_routes
from routes.auth import register_auth_routes
from routes.auth_utils import get_auth_from_request
from routes.procurements import register_procurement_routes
from routes.documents import register_document_routes
from routes.registry import register_registry_routes
from routes.team import register_team_routes


def register_routes(app, chat_service):
    """Register all routes with the FastHTML app."""
    rt = app.route
    register_page_routes(rt, chat_service)
    register_api_routes(rt, chat_service)
    register_auth_routes(rt, chat_service)
    register_procurement_routes(rt, chat_service)
    register_document_routes(rt, chat_service)
    register_registry_routes(rt, chat_service)
    register_team_routes(rt, chat_service)
