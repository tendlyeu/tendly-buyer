"""
Database layer for Tendly Chat - Shared access to Tendly's PostgreSQL database.
Copied from tendly/database.py - trimmed to only include models needed for chat.

Supports two connection modes:
1. GCP Cloud SQL via Python Connector (set USE_GCP_CLOUD_SQL=true)
2. Standard DATABASE_URL (default fallback)
"""

from sqlalchemy import create_engine, Column, String, Boolean, Integer, Float, DateTime, Text, JSON, or_
from sqlalchemy.engine import URL as SA_URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, deferred
from datetime import datetime
import os
import json
from urllib.parse import urlparse, unquote


def _create_engine():
    """Create SQLAlchemy engine based on environment configuration."""
    use_gcp_cloud_sql = os.environ.get('USE_GCP_CLOUD_SQL', 'false').lower() == 'true'

    if use_gcp_cloud_sql:
        from google.cloud.sql.connector import Connector
        from google.oauth2 import service_account
        import atexit

        instance_connection_name = os.environ.get(
            'CLOUD_SQL_INSTANCE',
            'scenic-impact-476918-n6:europe-north1:tendly-prod'
        )
        db_user = os.environ.get('DB_USER', 'tendly_admin')
        db_password = os.environ.get('DB_PASSWORD', '')
        db_name = os.environ.get('DB_NAME', 'tendly_prod')

        gcp_creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        credentials = None
        if gcp_creds_json:
            try:
                creds_info = json.loads(gcp_creds_json)
                credentials = service_account.Credentials.from_service_account_info(creds_info)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not parse GCP credentials: {e}")

        _cloud_sql_connector = Connector(
            credentials=credentials,
            refresh_strategy="lazy"
        ) if credentials else Connector(refresh_strategy="lazy")

        def _cleanup_connector():
            nonlocal _cloud_sql_connector
            if _cloud_sql_connector:
                _cloud_sql_connector.close()
                _cloud_sql_connector = None

        atexit.register(_cleanup_connector)

        print(f"Connecting to GCP Cloud SQL: {instance_connection_name}")
        print(f"   Database: {db_name}, User: {db_user}")

        def getconn():
            return _cloud_sql_connector.connect(
                instance_connection_name,
                "pg8000",
                user=db_user,
                password=db_password,
                db=db_name,
            )

        return create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_timeout=60,
            pool_size=5,
            max_overflow=10,
            echo=False,
        )
    else:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required when USE_GCP_CLOUD_SQL=false.")

        # Parse URL to handle passwords with special characters
        parsed = urlparse(database_url)
        sa_url = SA_URL.create(
            drivername="postgresql",
            username=unquote(parsed.username or ""),
            password=unquote(parsed.password or ""),
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            database=parsed.path.lstrip("/") if parsed.path else "",
        )

        return create_engine(
            sa_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_timeout=60,
            pool_size=5,
            max_overflow=10,
            echo=False,
            connect_args={
                "connect_timeout": 60,
                "application_name": "tendly_chat",
                "options": "-c statement_timeout=300000"
            }
        )


# Lazy engine creation — deferred until first get_session() call
_engine = None
_SessionLocal = None
Base = declarative_base()


def _get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = _create_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_session():
    """Get a new database session. Always close with session.close() in a finally block."""
    _get_engine()
    return _SessionLocal()


# ============================================================
# MODELS (Read-only copies from tendly/database.py)
# ============================================================

class Tender(Base):
    __tablename__ = 'tenders'

    procurement_id = Column(Integer, primary_key=True)
    procurement_reference_nr = Column(String, nullable=False)
    procurement_name = Column(String, nullable=False)
    procurement_name_en = Column(String, default="")
    procurement_name_et = Column(String, default="")
    procurement_name_lv = Column(String, default="")
    procurement_name_lt = Column(String, default="")
    procurement_name_pl = Column(String, default="")
    procurement_name_fr = Column(String, default="")
    contracting_authority_name = Column(String)
    procurement_status = Column(String)
    procurement_type = Column(String)  # E=Works, T=Services, A=Supplies
    procurement_process_type = Column(String)
    short_description = Column(Text, default="")
    short_description_en = Column(Text, default="")
    short_description_et = Column(Text, default="")
    short_description_lv = Column(Text, default="")
    short_description_lt = Column(Text, default="")
    short_description_pl = Column(Text, default="")
    short_description_fr = Column(Text, default="")
    is_e_procurement = Column(Boolean, default=False)
    main_cpv_id = Column(Integer)
    main_cpv_name = Column(String)
    is_green_procurement = Column(Boolean, default=False)
    is_suspended = Column(Boolean, default=False)
    buyer_email = Column(String, default="")
    country = Column(String(50), default="Estonia")
    country_code = Column(String(2), default="EE")
    currency = Column(String(3), default="EUR")
    source_portal_url = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Alias for backward compatibility
