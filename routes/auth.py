"""Authentication routes for Tendly Chat (login/logout)."""

import bcrypt

from starlette.responses import RedirectResponse, HTMLResponse
from fasthtml.common import *

from core.database import get_user, get_tendly_user, create_tendly_user
from config.i18n import t, get_language_from_request


def register_auth_routes(rt, chat_service):

    @rt("/login")
    def get(request):
        language = get_language_from_request(request)
        # Check if already logged in
        auth = request.session.get("auth")
        if auth and auth.get("email"):
            return RedirectResponse(url="/", status_code=302)

        error = request.query_params.get("error", "")
        return _login_page(language, error)

    @rt("/api/auth/login")
    async def post(request):
        language = get_language_from_request(request)
        try:
            data = await request.form()
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
        except Exception:
            return RedirectResponse(url="/login?error=invalid", status_code=302)

        if not email or not password:
            return RedirectResponse(url="/login?error=missing", status_code=302)

        # Look up user — try tendly schema first, then main users table
        tendly_user = get_tendly_user(email)
        user = get_user(email)

        if not tendly_user and not user:
            return RedirectResponse(url="/login?error=invalid", status_code=302)

        # Verify password (check whichever user we found)
        auth_user = tendly_user or user
        try:
            password_valid = bcrypt.checkpw(
                password.encode("utf-8"),
                auth_user.password_hash.encode("utf-8"),
            )
        except Exception:
            password_valid = False

        if not password_valid:
            return RedirectResponse(url="/login?error=invalid", status_code=302)

        if not auth_user.is_active:
            return RedirectResponse(url="/login?error=inactive", status_code=302)

        # Determine role: tendly schema user has explicit role, default to 'buyer'
        role = getattr(tendly_user, 'role', 'buyer') if tendly_user else 'buyer'

        # Set session auth with role
        request.session["auth"] = {
            "email": auth_user.email,
            "name": getattr(auth_user, 'name', '') or auth_user.email.split("@")[0],
            "role": role,
        }

        return RedirectResponse(url="/", status_code=302)

    @rt("/signup")
    def get(request):
        language = get_language_from_request(request)
        # Check if already logged in
        auth = request.session.get("auth")
        if auth and auth.get("email"):
            return RedirectResponse(url="/", status_code=302)

        error = request.query_params.get("error", "")
        return _signup_page(language, error)

    @rt("/api/auth/signup")
    async def post(request):
        language = get_language_from_request(request)
        try:
            data = await request.form()
            name = data.get("name", "").strip()
            email = data.get("email", "").strip().lower()
            company = data.get("company", "").strip()
            password = data.get("password", "")
            confirm_password = data.get("confirm_password", "")
        except Exception:
            return RedirectResponse(url="/signup?error=failed", status_code=302)

        if not name or not email or not password or not confirm_password:
            return RedirectResponse(url="/signup?error=missing", status_code=302)

        # Basic email format validation
        if "@" not in email or "." not in email.split("@")[-1]:
            return RedirectResponse(url="/signup?error=missing", status_code=302)

        if password != confirm_password:
            return RedirectResponse(url="/signup?error=password_mismatch", status_code=302)

        # Check if email already exists
        existing = get_tendly_user(email)
        if existing:
            return RedirectResponse(url="/signup?error=email_exists", status_code=302)

        # Hash password and create user
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        success = create_tendly_user(email, password_hash, name, role='buyer', company=company)

        if not success:
            return RedirectResponse(url="/signup?error=failed", status_code=302)

        # Set session
        request.session["auth"] = {"email": email, "name": name, "role": "buyer"}
        return RedirectResponse(url="/", status_code=302)

    @rt("/logout")
    def get(request):
        request.session.pop("auth", None)
        return RedirectResponse(url="/", status_code=302)


