#!/usr/bin/env python3
"""
Database Migration Script for Photobox API (Python Version)

Usage:
    python migrate.py up                    - Apply all pending migrations
    python migrate.py down                  - Rollback last migration
    python migrate.py down <migration_num>  - Rollback specific migration
    python migrate.py status                - Show migration status
"""

import os
import sys
import glob
import psycopg2
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_info(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def print_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def print_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print_info(f"Loaded environment from {env_path}")
    else:
        print_warning(f".env file not found at {env_path}")

def get_database_url() -> str:
    """Get database URL from environment"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print_error("DATABASE_URL environment variable is not set")
        print("Please set DATABASE_URL in your .env file or export it:")
        print("  export DATABASE_URL='postgresql://user:password@host:port/database'")
        sys.exit(1)
    return database_url

def get_db_connection(database_url: str):
    """Create database connection"""
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print_error(f"Failed to connect to database: {e}")
        sys.exit(1)

def get_migrations() -> List[str]:
    """Get list of migration files"""
    migration_dir = Path(__file__).parent
    pattern = str(migration_dir / "[0-9][0-9][0-9]_*.sql")
    files = glob.glob(pattern)
    # Filter out rollback files
    migrations = [f for f in files if not f.endswith('_rollback.sql')]
    migrations.sort()
    return [Path(f).name for f in migrations]

def apply_migration(database_url: str, migration_file: str) -> bool:
    """Apply a migration file"""
    print_info(f"Applying migration: {migration_file}")

    migration_path = Path(__file__).parent / migration_file

    try:
        with open(migration_path, 'r') as f:
            sql = f.read()

        conn = get_db_connection(database_url)
        cursor = conn.cursor()

        # Execute the migration
        cursor.execute(sql)
        conn.commit()

        cursor.close()
        conn.close()

        print_success(f"Migration applied successfully: {migration_file}")
        return True
    except Exception as e:
        print_error(f"Failed to apply migration: {migration_file}")
        print_error(f"Error: {e}")
        return False

def rollback_migration(database_url: str, migration_num: str) -> bool:
    """Rollback a migration"""
    migration_dir = Path(__file__).parent
    pattern = f"{migration_num}_*_rollback.sql"
    rollback_files = list(migration_dir.glob(pattern))

    if not rollback_files:
        print_error(f"Rollback file not found for migration: {migration_num}")
        return False

    rollback_file = rollback_files[0]
    print_warning(f"Rolling back migration: {rollback_file.name}")

    try:
        with open(rollback_file, 'r') as f:
            sql = f.read()

        conn = get_db_connection(database_url)
        cursor = conn.cursor()

        # Execute the rollback
        cursor.execute(sql)
        conn.commit()

        cursor.close()
        conn.close()

        print_success(f"Migration rolled back successfully: {rollback_file.name}")
        return True
    except Exception as e:
        print_error(f"Failed to rollback migration: {rollback_file.name}")
        print_error(f"Error: {e}")
        return False

def check_status(database_url: str):
    """Check migration status"""
    print_info("Checking database connection...")

    try:
        conn = get_db_connection(database_url)
        print_success("Database connection successful")

        cursor = conn.cursor()

        # Check if schema exists
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.schemata
                WHERE schema_name = 'photobox'
            )
        """)
        schema_exists = cursor.fetchone()[0]

        if schema_exists:
            print_success("Schema 'photobox' exists")

            # List tables
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'photobox'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()

            if tables:
                print_info("Existing tables in 'photobox' schema:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print_warning("No tables found in 'photobox' schema")
        else:
            print_warning("Schema 'photobox' does not exist")

        cursor.close()
        conn.close()

    except Exception as e:
        print_error(f"Failed to check status: {e}")
        sys.exit(1)

    # List migration files
    print_info("Available migration files:")
    migrations = get_migrations()

    if migrations:
        for migration in migrations:
            print(f"  - {migration}")
    else:
        print_warning("No migration files found")

def confirm_action(message: str) -> bool:
    """Ask user for confirmation"""
    response = input(f"{message} (y/N): ").lower().strip()
    return response in ['y', 'yes']

def migrate_up(database_url: str):
    """Apply all pending migrations"""
    print_info("Starting migration process...")

    migrations = get_migrations()

    if not migrations:
        print_warning("No migrations to apply")
        return

    # Show migrations to be applied
    print(f"\n{Colors.YELLOW}About to apply the following migrations:{Colors.NC}")
    for migration in migrations:
        print(f"  - {migration}")
    print()

    if not confirm_action("Do you want to continue?"):
        print_info("Migration cancelled")
        return

    # Apply migrations
    failed = False
    for migration in migrations:
        if not apply_migration(database_url, migration):
            failed = True
            break

    if not failed:
        print_success("All migrations applied successfully")
    else:
        print_error("Migration process failed")
        sys.exit(1)

def migrate_down(database_url: str, migration_num: Optional[str] = None):
    """Rollback migrations"""
    if migration_num is None:
        # Get last migration number
        migrations = get_migrations()
        if not migrations:
            print_warning("No migrations found")
            return

        last_migration = migrations[-1]
        migration_num = last_migration.split('_')[0]

    print_warning(f"About to rollback migration: {migration_num}")

    if not confirm_action("Do you want to continue?"):
        print_info("Rollback cancelled")
        return

    if not rollback_migration(database_url, migration_num):
        sys.exit(1)

def show_help():
    """Show help message"""
    print("Usage: python migrate.py {up|down|status} [migration_number]")
    print()
    print("Commands:")
    print("  up                    - Apply all pending migrations")
    print("  down                  - Rollback last migration")
    print("  down <migration_num>  - Rollback specific migration (e.g., 001)")
    print("  status                - Show migration status")
    print()
    print("Examples:")
    print("  python migrate.py up")
    print("  python migrate.py down")
    print("  python migrate.py down 001")
    print("  python migrate.py status")

def main():
    """Main entry point"""
    # Load environment variables
    load_env()

    # Parse command line arguments
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1]
    database_url = get_database_url()

    if command == 'up':
        migrate_up(database_url)
    elif command == 'down':
        migration_num = sys.argv[2] if len(sys.argv) > 2 else None
        migrate_down(database_url, migration_num)
    elif command == 'status':
        check_status(database_url)
    else:
        print_error(f"Unknown command: {command}")
        show_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
