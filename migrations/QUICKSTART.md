# Database Migrations - Quick Start Guide

Quick reference for running database migrations in Photobox API.

## Prerequisites

1. **PostgreSQL database** is running and accessible
2. **DATABASE_URL** is set in `.env` file:
    ```env
    DATABASE_URL=postgresql://user:password@host:port/database
    ```

## Quick Commands

### Python (Recommended)

```bash
# Install dependencies (first time only)
pip install -r migrations/requirements.txt

# Check current status
python migrations/migrate.py status

# Apply all migrations
python migrations/migrate.py up

# Rollback last migration
python migrations/migrate.py down
```

### Bash (Alternative)

```bash
# Check current status
./migrations/migrate.sh status

# Apply all migrations
./migrations/migrate.sh up

# Rollback last migration
./migrations/migrate.sh down
```

## First Time Setup

```bash
# 1. Install Python dependencies
pip install -r migrations/requirements.txt

# 2. Verify database connection
python migrations/migrate.py status

# 3. Apply initial schema
python migrations/migrate.py up
```

Expected output:

```
[INFO] Starting migration process...

About to apply the following migrations:
  - 001_initial_schema.sql

Do you want to continue? (y/N): y

[INFO] Applying migration: 001_initial_schema.sql
[SUCCESS] Migration applied successfully: 001_initial_schema.sql
[SUCCESS] All migrations applied successfully
```

## Verify Migration

After running migrations, verify the setup:

```bash
# Check status
python migrations/migrate.py status
```

Expected output:

```
[INFO] Checking database connection...
[SUCCESS] Database connection successful
[SUCCESS] Schema 'photobox' exists
[INFO] Existing tables in 'photobox' schema:
  - master_locations
  - master_price
  - transactions
```

## Common Issues

### Issue: "DATABASE_URL environment variable is not set"

**Solution:** Create `.env` file with DATABASE_URL

### Issue: "Failed to connect to database"

**Solution:**

-   Check database is running
-   Verify DATABASE_URL credentials
-   Check firewall/network access

### Issue: "schema photobox already exists"

**Solution:** Database already has the schema. Use `status` to check current state.

## What Gets Created

The initial migration creates:

1. **Schema:** `photobox`

2. **Tables:**

    - `master_locations` - Photobox machine locations
    - `master_price` - Price configurations
    - `transactions` - Payment transactions

3. **Sample Data:**
    - 1 default price (Rp 40,000 for 4 photos)
    - 3 sample locations (Mall Taman Anggrek, Mall Kelapa Gading, Grand Indonesia)

## Rollback

If you need to start over:

```bash
# This will DROP ALL TABLES and the schema
python migrations/migrate.py down

# Then reapply
python migrations/migrate.py up
```

**WARNING:** Rollback deletes ALL data. Use with caution!

## Next Steps

After migrations complete:

1. Start the API server: `uvicorn app.main:app --reload`
2. Check API health: http://localhost:8000/health
3. View API docs: http://localhost:8000/docs

## Need Help?

-   Full documentation: [README.md](README.md)
-   Project setup: [../README.md](../README.md)
-   API documentation: [../docs/endpoint.md](../docs/endpoint.md)
