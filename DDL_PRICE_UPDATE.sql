-- =====================================================
-- DDL for Price Feature Update
-- Photobox API - Transaction with Dynamic Pricing
-- =====================================================

-- 1. CREATE master_price table
CREATE TABLE photobox.master_price (
    mp_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mp_price NUMERIC(15, 2) NOT NULL,
    mp_description VARCHAR(255),
    mp_quota INTEGER,
    mp_is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Index for active price lookup
CREATE INDEX idx_master_price_active ON photobox.master_price(mp_is_active);
CREATE INDEX idx_master_price_created_at ON photobox.master_price(created_at);

-- 2. ALTER transactions table - remove old amount column and add price_id
-- Drop old amount column
ALTER TABLE photobox.transactions
DROP COLUMN tr_amount;

-- Add price_id column (UUID reference to master_price)
ALTER TABLE photobox.transactions
ADD COLUMN tr_price_id UUID REFERENCES photobox.master_price(mp_id);

-- Create index for transaction price lookup
CREATE INDEX idx_transactions_price_id ON photobox.transactions(tr_price_id);

-- 3. Insert default price data (migration data)
INSERT INTO photobox.master_price (mp_price, mp_description, mp_quota, mp_is_active)
VALUES (
    40000.00,
    'Default Photobox Price',
    NULL,  -- unlimited quota
    true
);