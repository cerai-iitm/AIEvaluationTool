from pydantic import BaseModel
from typing import Optional


class LlmPromptIds(BaseModel):
    llmPromptId: Optional[int]
    prompt: Optional[str]


class LlmPrompts(BaseModel):
    llmPromptId: Optional[int]
    prompt: Optional[str]
    language: Optional[str]