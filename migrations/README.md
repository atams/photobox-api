# Database Migrations

This directory contains SQL migration scripts for the Photobox API database.

## Migration Files

### 001_initial_schema.sql

Initial database schema creation including:

-   Schema: `photobox`
-   Tables:
    -   `master_locations`: Photobox machine locations
    -   `master_price`: Price configurations
    -   `transactions`: Payment transactions with QRIS integration
-   Indexes for performance optimization
-   Initial seed data (default price and sample locations)

### 001_initial_schema_rollback.sql

Rollback script to completely remove the initial schema.

## How to Run Migrations

### Method 1: Using Migration Scripts (Recommended)

We provide two migration scripts for convenience:

#### Python Script (migrate.py)

**Requirements:**

```bash
pip install psycopg2-binary python-dotenv
```

**Commands:**

```bash
# Check migration status
python migrations/migrate.py status

# Apply all pending migrations
python migrations/migrate.py up

# Rollback last migration
python migrations/migrate.py down

# Rollback specific migration
python migrations/migrate.py down 001
```

#### Bash Script (migrate.sh)

**Requirements:**

-   PostgreSQL client (`psql`)
-   Bash shell

**Commands:**

```bash
# Make script executable (first time only)
chmod +x migrations/migrate.sh

# Check migration status
./migrations/migrate.sh status

# Apply all pending migrations
./migrations/migrate.sh up

# Rollback last migration
./migrations/migrate.sh down

# Rollback specific migration
./migrations/migrate.sh down 001
```

### Method 2: Using psql (PostgreSQL CLI)

**Apply Migration:**

```bash
psql -h <host> -U <username> -d <database> -f migrations/001_initial_schema.sql
```

**Rollback Migration:**

```bash
psql -h <host> -U <username> -d <database> -f migrations/001_initial_schema_rollback.sql
```

### Method 3: Using environment variable for DATABASE_URL

**Apply Migration:**

```bash
psql $DATABASE_URL -f migrations/001_initial_schema.sql
```

**Rollback Migration:**

```bash
psql $DATABASE_URL -f migrations/001_initial_schema_rollback.sql
```

### Method 4: Using Docker (if database is containerized)

**Apply Migration:**

```bash
docker exec -i <container_name> psql -U <username> -d <database> < migrations/001_initial_schema.sql
```

## Migration Naming Convention

Migrations follow the format: `{number}_{description}.sql`

-   `number`: Sequential number (001, 002, 003, etc.)
-   `description`: Brief description of the migration (snake_case)

Rollback files use the suffix `_rollback.sql`

## Best Practices

1. **Always backup your database** before running migrations in production
2. **Test migrations** in a development/staging environment first
3. **Run rollback scripts** in reverse order if you need to undo multiple migrations
4. **Keep migrations idempotent** when possible (use `IF NOT EXISTS`, `IF EXISTS`, etc.)
5. **Document each migration** with clear comments about what it does
6. **Never modify existing migrations** that have been applied to production
7. **Create new migrations** for schema changes instead of editing old ones

## Migration Checklist

Before applying a migration to production:

-   [ ] Migration has been tested in development
-   [ ] Migration has been tested in staging
-   [ ] Database backup has been created
-   [ ] Downtime window has been scheduled (if needed)
-   [ ] Rollback script has been tested
-   [ ] Application code is compatible with new schema
-   [ ] Team members have been notified

## Schema Information

**Database**: PostgreSQL 12+
**Schema**: `photobox`
**Character Set**: UTF-8
**Timezone**: UTC (timestamptz columns)

## Initial Data

The initial migration includes sample data:

-   **Default Price**: Rp 40,000 for 4 photos
-   **Sample Locations**: 3 mall locations (can be removed/modified)

You can remove the initial data section from `001_initial_schema.sql` if you prefer to start with an empty database.

## Troubleshooting

### Error: "schema photobox already exists"

The schema already exists. If you want to recreate it, run the rollback script first.

### Error: "relation already exists"

One or more tables already exist. Run the rollback script to clean up, or check if a previous migration partially completed.

### Error: "foreign key constraint violation"

When rolling back, make sure to drop tables in the correct order (child tables before parent tables). The rollback script handles this automatically.

## Future Migrations

When creating new migrations:

1. Create a new file with the next sequential number
2. Include both forward migration and rollback script
3. Update this README with the new migration details
4. Test thoroughly before applying to production

Example:

```
002_add_photo_uploads_table.sql
002_add_photo_uploads_table_rollback.sql
```
