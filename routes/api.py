"""API routes for Tendly Buyer."""

import json
import asyncio

from starlette.responses import StreamingResponse, HTMLResponse, Response, RedirectResponse, JSONResponse
from fasthtml.common import to_xml

from components.tender_detail import tender_detail_panel
from components.artifacts.competitor_intel import competitor_intel_panel
from components.artifacts.tender_comparison import tender_comparison_panel
from components.artifacts.risk_analysis import risk_analysis_panel
from components.artifacts.winning_strategy import winning_strategy_panel
from components.artifacts.gap_analysis import gap_analysis_panel
from components.artifacts.requirements import requirements_panel
from components.artifacts.price_benchmark import price_benchmark_panel
from components.artifacts.rfp_draft import rfp_draft_panel
from config.i18n import get_language_from_request, SUPPORTED_LANGUAGES, LANGUAGE_COOKIE
from routes.auth_utils import get_auth_from_request
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
                    result = await chat_service.process_message_sync(conversation_id, message)
                else:
                    result = await chat_service.process_message(conversation_id, message)

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

    @rt("/api/conversations")
    def get(request):
        auth = get_auth_from_request(request)
        user_email = auth.get('email') if auth else None
        return chat_service.get_conversations(user_email=user_email)

    @rt("/api/conversations/new")
    def post(request):
        auth = get_auth_from_request(request)
        user_email = auth.get('email') if auth else None
        cid = chat_service.create_conversation(user_email=user_email)
        return {"conversation_id": cid}

    @rt("/api/conversations/{conversation_id}")
    def delete(request, conversation_id: str):
        chat_service.delete_conversation(conversation_id)
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

        # Fetch tender data snapshot
        tender_data = get_tender_data_for_save(tender_id)

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

        if artifact_type == "competitor_intel":
            # Look up artifact data from conversation store
            # The artifact_id is passed as a query param or from conversation
            conv_id = request.query_params.get("conversation_id", "")
            artifact = chat_service.get_artifact(conv_id, artifact_id) if conv_id else None
            if artifact and artifact.get("data"):
                panel = competitor_intel_panel(artifact["data"], language=language)
                return HTMLResponse(to_xml(panel))
            return Response("Artifact not found", status_code=404)

        if artifact_type == "tender_comparison":
            conv_id = request.query_params.get("conversation_id", "")
            artifact = chat_service.get_artifact(conv_id, artifact_id) if conv_id else None
            if artifact and artifact.get("data"):
                panel = tender_comparison_panel(artifact["data"], language=language)
                return HTMLResponse(to_xml(panel))
            return Response("Artifact not found", status_code=404)

        if artifact_type == "risk_analysis":
            conv_id = request.query_params.get("conversation_id", "")
            artifact = chat_service.get_artifact(conv_id, artifact_id) if conv_id else None
            if artifact and artifact.get("data"):
                panel = risk_analysis_panel(artifact["data"], language=language)
                return HTMLResponse(to_xml(panel))
            return Response("Artifact not found", status_code=404)

        if artifact_type == "winning_strategy":
            conv_id = request.query_params.get("conversation_id", "")
            artifact = chat_service.get_artifact(conv_id, artifact_id) if conv_id else None
            if artifact and artifact.get("data"):
                panel = winning_strategy_panel(artifact["data"], language=language)
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
        referer = request.headers.get("referer", "/")
        redirect_url = referer if referer else "/"
        response = RedirectResponse(url=redirect_url, status_code=302)
        response.set_cookie(
            key=LANGUAGE_COOKIE,
            value=lang,
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=False,
            samesite="lax",
        )
        return response
