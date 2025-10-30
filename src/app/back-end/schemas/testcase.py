from pydantic import BaseModel
from typing import Optional

class TestCase(BaseModel):
    id: Optional[int] = None
    testcase_name: Optional[str] = None
    strategy_name: Optional[str] = None
    domain_name: Optional[str] = None
    user_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    response_text: Optional[str] = None
    prompt: Optional[str] = None