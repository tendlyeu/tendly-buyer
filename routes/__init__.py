"""Route registration for Tendly Buyer."""

from fasthtml.core import all_meths

from routes.pages import register_page_routes
from routes.api import register_api_routes
from routes.auth import register_auth_routes
from routes.auth_utils import get_auth_from_request
from routes.procurements import register_procurement_routes
from routes.documents import register_document_routes
from routes.registry import register_registry_routes
from routes.team import register_team_routes


def _smart_rt(app_route):
    """Wrap app.route so handlers nested inside a register_* function still get
    their HTTP method inferred from the function name (get/post/delete/...).

    FastHTML 0.13.x infers the method from `nested_name(func)`, which for a
    nested handler becomes `register_xxx_get` and falls outside `all_meths` —
    causing every route to register for both GET and POST. We re-inject
    `methods=[func.__name__]` for any handler whose plain `__name__` is an HTTP
    verb and where `methods=` wasn't explicitly set."""

    def smart_rt(*args, **kwargs):
        def decorator(func):
            if "methods" not in kwargs and func.__name__ in all_meths:
                kw = dict(kwargs)
                kw["methods"] = [func.__name__]
                return app_route(*args, **kw)(func)
            return app_route(*args, **kwargs)(func)
        return decorator

    return smart_rt


def register_routes(app, chat_service):
    """Register all routes with the FastHTML app."""
    rt = _smart_rt(app.route)
    register_page_routes(rt, chat_service)
    register_api_routes(rt, chat_service)
    register_auth_routes(rt, chat_service)
    register_procurement_routes(rt, chat_service)
    register_document_routes(rt, chat_service)
    register_registry_routes(rt, chat_service)
    register_team_routes(rt, chat_service)
