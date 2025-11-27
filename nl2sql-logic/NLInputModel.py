from pydantic import BaseModel

class NLInputModel(BaseModel):
    nl_input: str
    session_id: str = None