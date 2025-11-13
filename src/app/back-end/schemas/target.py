from pydantic import BaseModel
from typing import Optional

class TargetIds(BaseModel):
    target_id: Optional[int] = None
    target_name: Optional[str]
    target_type: Optional[str]
    target_description: Optional[str]
    target_url: Optional[str]
    domain_name: Optional[str]
    lang_list: Optional[list[str]]


class TargetUpdate(BaseModel):
    target_id: Optional[int] = None
    target_name: Optional[str]
    target_type: Optional[str]
    target_description: Optional[str]
    target_url: Optional[str]
    domain_name: Optional[str]
    lang_list: Optional[list[str]]


class TargetCreate(BaseModel):
    target_name: str
    target_type: str
    target_description: Optional[str]
    target_url: str
    domain_name: str
    lang_list: list[str]