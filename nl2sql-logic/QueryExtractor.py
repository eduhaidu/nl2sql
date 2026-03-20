import re

def extract_sql_query(response: str) -> str:
    """
    Extract the best SQL query from a model response.
    If multiple queries are present, prefer the most specific one (with WHERE, JOIN, etc.).
    """

    # First, try to extract from ```sql code blocks
    code_block_pattern = r"```sql\s*(.*?)\s*```"
    matches = re.findall(code_block_pattern, response, re.DOTALL | re.IGNORECASE)
    if matches:
        # If multiple code blocks, analyze all queries and pick the best one
        if len(matches) > 1:
            return _select_best_query([m.strip() for m in matches])
        else:
            sql_query = matches[0].strip()
            # Check for multiple queries within a single block
            queries = _split_queries(sql_query)
            if len(queries) > 1:
                return _select_best_query(queries)
            return sql_query

    # Fallback: Extract all SELECT statements
    select_pattern = r'\b(SELECT\s+.*?;)'
    matches = re.findall(select_pattern, response, re.DOTALL | re.IGNORECASE)

    if matches:
        queries = [m.strip() for m in matches]
        if len(queries) > 1:
            return _select_best_query(queries)
        return queries[0]

    # Last resort: find SELECT without semicolon
    startPos = response.upper().find("SELECT")
    if startPos != -1:
        # Try to find end of query
        endPos = response.find(";", startPos)
        if endPos != -1:
            return response[startPos:endPos + 1].strip()
        else:
            # No semicolon found, return rest of text (might need cleaning)
            return response[startPos:].strip()

    return response.strip()


def _split_queries(sql_text: str) -> list:
    """Split multiple SQL queries separated by semicolons."""
    queries = []
    for query in sql_text.split(';'):
        query = query.strip()
        if query and query.upper().startswith('SELECT'):
            queries.append(query + ';')
    return queries


def _select_best_query(queries: list) -> str:
    """
    Select the most specific query from a list of queries.
    Heuristics:
    - Prefer queries with WHERE clauses (more specific)
    - Prefer queries with JOIN (more complex)
    - Prefer longer queries (usually more specific)
    - Avoid queries that select everything (e.g., SELECT * FROM Table with no WHERE)
    """
    if not queries:
        return ""

    if len(queries) == 1:
        return queries[0]

    scored_queries = []
    for query in queries:
        query_upper = query.upper()
        score = 0

        # Prefer queries with WHERE clause (most important)
        if 'WHERE' in query_upper:
            score += 100

        # Prefer queries with JOIN
        if 'JOIN' in query_upper:
            score += 50

        # Prefer queries with GROUP BY or ORDER BY
        if 'GROUP BY' in query_upper:
            score += 30
        if 'ORDER BY' in query_upper:
            score += 20

        # Prefer queries with aggregate functions
        if any(func in query_upper for func in ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(']):
            score += 40

        # Penalize very short queries (likely generic)
        if len(query) < 50:
            score -= 20

        # Prefer longer queries (more specific)
        score += len(query) / 10

        scored_queries.append((score, query))

    # Sort by score (highest first) and return the best query
    scored_queries.sort(key=lambda x: x[0], reverse=True)

    best_query = scored_queries[0][1]
    print(f"Selected best query from {len(queries)} options: {best_query[:80]}...")
    return best_query