from postgres_connection import get_connection
from FeedbackModel import FeedbackModel

class FeedbackStorage:
    def store_feedback(self, conversation_id, feedback: FeedbackModel):
        conn = get_connection()
        if not conn:
            print("Failed to connect to the database.")
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO query_feedback (conversation_id, user_question, generated_sql, feedback_type, corrected_sql, user_notes, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, NOW());
                """,
                (
                    conversation_id,
                    feedback.user_question,
                    feedback.generated_sql,
                    feedback.feedback_type,
                    feedback.corrected_sql,
                    feedback.comments
                )
            )
            conn.commit()
            print(f"Feedback stored for conversation ID {conversation_id}.")
            return True
        except Exception as e:
            print(f"Error storing feedback: {e}")
            return False
        finally:
            conn.close()

