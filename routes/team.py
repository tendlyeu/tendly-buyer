"""Team management routes for Tendly Buyer."""

from fasthtml.common import *
from starlette.responses import RedirectResponse

from components.layout import buyer_page
from config.i18n import get_language_from_request, t
from routes.auth_utils import get_auth_from_request, require_auth
from core.utils import _raw
from services.procurement_service import list_team_members, add_team_member, remove_team_member

ROLES = [
    ("domain_lead", "Domain Lead / Valdkonna juht"),
    ("procurement_manager", "Procurement Manager / Hankejuht"),
    ("board", "Board / Juhatus"),
    ("domain_specialist", "Domain Specialist / Valdkonna spetsialist"),
]

SPECIALTIES = [
    ("it", "IT & Technology"),
    ("kinnisvara", "Real Estate / Kinnisvara"),
    ("personal", "Personnel / Personal"),
    ("toitlustus", "Catering / Toitlustus"),
    ("ehitus", "Construction / Ehitus"),
    ("muu", "Other / Muu"),
]


def _member_card(member):
    role_colors = {
        "domain_lead": "#2563eb",
        "procurement_manager": "#7c3aed",
        "board": "#059669",
        "domain_specialist": "#d97706",
    }
    role = member.get("procurement_role", "")
    color = role_colors.get(role, "#6b7280")
    initial = (member.get("name") or member.get("user_email", "?"))[0].upper()

    return Div(
        Div(
            Div(initial, style=f"width:36px;height:36px;border-radius:50%;background:{color};color:white;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:14px;flex-shrink:0;"),
            Div(
                Div(member.get("name") or member.get("user_email", ""), style="font-size:14px;font-weight:600;color:#111827;"),
                Div(
                    Span(role.replace("_", " ").title(), style=f"font-size:11px;font-weight:600;color:{color};"),
                    Span(f" · {member.get('specialty', '').replace('_', ' ').title()}", style="font-size:11px;color:#9ca3af;") if member.get("specialty") else "",
                ),
                Div(member.get("user_email", ""), style="font-size:12px;color:#9ca3af;margin-top:1px;"),
            ),
            style="display:flex;align-items:center;gap:12px;",
        ),
        style="padding:12px 16px;background:white;border:1px solid #e5e7eb;border-radius:10px;margin-bottom:8px;",
    )


def _team_page_content(members, language="en"):
    role_options = [Option(label, value=val) for val, label in ROLES]
    specialty_options = [Option(label, value=val) for val, label in SPECIALTIES]

    add_form = Div(
        H3(t("team.add_member", language), style="font-size:15px;font-weight:600;color:#111827;margin:0 0 12px;"),
        Form(
            Div(
                Div(
                    Label(t("form.name", language), cls="form-label"),
                    Input(name="name", type="text", placeholder=t("form.full_name_placeholder", language), cls="form-input", required=True),
                    cls="form-group",
                ),
                Div(
                    Label(t("form.email", language), cls="form-label"),
                    Input(name="user_email", type="email", placeholder=t("form.email_placeholder", language), cls="form-input", required=True),
                    cls="form-group",
                ),
                cls="form-row",
            ),
            Div(
                Div(
                    Label(t("form.role", language), cls="form-label"),
                    Select(*role_options, name="procurement_role", cls="form-select"),
                    cls="form-group",
                ),
                Div(
                    Label(t("form.specialty", language), cls="form-label"),
                    Select(*specialty_options, name="specialty", cls="form-select"),
                    cls="form-group",
                ),
                cls="form-row",
            ),
            Div(
                Button(t("team.add", language), type="submit", cls="btn-primary"),
                cls="form-actions", style="justify-content:flex-start;border-top:none;margin-top:8px;padding-top:0;",
            ),
            action="/api/team",
            method="post",
        ),
        cls="dashboard-section",
    )

    if members:
        member_list = Div(*[_member_card(m) for m in members])
    else:
        member_list = Div(
            _raw('<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>'),
            P(t("team.empty", language), style="color:#6b7280;font-size:14px;margin:12px 0;"),
            style="text-align:center;padding:32px 0;",
        )

    return Div(
        Div(
            H1(t("team.title", language), style="font-size:22px;font-weight:700;color:#111827;margin:0;"),
            P(t("team.subtitle", language), style="font-size:14px;color:#6b7280;margin:4px 0 0;"),
            cls="page-header",
        ),
        add_form,
        Div(
            H3(t("team.members", language), style="font-size:15px;font-weight:600;color:#111827;margin:0 0 12px;"),
            member_list,
            cls="dashboard-section",
        ),
        cls="page-content",
    )


def register_team_routes(rt, chat_service):
    @rt("/team")
    @require_auth
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        members = list_team_members("default")
        content = _team_page_content(members, language)
        return buyer_page(content, language=language, auth=auth, active_page="team", chat_service=chat_service, title_key="team.page_title")

    @rt("/api/team")
    @require_auth
    async def post(request):
        form = await request.form()
        add_team_member(
            organization_id="default",
            user_email=form.get("user_email", ""),
            name=form.get("name", ""),
            procurement_role=form.get("procurement_role", ""),
            specialty=form.get("specialty", ""),
        )
        return RedirectResponse("/team", status_code=303)
