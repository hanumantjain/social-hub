-- Migration: Add Google OAuth support and schema updates
-- Created: 2025-11-16
-- Description: 
--   1. Add google_id column to users table for Google OAuth
--   2. Make password column nullable for OAuth users
--   3. Add title and tags columns to posts table

BEGIN;

-- ============================================
-- USERS TABLE CHANGES
-- ============================================

-- Add google_id column to users table (nullable, unique, indexed)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS google_id VARCHAR UNIQUE;

-- Create index on google_id if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- Make password column nullable (if it's not already)
-- Note: This will only change if the column is currently NOT NULL
-- PostgreSQL doesn't have a direct way to check, so we'll use DO block
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'password' 
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE users ALTER COLUMN password DROP NOT NULL;
    END IF;
END $$;

-- ============================================
-- POSTS TABLE CHANGES
-- ============================================

-- Add title column to posts table if it doesn't exist
ALTER TABLE posts 
ADD COLUMN IF NOT EXISTS title VARCHAR;

-- Add tags column to posts table if it doesn't exist
ALTER TABLE posts 
ADD COLUMN IF NOT EXISTS tags VARCHAR;

COMMIT;

