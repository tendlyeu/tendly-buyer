"""API routes for Tendly Buyer."""

import json
import asyncio
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse

from starlette.responses import StreamingResponse, HTMLResponse, Response, RedirectResponse, JSONResponse
from fasthtml.common import to_xml

from components.tender_detail import tender_detail_panel
# competitor_intel/winning_strategy artifacts are seller-side and are
# intentionally not surfaced in this buyer-only product.
from components.artifacts.tender_comparison import tender_comparison_panel
from components.artifacts.create_plan import create_plan_panel
from components.artifacts.legal_lookup import legal_lookup_panel
from components.artifacts.risk_analysis import risk_analysis_panel
from components.artifacts.gap_analysis import gap_analysis_panel
from components.artifacts.requirements import requirements_panel
from components.artifacts.price_benchmark import price_benchmark_panel
from components.artifacts.rfp_draft import rfp_draft_panel
from config.i18n import get_language_from_request, SUPPORTED_LANGUAGES, LANGUAGE_COOKIE
from routes.auth_utils import get_auth_from_request, require_auth
from core.rate_limiter import check_rate_limit, record_usage

# Auth-related database functions (may not exist yet if auth isn't fully deployed)
try:
    from core.database import save_tender, unsave_tender, is_tender_saved, get_tender_data_for_save
    _AUTH_DB_OK = True
except ImportError:
    _AUTH_DB_OK = False

    def save_tender(*a, **kw):
        return False

    def unsave_tender(*a, **kw):
        return False

    def is_tender_saved(*a, **kw):
        return False

    def get_tender_data_for_save(*a, **kw):
        return {}


