from pydantic import BaseModel
from typing import Optional

class PromptIds(BaseModel):
    prompt_id: Optional[int]
    user_prompt: Optional[str]
    system_prompt: Optional[str]