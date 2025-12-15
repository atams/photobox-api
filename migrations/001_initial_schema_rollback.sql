-- Migration Rollback: 001_initial_schema
-- Description: Rollback initial database schema for Photobox API
-- Author: Generated from DDL
-- Date: 2025-12-15

-- ============================================================================
-- ROLLBACK INSTRUCTIONS
-- ============================================================================
-- This script will completely remove all tables, indexes, and the schema
-- WARNING: This will delete ALL data in the photobox schema
-- Use with caution in production environments
-- ============================================================================

-- Drop indexes first
DROP INDEX IF EXISTS photobox.idx_transactions_email_sent_at;
DROP INDEX IF EXISTS photobox.idx_transactions_status_date;
DROP INDEX IF EXISTS photobox.idx_transactions_price_id;
DROP INDEX IF EXISTS photobox.idx_transactions_location;
DROP INDEX IF EXISTS photobox.idx_transactions_external_id;

-- Drop tables (respecting foreign key dependencies)
DROP TABLE IF EXISTS photobox.transactions CASCADE;
DROP TABLE IF EXISTS photobox.master_price CASCADE;
DROP TABLE IF EXISTS photobox.master_locations CASCADE;

-- Drop schema
DROP SCHEMA IF EXISTS photobox CASCADE;

-- ============================================================================
-- END OF ROLLBACK
-- ============================================================================
