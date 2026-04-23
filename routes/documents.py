"""Document management routes for Tendly Buyer."""

from fasthtml.common import *
from starlette.responses import RedirectResponse, JSONResponse

from components.layout import buyer_page
from config.i18n import get_language_from_request, t
from routes.auth_utils import get_auth_from_request
from core.utils import _raw
from services.procurement_service import list_documents, add_document, get_document, delete_document


DOCUMENT_TYPES = [
    ("contract_template", "Contract Template / Lepingumall"),
    ("technical_description", "Technical Description / Tehniline kirjeldus"),
    ("good_practice", "Good Practice / Hea tava"),
    ("org_chart", "Org Chart / Struktuuriskeem"),
    ("cv", "CV / Team Roles"),
    ("iso_certificate", "ISO Certificate"),
    ("product_list", "Product List / Tootenimekiri (XLS)"),
    ("software_list", "Software List / Tarkvara nimekiri"),
    ("rit_inventory", "IT Inventory / RIT"),
    ("rfp_draft", "RFP Draft"),
    ("other", "Other / Muu"),
]


def _document_card(doc):
    type_icons = {
        "contract_template": "📄", "technical_description": "📋",
        "good_practice": "📘", "org_chart": "🏢", "cv": "👤",
        "iso_certificate": "✅", "product_list": "📊",
        "software_list": "💻", "rit_inventory": "🖥️",
        "rfp_draft": "📝", "other": "📎",
    }
    icon = type_icons.get(doc.get("document_type", "other"), "📎")
    size_kb = doc.get("file_size", 0) / 1024
    size_str = f"{size_kb:.0f} KB" if size_kb > 0 else ""

    return Div(
        Div(
            Span(icon, style="font-size:24px;"),
            Div(
                Div(doc.get("title", "Untitled"), style="font-size:14px;font-weight:600;color:#111827;"),
                Div(
                    Span(doc.get("document_type", "other").replace("_", " ").title(), style="font-size:12px;color:#6b7280;"),
                    Span(size_str, style="font-size:12px;color:#9ca3af;margin-left:8px;") if size_str else "",
                    style="display:flex;align-items:center;gap:4px;margin-top:2px;",
                ),
            ),
            style="display:flex;align-items:center;gap:12px;flex:1;",
        ),
        Span(doc.get("status", "draft").capitalize(), style="font-size:11px;font-weight:600;color:#6b7280;background:#f3f4f6;padding:2px 8px;border-radius:4px;"),
        style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:white;border:1px solid #e5e7eb;border-radius:10px;margin-bottom:8px;",
    )


def _documents_page_content(docs, language="en"):
    type_options = [Option(label, value=val) for val, label in DOCUMENT_TYPES]

    upload_form = Div(
        H3(t("documents.upload_title", language), style="font-size:15px;font-weight:600;color:#111827;margin:0 0 12px;"),
        Form(
            Div(
                Div(
                    Label("Title", cls="form-label"),
                    Input(name="title", type="text", placeholder="Document title", cls="form-input", required=True),
                    cls="form-group",
                ),
                Div(
                    Label("Type", cls="form-label"),
                    Select(*type_options, name="document_type", cls="form-select"),
                    cls="form-group",
                ),
                cls="form-row",
            ),
            Div(
                Label("Content / Notes", cls="form-label"),
                Textarea(name="content_text", placeholder="Paste document content or notes here...", cls="form-textarea", rows="3"),
                cls="form-group",
            ),
            Div(
                Button(t("documents.add", language), type="submit", cls="btn-primary"),
                cls="form-actions", style="justify-content:flex-start;border-top:none;margin-top:8px;padding-top:0;",
            ),
            action="/api/documents",
            method="post",
        ),
        cls="dashboard-section",
    )

    if docs:
        doc_list = Div(*[_document_card(d) for d in docs])
    else:
        doc_list = Div(
            _raw('<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>'),
            P(t("documents.empty", language), style="color:#6b7280;font-size:14px;margin:12px 0;"),
            style="text-align:center;padding:32px 0;",
        )

    return Div(
        Div(
            H1(t("documents.title", language), style="font-size:22px;font-weight:700;color:#111827;margin:0;"),
            cls="page-header",
        ),
        upload_form,
        Div(
            H3(t("documents.library", language), style="font-size:15px;font-weight:600;color:#111827;margin:0 0 12px;"),
            doc_list,
            cls="dashboard-section",
        ),
        cls="page-content",
    )


def register_document_routes(rt, chat_service):
    @rt("/documents")
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        docs = list_documents()
        content = _documents_page_content(docs, language)
        return buyer_page(content, language=language, auth=auth, active_page="documents", chat_service=chat_service, title_key="documents.page_title")

    @rt("/documents/templates")
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        docs = list_documents()
        content = _documents_page_content(docs, language)
        return buyer_page(content, language=language, auth=auth, active_page="documents", chat_service=chat_service, title_key="documents.page_title")

    @rt("/api/documents")
    async def post(request):
        form = await request.form()
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        add_document(
            title=form.get("title", "Untitled"),
            document_type=form.get("document_type", "other"),
            content_text=form.get("content_text", ""),
            uploaded_by_email=user_email,
        )
        return RedirectResponse("/documents", status_code=303)
