from pydantic import BaseModel
from typing import Optional

class Domain(BaseModel):
    domain_id: Optional[int]
    domain_name: Optional[str]


class DomainCreate(BaseModel):
    domain_name: str

class DomainUpdate(BaseModel):
    domain_name: Optional[str] 