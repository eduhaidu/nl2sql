from pydantic import BaseModel
from typing import Optional

class DBURLInputModel(BaseModel):
    database_url: str