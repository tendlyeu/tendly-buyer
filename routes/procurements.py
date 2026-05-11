"""Procurement plan routes for Tendly Buyer."""

import json
import logging
import os
import re
from urllib.parse import quote

from fasthtml.common import to_xml
from starlette.responses import RedirectResponse, FileResponse, HTMLResponse

logger = logging.getLogger(__name__)

# CPV codes: 8-digit numeric main codes (the optional `-X` check-digit suffix
# is stripped at this UI layer — keep it simple).
_CPV_CODE_RE = re.compile(r"^\d{8}$")


def _normalise_cpv(raw):
    """Parse user-entered CPV input (possibly comma-separated) into a
    canonical CSV string.

    Returns:
        (normalised: str, errors: list[tuple[str, list[str]]])
        - On success: ('30192000,30197000', [])
        - On invalid tokens: (raw_unchanged, [('invalid', ['bad1', 'bad2'])])
        - On empty input: ('', [])
    """
    raw = (raw or "").strip()
    if not raw:
        return "", []
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    bad = [p for p in parts if not _CPV_CODE_RE.match(p)]
    if bad:
        return raw, [("invalid", bad)]
    # Dedupe while preserving order
    seen = set()
    ordered = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    return ",".join(ordered), []

from components.layout import buyer_page
from components.procurements.plan_list import (
    procurement_list_page,
    procurement_new_page,
    procurement_detail_page,
    procurement_step_page,
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
        language = get_language_from_request(request)
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

        # ---- Validation ----
        # Maarius's bug: CPV with commas raised a confusing error and there
        # was no clear required-fields signaling. Validate explicitly and
        # re-render the form with inline error messages on failure.
        title = (form.get("title") or "").strip()
        cpv_raw = form.get("cpv_code", "")
        cpv_norm, cpv_errors = _normalise_cpv(cpv_raw)

        errors = {}
        if not title:
            errors["title"] = "title_required"
        if not cpv_raw.strip():
            errors["cpv_code"] = "cpv_required"
        elif cpv_errors:
            errors["cpv_code"] = "cpv_invalid_codes"

        estimated_value_raw = form.get("estimated_value", "")
        estimated_value_parsed = None
        if estimated_value_raw and str(estimated_value_raw).strip():
            try:
                estimated_value_parsed = float(estimated_value_raw)
                if estimated_value_parsed < 0:
                    errors["estimated_value"] = "estimated_value_invalid"
            except (TypeError, ValueError):
                errors["estimated_value"] = "estimated_value_invalid"

        if errors:
            # Re-render new-plan form with submitted values + inline errors
            plan_draft = {
                "title": title,
                "description": form.get("description", ""),
                "category": form.get("category", ""),
                "cpv_code": cpv_raw,
                "estimated_value": form.get("estimated_value", ""),
                "fiscal_year": form.get("fiscal_year", ""),
                "procurement_method": form.get("procurement_method", ""),
                "metadata_json": {
                    "submission_deadline": submission_deadline,
                    "evaluation_criteria": evaluation_criteria,
                    "requirements": requirements,
                },
            }
            content = procurement_new_page(language=language, plan=plan_draft, errors=errors)
            return buyer_page(content, language=language, auth=auth,
                              active_page="procurements", chat_service=chat_service,
                              title_key="procurements.new_title")

        # ---- Build metadata + persist ----
        # Storage strategy (DB column is VARCHAR(20), can't hold multiple
        # 8-digit codes + commas): the FULL list lives in
        # `metadata_json["cpv_codes"]` (source of truth). The legacy
        # `cpv_code` column gets only the FIRST code so back-compat reads
        # (other services, exports) still get a valid 8-digit value.
        cpv_list = cpv_norm.split(",") if cpv_norm else []
        cpv_first = cpv_list[0] if cpv_list else ""

        metadata = {}
        if submission_deadline:
            metadata["submission_deadline"] = submission_deadline
        if evaluation_criteria:
            metadata["evaluation_criteria"] = evaluation_criteria
        if requirements:
            metadata["requirements"] = requirements
        if cpv_list:
            metadata["cpv_codes"] = cpv_list

        plan = create_plan(
            title=title,
            description=form.get("description", ""),
            category=form.get("category", "muu"),
            estimated_value=estimated_value_parsed,
            cpv_code=cpv_first,
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
        upload_error = request.query_params.get("upload_error", "")
        content = procurement_detail_page(plan=plan, steps=steps, documents=docs, language=language,
                                          upload_error=upload_error)
        return buyer_page(content, language=language, auth=auth, active_page="procurements", chat_service=chat_service, title_key="procurements.page_title", include_canvas=True)

    @rt("/procurements/{plan_id}/edit")
    @require_auth
    def get(request, plan_id: str):
        """Render the edit form pre-populated with the plan's current data."""
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        if not user_owns_plan(plan_id, user_email):
            return forbidden_response(request)
        plan = get_plan(plan_id)
        content = procurement_new_page(language=language, plan=plan)
        return buyer_page(content, language=language, auth=auth,
                          active_page="procurements", chat_service=chat_service,
                          title_key="procurements.page_title")

    @rt("/procurements/{plan_id}/edit")
    @require_auth
    async def post(request, plan_id: str):
        """Persist changes from the edit form."""
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        if not user_owns_plan(plan_id, user_email):
            return forbidden_response(request)
        form = await request.form()

        # Re-parse criteria + requirements from JSON inputs
        try:
            evaluation_criteria = json.loads(form.get("evaluation_criteria_json", "[]"))
        except (json.JSONDecodeError, TypeError):
            evaluation_criteria = []
        try:
            requirements = json.loads(form.get("requirements_json", "[]"))
        except (json.JSONDecodeError, TypeError):
            requirements = []

        # Validate (edit-specific: title still required; CPV is soft-required
        # so existing plans without one don't break, but if provided it must
        # be a valid 8-digit code or comma list).
        title = (form.get("title") or "").strip()
        cpv_raw = form.get("cpv_code", "")
        cpv_norm, cpv_errors = _normalise_cpv(cpv_raw)

        errors = {}
        if not title:
            errors["title"] = "title_required"
        if cpv_errors:
            errors["cpv_code"] = "cpv_invalid_codes"

        if errors:
            existing = get_plan(plan_id) or {}
            plan_draft = dict(existing)
            plan_draft.update({
                "title": title,
                "description": form.get("description", ""),
                "category": form.get("category", ""),
                "cpv_code": cpv_raw,
                "estimated_value": form.get("estimated_value", ""),
                "fiscal_year": form.get("fiscal_year", ""),
                "procurement_method": form.get("procurement_method", ""),
                "metadata_json": {
                    "submission_deadline": form.get("submission_deadline", ""),
                    "evaluation_criteria": evaluation_criteria,
                    "requirements": requirements,
                },
            })
            content = procurement_new_page(language=language, plan=plan_draft, errors=errors)
            return buyer_page(content, language=language, auth=auth,
                              active_page="procurements", chat_service=chat_service,
                              title_key="procurements.page_title")

        # Storage: full list in metadata_json["cpv_codes"], first code in
        # legacy cpv_code column (VARCHAR(20) can't hold multiple).
        cpv_list = cpv_norm.split(",") if cpv_norm else []
        cpv_first = cpv_list[0] if cpv_list else ""

        metadata = {}
        if form.get("submission_deadline"):
            metadata["submission_deadline"] = form.get("submission_deadline")
        if evaluation_criteria:
            metadata["evaluation_criteria"] = evaluation_criteria
        if requirements:
            metadata["requirements"] = requirements
        if cpv_list:
            metadata["cpv_codes"] = cpv_list

        from services.procurement_service import update_plan
        update_plan(
            plan_id,
            title=title,
            description=form.get("description", ""),
            category=form.get("category", "muu"),
            estimated_value=float(form.get("estimated_value") or 0) or None,
            cpv_code=cpv_first,
            fiscal_year=int(form.get("fiscal_year") or 2026),
            procurement_method=form.get("procurement_method", "open"),
            metadata_json=metadata or {},
        )
        return RedirectResponse(f"/procurements/{plan_id}", status_code=303)

    @rt("/procurements/{plan_id}/steps/{step_num}")
    @require_auth
    def get(request, plan_id: str, step_num: int):
        """Detail page for a single workflow step (replaces the old 404)."""
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        if not user_owns_plan(plan_id, user_email):
            return forbidden_response(request)
        plan = get_plan(plan_id)
        steps = get_steps(plan_id)
        step_data = next((s for s in steps if s.get("step_number") == step_num), None)
        content = procurement_step_page(plan=plan, step_number=step_num, step_data=step_data, language=language)
        return buyer_page(content, language=language, auth=auth, active_page="procurements", chat_service=chat_service, title_key="procurements.page_title")

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
            except Exception as e:
                # Surface the failure to the user instead of silently dropping
                # the upload (Maarius-class bug: "I uploaded my doc but it
                # never appeared"). Use a stable error code in the redirect
                # so procurement_detail_page can render a translated banner.
                code = getattr(e, "code", None) or "failed"
                logger.warning("Document upload failed for plan %s: %s", plan_id, e)
                return RedirectResponse(
                    f"/procurements/{plan_id}?upload_error={quote(code)}",
                    status_code=303,
                )
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

    def _render_review_panel(plan_id: str, language: str, analysis: dict, doc_count: int, reviewed_display: str):
        """Build the side-panel HTML for a review result."""
        from fasthtml.common import Div, Span, Button, NotStr
        panel = ai_review_panel(analysis, language)
        meta = Div(
            Span(
                f"{t('review.reviewed_at', language)}: {reviewed_display}",
                style="font-size:11px;color:#9ca3af;",
            ),
            Span(" · ", style="font-size:11px;color:#d1d5db;"),
            Span(
                f"{doc_count} {t('review.documents_analyzed', language)}",
                style="font-size:11px;color:#9ca3af;",
            ),
            style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;padding:0 4px;",
        )
        rerun = Button(
            NotStr('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>'),
            f" {t('review.rerun_review', language)}",
            type="button",
            onclick=f"runAiReview('{plan_id}', this)",
            cls="btn-secondary",
            style="font-size:12px;padding:6px 12px;display:inline-flex;align-items:center;gap:6px;",
        )
        footer = Div(
            meta, rerun,
            style="display:flex;align-items:center;justify-content:space-between;margin:14px 4px 4px;padding-top:12px;border-top:1px solid #f3f4f6;flex-wrap:wrap;gap:8px;",
        )
        return Div(panel, footer, cls="ai-review-canvas", style="padding:18px 16px 24px;")

    @rt("/api/procurements/{plan_id}/ai-review")
    @require_auth
    async def post(request, plan_id: str):
        """Run AI document review and return results as HTML fragment for the side canvas."""
        auth = get_auth_from_request(request)
        if not user_owns_plan(plan_id, auth.get("email") if auth else None):
            return forbidden_response(request)
        from services.document_review_service import DocumentReviewService
        from fasthtml.common import Div, P

        language = get_language_from_request(request)
        reviewer = DocumentReviewService()
        result = await reviewer.review_documents(plan_id)

        if not result.get("success"):
            error = result.get("error", "")
            if error in ("no_documents", "no_content"):
                # Prefer the more actionable, translated message; fall back
                # to the legacy `review.no_documents` key if newer key absent.
                msg = (t("procurements.no_documents_to_review", language)
                       or t("review.no_documents", language))
            else:
                msg = error or t("chat.error", language)
            error_html = Div(
                P(msg, style="font-size:13px;color:#dc2626;text-align:center;padding:24px 16px;"),
                cls="ai-review-canvas",
            )
            return HTMLResponse(to_xml(error_html))

        analysis = result.get("analysis", {})
        doc_count = result.get("document_count", 0)
        from datetime import datetime, timezone
        reviewed_display = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        return HTMLResponse(to_xml(_render_review_panel(plan_id, language, analysis, doc_count, reviewed_display)))

    @rt("/api/procurements/{plan_id}/ai-review")
    @require_auth
    def get(request, plan_id: str):
        """Return the most recent stored AI review for the side canvas (no re-run)."""
        auth = get_auth_from_request(request)
        if not user_owns_plan(plan_id, auth.get("email") if auth else None):
            return forbidden_response(request)
        from fasthtml.common import Div, P

        language = get_language_from_request(request)
        plan = get_plan(plan_id)
        existing = (plan.get("metadata_json") or {}).get("ai_review") if plan else None
        if not existing:
            empty = Div(
                P(
                    t("review.no_documents", language),
                    style="font-size:13px;color:#6b7280;text-align:center;padding:24px 16px;",
                ),
                cls="ai-review-canvas",
            )
            return HTMLResponse(to_xml(empty))
        analysis = existing.get("results", {}) or {}
        doc_count = existing.get("document_count", 0)
        reviewed_at = existing.get("reviewed_at", "")
        reviewed_display = reviewed_at[:16].replace("T", " ") if reviewed_at else ""
        return HTMLResponse(to_xml(_render_review_panel(plan_id, language, analysis, doc_count, reviewed_display)))
