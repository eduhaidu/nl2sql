from pydantic import BaseModel
from typing import Optional

class DBURLInputModel(BaseModel):
    database_url: str
    database_type: Optional[str] = None # e.g., 'sqlite', 'postgresql', 'mysql', etc. This can help the PromptManager tailor the SQL syntax.