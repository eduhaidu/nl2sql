from pydantic import BaseModel
from typing import Optional

class CredentialsModel(BaseModel):
    username: str
    email: Optional[str] = None
    password: str