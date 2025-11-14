from pydantic import BaseModel
from typing import Optional


class LlmPromptIds(BaseModel):
    llmPromptId: Optional[int]
    prompt: Optional[str]


class LlmPrompts(BaseModel):
    llmPromptId: Optional[int]
    prompt: Optional[str]
    language: Optional[str]


class LlmPromptCreate(BaseModel):
    prompt: str
    language: str


class LlmPromptUpdate(BaseModel):
    llmPromptId: Optional[int]
    prompt: Optional[str]
    language: Optional[str]


class LlmPromptDelete(BaseModel):
    llmPromptId: int
    message: str