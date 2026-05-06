-- Tendly schema tables
-- Run against the buyer DB (TENDLY_DB_URL).

CREATE SCHEMA IF NOT EXISTS tendly;

-- Users with buyer/seller role
CREATE TABLE IF NOT EXISTS tendly.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    company VARCHAR(255),
    role VARCHAR(20) DEFAULT 'seller' CHECK (role IN ('buyer', 'seller', 'both')),
    country VARCHAR(50),
    language VARCHAR(5) DEFAULT 'en',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tenders (UK imported data + future sources)
CREATE TABLE IF NOT EXISTS tendly.tenders (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255),
    source VARCHAR(50) DEFAULT 'contracts_finder',
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    procurement_method VARCHAR(100),
    procurement_method_details VARCHAR(500),
    main_category VARCHAR(50),
    cpv_code VARCHAR(20),
    cpv_description VARCHAR(255),
    estimated_value NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'GBP',
    buyer_name VARCHAR(500),
    buyer_id VARCHAR(255),
    submission_deadline TIMESTAMPTZ,
    contract_start TIMESTAMPTZ,
    contract_end TIMESTAMPTZ,
    country_code VARCHAR(2) DEFAULT 'GB',
    region VARCHAR(255),
    notice_url TEXT,
    is_sme_suitable BOOLEAN DEFAULT false,
    raw_data JSONB,
    published_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Awards (won contracts)
CREATE TABLE IF NOT EXISTS tendly.awards (
    id SERIAL PRIMARY KEY,
    tender_id INTEGER REFERENCES tendly.tenders(id) ON DELETE CASCADE,
    supplier_name VARCHAR(500),
    supplier_id VARCHAR(255),
    award_value NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'GBP',
    award_date TIMESTAMPTZ,
    status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RFP Drafts (buyer-created procurement documents)
CREATE TABLE IF NOT EXISTS tendly.rfp_drafts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES tendly.users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    description TEXT,
    category VARCHAR(50),
    cpv_code VARCHAR(20),
    cpv_description VARCHAR(255),
    estimated_value NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    procedure_type VARCHAR(100),
    evaluation_criteria JSONB,
    qualification_requirements JSONB,
    technical_specifications TEXT,
    draft_content TEXT,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'published')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Price benchmarks (cached)
CREATE TABLE IF NOT EXISTS tendly.price_benchmarks (
    id SERIAL PRIMARY KEY,
    cpv_code VARCHAR(20),
    category VARCHAR(50),
    country_code VARCHAR(2),
    avg_value NUMERIC(15,2),
    median_value NUMERIC(15,2),
    min_value NUMERIC(15,2),
    max_value NUMERIC(15,2),
    sample_count INTEGER,
    period_start DATE,
    period_end DATE,
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations (persistent, replaces in-memory)
CREATE TABLE IF NOT EXISTS tendly.conversations (
    id UUID PRIMARY KEY,
    user_id INTEGER REFERENCES tendly.users(id) ON DELETE SET NULL,
    title VARCHAR(500) DEFAULT 'New conversation',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messages
CREATE TABLE IF NOT EXISTS tendly.messages (
    id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES tendly.conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    tenders JSONB,
    artifacts JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
