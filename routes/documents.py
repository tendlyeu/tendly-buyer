"""Document management routes for Tendly Buyer."""

import os
from fasthtml.common import *
from starlette.responses import RedirectResponse, JSONResponse, FileResponse

from components.layout import buyer_page
from config.i18n import get_language_from_request, t
from routes.auth_utils import get_auth_from_request, require_auth
from core.utils import _raw
from services.procurement_service import list_documents, add_document, get_document, delete_document
from services.file_processor import FileProcessor


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
    has_file = bool(doc.get("file_path") and doc.get("file_name"))
    doc_id = doc.get("id", "")

    actions = []
    if has_file:
        actions.append(
            A(
                _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>'),
                href=f"/api/documents/{doc_id}/download",
                title="Download",
                style="display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:6px;color:#6b7280;text-decoration:none;",
                onmouseover="this.style.background='#f3f4f6';this.style.color='#2563eb'",
                onmouseout="this.style.background='transparent';this.style.color='#6b7280'",
            )
        )
    actions.append(
        Button(
            _raw('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>'),
            type="button",
            title="Delete",
            style="background:transparent;border:none;display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:6px;color:#6b7280;cursor:pointer;",
            onclick=f"if(confirm('Delete this document?'))fetch('/api/documents/{doc_id}',{{method:'DELETE'}}).then(()=>location.reload())",
            onmouseover="this.style.background='#fef2f2';this.style.color='#dc2626'",
            onmouseout="this.style.background='transparent';this.style.color='#6b7280'",
        )
    )

    return Div(
        Div(
            Span(icon, style="font-size:24px;"),
            Div(
                Div(doc.get("title", "Untitled"), style="font-size:14px;font-weight:600;color:#111827;"),
                Div(
                    Span(doc.get("document_type", "other").replace("_", " ").title(), style="font-size:12px;color:#6b7280;"),
                    Span(" • " + size_str, style="font-size:12px;color:#9ca3af;") if size_str else "",
                    Span(" • " + (doc.get("file_name") or ""), style="font-size:11px;color:#9ca3af;") if has_file else "",
                    style="display:flex;align-items:center;gap:2px;margin-top:2px;",
                ),
            ),
            style="display:flex;align-items:center;gap:12px;flex:1;min-width:0;",
        ),
        Div(
            Span(doc.get("status", "draft").capitalize(), style="font-size:11px;font-weight:600;color:#6b7280;background:#f3f4f6;padding:2px 8px;border-radius:4px;"),
            *actions,
            style="display:flex;align-items:center;gap:6px;flex-shrink:0;",
        ),
        style="display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 16px;background:white;border:1px solid #e5e7eb;border-radius:10px;margin-bottom:8px;",
    )


def _documents_page_content(docs, language="en"):
    type_options = [Option(label, value=val) for val, label in DOCUMENT_TYPES]

    upload_form = Div(
        H3(t("documents.upload_title", language), style="font-size:15px;font-weight:600;color:#111827;margin:0 0 12px;"),
        Form(
            Div(
                Div(
                    Label(t("form.title", language), cls="form-label"),
                    Input(name="title", type="text", placeholder=t("form.document_title_placeholder", language), cls="form-input", required=True),
                    cls="form-group",
                ),
                Div(
                    Label(t("form.type", language), cls="form-label"),
                    Select(*type_options, name="document_type", cls="form-select"),
                    cls="form-group",
                ),
                cls="form-row",
            ),
            Div(
                Label(t("documents.file_label", language) or "File (PDF, DOCX, XLSX, TXT, CSV — max 10 MB)",
                      cls="form-label"),
                Input(name="document", type="file",
                      accept=".pdf,.docx,.xlsx,.txt,.csv",
                      cls="form-input", style="padding:8px;"),
                cls="form-group",
            ),
            Div(
                Label(t("form.content_notes", language), cls="form-label"),
                Textarea(name="content_text", placeholder=t("form.document_content_placeholder", language), cls="form-textarea", rows="3"),
                cls="form-group",
            ),
            Div(
                Button(t("documents.add", language), type="submit", cls="btn-primary"),
                cls="form-actions", style="justify-content:flex-start;border-top:none;margin-top:8px;padding-top:0;",
            ),
            action="/api/documents",
            method="post",
            enctype="multipart/form-data",
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
    @require_auth
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        org_id = auth.get("email") if auth else None
        docs = list_documents(organization_id=org_id)
        content = _documents_page_content(docs, language)
        return buyer_page(content, language=language, auth=auth, active_page="documents", chat_service=chat_service, title_key="documents.page_title")

    @rt("/documents/templates")
    @require_auth
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        org_id = auth.get("email") if auth else None
        docs = list_documents(organization_id=org_id)
        content = _documents_page_content(docs, language)
        return buyer_page(content, language=language, auth=auth, active_page="documents", chat_service=chat_service, title_key="documents.page_title")

    @rt("/api/documents")
    @require_auth
    async def post(request):
        form = await request.form()
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        title = form.get("title", "Untitled")
        document_type = form.get("document_type", "other")
        content_text = form.get("content_text", "") or ""
        uploaded_file = form.get("document")

        # If a file was attached, run it through FileProcessor (extracts
        # text from PDF/DOCX/XLSX) and persist with file_path so it can
        # be downloaded later. Otherwise fall back to a text-only document.
        kwargs = {
            "title": title,
            "document_type": document_type,
            "content_text": content_text,
            "uploaded_by_email": user_email,
            "organization_id": user_email,
        }
        if uploaded_file and hasattr(uploaded_file, "filename") and uploaded_file.filename:
            try:
                # Standalone documents (not tied to a plan) live in
                # uploads/library/<user_email-slug>/...
                slug = (user_email or "anon").replace("@", "_at_").replace(".", "_")
                result = await FileProcessor().process_upload(uploaded_file, plan_id=f"library/{slug}")
                kwargs.update({
                    "file_name": result["file_name"],
                    "file_size": result["file_size"],
                    "mime_type": result["mime_type"],
                    "file_path": result["file_path"],
                    # Use extracted text as content_text if user didn't provide notes
                    "content_text": content_text or result["content_text"],
                })
            except ValueError:
                # bad extension / too large / empty — fall through to text-only save
                pass
            except Exception:
                pass

        add_document(**kwargs)
        return RedirectResponse("/documents", status_code=303)

    @rt("/api/documents/{doc_id}/download")
    @require_auth
    def get(request, doc_id: str):
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        doc = get_document(doc_id)
        if not doc or doc.get("organization_id") != user_email:
            return RedirectResponse("/documents", status_code=302)
        path = doc.get("file_path", "")
        if not path or not os.path.exists(path):
            return RedirectResponse("/documents", status_code=302)
        return FileResponse(
            path,
            filename=doc.get("file_name", "download"),
            media_type=doc.get("mime_type", "application/octet-stream"),
        )

    @rt("/api/documents/{doc_id}")
    @require_auth
    async def delete(request, doc_id: str):
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        doc = get_document(doc_id)
        if doc and doc.get("organization_id") == user_email:
            file_path = doc.get("file_path", "")
            if file_path:
                try: FileProcessor.delete_file(file_path)
                except Exception: pass
            delete_document(doc_id)
        return ""
