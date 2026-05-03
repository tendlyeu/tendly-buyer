"""
Tendly Buyer - AI-powered procurement buyer portal.
Entry point for the FastHTML application.
"""

import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(override=True)

from fasthtml.common import *
from starlette.middleware.sessions import SessionMiddleware

# GA4 Measurement ID (same as main tendly app for cross-domain tracking)
GA4_MEASUREMENT_ID = "G-EVV9Z173MN"

# ---------------------------------------------------------------------------
# Chat service import with graceful fallback
# ---------------------------------------------------------------------------
try:
    from chat_service import chat_service
    _CHAT_SERVICE_OK = True
except Exception as _import_err:
    print(f"Warning: chat_service import failed ({_import_err}). Using fallback.")
    _CHAT_SERVICE_OK = False

    class _FallbackChatService:
        """Minimal stub so the UI always renders."""
        def __init__(self):
            self.conversations = {}

        def create_conversation(self):
            cid = str(uuid.uuid4())
            self.conversations[cid] = {
                "messages": [], "created_at": datetime.utcnow().isoformat(), "title": "New conversation",
            }
            return cid

        def get_conversations(self):
            return sorted(
                [{"id": k, "title": v["title"], "created_at": v["created_at"], "message_count": len(v["messages"])} for k, v in self.conversations.items()],
                key=lambda c: c["created_at"], reverse=True,
            )

        def get_conversation(self, cid):
            c = self.conversations.get(cid)
            if not c:
                return None
            return {"id": cid, **c}

        def delete_conversation(self, cid):
            return self.conversations.pop(cid, None) is not None

        async def process_message(self, cid, msg):
            if cid not in self.conversations:
                self.conversations[cid] = {"messages": [], "created_at": datetime.utcnow().isoformat(), "title": msg[:60]}
            conv = self.conversations[cid]
            if conv["title"] == "New conversation":
                conv["title"] = msg[:60]
            conv["messages"].append({"role": "user", "content": msg, "tenders": [], "timestamp": datetime.utcnow().isoformat()})
            resp = "The chat service is currently unavailable. Please check the server logs and try again."
            conv["messages"].append({"role": "assistant", "content": resp, "tenders": [], "timestamp": datetime.utcnow().isoformat()})
            return {"response": resp, "tenders": [], "conversation_id": cid, "title": conv["title"]}

        def get_tender_detail(self, tid):
            return None

    chat_service = _FallbackChatService()

# ---------------------------------------------------------------------------
# Import CSS/JS and register routes
# ---------------------------------------------------------------------------
from static import CSS_STYLES, JS_CODE
from routes import register_routes

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app, rt = fast_app(
    hdrs=[
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Link(rel="icon", type="image/svg+xml", href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0%25' stop-color='%232563eb'/%3E%3Cstop offset='100%25' stop-color='%237c3aed'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='32' height='32' rx='8' fill='url(%23g)'/%3E%3Ctext x='50%25' y='55%25' text-anchor='middle' dominant-baseline='central' fill='white' font-size='18' font-weight='700' font-family='system-ui'%3ET%3C/text%3E%3C/svg%3E"),
        # Google Consent Mode v2 defaults + GA4 with cross-domain tracking
        Script(f"""
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('consent', 'default', {{
                'ad_storage': 'denied',
                'ad_user_data': 'denied',
                'ad_personalization': 'denied',
                'analytics_storage': 'denied',
                'functionality_storage': 'denied',
                'personalization_storage': 'denied',
                'security_storage': 'granted',
                'wait_for_update': 500
            }});
            // Restore consent from localStorage
            (function() {{
                var consent = localStorage.getItem('tendly_cookie_consent');
                var prefs = JSON.parse(localStorage.getItem('tendly_cookie_preferences') || '{{}}');
                if (consent && consent !== 'rejected') {{
                    var ag = prefs.analytics ? 'granted' : 'denied';
                    var mg = prefs.marketing ? 'granted' : 'denied';
                    var pg = prefs.preferences ? 'granted' : 'denied';
                    gtag('consent', 'update', {{
                        'ad_storage': mg, 'ad_user_data': mg, 'ad_personalization': mg,
                        'analytics_storage': ag, 'functionality_storage': pg, 'personalization_storage': pg
                    }});
                }}
            }})();
        """, type="text/javascript"),
        Script(src=f"https://www.googletagmanager.com/gtag/js?id={GA4_MEASUREMENT_ID}", async_=True),
        Script(f"""
            gtag('js', new Date());
            gtag('set', 'linker', {{'domains': ['tendly.eu', 'buyer.tendly.eu', 'chat.tendly.eu']}});
            gtag('config', '{GA4_MEASUREMENT_ID}', {{'send_page_view': true}});
        """, type="text/javascript"),
        Style(CSS_STYLES),
        Script(JS_CODE),
    ],
    live=False,
)

register_routes(app, chat_service)

# Add session middleware (same secret as main tendly app for shared auth)
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET", "tendly-dev-secret-key"))

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5004)))
