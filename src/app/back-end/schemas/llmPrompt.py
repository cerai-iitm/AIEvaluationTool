from pydantic import BaseModel
from typing import Optional


class LlmPromptIds(BaseModel):
    llmPromptId: Optional[int]
    prompt: Optional[str]