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
