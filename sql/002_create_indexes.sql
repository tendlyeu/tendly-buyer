-- Indexes for tendly schema

CREATE INDEX IF NOT EXISTS idx_tendly_tenders_cpv ON tendly.tenders(cpv_code);
CREATE INDEX IF NOT EXISTS idx_tendly_tenders_buyer ON tendly.tenders(buyer_name);
CREATE INDEX IF NOT EXISTS idx_tendly_tenders_country ON tendly.tenders(country_code);
CREATE INDEX IF NOT EXISTS idx_tendly_tenders_deadline ON tendly.tenders(submission_deadline);
CREATE INDEX IF NOT EXISTS idx_tendly_tenders_status ON tendly.tenders(status);
CREATE INDEX IF NOT EXISTS idx_tendly_tenders_category ON tendly.tenders(main_category);
CREATE INDEX IF NOT EXISTS idx_tendly_tenders_external ON tendly.tenders(external_id);
CREATE INDEX IF NOT EXISTS idx_tendly_tenders_source ON tendly.tenders(source);
CREATE INDEX IF NOT EXISTS idx_tendly_tenders_value ON tendly.tenders(estimated_value);
CREATE INDEX IF NOT EXISTS idx_tendly_tenders_published ON tendly.tenders(published_date);

CREATE INDEX IF NOT EXISTS idx_tendly_awards_tender ON tendly.awards(tender_id);
CREATE INDEX IF NOT EXISTS idx_tendly_awards_supplier ON tendly.awards(supplier_name);

CREATE INDEX IF NOT EXISTS idx_tendly_rfp_user ON tendly.rfp_drafts(user_id);
CREATE INDEX IF NOT EXISTS idx_tendly_rfp_status ON tendly.rfp_drafts(status);
CREATE INDEX IF NOT EXISTS idx_tendly_rfp_cpv ON tendly.rfp_drafts(cpv_code);

CREATE INDEX IF NOT EXISTS idx_tendly_benchmarks_cpv ON tendly.price_benchmarks(cpv_code);
CREATE INDEX IF NOT EXISTS idx_tendly_benchmarks_country ON tendly.price_benchmarks(country_code);

CREATE INDEX IF NOT EXISTS idx_tendly_conversations_user ON tendly.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_tendly_messages_conv ON tendly.messages(conversation_id);
