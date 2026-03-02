-- Migration script to add db_url and database_type to existing conversations table
-- Run this if you already have the conversations table without these columns

-- Add the new columns
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS name TEXT,
ADD COLUMN IF NOT EXISTS db_url TEXT,
ADD COLUMN IF NOT EXISTS database_type VARCHAR(50);

-- If you have existing conversations without db_url, you may need to either:
-- 1. Delete them: DELETE FROM conversations;
-- 2. Or set a placeholder: UPDATE conversations SET db_url = 'sqlite:///placeholder.db' WHERE db_url IS NULL;

-- Make db_url NOT NULL after fixing existing data
-- ALTER TABLE conversations ALTER COLUMN db_url SET NOT NULL;

SELECT 'Migration completed! Check existing conversations and set db_url if needed.' as status;
