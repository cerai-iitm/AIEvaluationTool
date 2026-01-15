from typing import Optional

from pydantic import BaseModel, Field


class ResponseBase(BaseModel):
    response_text: str = Field(..., description="The text of the response.")
    response_type: str = Field(..., description="The type of the response.")
    language: str = Field(..., description="The language of the response.")


class ResponseCreateV2(ResponseBase):
    user_prompt: str = Field(..., description="The user prompt.")
    system_prompt: Optional[str] = Field(None, description="The system prompt.")
    language: Optional[str] = Field(None, description="The language of the response.")
    notes: Optional[str] = Field(None, description="User notes for this operation.")


class ResponseUpdateV2(BaseModel):
    response_text: Optional[str] = Field(
        None, description="The new text of the response."
    )
    response_type: Optional[str] = Field(
        None, description="The new type of the response."
    )
    language: Optional[str] = Field(
        None, description="The new language of the response."
    )
    user_prompt: Optional[str] = Field(
        None, description="The new user prompt."
    )
    system_prompt: Optional[str] = Field(
        None, description="The new system prompt."
    )
    notes: Optional[str] = Field(None, description="User notes for this operation.")


class ResponseListResponse(BaseModel):
    response_id: int
    response_text: str


class ResponseDetailResponse(BaseModel):
    response_id: int
    response_text: str
    response_type: str
    language: Optional[str]
    user_prompt: str
    system_prompt: Optional[str]
    

    class Config:
        from_attributes = True
