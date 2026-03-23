from postgres_connection import get_connection
import json
import ast

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
            # Store result as JSON for better retrieval
            result_json = json.dumps(result)
            cursor.execute("""
                INSERT INTO query_results (conversation_id, sql_query, result, created_at)
                VALUES (%s, %s, %s, NOW());
            """, (conversation_id, sql_query, result_json))
            conn.commit()
            print(f"Query execution saved for conversation ID: {conversation_id}")
            return conversation_id
        except Exception as e:
            print(f"Error saving query execution: {e}")
            return False
        finally:
            conn.close()

    def get_query_results_for_conversation(self, conversation_id):
        """
        Retrieve all cached query results for a conversation.
        Returns a dictionary mapping SQL queries to their results.
        """
        conn = get_connection()
        if not conn:
            print("Failed to connect to the database.")
            return {}
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sql_query, result, created_at
                FROM query_results
                WHERE conversation_id = %s
                ORDER BY created_at;
            """, (conversation_id,))
            results = cursor.fetchall()

            # Create a mapping of SQL query -> result
            # Use the last result for each unique query (in case of retries)
            query_results = {}
            for sql_query, result_str, created_at in results:
                try:
                    # Try to parse as JSON first
                    result = json.loads(result_str)
                except (json.JSONDecodeError, TypeError):
                    try:
                        # Fallback to ast.literal_eval for older string-based storage
                        result = ast.literal_eval(result_str)
                    except (ValueError, SyntaxError):
                        # If all parsing fails, use the string as-is
                        result = result_str

                # Normalize SQL query (remove extra whitespace) for matching
                normalized_query = ' '.join(sql_query.split())
                query_results[normalized_query] = result
                print(f"Loaded cached result for query: {sql_query[:60]}...")

            return query_results
        except Exception as e:
            print(f"Error retrieving query results: {e}")
            return {}
        finally:
            conn.close()