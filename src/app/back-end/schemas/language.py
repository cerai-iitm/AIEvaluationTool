from pydantic import BaseModel
from typing import Optional


class Language(BaseModel):
    lang_id: Optional[int]
    lang_name: Optional[str]


class LanguageCreate(BaseModel):
    lang_name: str

class LanguageUpdate(BaseModel):
    lang_name: Optional[str]