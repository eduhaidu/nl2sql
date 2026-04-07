from pydantic import BaseModel
from typing import Optional

class DBURLInputModel(BaseModel):
    database_url: str
    database_type: Optional[str] = "sqlite" # e.g., 'sqlite', 'postgresql', 'mysql', etc. This can help the PromptManager tailor the SQL syntax.
    user_id: Optional[str] = None  # Add user_id to associate the conversation with a specific user