import re

def extract_sql_query(response: str) -> str:
    # Use regex to find the SQL query in the response
    startPos = response.find("SELECT")
    endPos = response.rfind(";")
    if startPos != -1 and endPos != -1 and endPos > startPos:
        return response[startPos:endPos + 1].strip()
    code_block_pattern = r"```sql(.*?)```"
    match = re.search(code_block_pattern, response, re.DOTALL)
    if match:
        sql_query = match.group(1).strip()
        return sql_query
    return response.strip()