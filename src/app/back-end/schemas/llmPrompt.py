from pydantic import BaseModel
from typing import Optional


class LlmPromptIds(BaseModel):
    prompt_id: Optional[int]
    prompt: Optional[str]