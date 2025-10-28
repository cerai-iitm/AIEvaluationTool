from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    user_name: str
    password: str
    role: str
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]

    # class Config:
    #     orm_mode = True

class User(BaseModel):
    username: str
    role: str



class Login(BaseModel):
    # user_id: Optional[int]
    user_name: str
    password: str
    # is_active: Optional[bool]
    # role: Optional[str]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "user_name": "admin",
                "password": "admin123",
                # "role": "admin",
                # "is_active": True
            }
        }

