import re

def extract_sql_query(response: str) -> str:
    # First, try to extract from ```sql code blocks
    code_block_pattern = r"```sql\s*(.*?)\s*```"
    match = re.search(code_block_pattern, response, re.DOTALL)
    if match:
        sql_query = match.group(1).strip()
        # If there are multiple queries in the block, take only the first one
        if ';' in sql_query:
            # Find the first complete query
            first_query_end = sql_query.find(';')
            return sql_query[:first_query_end + 1].strip()
        return sql_query
    
    # Fallback: Look for SELECT...;
    startPos = response.find("SELECT")
    if startPos != -1:
        # Find the FIRST semicolon after SELECT, not the last one
        endPos = response.find(";", startPos)
        if endPos != -1:
            return response[startPos:endPos + 1].strip()
    
    return response.strip()