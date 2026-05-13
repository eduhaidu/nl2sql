from pydantic import BaseModel
from typing import Optional

class FeedbackModel(BaseModel):
    user_question: str
    generated_sql: str
    feedback_type: str  # e.g., "correct", "incorrect", "partially_correct"
    corrected_sql: Optional[str]   # Optional field for corrected SQL if feedback is "incorrect" or "partially_correct"
    comments: Optional[str]   # Optional field for additional comments