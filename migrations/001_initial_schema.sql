-- Migration: 001_initial_schema
-- Description: Create initial database schema for Photobox API
-- Author: Generated from DDL
-- Date: 2025-12-15

-- ============================================================================
-- SCHEMA CREATION
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS photobox;

-- ============================================================================
-- TABLE: master_locations
-- Description: Photobox machine locations master data
-- ============================================================================

CREATE TABLE photobox.master_locations (
    ml_id bigserial NOT NULL,
    ml_machine_code varchar(50) NOT NULL,
    ml_name varchar(100) NOT NULL,
    ml_address text NULL,
    ml_is_active bool DEFAULT true NULL,
    created_at timestamptz DEFAULT now() NULL,

    -- Constraints
    CONSTRAINT master_locations_pkey PRIMARY KEY (ml_id),
    CONSTRAINT master_locations_ml_machine_code_key UNIQUE (ml_machine_code)
);

-- ============================================================================
-- TABLE: master_price
-- Description: Price configurations for photobox services
-- ============================================================================

CREATE TABLE photobox.master_price (
    mp_id uuid DEFAULT gen_random_uuid() NOT NULL,
    mp_price numeric(15, 2) NOT NULL,
    mp_description varchar(255) NULL,
    mp_quota int4 NULL,
    mp_is_active bool DEFAULT true NOT NULL,
    created_at timestamptz DEFAULT now() NULL,
    updated_at timestamptz NULL,

    -- Constraints
    CONSTRAINT master_price_pkey PRIMARY KEY (mp_id)
);

-- ============================================================================
-- TABLE: transactions
-- Description: Payment transactions with QRIS integration
-- ============================================================================

CREATE TABLE photobox.transactions (
    tr_id bigserial NOT NULL,
    tr_location_id int8 NULL,
    tr_external_id varchar(255) NOT NULL,
    tr_xendit_id varchar(255) NULL,
    tr_status varchar(50) DEFAULT 'PENDING'::character varying NOT NULL,
    tr_qr_string text NULL,
    tr_paid_at timestamptz NULL,
    created_at timestamptz DEFAULT now() NULL,
    tr_price_id uuid NULL,
    tr_email varchar(255) NULL,
    tr_send_invoice bool DEFAULT false NOT NULL,
    tr_email_sent_at timestamptz NULL,

    -- Constraints
    CONSTRAINT transactions_pkey PRIMARY KEY (tr_id),
    CONSTRAINT transactions_tr_external_id_key UNIQUE (tr_external_id),

    -- Foreign Keys
    CONSTRAINT transactions_tr_location_id_fkey
        FOREIGN KEY (tr_location_id)
        REFERENCES photobox.master_locations(ml_id)
        ON DELETE SET NULL,

    CONSTRAINT transactions_tr_price_id_fkey
        FOREIGN KEY (tr_price_id)
        REFERENCES photobox.master_price(mp_id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Transactions indexes for performance optimization
CREATE INDEX idx_transactions_external_id ON photobox.transactions (tr_external_id);
CREATE INDEX idx_transactions_location ON photobox.transactions (tr_location_id);
CREATE INDEX idx_transactions_price_id ON photobox.transactions (tr_price_id);
CREATE INDEX idx_transactions_status_date ON photobox.transactions (tr_status, created_at);
CREATE INDEX idx_transactions_email_sent_at ON photobox.transactions (tr_email_sent_at);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON SCHEMA photobox IS 'Photobox API database schema';

COMMENT ON TABLE photobox.master_locations IS 'Master data for photobox machine locations';
COMMENT ON COLUMN photobox.master_locations.ml_id IS 'Primary key - Location ID';
COMMENT ON COLUMN photobox.master_locations.ml_machine_code IS 'Unique machine identifier code';
COMMENT ON COLUMN photobox.master_locations.ml_name IS 'Location name';
COMMENT ON COLUMN photobox.master_locations.ml_address IS 'Physical address of the location';
COMMENT ON COLUMN photobox.master_locations.ml_is_active IS 'Active status flag';
COMMENT ON COLUMN photobox.master_locations.created_at IS 'Record creation timestamp';

COMMENT ON TABLE photobox.master_price IS 'Price configurations for photobox services';
COMMENT ON COLUMN photobox.master_price.mp_id IS 'Primary key - Price ID (UUID)';
COMMENT ON COLUMN photobox.master_price.mp_price IS 'Price amount in IDR';
COMMENT ON COLUMN photobox.master_price.mp_description IS 'Price description';
COMMENT ON COLUMN photobox.master_price.mp_quota IS 'Number of photos allowed for this price';
COMMENT ON COLUMN photobox.master_price.mp_is_active IS 'Active status flag';
COMMENT ON COLUMN photobox.master_price.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN photobox.master_price.updated_at IS 'Record last update timestamp';

COMMENT ON TABLE photobox.transactions IS 'Payment transactions with QRIS integration';
COMMENT ON COLUMN photobox.transactions.tr_id IS 'Primary key - Transaction ID';
COMMENT ON COLUMN photobox.transactions.tr_location_id IS 'Foreign key to master_locations';
COMMENT ON COLUMN photobox.transactions.tr_external_id IS 'Unique external transaction identifier (format: TRX-{location}-{timestamp}-{random})';
COMMENT ON COLUMN photobox.transactions.tr_xendit_id IS 'Xendit payment identifier';
COMMENT ON COLUMN photobox.transactions.tr_status IS 'Transaction status: PENDING, COMPLETED, FAILED, EXPIRED';
COMMENT ON COLUMN photobox.transactions.tr_qr_string IS 'QRIS string for QR code generation';
COMMENT ON COLUMN photobox.transactions.tr_paid_at IS 'Payment completion timestamp';
COMMENT ON COLUMN photobox.transactions.created_at IS 'Transaction creation timestamp';
COMMENT ON COLUMN photobox.transactions.tr_price_id IS 'Foreign key to master_price';
COMMENT ON COLUMN photobox.transactions.tr_email IS 'Customer email for invoice';
COMMENT ON COLUMN photobox.transactions.tr_send_invoice IS 'Flag to send invoice via email';
COMMENT ON COLUMN photobox.transactions.tr_email_sent_at IS 'Email sent timestamp';

-- ============================================================================
-- INITIAL DATA (Optional)
-- ============================================================================

-- Insert default price (Rp 40,000 for 4 photos)
INSERT INTO photobox.master_price (mp_price, mp_description, mp_quota, mp_is_active)
VALUES
    (40000.00, 'Standard Package - 4 Photos', 4, true);

-- Insert sample locations (can be removed or modified as needed)
INSERT INTO photobox.master_locations (ml_machine_code, ml_name, ml_address, ml_is_active)
VALUES
    ('PB001', 'Mall Taman Anggrek', 'Jl. Letjen S. Parman Kav. 21, Jakarta Barat', true),
    ('PB002', 'Mall Kelapa Gading', 'Jl. Boulevard Barat Raya, Jakarta Utara', true),
    ('PB003', 'Grand Indonesia', 'Jl. M.H. Thamrin No. 1, Jakarta Pusat', true);

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
