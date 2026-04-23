"""
Rate limiter for Tendly Chat.
Tracks usage by IP (anonymous) and user email (authenticated).
Limits:
- Anonymous: 5 messages total
- Free users (starter plan): 20 messages per day
- Paid users (professional/enterprise): Unlimited
"""

import time
from collections import defaultdict


# In-memory stores (reset on server restart)
_ip_usage = defaultdict(list)      # IP -> list of timestamps
_user_usage = defaultdict(list)    # email -> list of timestamps

# Limits
ANONYMOUS_LIMIT = 5                 # Total messages for non-logged-in users
FREE_USER_DAILY_LIMIT = 20          # Messages per day for free users
PAID_PLANS = {"professional", "enterprise"}

# Time window: 24 hours in seconds
DAY_SECONDS = 86400


def _clean_old_entries(entries, window_seconds=DAY_SECONDS):
    """Remove entries older than the time window."""
    cutoff = time.time() - window_seconds
    return [ts for ts in entries if ts > cutoff]


def _get_user_plan(email):
    """Look up user subscription plan from the database."""
    try:
        from sqlalchemy import text
        from database import get_session

        db = get_session()
        try:
            row = db.execute(
                text("SELECT plan, status FROM subscriptions WHERE user_email = :email"),
                {"email": email}
            ).fetchone()
            if row and row[1] == "active":
                return row[0]
        finally:
            db.close()
    except Exception:
        pass
    return "starter"


def check_rate_limit(request, user_email=None):
    """
    Check if the request is within rate limits.

    Returns:
        dict with keys:
            - allowed (bool): Whether the message is allowed
            - remaining (int): Messages remaining (-1 for unlimited)
            - limit (int): Total limit (-1 for unlimited)
            - reason (str): Reason if blocked
            - tier (str): 'anonymous', 'free', 'paid'
    """
    if user_email:
        # Authenticated user
        plan = _get_user_plan(user_email)

        if plan in PAID_PLANS:
            return {
                "allowed": True,
                "remaining": -1,
                "limit": -1,
                "reason": "",
                "tier": "paid",
            }

        # Free user: daily limit
        key = user_email.lower().strip()
        _user_usage[key] = _clean_old_entries(_user_usage[key])
        used = len(_user_usage[key])
        remaining = max(0, FREE_USER_DAILY_LIMIT - used)

        if used >= FREE_USER_DAILY_LIMIT:
            return {
                "allowed": False,
                "remaining": 0,
                "limit": FREE_USER_DAILY_LIMIT,
                "reason": "daily_limit",
                "tier": "free",
            }

        return {
            "allowed": True,
            "remaining": remaining,
            "limit": FREE_USER_DAILY_LIMIT,
            "reason": "",
            "tier": "free",
        }
    else:
        # Anonymous user: total limit tracked by IP
        ip = _get_client_ip(request)
        used = len(_ip_usage[ip])
        remaining = max(0, ANONYMOUS_LIMIT - used)

        if used >= ANONYMOUS_LIMIT:
            return {
                "allowed": False,
                "remaining": 0,
                "limit": ANONYMOUS_LIMIT,
                "reason": "anonymous_limit",
                "tier": "anonymous",
            }

        return {
            "allowed": True,
            "remaining": remaining,
            "limit": ANONYMOUS_LIMIT,
            "reason": "",
            "tier": "anonymous",
        }


def record_usage(request, user_email=None):
    """Record a message usage after successful processing."""
    now = time.time()
    if user_email:
        key = user_email.lower().strip()
        _user_usage[key].append(now)
    else:
        ip = _get_client_ip(request)
        _ip_usage[ip].append(now)


def get_usage_info(request, user_email=None):
    """Get current usage info without recording."""
    return check_rate_limit(request, user_email)


def _get_client_ip(request):
    """Extract client IP from request, handling proxies."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = getattr(request, "client", None)
    if client:
        return client.host
    return "unknown"