def register_api_routes(rt, chat_service):
    @rt("/api/chat")
    async def post(request):
        data = await request.json()
        conversation_id = data.get("conversation_id")
        # Authoritative UI language (cookie / query-param). Used as a hard
        # signal for the LLM so a one-word "Hi" with the picker on English
        # doesn't drift to Estonian.
        ui_language = get_language_from_request(request)
        message = data.get("message", "").strip()

        if not message:
            async def empty_stream():
                yield f"event: error\ndata: {json.dumps({'error': 'Empty message'})}\n\n"
            return StreamingResponse(empty_stream(), media_type="text/event-stream")

        # Get auth for logging
        auth = get_auth_from_request(request)
        user_email = auth.get('email') if auth else None

        if not conversation_id:
            conversation_id = chat_service.create_conversation(user_email=user_email)
        else:
            # Verify the caller owns this conversation (or it's anonymous and
            # the caller is anonymous). Reject otherwise — without this,
            # knowing a conversation_id lets any logged-in user post into
            # someone else's conversation and read leaked plan context.
            existing = chat_service.get_conversation(conversation_id, user_email=user_email)
            if existing is None:
                # Fallback: maybe the conversation row doesn't exist yet
                # (the client generated an ID locally before the first turn
                # was persisted). Re-create owned by this caller.
                from chat_service import ChatContext, get_tendly_session
                _sess = get_tendly_session()
                try:
                    _row = _sess.query(ChatContext).filter(
                        ChatContext.conversation_id == conversation_id
                    ).first()
                finally:
                    _sess.close()
                if _row is not None:
                    # Row exists but not owned by caller — refuse and start a
                    # fresh conversation instead of leaking the other tenant.
                    conversation_id = chat_service.create_conversation(user_email=user_email)

        # Check rate limits
        rate_result = check_rate_limit(request, user_email)
        if not rate_result["allowed"]:
            async def limit_stream():
                yield f"event: rate_limit\ndata: {json.dumps(rate_result)}\n\n"
            return StreamingResponse(limit_stream(), media_type="text/event-stream")

        # Record usage
        record_usage(request, user_email)

        # Recalculate remaining after recording
        updated_rate = check_rate_limit(request, user_email)

        async def event_stream():
            yield f"event: status\ndata: {json.dumps({'status': 'thinking'})}\n\n"

            try:
                if hasattr(chat_service, 'process_message_sync'):
                    result = await chat_service.process_message_sync(conversation_id, message, user_email=user_email, ui_language=ui_language)
                else:
                    result = await chat_service.process_message(conversation_id, message, user_email=user_email, ui_language=ui_language)

                response_text = result.get("response", "")
                words = response_text.split(" ")
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    yield f"event: chunk\ndata: {json.dumps({'text': chunk})}\n\n"
                    await asyncio.sleep(0.018)

                tenders = result.get("tenders", [])
                if tenders:
                    yield f"event: tenders\ndata: {json.dumps(tenders, default=str)}\n\n"

                artifact = result.get("artifact")
                if artifact:
                    # Always include conversation_id so the client can fetch
                    # /api/artifact/{type}/{id}?conversation_id=... even if it
                    # didn't yet know the conversation (e.g. brand-new chat).
                    artifact_payload = dict(artifact)
                    artifact_payload.setdefault("conversation_id", conversation_id)
                    yield f"event: artifact\ndata: {json.dumps(artifact_payload, default=str)}\n\n"

                # Include rate limit info in done event
                done_data = {
                    'conversation_id': conversation_id,
                    'title': result.get('title', 'New Chat'),
                    'rate': {
                        'remaining': updated_rate['remaining'],
                        'limit': updated_rate['limit'],
                        'tier': updated_rate['tier'],
                    },
                }
                yield f"event: done\ndata: {json.dumps(done_data)}\n\n"

            except Exception as e:
                print(f"SSE stream error: {e}")
                import traceback
                traceback.print_exc()
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @rt("/api/chat/attach")
    @require_auth
    async def post(request):
        """Attach a file uploaded from the chat input to the conversation's
        most recently-created procurement plan.

        Returns JSON: {ok, plan_id, plan_title, doc_id, filename, content_chars}
        On failure (no plan in conversation, bad file): {ok:false, error}
        """
        auth = get_auth_from_request(request)
        user_email = auth.get("email") if auth else None
        form = await request.form()
        conversation_id = form.get("conversation_id", "")
        uploaded = form.get("file")

        if not uploaded or not hasattr(uploaded, "filename") or not uploaded.filename:
            return JSONResponse({"ok": False, "error": "no_file"}, status_code=400)
        # Reject pathological filenames before we touch the filesystem (avoids
        # leaking the absolute upload directory path in a 500 error).
        if len(uploaded.filename) > 255:
            return JSONResponse({
                "ok": False, "error": "bad_file",
                "message": "Filename is too long (max 255 characters).",
            }, status_code=400)
        # If the user attaches a file as their first action (no chat sent yet,
        # so the JS doesn't have an activeConversationId), spin up a new
        # conversation here so the file has somewhere to live.
        if not conversation_id:
            conversation_id = chat_service.create_conversation(user_email=user_email)

        # Find the most recently-created plan attached to THIS conversation.
        # We look at the conversation's stored artifacts for a "create_plan"
        # entry — that's the plan the user just made via chat. If there's
        # no such artifact, fall back to the user's most recent plan
        # overall (any plan they own).
        from services.procurement_service import (
            list_plans, add_document, get_plan,
        )
        target_plan_id = None
        target_plan_title = None
        try:
            artifacts = chat_service.get_conversation_artifacts(conversation_id) or []
        except Exception:
            artifacts = []
        for art in reversed(artifacts):
            if art.get("type") == "create_plan":
                pid = (art.get("data") or {}).get("plan_id")
                if pid:
                    plan = get_plan(pid)
                    if plan and plan.get("organization_id") == user_email:
                        target_plan_id = pid
                        target_plan_title = plan.get("title")
                        break

        if not target_plan_id:
            # Fall back: most-recent plan the user owns
            plans = list_plans(organization_id=user_email)
            if plans:
                target_plan_id = plans[0].get("id")
                target_plan_title = plans[0].get("title")

        if not target_plan_id:
            return JSONResponse({
                "ok": False,
                "error": "no_plan",
                "message": "No procurement plan found in this conversation. Ask the agent to create one first, then attach files.",
            }, status_code=400)

        # Persist via FileProcessor (same path as /api/procurements/.../documents)
        from services.file_processor import FileProcessor
        try:
            result = await FileProcessor().process_upload(uploaded, target_plan_id)
        except ValueError as e:
            return JSONResponse({"ok": False, "error": "bad_file", "message": str(e)}, status_code=400)
        except Exception as e:
            # Avoid leaking server filesystem paths or internal exception
            # details. Log them server-side and return a generic message.
            print(f"chat attach upload_failed: {e}")
            return JSONResponse({"ok": False, "error": "upload_failed", "message": "Upload failed. Please try a different file."}, status_code=500)

        doc = add_document(
            title=uploaded.filename,
            document_type="other",
            file_name=result["file_name"],
            file_size=result["file_size"],
            mime_type=result["mime_type"],
            content_text=result["content_text"],
            procurement_plan_id=target_plan_id,
            uploaded_by_email=user_email,
            organization_id=user_email,
            file_path=result["file_path"],
        )

        # Inject the extracted text into the conversation as a system
        # primer so the LLM actually USES the document on the next turn
        # (#1181). Without this the chat acknowledged the upload but
        # then hallucinated answers because the file content never
        # reached the prompt.
        content_text = (result.get("content_text") or "").strip()
        if content_text:
            from datetime import datetime as _dt
            MAX_DOC_CHARS = 12000
            preview = content_text[:MAX_DOC_CHARS]
            truncated_note = "" if len(content_text) <= MAX_DOC_CHARS else (
                f"\n\n[document truncated: showing first {MAX_DOC_CHARS} of "
                f"{len(content_text)} characters]"
            )
            primer = (
                "ATTACHED DOCUMENT — the buyer just uploaded this file via "
                "the chat paperclip. Treat its contents as authoritative "
                "context for the rest of the conversation. When the user "
                "asks about 'my document', 'this doc', 'past procurement', "
                "etc. you MUST answer from the text below, not from "
                "general knowledge. NEVER say you can't see the file — "
                "the text is right here.\n"
                f"\nFile: {uploaded.filename} (plan: {target_plan_title or '—'})\n"
                f"Document ID: {doc.get('id')}\n\n"
                f"=== BEGIN DOCUMENT TEXT ==={truncated_note}\n"
                f"{preview}\n"
                f"=== END DOCUMENT TEXT ==="
            )
            try:
                chat_service._append_message(conversation_id, {
                    "role": "system",
                    "content": primer,
                    "tenders": [],
                    "timestamp": _dt.utcnow().isoformat(),
                })
            except Exception:
                pass

        return JSONResponse({
            "ok": True,
            "conversation_id": conversation_id,
            "plan_id": target_plan_id,
            "plan_title": target_plan_title,
            "doc_id": doc.get("id"),
            "filename": uploaded.filename,
            "content_chars": len(result.get("content_text") or ""),
        })

    @rt("/api/conversations")
    def get(request):
        auth = get_auth_from_request(request)
        user_email = auth.get('email') if auth else None
        # Always return JSON list (empty list serialises to a zero-byte body
        # via FastHTML's default; force a real JSON array).
        return JSONResponse(chat_service.get_conversations(user_email=user_email))

    @rt("/api/conversations/new")
    def post(request):
        auth = get_auth_from_request(request)
        user_email = auth.get('email') if auth else None
        cid = chat_service.create_conversation(user_email=user_email)
        return {"conversation_id": cid}

    @rt("/api/conversations/{conversation_id}")
    def delete(request, conversation_id: str):
        auth = get_auth_from_request(request)
        user_email = auth.get('email') if auth else None
        chat_service.delete_conversation(conversation_id, user_email=user_email)
        return {"ok": True}

    @rt("/api/tender/{tender_id}")
    def get(request, tender_id: int):
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)
        user_email = auth.get('email') if auth else None
        detail = chat_service.get_tender_detail(tender_id)
        # Check if tender is saved by this user
        saved = False
        if user_email and detail:
            saved = is_tender_saved(user_email, tender_id)
        panel = tender_detail_panel(detail, language=language, auth=auth, is_saved=saved)
        if not panel:
            return Response("Tender not found", status_code=404)
        return HTMLResponse(to_xml(panel))

    @rt("/api/auth/status")
    def get(request):
        """Return current auth status for the client."""
        auth = get_auth_from_request(request)
        if auth:
            return JSONResponse({
                "authenticated": True,
                "email": auth.get("email", ""),
                "name": auth.get("name", ""),
            })
        return JSONResponse({"authenticated": False})

    @rt("/api/save-tender/{tender_id}")
    async def post(request, tender_id: int):
        """Save a tender to the user's pipeline."""
        auth = get_auth_from_request(request)
        if not auth or not auth.get('email'):
            return JSONResponse(
                {"error": "Authentication required", "authenticated": False},
                status_code=401
            )

        user_email = auth['email']
        user_name = auth.get('name', '')

        # Check if already saved
        if is_tender_saved(user_email, tender_id):
            return JSONResponse({"ok": True, "already_saved": True})

        # Fetch tender data snapshot — reject unknown tender ids (empty dict)
        tender_data = get_tender_data_for_save(tender_id)
        if not tender_data:
            return JSONResponse({"error": "Tender not found"}, status_code=404)

        success = save_tender(
            user_email=user_email,
            tender_id=tender_id,
            tender_data=tender_data,
            user_name=user_name
        )

        if success:
            return JSONResponse({"ok": True})
        return JSONResponse({"error": "Failed to save tender"}, status_code=500)

    @rt("/api/unsave-tender/{tender_id}")
    async def post(request, tender_id: int):
        """Remove a tender from the user's pipeline."""
        auth = get_auth_from_request(request)
        if not auth or not auth.get('email'):
            return JSONResponse(
                {"error": "Authentication required", "authenticated": False},
                status_code=401
            )

        success = unsave_tender(auth['email'], tender_id)
        if success:
            return JSONResponse({"ok": True})
        return JSONResponse({"error": "Failed to unsave tender"}, status_code=500)

    @rt("/api/artifact/{artifact_type}/{artifact_id}")
    def get(request, artifact_type: str, artifact_id: str):
        """Fetch a server-rendered HTML fragment for a canvas artifact.

        Currently supports:
        - tender_detail: renders the tender detail panel inside the canvas
        More artifact types will be added in Phase 2/3.
        """
        language = get_language_from_request(request)
        auth = get_auth_from_request(request)

        if artifact_type == "tender_detail":
            # Extract tender_id from artifact_id (format: "tender_{id}")
            tender_id_str = artifact_id.replace("tender_", "")
            try:
                tender_id = int(tender_id_str)
            except (ValueError, TypeError):
                return Response("Invalid artifact ID", status_code=400)

            user_email = auth.get('email') if auth else None
            detail = chat_service.get_tender_detail(tender_id)
            saved = False
            if user_email and detail:
                saved = is_tender_saved(user_email, tender_id)
            panel = tender_detail_panel(detail, language=language, auth=auth, is_saved=saved)
            if not panel:
                return Response("Tender not found", status_code=404)
            return HTMLResponse(to_xml(panel))

        if artifact_type == "tender_comparison":
            conv_id = request.query_params.get("conversation_id", "")
            artifact = chat_service.get_artifact(conv_id, artifact_id) if conv_id else None
            if artifact and artifact.get("data"):
                panel = tender_comparison_panel(artifact["data"], language=language)
                return HTMLResponse(to_xml(panel))
            return Response("Artifact not found", status_code=404)

        if artifact_type == "create_plan":
            conv_id = request.query_params.get("conversation_id", "")
            artifact = chat_service.get_artifact(conv_id, artifact_id) if conv_id else None
            if artifact and artifact.get("data"):
                panel = create_plan_panel(artifact["data"], language=language)
                return HTMLResponse(to_xml(panel))
            return Response("Artifact not found", status_code=404)

        if artifact_type == "legal_lookup":
            conv_id = request.query_params.get("conversation_id", "")
            artifact = chat_service.get_artifact(conv_id, artifact_id) if conv_id else None
            if artifact and artifact.get("data"):
                panel = legal_lookup_panel(artifact["data"], language=language)
                return HTMLResponse(to_xml(panel))
            return Response("Artifact not found", status_code=404)

        if artifact_type == "risk_analysis":
            conv_id = request.query_params.get("conversation_id", "")
            artifact = chat_service.get_artifact(conv_id, artifact_id) if conv_id else None
            if artifact and artifact.get("data"):
                panel = risk_analysis_panel(artifact["data"], language=language)
                return HTMLResponse(to_xml(panel))
            return Response("Artifact not found", status_code=404)

        if artifact_type == "gap_analysis":
            conv_id = request.query_params.get("conversation_id", "")
            artifact = chat_service.get_artifact(conv_id, artifact_id) if conv_id else None
            if artifact and artifact.get("data"):
                panel = gap_analysis_panel(artifact["data"], language=language)
                return HTMLResponse(to_xml(panel))
            return Response("Artifact not found", status_code=404)

        if artifact_type == "requirements":
            conv_id = request.query_params.get("conversation_id", "")
            artifact = chat_service.get_artifact(conv_id, artifact_id) if conv_id else None
            if artifact and artifact.get("data"):
                panel = requirements_panel(artifact["data"], language=language)
                return HTMLResponse(to_xml(panel))
            return Response("Artifact not found", status_code=404)

        if artifact_type == "price_benchmark":
            conv_id = request.query_params.get("conversation_id", "")
            artifact = chat_service.get_artifact(conv_id, artifact_id) if conv_id else None
            if artifact and artifact.get("data"):
                panel = price_benchmark_panel(artifact["data"], language=language)
                return HTMLResponse(to_xml(panel))
            return Response("Artifact not found", status_code=404)

        if artifact_type == "rfp_draft":
            conv_id = request.query_params.get("conversation_id", "")
            artifact = chat_service.get_artifact(conv_id, artifact_id) if conv_id else None
            if artifact and artifact.get("data"):
                panel = rfp_draft_panel(artifact["data"], language=language)
                return HTMLResponse(to_xml(panel))
            return Response("Artifact not found", status_code=404)

        return Response(f"Unknown artifact type: {artifact_type}", status_code=404)

    @rt("/api/role/switch/{role}")
    @require_auth
    def post(request, role: str):
        """Switch between buyer and seller role."""
        if role not in ("buyer", "seller"):
            return JSONResponse({"error": "Invalid role"}, status_code=400)
        auth = request.session.get("auth")
        if auth:
            auth["role"] = role
            request.session["auth"] = auth
        return JSONResponse({"ok": True, "role": role})

    @rt("/set-language/{lang}")
    def get(request, lang: str):
        if lang not in SUPPORTED_LANGUAGES:
            lang = "en"
        referer = request.headers.get("referer", "/") or "/"
        # Strip ?lang=... so the new cookie value isn't immediately overridden
        # by a stale query param (the bug Maarius hit when ET->EN didn't take).
        # Also reject cross-origin referer to prevent open-redirect via crafted
        # Referer header.
        try:
            parts = urlparse(referer)
            if parts.netloc and parts.netloc != request.url.netloc:
                parts = urlparse("/")
            qs = [(k, v) for (k, v) in parse_qsl(parts.query, keep_blank_values=True) if k != "lang"]
            redirect_url = urlunparse(parts._replace(query=urlencode(qs))) or "/"
        except Exception:
            redirect_url = "/"
        response = RedirectResponse(url=redirect_url, status_code=302)
        response.set_cookie(
            key=LANGUAGE_COOKIE,
            value=lang,
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=False,
            samesite="lax",
        )
        return response