EstonianTender = Tender


class TenderDetail(Base):
    __tablename__ = 'tender_details'

    procurement_id = Column(Integer, primary_key=True)
    estimated_cost = Column(Float)
    duration_in_months = Column(Integer)
    is_eu_financing = Column(Boolean, default=False)
    is_green = Column(Boolean, default=False)
    has_innovative_aspects = Column(Boolean, default=False)
    short_description = Column(Text, default="")
    short_description_en = Column(Text, default="")
    short_description_et = Column(Text, default="")
    short_description_lv = Column(Text, default="")
    short_description_lt = Column(Text, default="")
    short_description_pl = Column(Text, default="")
    short_description_fr = Column(Text, default="")
    submission_deadline = Column(DateTime)
    procedure_type_code = Column(String, default="")
    tender_name = Column(String, default="")
    tender_name_en = Column(String, default="")
    tender_name_et = Column(String, default="")
    tender_name_lv = Column(String, default="")
    tender_name_lt = Column(String, default="")
    tender_name_pl = Column(String, default="")
    tender_name_fr = Column(String, default="")
    primary_cpv_id = Column(Integer)
    primary_cpv_code = Column(String, default="")
    primary_cpv_name = Column(String, default="")
    nuts_code = Column(String, default="")
    ai_requirements = Column(Text, default="")
    ai_requirements_en = Column(Text, default="")
    ai_requirements_et = Column(Text, default="")
    ai_requirements_lv = Column(Text, default="")
    ai_requirements_lt = Column(Text, default="")
    ai_requirements_pl = Column(Text, default="")
    ai_requirements_fr = Column(Text, default="")
    document_url = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Alias for backward compatibility
EstonianTenderDetail = TenderDetail


class TenderResult(Base):
    __tablename__ = 'tender_results'

    procurement_id = Column(Integer, primary_key=True)
    winner_name = Column(String, default="")
    winner_reg_code = Column(String, default="")
    contract_cost = Column(Float)
    contract_actual_cost = Column(Float)
    contract_status = Column(String, default="")
    offer_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


EstonianTenderResult = TenderResult


class TenderDocuments(Base):
    __tablename__ = 'tender_documents'

    tender_id = Column(Integer, primary_key=True)
    procurement_doc_old_id = Column(Integer, primary_key=True)
    document_name = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    document_type = Column(String, default="")
    ai_summary = Column(Text, default="")
    ai_summary_en = Column(Text, default="")
    ai_summary_ee = Column(Text, default="")
    ai_summary_lv = Column(Text, default="")
    ai_summary_lt = Column(Text, default="")
    ai_summary_pl = Column(Text, default="")
    ai_summary_fr = Column(Text, default="")
    web_url = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenderQualityScore(Base):
    __tablename__ = 'tender_quality_scores'

    procurement_id = Column(Integer, primary_key=True)
    overall_score = Column(Float, default=0.0)
    analysis_en = Column(JSON, nullable=True)
    analysis_et = Column(JSON, nullable=True)
    analysis_lv = Column(JSON, nullable=True)
    analysis_lt = Column(JSON, nullable=True)
    analysis_pl = Column(JSON, nullable=True)
    analysis_fr = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenderEvaluationCriteria(Base):
    __tablename__ = 'tender_evaluation_criteria'

    id = Column(String, primary_key=True)
    procurement_id = Column(Integer, nullable=False)
    criterion_name = Column(String, nullable=False)
    criterion_name_en = Column(String, default="")
    criterion_name_et = Column(String, default="")
    criterion_name_lv = Column(String, default="")
    criterion_name_lt = Column(String, default="")
    criterion_name_pl = Column(String, default="")
    criterion_name_fr = Column(String, default="")
    weight_percentage = Column(Float, nullable=True)
    description = Column(Text, default="")
    description_en = Column(Text, default="")
    description_et = Column(Text, default="")
    description_lv = Column(Text, default="")
    description_lt = Column(Text, default="")
    description_pl = Column(Text, default="")
    description_fr = Column(Text, default="")
    criterion_type = Column(String, default="quality")
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# USER & SAVED TENDERS MODELS (for authentication and pipeline)
# ============================================================

