from pydantic import BaseModel
from typing import Optional

class NLInputModel(BaseModel):
    nl_input: str
    session_id: Optional[str]