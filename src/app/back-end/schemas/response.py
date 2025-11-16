from pydantic import BaseModel
from typing import Optional

class Response(BaseModel):
    response_id: Optional[int] = None
    response_text: Optional[str] = None
    response_type: Optional[str] = None
    prompt_id: Optional[int] = None
    lang_id: Optional[int] = None
    digest: Optional[str] = None

class ResponseUpdate(BaseModel):
    response_text: Optional[str] = None
    response_type: Optional[str] = None
    user_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    lang_name: Optional[str] = None

class ResponseCreate(BaseModel):
    response_text: str
    response_type: str
    lang_name: str
    user_prompt: str
    system_prompt: Optional[str] = None


class ResponseIds(BaseModel):
    response_id: Optional[int] = None
    response_text: Optional[str] = None


class Responses(BaseModel):
    response_id: Optional[int] = None
    response_text: Optional[str] = None
    response_type: Optional[str] = None
    user_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    lang_name: Optional[str] = None
