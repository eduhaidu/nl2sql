import re

def extract_sql_query(response: str) -> str:
    # Use regex to find the SQL query in the response
    pattern = r"```sql (.*?)```"
    match = re.search(pattern, response, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    else:
        return response.strip()