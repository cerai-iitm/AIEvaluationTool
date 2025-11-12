from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    user_name: str
    email: EmailStr
    role: str
    password: str
    confirm_password: str
    is_active: Optional[bool] = True
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

class UserHistory(BaseModel):
    table: str
    table_name: str
    note: str
    Operation: str


class UserOut(BaseModel):
    user_name: str
    email: EmailStr
    role: str


class UserActivityCreate(BaseModel):
    entity_type: str
    entity_id: str
    note: str
    operation: str  # create | update | delete


class UserActivityResponse(BaseModel):
    user_name: str
    description: str
    type: str
    testCaseId: str
    status: str
    timestamp: str