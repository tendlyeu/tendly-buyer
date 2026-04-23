"""Procurement plan CRUD service."""

import uuid
from datetime import datetime
from core.database import (
    ProcurementPlan, ProcurementStep, ProcurementDocument,
    ApprovalAction, TeamMember, ChatContext,
)

WORKFLOW_STEPS = [
    (1, "domain_review", "domain_lead"),
    (2, "market_research", "domain_lead"),
    (3, "plan_review", "procurement_manager"),
    (4, "board_approval", "board"),
    (5, "document_preparation", "domain_specialist"),
]

# In-memory store (swap for DB session in production when tendly schema is available)
_plans = {}
_steps = {}
_documents = {}
_approvals = {}
_team = {}


def create_plan(title, description="", category="", estimated_value=None,
                cpv_code="", fiscal_year=2026, procurement_method="open",
                created_by_email=None, organization_id=None):
    plan_id = str(uuid.uuid4())
    plan = {
        "id": plan_id,
        "organization_id": organization_id or "",
        "created_by_email": created_by_email or "",
        "title": title,
        "description": description,
        "status": "draft",
        "current_step": 1,
        "category": category,
        "cpv_code": cpv_code,
        "estimated_value": float(estimated_value) if estimated_value else 0,
        "currency": "EUR",
        "procurement_method": procurement_method,
        "fiscal_year": fiscal_year,
        "budget_approved": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    _plans[plan_id] = plan

    # Create workflow steps
    for step_num, step_name, role in WORKFLOW_STEPS:
        step_id = str(uuid.uuid4())
        _steps[step_id] = {
            "id": step_id,
            "procurement_plan_id": plan_id,
            "step_number": step_num,
            "step_name": step_name,
            "status": "in_progress" if step_num == 1 else "pending",
            "assigned_role": role,
            "assigned_to_email": "",
            "notes": "",
            "completed_at": None,
            "completed_by": None,
        }

    return plan


def get_plan(plan_id):
    return _plans.get(plan_id)


def list_plans(organization_id=None, status=None):
    plans = list(_plans.values())
    if organization_id:
        plans = [p for p in plans if p.get("organization_id") == organization_id]
    if status:
        plans = [p for p in plans if p.get("status") == status]
    return sorted(plans, key=lambda p: p.get("created_at", ""), reverse=True)


def update_plan(plan_id, **kwargs):
    plan = _plans.get(plan_id)
    if not plan:
        return None
    for k, v in kwargs.items():
        if k in plan:
            plan[k] = v
    plan["updated_at"] = datetime.utcnow().isoformat()
    return plan


def delete_plan(plan_id):
    return _plans.pop(plan_id, None) is not None


def get_steps(plan_id):
    return sorted(
        [s for s in _steps.values() if s["procurement_plan_id"] == plan_id],
        key=lambda s: s["step_number"],
    )


def complete_step(plan_id, step_number, completed_by=None, notes=""):
    plan = _plans.get(plan_id)
    if not plan:
        return False
    if step_number != plan.get("current_step", 1):
        return False

    for s in _steps.values():
        if s["procurement_plan_id"] == plan_id and s["step_number"] == step_number:
            s["status"] = "completed"
            s["completed_at"] = datetime.utcnow().isoformat()
            s["completed_by"] = completed_by or ""
            if notes:
                s["notes"] = notes

    next_step = step_number + 1
    plan["current_step"] = min(next_step, 5)
    if next_step > 5:
        plan["status"] = "completed"
    elif next_step > 4:
        plan["status"] = "approved"
    elif next_step > 2:
        plan["status"] = "review"
    else:
        plan["status"] = "planning"

    for s in _steps.values():
        if s["procurement_plan_id"] == plan_id and s["step_number"] == next_step:
            s["status"] = "in_progress"

    plan["updated_at"] = datetime.utcnow().isoformat()

    _approvals[str(uuid.uuid4())] = {
        "procurement_plan_id": plan_id,
        "step_number": step_number,
        "action": "complete",
        "actor_email": completed_by or "",
        "comment": notes,
        "created_at": datetime.utcnow().isoformat(),
    }

    return True


def get_approvals(plan_id):
    return sorted(
        [a for a in _approvals.values() if a["procurement_plan_id"] == plan_id],
        key=lambda a: a.get("created_at", ""),
    )


def get_stats(organization_id=None):
    plans = list_plans(organization_id=organization_id)
    docs = [d for d in _documents.values() if not organization_id or d.get("organization_id") == organization_id]
    return {
        "active": len([p for p in plans if p["status"] not in ("completed", "cancelled")]),
        "pending_approval": len([p for p in plans if p["status"] == "review"]),
        "completed": len([p for p in plans if p["status"] == "completed"]),
        "documents": len(docs),
    }


# --- Document management ---

def add_document(title, document_type="other", file_name="", file_size=0,
                 mime_type="", content_text="", procurement_plan_id=None,
                 uploaded_by_email=None, organization_id=None):
    doc_id = str(uuid.uuid4())
    doc = {
        "id": doc_id,
        "procurement_plan_id": procurement_plan_id,
        "organization_id": organization_id or "",
        "uploaded_by_email": uploaded_by_email or "",
        "title": title,
        "document_type": document_type,
        "file_name": file_name,
        "file_size": file_size,
        "mime_type": mime_type,
        "content_text": content_text,
        "ai_summary": "",
        "version": 1,
        "status": "draft",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    _documents[doc_id] = doc
    return doc


def list_documents(procurement_plan_id=None, organization_id=None, document_type=None):
    docs = list(_documents.values())
    if procurement_plan_id:
        docs = [d for d in docs if d.get("procurement_plan_id") == procurement_plan_id]
    if organization_id:
        docs = [d for d in docs if d.get("organization_id") == organization_id]
    if document_type:
        docs = [d for d in docs if d.get("document_type") == document_type]
    return sorted(docs, key=lambda d: d.get("created_at", ""), reverse=True)


def get_document(doc_id):
    return _documents.get(doc_id)


def delete_document(doc_id):
    return _documents.pop(doc_id, None) is not None


# --- Team management ---

def add_team_member(organization_id, user_email, name="", procurement_role="", specialty=""):
    member_id = str(uuid.uuid4())
    member = {
        "id": member_id,
        "organization_id": organization_id,
        "user_email": user_email,
        "name": name,
        "procurement_role": procurement_role,
        "specialty": specialty,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
    }
    _team[member_id] = member
    return member


def list_team_members(organization_id):
    return [m for m in _team.values() if m["organization_id"] == organization_id and m.get("is_active", True)]


def remove_team_member(member_id):
    member = _team.get(member_id)
    if member:
        member["is_active"] = False
        return True
    return False