def _login_page(language, error=""):
    """Render a standalone login page matching the chat aesthetic."""
    error_html = ""
    if error == "invalid":
        error_html = t("auth.login_error_invalid", language)
    elif error == "missing":
        error_html = t("auth.login_error_missing", language)
    elif error == "inactive":
        error_html = t("auth.login_error_inactive", language)

    return (
        Title(t("auth.login_page_title", language)),
        Style(_LOGIN_CSS),
        Body(
            Div(
                Div(
                    Div(
                        Div("T", cls="login-logo-mark"),
                        Span("Tendly", cls="login-logo-text"),
                        Span(t("app.chat", language), cls="login-logo-badge"),
                        Span("BETA", cls="login-logo-badge-beta"),
                        cls="login-logo",
                    ),
                    H1(t("auth.login_title", language), cls="login-heading"),
                    P(t("auth.login_subtitle", language), cls="login-subtext"),
                    Div(
                        Span(error_html, cls="login-error-text"),
                        cls="login-error",
                    ) if error_html else None,
                    Form(
                        Div(
                            Label(t("auth.email_label", language), cls="login-label", _for="email"),
                            Input(
                                type="email",
                                name="email",
                                id="email",
                                placeholder=t("auth.email_placeholder", language),
                                required=True,
                                autofocus=True,
                                cls="login-input",
                            ),
                            cls="login-field",
                        ),
                        Div(
                            Label(t("auth.password_label", language), cls="login-label", _for="password"),
                            Input(
                                type="password",
                                name="password",
                                id="password",
                                placeholder=t("auth.password_placeholder", language),
                                required=True,
                                cls="login-input",
                            ),
                            cls="login-field",
                        ),
                        Button(
                            t("auth.login_button", language),
                            type="submit",
                            cls="login-submit-btn",
                        ),
                        action="/api/auth/login",
                        method="post",
                        cls="login-form",
                    ),
                    Div(
                        Span(t("auth.no_account", language)),
                        A(
                            t("auth.signup_button", language),
                            href="/signup",
                            cls="login-signup-link",
                        ),
                        cls="login-footer-text",
                    ),
                    A(
                        t("auth.back_to_chat", language),
                        href="/",
                        cls="login-back-link",
                    ),
                    cls="login-card",
                ),
                cls="login-page",
            ),
        ),
    )


def _signup_page(language, error=""):
    """Render a standalone signup page matching the login page aesthetic."""
    error_html = ""
    if error == "missing":
        error_html = t("auth.login_error_missing", language)
    elif error == "password_mismatch":
        error_html = t("auth.password_mismatch", language)
    elif error == "email_exists":
        error_html = t("auth.email_exists", language)
    elif error == "failed":
        error_html = t("auth.signup_failed", language)

    return (
        Title(t("auth.signup_title", language)),
        Style(_LOGIN_CSS),
        Body(
            Div(
                Div(
                    Div(
                        Div("T", cls="login-logo-mark"),
                        Span("Tendly", cls="login-logo-text"),
                        Span(t("app.buyer_badge", language), cls="login-logo-badge"),
                        Span("BETA", cls="login-logo-badge-beta"),
                        cls="login-logo",
                    ),
                    H1(t("auth.signup_title", language), cls="login-heading"),
                    P(t("auth.signup_subtitle", language), cls="login-subtext"),
                    Div(
                        Span(error_html, cls="login-error-text"),
                        cls="login-error",
                    ) if error_html else None,
                    Form(
                        Div(
                            Label(t("auth.name_label", language), cls="login-label", _for="name"),
                            Input(
                                type="text",
                                name="name",
                                id="name",
                                placeholder=t("auth.name_placeholder", language),
                                required=True,
                                autofocus=True,
                                cls="login-input",
                            ),
                            cls="login-field",
                        ),
                        Div(
                            Label(t("auth.email_label", language), cls="login-label", _for="email"),
                            Input(
                                type="email",
                                name="email",
                                id="email",
                                placeholder=t("auth.email_placeholder", language),
                                required=True,
                                cls="login-input",
                            ),
                            cls="login-field",
                        ),
                        Div(
                            Label(t("auth.company_label", language), cls="login-label", _for="company"),
                            Input(
                                type="text",
                                name="company",
                                id="company",
                                placeholder=t("auth.company_placeholder", language),
                                required=True,
                                cls="login-input",
                            ),
                            cls="login-field",
                        ),
                        Div(
                            Label(t("auth.password_label", language), cls="login-label", _for="password"),
                            Input(
                                type="password",
                                name="password",
                                id="password",
                                placeholder=t("auth.password_placeholder", language),
                                required=True,
                                cls="login-input",
                            ),
                            cls="login-field",
                        ),
                        Div(
                            Label(t("auth.confirm_password_label", language), cls="login-label", _for="confirm_password"),
                            Input(
                                type="password",
                                name="confirm_password",
                                id="confirm_password",
                                placeholder=t("auth.confirm_password_placeholder", language),
                                required=True,
                                cls="login-input",
                            ),
                            cls="login-field",
                        ),
                        Button(
                            t("auth.signup_submit", language),
                            type="submit",
                            cls="login-submit-btn",
                        ),
                        action="/api/auth/signup",
                        method="post",
                        cls="login-form",
                    ),
                    Div(
                        Span(t("auth.have_account", language)),
                        A(
                            t("auth.login_button", language),
                            href="/login",
                            cls="login-signup-link",
                        ),
                        cls="login-footer-text",
                    ),
                    cls="login-card",
                ),
                cls="login-page",
            ),
        ),
    )