class User(Base):
    __tablename__ = 'users'

    email = Column(String, primary_key=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    company = Column(String, default="")
    industry = Column(String, default="")
    country = Column(String, default="")
    website = Column(String, default="")
    phone = Column(String, default="")
    auth0_sub = Column(String, default="")
    profile_picture = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    last_seen_at = deferred(Column(DateTime, nullable=True))


class SavedTenders(Base):
    __tablename__ = 'saved_tenders'

    user_email = Column(String, primary_key=True)
    tender_id = Column(Integer, primary_key=True)
    organization_id = Column(String, nullable=True)
    tender_name = Column(String, default="")
    tender_name_en = Column(String, default="")
    tender_name_et = Column(String, default="")
    tender_name_lv = Column(String, default="")
    tender_name_lt = Column(String, default="")
    tender_name_pl = Column(String, default="")
    tender_name_fr = Column(String, default="")
    tender_authority = Column(String, default="")
    tender_value = Column(Float)
    tender_type = Column(String, default="")
    submission_deadline = Column(DateTime)
    cpv_code = Column(Integer)
    cpv_name = Column(String, default="")
    tender_description = Column(Text, default="")
    tender_description_en = Column(Text, default="")
    tender_description_et = Column(Text, default="")
    tender_description_lv = Column(Text, default="")
    tender_description_lt = Column(Text, default="")
    tender_description_pl = Column(Text, default="")
    tender_description_fr = Column(Text, default="")
    user_notes = Column(Text, default="")
    saved_by_name = Column(String, default="")
    notes_by_email = Column(String, nullable=True)
    notes_by_name = Column(String, default="")
    user_tags = Column(String, default="")
    pipeline_stage = deferred(Column(String, nullable=True))
    is_active = Column(Boolean, default=True)
    reminder_set = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user(email: str):
    """Get user by email."""
    if not email:
        return None
    email = email.lower().strip()
    db = get_session()
    try:
        return db.query(User).filter(User.email == email).first()
    except Exception as e:
        print(f"Database error in get_user: {e}")
        return None
    finally:
        db.close()


def is_tender_saved(user_email: str, tender_id: int) -> bool:
    """Check if a tender is already saved by a user."""
    db = get_session()
    try:
        existing = db.query(SavedTenders).filter(
            SavedTenders.user_email == user_email,
            SavedTenders.tender_id == tender_id,
            SavedTenders.is_active == True
        ).first()
        return existing is not None
    except Exception:
        return False
    finally:
        db.close()


def save_tender(user_email: str, tender_id: int, tender_data: dict = None,
                user_name: str = None) -> bool:
    """Save/bookmark a tender for a user."""
    db = get_session()
    try:
        existing = db.query(SavedTenders).filter(
            SavedTenders.user_email == user_email,
            SavedTenders.tender_id == tender_id
        ).first()

        if existing:
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
            db.commit()
            return True

        if not user_name:
            user = db.query(User).filter(User.email == user_email).first()
            user_name = user.name if user else user_email.split('@')[0]

        saved_tender = SavedTenders(
            user_email=user_email,
            tender_id=tender_id,
            tender_name=tender_data.get('tender_name', '') if tender_data else '',
            tender_name_en=tender_data.get('tender_name_en', '') if tender_data else '',
            tender_name_et=tender_data.get('tender_name_et', '') if tender_data else '',
            tender_name_lv=tender_data.get('tender_name_lv', '') if tender_data else '',
            tender_authority=tender_data.get('tender_authority', '') if tender_data else '',
            tender_value=tender_data.get('tender_value') if tender_data else None,
            tender_type=tender_data.get('tender_type', '') if tender_data else '',
            submission_deadline=tender_data.get('submission_deadline') if tender_data else None,
            cpv_code=tender_data.get('cpv_code') if tender_data else None,
            cpv_name=tender_data.get('cpv_name', '') if tender_data else '',
            tender_description=tender_data.get('tender_description', '') if tender_data else '',
            tender_description_en=tender_data.get('tender_description_en', '') if tender_data else '',
            tender_description_et=tender_data.get('tender_description_et', '') if tender_data else '',
            tender_description_lv=tender_data.get('tender_description_lv', '') if tender_data else '',
            saved_by_name=user_name
        )

        db.add(saved_tender)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error saving tender: {e}")
        return False
    finally:
        db.close()


def unsave_tender(user_email: str, tender_id: int) -> bool:
    """Remove a saved tender for a user."""
    db = get_session()
    try:
        deleted_count = db.query(SavedTenders).filter(
            SavedTenders.user_email == user_email,
            SavedTenders.tender_id == tender_id
        ).delete(synchronize_session='fetch')
        db.commit()
        return deleted_count > 0
    except Exception as e:
        db.rollback()
        print(f"Error unsaving tender: {e}")
        return False
    finally:
        db.close()


def get_tender_data_for_save(tender_id: int) -> dict:
    """Fetch tender data snapshot for saving to pipeline."""
    db = get_session()
    try:
        tender = db.query(Tender).filter(Tender.procurement_id == tender_id).first()
        detail = db.query(TenderDetail).filter(TenderDetail.procurement_id == tender_id).first()
        if not tender:
            return {}
        return {
            'tender_name': tender.procurement_name or '',
            'tender_name_en': tender.procurement_name_en or '',
            'tender_name_et': tender.procurement_name_et or '',
            'tender_name_lv': tender.procurement_name_lv or '',
            'tender_authority': tender.contracting_authority_name or '',
            'tender_value': detail.estimated_cost if detail else None,
            'tender_type': tender.procurement_type or '',
            'submission_deadline': detail.submission_deadline if detail else None,
            'cpv_code': tender.main_cpv_id,
            'cpv_name': tender.main_cpv_name or '',
            'tender_description': tender.short_description or '',
            'tender_description_en': tender.short_description_en or '',
            'tender_description_et': tender.short_description_et or '',
            'tender_description_lv': tender.short_description_lv or '',
        }
    except Exception as e:
        print(f"Error fetching tender data for save: {e}")
        return {}
    finally:
        db.close()


# ============================================================
# TENDLY SCHEMA — writable database for buyer tools
# ============================================================

TENDLY_DB_URL = os.environ.get(
    "TENDLY_DB_URL",
    "postgresql://finespresso:mlfpass2026@72.62.114.124:5432/finespresso_db",
)

_tendly_engine = None
_TendlySession = None
TendlyBase = declarative_base()


def _get_tendly_engine():
    global _tendly_engine, _TendlySession
    if _tendly_engine is None:
        _tendly_engine = create_engine(
            TENDLY_DB_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
            echo=False,
        )
        _TendlySession = sessionmaker(bind=_tendly_engine)
    return _tendly_engine


def get_tendly_session():
    """Get a session for the tendly schema (writable)."""
    _get_tendly_engine()
    return _TendlySession()


# --- Tendly schema models ---

from sqlalchemy import Numeric
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB
import uuid


class TendlyUser(TendlyBase):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'tendly'}

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    company = Column(String(255))
    role = Column(String(20), default='seller')
    country = Column(String(50))
    language = Column(String(5), default='en')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TendlyTender(TendlyBase):
    __tablename__ = 'tenders'
    __table_args__ = {'schema': 'tendly'}

    id = Column(Integer, primary_key=True)
    external_id = Column(String(255))
    source = Column(String(50), default='contracts_finder')
    title = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(String(50), default='active')
    procurement_method = Column(String(100))
    procurement_method_details = Column(String(500))
    main_category = Column(String(50))
    cpv_code = Column(String(20))
    cpv_description = Column(String(255))
    estimated_value = Column(Numeric(15, 2))
    currency = Column(String(3), default='GBP')
    buyer_name = Column(String(500))
    buyer_id = Column(String(255))
    submission_deadline = Column(DateTime)
    contract_start = Column(DateTime)
    contract_end = Column(DateTime)
    country_code = Column(String(2), default='GB')
    region = Column(String(255))
    notice_url = Column(Text)
    is_sme_suitable = Column(Boolean, default=False)
    published_date = Column(DateTime)
    raw_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TendlyAward(TendlyBase):
    __tablename__ = 'awards'
    __table_args__ = {'schema': 'tendly'}

    id = Column(Integer, primary_key=True)
    tender_id = Column(Integer)
    supplier_name = Column(String(500))
    supplier_id = Column(String(255))
    award_value = Column(Numeric(15, 2))
    currency = Column(String(3), default='GBP')
    award_date = Column(DateTime)
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class RfpDraft(TendlyBase):
    __tablename__ = 'rfp_drafts'
    __table_args__ = {'schema': 'tendly'}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    title = Column(String(500))
    description = Column(Text)
    category = Column(String(50))
    cpv_code = Column(String(20))
    cpv_description = Column(String(255))
    estimated_value = Column(Numeric(15, 2))
    currency = Column(String(3), default='EUR')
    procedure_type = Column(String(100))
    evaluation_criteria = Column(JSONB)
    qualification_requirements = Column(JSONB)
    technical_specifications = Column(Text)
    draft_content = Column(Text)
    status = Column(String(20), default='draft')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PriceBenchmark(TendlyBase):
    __tablename__ = 'price_benchmarks'
    __table_args__ = {'schema': 'tendly'}

    id = Column(Integer, primary_key=True)
    cpv_code = Column(String(20))
    category = Column(String(50))
    country_code = Column(String(2))
    avg_value = Column(Numeric(15, 2))
    median_value = Column(Numeric(15, 2))
    min_value = Column(Numeric(15, 2))
    max_value = Column(Numeric(15, 2))
    sample_count = Column(Integer)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    computed_at = Column(DateTime, default=datetime.utcnow)


