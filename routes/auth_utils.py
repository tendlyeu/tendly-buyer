"""Auth utilities for route handlers."""

from functools import wraps
from inspect import iscoroutinefunction

from starlette.responses import JSONResponse, RedirectResponse


def get_auth_from_request(request):
    """Extract auth data from session. Returns dict or None."""
    try:
        session = request.session
        return session.get('auth', None)
    except Exception:
        return None


def _is_unauth_response(request):
    """Build the right unauthenticated response for the request:
    - JSON 401 for /api/* (and HTMX/XHR/JSON Accept)
    - 302 redirect to /login for normal page navigations."""
    path = getattr(request.url, "path", "")
    accept = request.headers.get("accept", "")
    if path.startswith("/api/") or "application/json" in accept or request.headers.get("hx-request"):
        return JSONResponse({"error": "authentication required"}, status_code=401)
    return RedirectResponse(url="/login?error=auth_required", status_code=302)


def require_auth(handler):
    """Decorator that blocks anonymous access to a route handler.

    Works for both `def` and `async def` handlers, with the FastHTML/Starlette
    convention of `request` as the first arg (or as a `request=` kwarg)."""

    def _request_from(args, kwargs):
        if args and hasattr(args[0], "session"):
            return args[0]
        return kwargs.get("request")

    if iscoroutinefunction(handler):
        @wraps(handler)
        async def wrapped(*args, **kwargs):
            req = _request_from(args, kwargs)
            if req is None or not get_auth_from_request(req):
                return _is_unauth_response(req) if req is not None else JSONResponse({"error": "authentication required"}, status_code=401)
            return await handler(*args, **kwargs)
        return wrapped
    else:
        @wraps(handler)
        def wrapped(*args, **kwargs):
            req = _request_from(args, kwargs)
            if req is None or not get_auth_from_request(req):
                return _is_unauth_response(req) if req is not None else JSONResponse({"error": "authentication required"}, status_code=401)
            return handler(*args, **kwargs)
        return wrapped
