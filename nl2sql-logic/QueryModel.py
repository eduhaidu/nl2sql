from pydantic import BaseModel
from typing import Optional

class QueryModel(BaseModel):
    query: str