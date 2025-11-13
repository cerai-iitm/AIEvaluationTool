from pydantic import BaseModel
from typing import Optional

class Domain(BaseModel):
    domain_id: int 
    domain_name: str 