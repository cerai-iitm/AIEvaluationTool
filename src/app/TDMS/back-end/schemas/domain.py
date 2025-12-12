from typing import Optional

from pydantic import BaseModel, Field


class DomainBase(BaseModel):
    domain_name: str = Field(..., description="The name of the domain.")


class DomainCreateV2(DomainBase):
    pass


class DomainUpdateV2(BaseModel):
    domain_name: Optional[str] = Field(None, description="The new name of the domain.")


class DomainListResponse(BaseModel):
    domain_id: int
    domain_name: str


class DomainDetailResponse(BaseModel):
    domain_id: int
    domain_name: str

    class Config:
        from_attributes = True
