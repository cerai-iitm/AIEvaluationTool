from typing import Optional

from pydantic import BaseModel, Field


class LlmPromptBase(BaseModel):
    prompt: str = Field(..., description="The LLM prompt.")
    language: str = Field(..., description="The language of the prompt.")


class LlmPromptCreateV2(LlmPromptBase):
    pass


class LlmPromptUpdateV2(BaseModel):
    prompt: Optional[str] = Field(None, description="The new LLM prompt.")
    language: Optional[str] = Field(None, description="The new language of the prompt.")


class LlmPromptListResponse(BaseModel):
    llmjudgeprompt_id: int
    llmjudgeprompt_name: str


class LlmPromptDetailResponse(BaseModel):
    llmPromptId: int
    prompt: str
    language: Optional[str]

    class Config:
        from_attributes = True
