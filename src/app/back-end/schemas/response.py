from typing import Optional

from pydantic import BaseModel, Field


class ResponseBase(BaseModel):
    response_text: str = Field(..., description="The text of the response.")
    response_type: str = Field(..., description="The type of the response.")
    language: str = Field(..., description="The language of the response.")


class ResponseCreateV2(ResponseBase):
    prompt_id: int = Field(
        ..., description="The ID of the prompt this response is for."
    )


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
