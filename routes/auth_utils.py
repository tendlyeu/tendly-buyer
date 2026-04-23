"""Auth utilities for route handlers."""


def get_auth_from_request(request):
    """Extract auth data from session. Returns dict or None."""
    try:
        session = request.session
        return session.get('auth', None)
    except Exception:
        return None
