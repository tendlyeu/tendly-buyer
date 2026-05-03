-- Buyer-specific tables for Tendly Buyer portal
-- These tables live in the 'tendly' schema and are managed via TendlyBase models.
-- Mirrors: core/database.py — ProcurementPlan, ProcurementStep, ProcurementDocument,
--          ApprovalAction, TeamMember, ChatContext
--
-- Run after 001_create_tables.sql and 002_create_indexes.sql.

-- ============================================================
-- Procurement Plans
-- ============================================================

CREATE TABLE IF NOT EXISTS tendly.procurement_plans (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(255),
    created_by_email VARCHAR(255),
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status VARCHAR(50) DEFAULT 'draft',
    current_step INTEGER DEFAULT 1,
    category VARCHAR(100) DEFAULT '',
    cpv_code VARCHAR(20) DEFAULT '',
    estimated_value NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    procurement_method VARCHAR(100) DEFAULT 'open',
    fiscal_year INTEGER,
    budget_approved BOOLEAN DEFAULT false,
    budget_approved_at TIMESTAMPTZ,
    budget_approved_by VARCHAR(255),
    metadata_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_procurement_plans_org
    ON tendly.procurement_plans(organization_id);
CREATE INDEX IF NOT EXISTS idx_procurement_plans_status
    ON tendly.procurement_plans(status);
CREATE INDEX IF NOT EXISTS idx_procurement_plans_created_by
    ON tendly.procurement_plans(created_by_email);
CREATE INDEX IF NOT EXISTS idx_procurement_plans_fiscal_year
    ON tendly.procurement_plans(fiscal_year);

-- ============================================================
-- Procurement Steps (workflow steps per plan)
-- ============================================================

CREATE TABLE IF NOT EXISTS tendly.procurement_steps (
    id VARCHAR(36) PRIMARY KEY,
    procurement_plan_id VARCHAR(36) NOT NULL,
    step_number INTEGER NOT NULL,
    step_name VARCHAR(100) DEFAULT '',
    status VARCHAR(50) DEFAULT 'pending',
    assigned_role VARCHAR(50) DEFAULT '',
    assigned_to_email VARCHAR(255),
    notes TEXT DEFAULT '',
    completed_at TIMESTAMPTZ,
    completed_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_procurement_steps_plan
    ON tendly.procurement_steps(procurement_plan_id);
CREATE INDEX IF NOT EXISTS idx_procurement_steps_status
    ON tendly.procurement_steps(status);

-- ============================================================
-- Procurement Documents
-- ============================================================

CREATE TABLE IF NOT EXISTS tendly.procurement_documents (
    id VARCHAR(36) PRIMARY KEY,
    procurement_plan_id VARCHAR(36),
    organization_id VARCHAR(255),
    uploaded_by_email VARCHAR(255),
    title TEXT NOT NULL,
    document_type VARCHAR(50) DEFAULT 'other',
    file_name VARCHAR(500) DEFAULT '',
    file_path VARCHAR(1000) DEFAULT '',
    file_size INTEGER DEFAULT 0,
    mime_type VARCHAR(100) DEFAULT '',
    content_text TEXT DEFAULT '',
    ai_summary TEXT DEFAULT '',
    ai_analysis JSONB DEFAULT '{}',
    version INTEGER DEFAULT 1,
    parent_document_id VARCHAR(36),
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_procurement_documents_plan
    ON tendly.procurement_documents(procurement_plan_id);
CREATE INDEX IF NOT EXISTS idx_procurement_documents_org
    ON tendly.procurement_documents(organization_id);
CREATE INDEX IF NOT EXISTS idx_procurement_documents_type
    ON tendly.procurement_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_procurement_documents_uploaded_by
    ON tendly.procurement_documents(uploaded_by_email);

-- ============================================================
-- Approval Actions (audit trail)
-- ============================================================

CREATE TABLE IF NOT EXISTS tendly.approval_actions (
    id VARCHAR(36) PRIMARY KEY,
    procurement_plan_id VARCHAR(36) NOT NULL,
    step_number INTEGER,
    action VARCHAR(50) DEFAULT '',
    actor_email VARCHAR(255),
    actor_role VARCHAR(50),
    comment TEXT DEFAULT '',
    previous_status VARCHAR(50),
    new_status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_approval_actions_plan
    ON tendly.approval_actions(procurement_plan_id);
CREATE INDEX IF NOT EXISTS idx_approval_actions_actor
    ON tendly.approval_actions(actor_email);

-- ============================================================
-- Team Members
-- ============================================================

CREATE TABLE IF NOT EXISTS tendly.team_members (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    name VARCHAR(255) DEFAULT '',
    procurement_role VARCHAR(50) DEFAULT '',
    specialty VARCHAR(100) DEFAULT '',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_team_members_org
    ON tendly.team_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_team_members_email
    ON tendly.team_members(user_email);
CREATE INDEX IF NOT EXISTS idx_team_members_active
    ON tendly.team_members(organization_id, is_active);

-- ============================================================
-- Chat Contexts (persistent conversations)
-- ============================================================

CREATE TABLE IF NOT EXISTS tendly.chat_contexts (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(255) NOT NULL,
    user_email VARCHAR(255),
    organization_id VARCHAR(255),
    procurement_plan_id VARCHAR(36),
    title TEXT DEFAULT 'New conversation',
    messages JSONB DEFAULT '[]',
    artifacts JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_contexts_conversation
    ON tendly.chat_contexts(conversation_id);
CREATE INDEX IF NOT EXISTS idx_chat_contexts_user
    ON tendly.chat_contexts(user_email);
CREATE INDEX IF NOT EXISTS idx_chat_contexts_org
    ON tendly.chat_contexts(organization_id);
