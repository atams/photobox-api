#!/bin/bash

# ============================================================================
# Database Migration Script for Photobox API
# ============================================================================
# Usage:
#   ./migrate.sh up                    - Apply all pending migrations
#   ./migrate.sh down                  - Rollback last migration
#   ./migrate.sh down <migration_num>  - Rollback specific migration
#   ./migrate.sh status                - Show migration status
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load environment variables from .env file
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}Error: DATABASE_URL environment variable is not set${NC}"
    echo "Please set DATABASE_URL in your .env file or export it:"
    echo "  export DATABASE_URL='postgresql://user:password@host:port/database'"
    exit 1
fi

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get list of migration files
get_migrations() {
    ls -1 [0-9][0-9][0-9]_*.sql 2>/dev/null | grep -v "_rollback.sql" || echo ""
}

# Function to apply a migration
apply_migration() {
    local migration_file=$1
    print_info "Applying migration: $migration_file"

    if psql "$DATABASE_URL" -f "$migration_file" > /dev/null 2>&1; then
        print_success "Migration applied successfully: $migration_file"
        return 0
    else
        print_error "Failed to apply migration: $migration_file"
        return 1
    fi
}

# Function to rollback a migration
rollback_migration() {
    local migration_num=$1
    local rollback_file="${migration_num}_*_rollback.sql"

    # Find the rollback file
    local rollback_path=$(ls $rollback_file 2>/dev/null | head -1)

    if [ -z "$rollback_path" ]; then
        print_error "Rollback file not found for migration: $migration_num"
        return 1
    fi

    print_warning "Rolling back migration: $rollback_path"

    if psql "$DATABASE_URL" -f "$rollback_path" > /dev/null 2>&1; then
        print_success "Migration rolled back successfully: $rollback_path"
        return 0
    else
        print_error "Failed to rollback migration: $rollback_path"
        return 1
    fi
}

# Function to check migration status
check_status() {
    print_info "Checking database connection..."

    if psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
        print_success "Database connection successful"
    else
        print_error "Failed to connect to database"
        exit 1
    fi

    print_info "Available migration files:"
    migrations=$(get_migrations)

    if [ -z "$migrations" ]; then
        print_warning "No migration files found"
    else
        echo "$migrations" | while read -r migration; do
            echo "  - $migration"
        done
    fi

    print_info "Checking if schema exists..."
    schema_exists=$(psql "$DATABASE_URL" -t -c "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'photobox');" | tr -d ' ')

    if [ "$schema_exists" = "t" ]; then
        print_success "Schema 'photobox' exists"

        # Check tables
        print_info "Existing tables in 'photobox' schema:"
        psql "$DATABASE_URL" -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'photobox' ORDER BY table_name;" -t | while read -r table; do
            table_trimmed=$(echo "$table" | tr -d ' ')
            if [ -n "$table_trimmed" ]; then
                echo "  - $table_trimmed"
            fi
        done
    else
        print_warning "Schema 'photobox' does not exist"
    fi
}

# Main script logic
case "$1" in
    up)
        print_info "Starting migration process..."
        migrations=$(get_migrations)

        if [ -z "$migrations" ]; then
            print_warning "No migrations to apply"
            exit 0
        fi

        # Ask for confirmation
        echo ""
        echo -e "${YELLOW}About to apply the following migrations:${NC}"
        echo "$migrations" | while read -r migration; do
            echo "  - $migration"
        done
        echo ""
        read -p "Do you want to continue? (y/N): " -n 1 -r
        echo

        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Migration cancelled"
            exit 0
        fi

        # Apply migrations
        failed=0
        echo "$migrations" | while read -r migration; do
            if ! apply_migration "$migration"; then
                failed=1
                break
            fi
        done

        if [ $failed -eq 0 ]; then
            print_success "All migrations applied successfully"
        else
            print_error "Migration process failed"
            exit 1
        fi
        ;;

    down)
        migration_num=$2

        if [ -z "$migration_num" ]; then
            # Get the last migration number
            last_migration=$(get_migrations | tail -1)
            if [ -z "$last_migration" ]; then
                print_warning "No migrations found"
                exit 0
            fi
            migration_num=$(echo "$last_migration" | cut -d'_' -f1)
        fi

        print_warning "About to rollback migration: $migration_num"
        read -p "Do you want to continue? (y/N): " -n 1 -r
        echo

        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Rollback cancelled"
            exit 0
        fi

        rollback_migration "$migration_num"
        ;;

    status)
        check_status
        ;;

    *)
        echo "Usage: $0 {up|down|status} [migration_number]"
        echo ""
        echo "Commands:"
        echo "  up                    - Apply all pending migrations"
        echo "  down                  - Rollback last migration"
        echo "  down <migration_num>  - Rollback specific migration (e.g., 001)"
        echo "  status                - Show migration status"
        echo ""
        echo "Examples:"
        echo "  $0 up"
        echo "  $0 down"
        echo "  $0 down 001"
        echo "  $0 status"
        exit 1
        ;;
esac

exit 0