class ProcurementPlan(TendlyBase):
    __tablename__ = 'procurement_plans'
    __table_args__ = {'schema': 'tendly'}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(255))
    created_by_email = Column(String(255))
    title = Column(Text, nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default='draft')
    current_step = Column(Integer, default=1)
    category = Column(String(100), default="")
    cpv_code = Column(String(20), default="")
    estimated_value = Column(Numeric(15, 2))
    currency = Column(String(3), default='EUR')
    procurement_method = Column(String(100), default="open")
    fiscal_year = Column(Integer)
    budget_approved = Column(Boolean, default=False)
    budget_approved_at = Column(DateTime)
    budget_approved_by = Column(String(255))
    metadata_json = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProcurementStep(TendlyBase):
    __tablename__ = 'procurement_steps'
    __table_args__ = {'schema': 'tendly'}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    procurement_plan_id = Column(String(36), nullable=False)
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(100), default="")
    status = Column(String(50), default='pending')
    assigned_role = Column(String(50), default="")
    assigned_to_email = Column(String(255))
    notes = Column(Text, default="")
    completed_at = Column(DateTime)
    completed_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProcurementDocument(TendlyBase):
    __tablename__ = 'procurement_documents'
    __table_args__ = {'schema': 'tendly'}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    procurement_plan_id = Column(String(36))
    organization_id = Column(String(255))
    uploaded_by_email = Column(String(255))
    title = Column(Text, nullable=False)
    document_type = Column(String(50), default="other")
    file_name = Column(String(500), default="")
    file_path = Column(String(1000), default="")
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), default="")
    content_text = Column(Text, default="")
    ai_summary = Column(Text, default="")
    ai_analysis = Column(JSONB, default={})
    version = Column(Integer, default=1)
    parent_document_id = Column(String(36))
    status = Column(String(50), default='draft')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ApprovalAction(TendlyBase):
    __tablename__ = 'approval_actions'
    __table_args__ = {'schema': 'tendly'}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    procurement_plan_id = Column(String(36), nullable=False)
    step_number = Column(Integer)
    action = Column(String(50), default="")
    actor_email = Column(String(255))
    actor_role = Column(String(50))
    comment = Column(Text, default="")
    previous_status = Column(String(50))
    new_status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class TeamMember(TendlyBase):
    __tablename__ = 'team_members'
    __table_args__ = {'schema': 'tendly'}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(255), nullable=False)
    user_email = Column(String(255), nullable=False)
    name = Column(String(255), default="")
    procurement_role = Column(String(50), default="")
    specialty = Column(String(100), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatContext(TendlyBase):
    __tablename__ = 'chat_contexts'
    __table_args__ = {'schema': 'tendly'}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(255), nullable=False)
    user_email = Column(String(255))
    organization_id = Column(String(255))
    procurement_plan_id = Column(String(36))
    title = Column(Text, default="New conversation")
    messages = Column(JSONB, default=[])
    artifacts = Column(JSONB, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# --- Tendly user helpers ---

def get_tendly_user(email: str):
    """Get user from the tendly schema by email."""
    if not email:
        return None
    db = get_tendly_session()
    try:
        return db.query(TendlyUser).filter(TendlyUser.email == email.lower().strip()).first()
    except Exception as e:
        print(f"Error in get_tendly_user: {e}")
        return None
    finally:
        db.close()


def create_tendly_user(email: str, password_hash: str, name: str = "",
                       role: str = "seller", company: str = "") -> bool:
    """Create a new user in the tendly schema."""
    db = get_tendly_session()
    try:
        user = TendlyUser(
            email=email.lower().strip(),
            password_hash=password_hash,
            name=name,
            role=role,
            company=company,
        )
        db.add(user)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error creating tendly user: {e}")
        return False
    finally:
        db.close()
