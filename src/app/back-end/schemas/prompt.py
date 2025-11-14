from pydantic import BaseModel
from typing import Optional

class PromptIds(BaseModel):
    prompt_id: Optional[int]
    user_prompt: Optional[str]
    system_prompt: Optional[str]

class Prompts(BaseModel):
    prompt_id: Optional[int]
    user_prompt: Optional[str]
    system_prompt: Optional[str]
    language: Optional[str]
    domain: Optional[str]

class PromptUpdate(BaseModel):
    prompt_id: Optional[int]
    user_prompt: Optional[str]
    system_prompt: Optional[str]
    language: Optional[str]
    domain: Optional[str]

class PromptCreate(BaseModel):
    user_prompt: str
    system_prompt: str
    language: str
    domain: str

class PromptDelete(BaseModel):
    prompt_id: int
    message: str