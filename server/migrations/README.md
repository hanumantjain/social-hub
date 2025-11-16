# Database Migrations

This directory contains database migration scripts for schema changes.

## Migration Files

- `001_add_google_oauth_and_title.sql` - Adds Google OAuth support (google_id column) and title column to posts

## Running Migrations

### Option 1: Using Python Script (Recommended)
```bash
# From the server directory
python migrations/migrate.py

# Or using Docker
docker compose exec server python migrations/migrate.py
```

### Option 2: Manual SQL Execution
```bash
# Execute migration directly
docker compose exec db psql -U postgres -d socialdb -f /path/to/migration.sql

# Or copy file into container first
docker cp server/migrations/001_add_google_oauth_and_title.sql db_social:/tmp/
docker compose exec db psql -U postgres -d socialdb -f /tmp/001_add_google_oauth_and_title.sql
```

### Option 3: Using psql directly
```bash
docker compose exec db psql -U postgres -d socialdb
# Then paste the SQL commands from the migration file
```

## Migration History

The migration script tracks applied migrations in the `schema_migrations` table to prevent duplicate execution.

## Creating New Migrations

1. Create a new SQL file: `00N_description.sql` (increment N)
2. Write your ALTER TABLE / CREATE TABLE statements
3. Wrap everything in BEGIN/COMMIT for transaction safety
4. Run the migration using one of the methods above

