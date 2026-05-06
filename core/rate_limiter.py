"""
Rate limiter for Tendly Chat.
Tracks usage by IP (anonymous) and user email (authenticated).
Limits:
- Anonymous: 5 messages total (override with TENDLY_ANON_LIMIT)
- Authenticated users: UNLIMITED by default. Set TENDLY_FREE_DAILY_LIMIT
  to a positive integer to re-enable the per-user daily cap (was 20).
- Paid users (professional/enterprise): Unlimited
"""

import os
import time
from collections import defaultdict


# In-memory stores (reset on server restart)
_ip_usage = defaultdict(list)      # IP -> list of timestamps
_user_usage = defaultdict(list)    # email -> list of timestamps

# Limits — env-overridable so staging / load tests can lift the cap
# without code changes. 0 (or negative) = unlimited.
# Default 0 → no cap for anyone (anonymous or authenticated). Set the
# corresponding env var to a positive integer to re-enable a cap.
ANONYMOUS_LIMIT = int(os.environ.get("TENDLY_ANON_LIMIT", "0"))
FREE_USER_DAILY_LIMIT = int(os.environ.get("TENDLY_FREE_DAILY_LIMIT", "0"))
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
        from core.database import get_session

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

        # FREE_USER_DAILY_LIMIT <= 0 means "unlimited" (the default since
        # we want logged-in buyers to use the chat freely while drafting
        # tenders). Set TENDLY_FREE_DAILY_LIMIT=20 in the env to bring
        # the old cap back.
        if FREE_USER_DAILY_LIMIT <= 0:
            return {
                "allowed": True,
                "remaining": -1,
                "limit": -1,
                "reason": "",
                "tier": "free",
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
        # Anonymous user: total limit tracked by IP. ANONYMOUS_LIMIT <= 0
        # means unlimited (the default — we don't gate the buyer chat at
        # all anymore). Set TENDLY_ANON_LIMIT in the env to re-enable.
        if ANONYMOUS_LIMIT <= 0:
            return {
                "allowed": True,
                "remaining": -1,
                "limit": -1,
                "reason": "",
                "tier": "anonymous",
            }

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
