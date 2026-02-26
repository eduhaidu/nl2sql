# Database Setup Instructions

## PostgreSQL Schema Initialization

The application requires PostgreSQL tables to store conversations and messages. These tables **must be created manually** before running the application.

## Quick Setup

1. **Ensure PostgreSQL is running**:

   ```bash
   # Check if PostgreSQL is running
   psql --version
   ```

2. **Create the database** (if it doesn't exist):

   ```bash
   createdb nl2sqldb
   ```

3. **Run the schema initialization script**:

   ```bash
   psql -U eduhaidu -d nl2sqldb -f init_schema.sql
   ```

   Or connect to psql and run the script:

   ```bash
   psql -U eduhaidu -d nl2sqldb
   ```

   Then in the psql prompt:

   ```sql
   \i init_schema.sql
   ```

4. **Verify tables were created**:

   ```sql
   \dt
   ```

   You should see:
   - `conversations`
   - `conversation_history`
   - `query_results`

## Database Configuration

The connection settings are in `postgres_connection.py`:

- **Host**: localhost
- **Port**: 5432
- **Database**: nl2sqldb
- **User**: eduhaidu
- **Password**: (empty)

**Update these values** if your PostgreSQL setup is different.

## Schema Details

### `conversations` table

Stores each database import as a separate conversation:

- `id` - Primary key (auto-increment)
- `created_at` - Timestamp of conversation creation

### `conversation_history` table

Stores all messages (user questions and assistant responses):

- `id` - Primary key (auto-increment)
- `conversation_id` - Foreign key to conversations
- `message` - The message content
- `sender` - Either 'user' or 'assistant'
- `timestamp` - When the message was sent

### `query_results` table

Stores executed SQL queries and their results:

- `id` - Primary key (auto-increment)
- `conversation_id` - Foreign key to conversations
- `sql_query` - The SQL query that was executed
- `result` - The query result (as text/JSON)
- `created_at` - When the query was executed

## Troubleshooting

### "relation does not exist" error

This means the tables haven't been created yet. Run `init_schema.sql` as shown above.

### Connection refused

Make sure PostgreSQL is running:

```bash
brew services start postgresql@14  # macOS with Homebrew
```

### Authentication failed

Update the username/password in `postgres_connection.py` to match your PostgreSQL credentials.

### Permission denied

Ensure your PostgreSQL user has CREATE TABLE permissions:

```sql
GRANT ALL PRIVILEGES ON DATABASE nl2sqldb TO eduhaidu;
```

## Sample Queries for Testing

```sql
-- View all conversations
SELECT * FROM conversations ORDER BY created_at DESC;

-- View messages for a specific conversation
SELECT sender, message, timestamp
FROM conversation_history
WHERE conversation_id = 1
ORDER BY timestamp;

-- View query execution history
SELECT sql_query, created_at
FROM query_results
WHERE conversation_id = 1
ORDER BY created_at DESC;

-- Clean up old conversations (optional)
DELETE FROM conversations WHERE created_at < NOW() - INTERVAL '30 days';
```