_LOGIN_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { height: 100%; }
body {
    height: 100%;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: #f9fafb;
    color: #111827;
    line-height: 1.5;
}
.login-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    background: radial-gradient(ellipse at 50% 0%, rgba(124,58,237,0.06) 0%, transparent 60%);
}
.login-card {
    background: #fff;
    border-radius: 16px;
    padding: 40px 36px;
    max-width: 420px;
    width: 100%;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    text-align: center;
}
.login-logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-bottom: 28px;
}
.login-logo-mark {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 15px; color: #fff;
}
.login-logo-text {
    font-size: 18px;
    font-weight: 700;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.login-logo-badge {
    font-size: 9px;
    font-weight: 600;
    color: #7c3aed;
    background: #f5f3ff;
    padding: 2px 6px;
    border-radius: 4px;
    text-transform: uppercase;
}
.login-logo-badge-beta {
    font-size: 9px;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(135deg, #7c3aed, #a855f7);
    padding: 2px 6px;
    border-radius: 4px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.login-heading {
    font-size: 24px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 8px;
}
.login-subtext {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 28px;
}
.login-error {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 18px;
}
.login-error-text {
    font-size: 13px;
    color: #dc2626;
}
.login-form {
    text-align: left;
}
.login-field {
    margin-bottom: 18px;
}
.login-label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 6px;
}
.login-input {
    width: 100%;
    padding: 10px 14px;
    border: 1.5px solid #e5e7eb;
    border-radius: 10px;
    font-size: 15px;
    font-family: inherit;
    color: #111827;
    background: #fff;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.login-input:focus {
    border-color: #7c3aed;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.1);
}
.login-input::placeholder {
    color: #9ca3af;
}
.login-submit-btn {
    width: 100%;
    padding: 12px;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    color: #fff;
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
    margin-top: 4px;
}
.login-submit-btn:hover {
    opacity: 0.9;
}
.login-footer-text {
    margin-top: 24px;
    font-size: 13px;
    color: #6b7280;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
}
.login-signup-link {
    color: #7c3aed;
    font-weight: 600;
    text-decoration: none;
}
.login-signup-link:hover {
    text-decoration: underline;
}
.login-back-link {
    display: inline-block;
    margin-top: 16px;
    font-size: 13px;
    color: #9ca3af;
    text-decoration: none;
}
.login-back-link:hover {
    color: #6b7280;
}
@media (max-width: 480px) {
    .login-card {
        padding: 28px 20px;
    }
    .login-heading {
        font-size: 20px;
    }
}
"""
