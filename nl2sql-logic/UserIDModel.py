from pydantic import BaseModel

class UserIDModel(BaseModel):
    user_id: int