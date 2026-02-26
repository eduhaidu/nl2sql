from postgres_connection import get_connection

class ResultStorage:
    def __init__(self):
        pass

    def save_query_execution(self, conversation_id, sql_query, result):
        conn = get_connection()
        if not conn:
            print("Failed to connect to the database.")
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO query_results (conversation_id, sql_query, result, created_at)
                VALUES (%s, %s, %s, NOW());
            """, (conversation_id, sql_query, str(result)))
            conn.commit()
            print(f"Query execution saved for conversation ID: {conversation_id}")
            return conversation_id
        except Exception as e:
            print(f"Error saving query execution: {e}")
            return False
        finally:
            conn.close()