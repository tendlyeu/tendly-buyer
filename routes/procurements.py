"""Procurement plan routes for Tendly Buyer."""

import json
import os

from fasthtml.common import to_xml
from starlette.responses import RedirectResponse, FileResponse, HTMLResponse

from components.layout import buyer_page
from components.procurements.plan_list import (
    procurement_list_page,
    procurement_new_page,
    procurement_detail_page,
)
from components.procurements.ai_review_panel import ai_review_panel
from config.i18n import get_language_from_request, t
from routes.auth_utils import get_auth_from_request, require_auth, user_owns_plan, forbidden_response
from services.procurement_service import (
    create_plan, get_plan, list_plans, get_steps, complete_step, get_stats,
    list_documents, add_document, get_document, delete_document,
)
from services.file_processor import FileProcessor


def register_procurement_routes(rt, chat_service):
    @rt("/procurements")
    @require_auth
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        plans = list_plans(organization_id=user_email)
        content = procurement_list_page(plans=plans, language=language)
        return buyer_page(content, language=language, auth=auth, active_page="procurements", chat_service=chat_service, title_key="procurements.page_title")

    @rt("/procurements/new")
    @require_auth
    def get(request):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        content = procurement_new_page(language=language)
        return buyer_page(content, language=language, auth=auth, active_page="procurements", chat_service=chat_service, title_key="procurements.new_title")

    @rt("/procurements")
    @require_auth
    async def post(request):
        form = await request.form()
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None

        # Parse new form fields
        submission_deadline = form.get("submission_deadline", "")

        # Parse evaluation criteria and requirements from JSON hidden fields
        try:
            evaluation_criteria = json.loads(form.get("evaluation_criteria_json", "[]"))
        except (json.JSONDecodeError, TypeError):
            evaluation_criteria = []

        try:
            requirements = json.loads(form.get("requirements_json", "[]"))
        except (json.JSONDecodeError, TypeError):
            requirements = []

        # Build metadata_json with the new structured data
        metadata = {}
        if submission_deadline:
            metadata["submission_deadline"] = submission_deadline
        if evaluation_criteria:
            metadata["evaluation_criteria"] = evaluation_criteria
        if requirements:
            metadata["requirements"] = requirements

        plan = create_plan(
            title=form.get("title", "Untitled"),
            description=form.get("description", ""),
            category=form.get("category", "muu"),
            estimated_value=form.get("estimated_value") or None,
            cpv_code=form.get("cpv_code", ""),
            fiscal_year=int(form.get("fiscal_year") or 2026),
            procurement_method=form.get("procurement_method", "open"),
            created_by_email=user_email,
            organization_id=user_email,
            metadata_json=metadata if metadata else None,
        )
        return RedirectResponse(f"/procurements/{plan['id']}", status_code=303)

    @rt("/procurements/{plan_id}")
    @require_auth
    def get(request, plan_id: str):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        plan = get_plan(plan_id)
        # Tenant isolation: only the creator can view their plan.
        # NOTE: when team-level sharing arrives, replace this with an
        # organization-membership check.
        if not plan or (plan.get("organization_id") and plan.get("organization_id") != user_email):
            return RedirectResponse("/procurements", status_code=302)
        steps = get_steps(plan_id)
        docs = list_documents(procurement_plan_id=plan_id)
        content = procurement_detail_page(plan=plan, steps=steps, documents=docs, language=language)
        return buyer_page(content, language=language, auth=auth, active_page="procurements", chat_service=chat_service, title_key="procurements.page_title")

    @rt("/procurements/{plan_id}/edit")
    @require_auth
    def get(request, plan_id: str):
        # The detail page links here for "Edit". A full edit form is a
        # bigger feature; for now redirect to detail (and a follow-up CL
        # can replace this with a real edit page).
        auth = get_auth_from_request(request)
        if not user_owns_plan(plan_id, auth.get("email") if auth else None):
            return forbidden_response(request)
        return RedirectResponse(f"/procurements/{plan_id}", status_code=302)

    @rt("/procurements/{plan_id}/steps/{step_num}/complete")
    @require_auth
    async def post(request, plan_id: str, step_num: int):
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        if not user_owns_plan(plan_id, user_email):
            return forbidden_response(request)
        complete_step(plan_id, step_num, completed_by=user_email)
        return RedirectResponse(f"/procurements/{plan_id}", status_code=303)

    # --- Document upload, download, delete ---

    @rt("/api/procurements/{plan_id}/documents")
    @require_auth
    async def post(request, plan_id: str):
        """Handle multipart file upload for a procurement plan."""
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        if not user_owns_plan(plan_id, user_email):
            return forbidden_response(request)

        form = await request.form()
        title = form.get("title", "Untitled")
        document_type = form.get("document_type", "other")
        uploaded_file = form.get("document")

        if uploaded_file and hasattr(uploaded_file, "filename") and uploaded_file.filename:
            processor = FileProcessor()
            try:
                result = await processor.process_upload(uploaded_file, plan_id)
                add_document(
                    title=title,
                    document_type=document_type,
                    file_name=result["file_name"],
                    file_size=result["file_size"],
                    mime_type=result["mime_type"],
                    content_text=result["content_text"],
                    procurement_plan_id=plan_id,
                    uploaded_by_email=user_email,
                    organization_id=user_email,
                    file_path=result["file_path"],
                )
            except ValueError as e:
                # Validation error (bad extension, too large, empty) -
                # redirect back with the plan page showing current docs
                pass
        else:
            # No file selected - still store as a text-only document
            add_document(
                title=title,
                document_type=document_type,
                content_text="",
                procurement_plan_id=plan_id,
                uploaded_by_email=user_email,
                organization_id=user_email,
            )

        return RedirectResponse(f"/procurements/{plan_id}", status_code=303)

    @rt("/api/procurements/{plan_id}/documents/{doc_id}/download")
    @require_auth
    def get(request, plan_id: str, doc_id: str):
        """Serve a document file from disk."""
        auth = get_auth_from_request(request)
        if not user_owns_plan(plan_id, auth.get("email") if auth else None):
            return forbidden_response(request)
        doc = get_document(doc_id)
        if not doc or doc.get("procurement_plan_id") != plan_id:
            return RedirectResponse(f"/procurements/{plan_id}", status_code=302)

        file_path = doc.get("file_path", "")
        if not file_path or not os.path.exists(file_path):
            return RedirectResponse(f"/procurements/{plan_id}", status_code=302)

        return FileResponse(
            file_path,
            filename=doc.get("file_name", "download"),
            media_type=doc.get("mime_type", "application/octet-stream"),
        )

    @rt("/api/procurements/{plan_id}/documents/{doc_id}")
    @require_auth
    async def delete(request, plan_id: str, doc_id: str):
        """Delete a document (from DB and disk)."""
        auth = get_auth_from_request(request)
        if not user_owns_plan(plan_id, auth.get("email") if auth else None):
            return forbidden_response(request)
        doc = get_document(doc_id)
        # Belt-and-braces: doc must also belong to this plan
        if doc and doc.get("procurement_plan_id") == plan_id:
            file_path = doc.get("file_path", "")
            if file_path:
                FileProcessor.delete_file(file_path)
            delete_document(doc_id)
        # Return empty response for HTMX (the card is removed via hx-swap)
        return ""

    # --- AI Document Review ---

    @rt("/api/procurements/{plan_id}/ai-review")
    @require_auth
    async def post(request, plan_id: str):
        """Run AI document review and return results as HTML fragment."""
        auth = get_auth_from_request(request)
        if not user_owns_plan(plan_id, auth.get("email") if auth else None):
            return forbidden_response(request)
        from services.document_review_service import DocumentReviewService
        from fasthtml.common import Div, P, Span, Button, NotStr

        language = get_language_from_request(request)
        reviewer = DocumentReviewService()
        result = await reviewer.review_documents(plan_id)

        if not result.get("success"):
            error = result.get("error", "")
            if error == "no_documents":
                msg = t("review.no_documents", language)
            elif error == "no_content":
                msg = t("review.no_documents", language)
            else:
                msg = error or t("chat.error", language)
            error_html = Div(
                P(msg, style="font-size:13px;color:#dc2626;text-align:center;padding:16px 0;"),
                id="ai-review-results",
            )
            return HTMLResponse(to_xml(error_html))

        analysis = result.get("analysis", {})
        doc_count = result.get("document_count", 0)

        panel = ai_review_panel(analysis, language)

        # Metadata footer with re-run button
        from datetime import datetime, timezone
        reviewed_display = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

        from core.utils import _raw

        footer = Div(
            Div(
                Span(
                    f"{t('review.reviewed_at', language)}: {reviewed_display}",
                    style="font-size:11px;color:#9ca3af;",
                ),
                Span(" | ", style="font-size:11px;color:#d1d5db;"),
                Span(
                    f"{doc_count} {t('review.documents_analyzed', language)}",
                    style="font-size:11px;color:#9ca3af;",
                ),
                style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;",
            ),
            Button(
                NotStr('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>'),
                f" {t('review.rerun_review', language)}",
                hx_post=f"/api/procurements/{plan_id}/ai-review",
                hx_target="#ai-review-results",
                hx_indicator="#review-loading",
                cls="btn-secondary",
                style="font-size:12px;padding:6px 12px;",
            ),
            style="display:flex;align-items:center;justify-content:space-between;margin-top:14px;padding-top:12px;border-top:1px solid #f3f4f6;flex-wrap:wrap;gap:8px;",
        )

        result_html = Div(panel, footer, id="ai-review-results")
        return HTMLResponse(to_xml(result_html))
