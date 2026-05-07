"""Team management routes for Tendly Buyer.

Team management is gated behind a "coming soon" placeholder until the
invite/email flow is wired up. The form previously rendered here
appeared to add members but never sent invitations, so it's hidden
until the feature lands.
"""

from fasthtml.common import *
from starlette.responses import RedirectResponse

from components.layout import buyer_page
from config.i18n import get_language_from_request, t
from routes.auth_utils import get_auth_from_request, require_auth
from core.utils import _raw


def _team_coming_soon_content(language="en"):
    return Div(
        Div(
            H1(t("team.title", language), style="font-size:22px;font-weight:700;color:#111827;margin:0;"),
            P(t("team.subtitle", language), style="font-size:14px;color:#6b7280;margin:4px 0 0;"),
            cls="page-header",
        ),
        Div(
            Div(
                _raw(
                    '<svg width="56" height="56" viewBox="0 0 24 24" fill="none" '
                    'stroke="#3b82f6" stroke-width="1.5" stroke-linecap="round" '
                    'stroke-linejoin="round" style="margin-bottom:14px;">'
                    '<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>'
                    '<circle cx="9" cy="7" r="4"/>'
                    '<path d="M23 21v-2a4 4 0 00-3-3.87"/>'
                    '<path d="M16 3.13a4 4 0 010 7.75"/>'
                    '</svg>'
                ),
                H2(
                    t("team.coming_soon_title", language) or "Team management — coming soon",
                    style="font-size:18px;font-weight:700;color:#111827;margin:0 0 8px;",
                ),
                P(
                    t("team.coming_soon_body", language)
                    or (
                        "Soon you'll be able to invite procurement managers, "
                        "domain leads and board approvers to collaborate on "
                        "plans. We're polishing the invite flow — stay tuned."
                    ),
                    style="font-size:14px;color:#4b5563;line-height:1.6;max-width:520px;margin:0 auto;",
                ),
                style="text-align:center;padding:48px 24px;",
            ),
            cls="dashboard-section",
            style="background:white;",
        ),
        cls="page-content",
    )


def register_team_routes(rt, chat_service):
    @rt("/team")
    @require_auth
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        content = _team_coming_soon_content(language)
        return buyer_page(content, language=language, auth=auth, active_page="team", chat_service=chat_service, title_key="team.page_title")

    @rt("/api/team")
    @require_auth
    async def post(request):
        # Team management is disabled; redirect to the coming-soon page
        # rather than silently writing a member that won't get an invite.
        return RedirectResponse("/team", status_code=303)
