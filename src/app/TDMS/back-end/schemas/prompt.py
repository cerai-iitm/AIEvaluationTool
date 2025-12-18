from typing import Optional

from pydantic import BaseModel, Field


class PromptBase(BaseModel):
    user_prompt: str = Field(..., description="The user prompt.")
    system_prompt: Optional[str] = Field(None, description="The system prompt.")
    language: str = Field(..., description="The language of the prompt.")
    domain: str = Field(..., description="The domain of the prompt.")

# class Prompt(BaseModel):
#     user_prompt: str
#     system_prompt: Optional[str]

class PromptCreateV2(BaseModel):
    user_prompt: str
    system_prompt: Optional[str]
    language: str
    domain: str




class PromptUpdateV2(BaseModel):
    user_prompt: Optional[str] = Field(None, description="The new user prompt.")
    system_prompt: Optional[str] = Field(None, description="The new system prompt.")
    language: Optional[str] = Field(None, description="The new language of the prompt.")
    domain: Optional[str] = Field(None, description="The new domain of the prompt.")


class PromptListResponse(BaseModel):
    prompt_id: int
    user_prompt: str
    system_prompt: Optional[str]


class PromptDetailResponse(BaseModel):
    prompt_id: int
    user_prompt: str
    system_prompt: Optional[str]
    language: Optional[str]
    domain: Optional[str]


class UserPrompt(BaseModel):
    prompt_id: int
    user_prompt: str

class SystemPrompt(BaseModel):
    prompt_id: int
    system_prompt: str

