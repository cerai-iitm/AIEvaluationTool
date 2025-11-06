from pydantic import BaseModel
from typing import Optional

class Response(BaseModel):
    response_id: Optional[int]
    response_text: Optional[str]
    response_type: Optional[str]
    prompt_id: Optional[int]
    lang_id: Optional[int]
    digest: Optional[str]


class ResponseIds(BaseModel):
    response_id: Optional[int]
    response_text: Optional[str]