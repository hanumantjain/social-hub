#!/usr/bin/env python3
"""
Database Migration Script
Applies SQL migrations to update the database schema.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import database module
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import engine, SessionLocal
from logger import logger

def get_migration_files():
    """Get all migration SQL files in order"""
    migrations_dir = Path(__file__).parent
    migration_files = sorted(migrations_dir.glob("*.sql"))
    return migration_files

def check_migration_applied(db, migration_name):
    """Check if a migration has already been applied"""
    # Create migrations table if it doesn't exist
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            migration_name VARCHAR(255) UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()
    
    # Check if migration exists
    result = db.execute(text("""
        SELECT 1 FROM schema_migrations 
        WHERE migration_name = :migration_name
    """), {"migration_name": migration_name})
    
    return result.fetchone() is not None

def mark_migration_applied(db, migration_name):
    """Mark a migration as applied"""
    db.execute(text("""
        INSERT INTO schema_migrations (migration_name) 
        VALUES (:migration_name)
        ON CONFLICT (migration_name) DO NOTHING
    """), {"migration_name": migration_name})
    db.commit()

def apply_migration(migration_file):
    """Apply a single migration file"""
    migration_name = migration_file.name
    
    db = SessionLocal()
    try:
        # Check if migration already applied
        if check_migration_applied(db, migration_name):
            logger.info(f"Migration {migration_name} already applied, skipping...")
            return True
        
        logger.info(f"Applying migration: {migration_name}")
        
        # Read and execute migration SQL
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        
        # Execute migration (it should handle its own transactions)
        db.execute(text(sql_content))
        db.commit()
        
        # Mark migration as applied
        mark_migration_applied(db, migration_name)
        
        logger.info(f"✓ Successfully applied migration: {migration_name}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error applying migration {migration_name}: {str(e)}")
        raise
    finally:
        db.close()

def run_migrations():
    """Run all pending migrations"""
    logger.info("Starting database migrations...")
    
    migration_files = get_migration_files()
    
    if not migration_files:
        logger.info("No migration files found.")
        return True
    
    logger.info(f"Found {len(migration_files)} migration file(s)")
    
    for migration_file in migration_files:
        try:
            apply_migration(migration_file)
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            # Don't exit when called from startup - just log the error
            if __name__ == "__main__":
                sys.exit(1)
            return False
    
    logger.info("All migrations completed successfully!")
    return True

if __name__ == "__main__":
    run_migrations()

