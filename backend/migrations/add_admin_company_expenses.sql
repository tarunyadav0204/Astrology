-- Internal admin expense log (not user-facing). Optional invoice file on disk; path stored here.
-- Applied on backend startup via admin_expense_schema.ensure_admin_company_expenses_schema().

CREATE TABLE IF NOT EXISTS admin_company_expenses (
    id BIGSERIAL PRIMARY KEY,
    spent_date DATE NOT NULL,
    amount NUMERIC(14, 2) NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'INR',
    vendor TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    notes TEXT,
    invoice_original_name TEXT,
    invoice_storage_path TEXT,
    invoice_mime TEXT,
    invoice_size_bytes BIGINT NOT NULL DEFAULT 0,
    created_by_userid INTEGER REFERENCES users (userid) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_company_expenses_spent_date
    ON admin_company_expenses (spent_date DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_admin_company_expenses_category
    ON admin_company_expenses (LOWER(category));

-- Dropdown masters (managed under Admin → Expenses → "Vendors & paid by")
CREATE TABLE IF NOT EXISTS admin_expense_vendors (
    id SERIAL PRIMARY KEY,
    label TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_expense_vendors_label_lower
    ON admin_expense_vendors (LOWER(TRIM(label)));

CREATE TABLE IF NOT EXISTS admin_expense_paid_by (
    id SERIAL PRIMARY KEY,
    label TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_expense_paid_by_label_lower
    ON admin_expense_paid_by (LOWER(TRIM(label)));

ALTER TABLE admin_company_expenses
    ADD COLUMN IF NOT EXISTS vendor_id INTEGER REFERENCES admin_expense_vendors (id) ON DELETE SET NULL;

ALTER TABLE admin_company_expenses
    ADD COLUMN IF NOT EXISTS paid_by_id INTEGER REFERENCES admin_expense_paid_by (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_admin_company_expenses_vendor_id
    ON admin_company_expenses (vendor_id);

CREATE INDEX IF NOT EXISTS idx_admin_company_expenses_paid_by_id
    ON admin_company_expenses (paid_by_id);

-- Provider-import metadata. Manual expenses keep the defaults below.
ALTER TABLE admin_company_expenses
    ADD COLUMN IF NOT EXISTS source_provider VARCHAR(32) NOT NULL DEFAULT 'manual';

ALTER TABLE admin_company_expenses
    ADD COLUMN IF NOT EXISTS source_account_id TEXT;

ALTER TABLE admin_company_expenses
    ADD COLUMN IF NOT EXISTS source_period VARCHAR(7);

ALTER TABLE admin_company_expenses
    ADD COLUMN IF NOT EXISTS source_external_id TEXT;

ALTER TABLE admin_company_expenses
    ADD COLUMN IF NOT EXISTS import_status VARCHAR(24);

ALTER TABLE admin_company_expenses
    ADD COLUMN IF NOT EXISTS source_last_synced_at TIMESTAMPTZ;

ALTER TABLE admin_company_expenses
    ADD COLUMN IF NOT EXISTS source_amount NUMERIC(18, 6);

ALTER TABLE admin_company_expenses
    ADD COLUMN IF NOT EXISTS manual_adjustment NUMERIC(18, 6) NOT NULL DEFAULT 0;

CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_company_expenses_source_external_id
    ON admin_company_expenses (source_provider, source_external_id)
    WHERE source_external_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_admin_company_expenses_source_period
    ON admin_company_expenses (source_provider, source_period);

-- Non-secret connection settings for one provider account. Authentication uses
-- the runtime's Google identity / GOOGLE_SERVICE_ACCOUNT_KEY, never this table.
CREATE TABLE IF NOT EXISTS admin_expense_integrations (
    id BIGSERIAL PRIMARY KEY,
    provider VARCHAR(32) NOT NULL,
    source_account_id TEXT NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    vendor_id INTEGER NOT NULL REFERENCES admin_expense_vendors (id),
    paid_by_id INTEGER NOT NULL REFERENCES admin_expense_paid_by (id),
    category TEXT NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_sync_started_at TIMESTAMPTZ,
    last_sync_completed_at TIMESTAMPTZ,
    last_sync_status VARCHAR(24),
    last_sync_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provider, source_account_id)
);

-- Daily normalized values make every monthly total explainable and allow safe
-- re-fetching when Google posts late credits, taxes, or adjustments.
CREATE TABLE IF NOT EXISTS admin_expense_import_daily (
    id BIGSERIAL PRIMARY KEY,
    provider VARCHAR(32) NOT NULL,
    source_account_id TEXT NOT NULL,
    invoice_month VARCHAR(6) NOT NULL,
    usage_date DATE NOT NULL,
    currency VARCHAR(8) NOT NULL,
    amount NUMERIC(18, 6) NOT NULL,
    source_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provider, source_account_id, invoice_month, usage_date, currency)
);

CREATE INDEX IF NOT EXISTS idx_admin_expense_import_daily_month
    ON admin_expense_import_daily (provider, source_account_id, invoice_month);

CREATE TABLE IF NOT EXISTS admin_expense_sync_runs (
    id BIGSERIAL PRIMARY KEY,
    provider VARCHAR(32) NOT NULL,
    source_account_id TEXT,
    status VARCHAR(24) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    rows_fetched INTEGER NOT NULL DEFAULT 0,
    expenses_created INTEGER NOT NULL DEFAULT 0,
    expenses_updated INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_admin_expense_sync_runs_provider_started
    ON admin_expense_sync_runs (provider, started_at DESC);
