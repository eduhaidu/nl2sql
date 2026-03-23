# ChatQL Logic

ChatQL Logic is the backend service for a conversational Natural Language to SQL system.
It accepts natural language questions, generates SQL with an LLM, executes safe read queries,
and stores conversation history, feedback, and cached results.

## What this service does

- Connects to user-provided SQL databases
- Extracts schema metadata and enriches it with table and column descriptions
- Selects relevant schema and examples for each user question
- Generates SQL using an Ollama-hosted model
- Executes SELECT queries and returns tabular results
- Persists conversation history and query outputs in PostgreSQL
- Learns from user feedback by saving successful examples

## Supported target databases

- SQLite
- PostgreSQL
- MySQL
- SQL Server

## High-level architecture

1. FastAPI app in main.py exposes HTTP endpoints.
2. SessionManager builds an in-memory session per imported database.
3. SchemaProcessor reflects schema through SQLAlchemy.
4. DescriptionHeuristics adds table and column descriptions.
5. PromptManager builds request context:
   - latest user question
   - filtered schema
   - selected static and production examples
6. Ollama model returns SQL candidate text.
7. QueryExtractor extracts a runnable SQL statement.
8. SQLAlchemySession executes the query.
9. ResultStorage and conversation controllers persist history and results.

## Request flow

### 1) Import a database

Client calls POST /dbimport with:

- database_url
- database_type

Backend creates:

- a persistent conversation record
- an in-memory generation/execution session
- schema context for prompting

### 2) Ask a question

Client calls POST /nlinput with:

- session_id
- nl_input

Backend returns:

- response: raw model response
- query: extracted SQL

### 3) Execute SQL

Client calls POST /executesql/{session_id} with query payload.
Only SELECT is allowed.

### 4) Feedback loop

Client calls POST /feedback/{conversation_id}.
Successful/corrected queries are stored and can be reused as production examples.

## Project structure (important files)

- main.py: API routes and orchestration
- session_manager.py: session lifecycle and per-session objects
- prompt_manager.py: schema filtering, example selection, LLM prompting
- schema_processor.py: schema reflection and normalization
- description_heuristics.py: automatic schema descriptions
- QueryExtractor.py: SQL extraction from model output
- SQLAlchemySession.py: query execution
- conversation_controller.py: conversation CRUD and history persistence
- feedback_storage.py: feedback persistence
- example_manager.py: static and production example pools

## Prerequisites

- Python 3.13+
- PostgreSQL running (for conversation and feedback persistence)
- Ollama running locally with your SQL model available

## Setup

From this folder (nl2sql-logic):

```bash
uv sync
```

If needed, install dependencies explicitly:

```bash
uv add fastapi[standard] uvicorn sqlalchemy psycopg2-binary ollama sentence-transformers langchain pandas
```

## Run the API

```bash
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/
```

## Core endpoints

- GET /: basic service status
- POST /dbimport: create conversation and session from database URL
- POST /nlinput: generate SQL from natural language
- POST /executesql/{session_id}: execute generated SQL
- POST /validate/{session_id}: validation workflow
- POST /retry/{session_id}: retry generation with error context
- GET /conversations: list conversations
- GET /conversations/{conversation_id}: load conversation history and cached results
- PUT /conversations/{conversation_id}: rename conversation
- DELETE /conversations/{conversation_id}: delete conversation and cleanup session
- POST /feedback/{conversation_id}: save feedback and update production examples

## Example API calls

### Import database

```bash
curl -X POST http://127.0.0.1:8000/dbimport \
    -H "Content-Type: application/json" \
    -d '{
        "database_url": "sqlite:///test_databases/sample.db",
        "database_type": "sqlite"
    }'
```

### Generate SQL

```bash
curl -X POST http://127.0.0.1:8000/nlinput \
    -H "Content-Type: application/json" \
    -d '{
        "session_id": "YOUR_SESSION_ID",
        "nl_input": "Show top 5 customers by total order value"
    }'
```

### Execute SQL

```bash
curl -X POST http://127.0.0.1:8000/executesql/YOUR_SESSION_ID \
    -H "Content-Type: application/json" \
    -d '{
        "query": "SELECT customer_id, SUM(total) AS total_spend FROM orders GROUP BY customer_id ORDER BY total_spend DESC LIMIT 5;"
    }'
```

## Context strategy and quality controls

The generation quality depends on context discipline.
Current best practice in this project:

- Keep persistent history compact (question + SQL intent)
- Inject fresh schema context per turn
- Filter to relevant tables/columns
- Use mixed static and production examples
- Validate and retry when execution fails

## Troubleshooting

### Model outputs unrelated SQL

- Reduce conversational noise in prompt history
- Ensure latest question is clearly framed
- Raise schema relevance threshold if too many tables are included
- Verify examples are high-quality and on-topic

### Empty or incorrect results

- Confirm generated SQL is a SELECT query
- Verify database URL and schema reflection
- Check whether column names require quoting

### Feedback does not improve outputs

- Confirm feedback endpoint is called from frontend
- Verify production examples are being written to the example pool
- Remove low-quality or contradictory production examples

## Security notes

- This backend currently restricts execution to SELECT statements.
- Always validate and sanitize external database URLs before production deployment.
- Add authentication and rate limiting before exposing publicly.

## Frontend companion

The UI is in the sibling folder:

- ../nl2sql-interface/nl2sql-interface

Run both services for full local usage:

1. Backend on 127.0.0.1:8000
2. Frontend on localhost:3000
