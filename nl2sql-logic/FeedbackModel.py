from pydantic import BaseModel

class FeedbackModel(BaseModel):
    user_question: str
    generated_sql: str
    feedback_type: str  # e.g., "correct", "incorrect", "partially_correct"
    corrected_sql: str = None  # Optional field for corrected SQL if feedback is "incorrect" or "partially_correct"
    comments: str = None  # Optional field for additional comments