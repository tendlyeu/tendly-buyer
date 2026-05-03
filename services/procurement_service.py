"""Procurement plan CRUD service — persisted to PostgreSQL via SQLAlchemy."""

import uuid
from datetime import datetime
from core.database import (
    get_tendly_session,
    ProcurementPlan, ProcurementStep, ProcurementDocument,
    ApprovalAction, TeamMember,
)

WORKFLOW_STEPS = [
    (1, "domain_review", "domain_lead"),
    (2, "market_research", "domain_lead"),
    (3, "plan_review", "procurement_manager"),
    (4, "board_approval", "board"),
    (5, "document_preparation", "domain_specialist"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _model_to_dict(obj):
    """Convert a SQLAlchemy ORM object to a plain dict.

    Datetime values are serialised to ISO-8601 strings so that the
    returned dict has the exact same shape as the old in-memory dicts.
    """
    if obj is None:
        return None
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        d[col.name] = val
    return d


# ---------------------------------------------------------------------------
# Plan CRUD
# ---------------------------------------------------------------------------

def create_plan(title, description="", category="", estimated_value=None,
                cpv_code="", fiscal_year=2026, procurement_method="open",
                created_by_email=None, organization_id=None, metadata_json=None):
    plan_id = str(uuid.uuid4())
    session = get_tendly_session()
    try:
        plan = ProcurementPlan(
            id=plan_id,
            organization_id=organization_id or "",
            created_by_email=created_by_email or "",
            title=title,
            description=description,
            status="draft",
            current_step=1,
            category=category,
            cpv_code=cpv_code,
            estimated_value=float(estimated_value) if estimated_value else 0,
            currency="EUR",
            procurement_method=procurement_method,
            fiscal_year=fiscal_year,
            budget_approved=False,
            metadata_json=metadata_json or {},
        )
        session.add(plan)

        # Create workflow steps
        for step_num, step_name, role in WORKFLOW_STEPS:
            step = ProcurementStep(
                id=str(uuid.uuid4()),
                procurement_plan_id=plan_id,
                step_number=step_num,
                step_name=step_name,
                status="in_progress" if step_num == 1 else "pending",
                assigned_role=role,
                assigned_to_email="",
                notes="",
            )
            session.add(step)

        session.commit()
        # Re-read so timestamps are populated by the DB
        session.refresh(plan)
        return _model_to_dict(plan)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_plan(plan_id):
    session = get_tendly_session()
    try:
        plan = session.query(ProcurementPlan).filter(ProcurementPlan.id == plan_id).first()
        return _model_to_dict(plan)
    finally:
        session.close()


def list_plans(organization_id=None, status=None):
    session = get_tendly_session()
    try:
        q = session.query(ProcurementPlan)
        if organization_id:
            q = q.filter(ProcurementPlan.organization_id == organization_id)
        if status:
            q = q.filter(ProcurementPlan.status == status)
        q = q.order_by(ProcurementPlan.created_at.desc())
        return [_model_to_dict(p) for p in q.all()]
    finally:
        session.close()


def update_plan(plan_id, **kwargs):
    session = get_tendly_session()
    try:
        plan = session.query(ProcurementPlan).filter(ProcurementPlan.id == plan_id).first()
        if not plan:
            return None
        for k, v in kwargs.items():
            if hasattr(plan, k):
                setattr(plan, k, v)
        plan.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(plan)
        return _model_to_dict(plan)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_plan(plan_id):
    session = get_tendly_session()
    try:
        plan = session.query(ProcurementPlan).filter(ProcurementPlan.id == plan_id).first()
        if not plan:
            return False
        # Delete related steps, approvals
        session.query(ProcurementStep).filter(ProcurementStep.procurement_plan_id == plan_id).delete(synchronize_session='fetch')
        session.query(ApprovalAction).filter(ApprovalAction.procurement_plan_id == plan_id).delete(synchronize_session='fetch')
        session.delete(plan)
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def get_steps(plan_id):
    session = get_tendly_session()
    try:
        steps = (
            session.query(ProcurementStep)
            .filter(ProcurementStep.procurement_plan_id == plan_id)
            .order_by(ProcurementStep.step_number)
            .all()
        )
        return [_model_to_dict(s) for s in steps]
    finally:
        session.close()


def complete_step(plan_id, step_number, completed_by=None, notes=""):
    session = get_tendly_session()
    try:
        plan = session.query(ProcurementPlan).filter(ProcurementPlan.id == plan_id).first()
        if not plan:
            return False
        if step_number != (plan.current_step or 1):
            return False

        # Mark current step completed
        current_step = (
            session.query(ProcurementStep)
            .filter(
                ProcurementStep.procurement_plan_id == plan_id,
                ProcurementStep.step_number == step_number,
            )
            .first()
        )
        if current_step:
            current_step.status = "completed"
            current_step.completed_at = datetime.utcnow()
            current_step.completed_by = completed_by or ""
            if notes:
                current_step.notes = notes

        # Advance plan
        next_step = step_number + 1
        plan.current_step = min(next_step, 5)
        if next_step > 5:
            plan.status = "completed"
        elif next_step > 4:
            plan.status = "approved"
        elif next_step > 2:
            plan.status = "review"
        else:
            plan.status = "planning"

        # Activate next step
        next_step_obj = (
            session.query(ProcurementStep)
            .filter(
                ProcurementStep.procurement_plan_id == plan_id,
                ProcurementStep.step_number == next_step,
            )
            .first()
        )
        if next_step_obj:
            next_step_obj.status = "in_progress"

        plan.updated_at = datetime.utcnow()

        # Record approval action
        approval = ApprovalAction(
            id=str(uuid.uuid4()),
            procurement_plan_id=plan_id,
            step_number=step_number,
            action="complete",
            actor_email=completed_by or "",
            comment=notes,
        )
        session.add(approval)

        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------

def get_approvals(plan_id):
    session = get_tendly_session()
    try:
        approvals = (
            session.query(ApprovalAction)
            .filter(ApprovalAction.procurement_plan_id == plan_id)
            .order_by(ApprovalAction.created_at)
            .all()
        )
        return [_model_to_dict(a) for a in approvals]
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def get_stats(organization_id=None):
    session = get_tendly_session()
    try:
        pq = session.query(ProcurementPlan)
        dq = session.query(ProcurementDocument)
        if organization_id:
            pq = pq.filter(ProcurementPlan.organization_id == organization_id)
            dq = dq.filter(ProcurementDocument.organization_id == organization_id)

        plans = pq.all()
        doc_count = dq.count()
        return {
            "active": len([p for p in plans if p.status not in ("completed", "cancelled")]),
            "pending_approval": len([p for p in plans if p.status == "review"]),
            "completed": len([p for p in plans if p.status == "completed"]),
            "documents": doc_count,
        }
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Document management
# ---------------------------------------------------------------------------

def add_document(title, document_type="other", file_name="", file_size=0,
                 mime_type="", content_text="", procurement_plan_id=None,
                 uploaded_by_email=None, organization_id=None, file_path=""):
    session = get_tendly_session()
    try:
        doc = ProcurementDocument(
            id=str(uuid.uuid4()),
            procurement_plan_id=procurement_plan_id,
            organization_id=organization_id or "",
            uploaded_by_email=uploaded_by_email or "",
            title=title,
            document_type=document_type,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            content_text=content_text,
            ai_summary="",
            version=1,
            status="draft",
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return _model_to_dict(doc)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def list_documents(procurement_plan_id=None, organization_id=None, document_type=None):
    session = get_tendly_session()
    try:
        q = session.query(ProcurementDocument)
        if procurement_plan_id:
            q = q.filter(ProcurementDocument.procurement_plan_id == procurement_plan_id)
        if organization_id:
            q = q.filter(ProcurementDocument.organization_id == organization_id)
        if document_type:
            q = q.filter(ProcurementDocument.document_type == document_type)
        q = q.order_by(ProcurementDocument.created_at.desc())
        return [_model_to_dict(d) for d in q.all()]
    finally:
        session.close()


def get_document(doc_id):
    session = get_tendly_session()
    try:
        doc = session.query(ProcurementDocument).filter(ProcurementDocument.id == doc_id).first()
        return _model_to_dict(doc)
    finally:
        session.close()


def delete_document(doc_id):
    session = get_tendly_session()
    try:
        doc = session.query(ProcurementDocument).filter(ProcurementDocument.id == doc_id).first()
        if not doc:
            return False
        session.delete(doc)
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Team management
# ---------------------------------------------------------------------------

def add_team_member(organization_id, user_email, name="", procurement_role="", specialty=""):
    session = get_tendly_session()
    try:
        member = TeamMember(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            user_email=user_email,
            name=name,
            procurement_role=procurement_role,
            specialty=specialty,
            is_active=True,
        )
        session.add(member)
        session.commit()
        session.refresh(member)
        return _model_to_dict(member)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def list_team_members(organization_id):
    session = get_tendly_session()
    try:
        members = (
            session.query(TeamMember)
            .filter(
                TeamMember.organization_id == organization_id,
                TeamMember.is_active == True,
            )
            .all()
        )
        return [_model_to_dict(m) for m in members]
    finally:
        session.close()


def remove_team_member(member_id):
    session = get_tendly_session()
    try:
        member = session.query(TeamMember).filter(TeamMember.id == member_id).first()
        if not member:
            return False
        member.is_active = False
        member.updated_at = datetime.utcnow()
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
