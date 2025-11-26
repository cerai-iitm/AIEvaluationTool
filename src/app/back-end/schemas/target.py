from typing import List, Optional

from pydantic import BaseModel, Field


class TargetBase(BaseModel):
    target_name: str = Field(..., description="The name of the target.")
    target_type: str = Field(
        ..., description="The type of the target (e.g., WebApp, API)."
    )
    target_description: Optional[str] = Field(
        None, description="A description of the target."
    )
    target_url: Optional[str] = Field(None, description="The URL of the target.")
    domain_name: str = Field(..., description="The name of the associated domain.")
    lang_list: List[str] = Field(
        [], description="A list of languages supported by the target."
    )


class TargetCreateV2(TargetBase):
    pass


class TargetUpdateV2(BaseModel):
    target_name: Optional[str] = Field(None, description="The new name of the target.")
    target_type: Optional[str] = Field(None, description="The new type of the target.")
    target_description: Optional[str] = Field(
        None, description="The new description of the target."
    )
    target_url: Optional[str] = Field(None, description="The new URL of the target.")
    domain_name: Optional[str] = Field(
        None, description="The new domain name for the target."
    )
    lang_list: Optional[List[str]] = Field(
        None, description="The new list of supported languages."
    )


class TargetListResponse(BaseModel):
    target_id: int
    target_name: str
    target_type: Optional[str]
    domain_name: Optional[str]


class TargetDetailResponse(BaseModel):
    target_id: int
    target_name: str
    target_type: Optional[str]
    target_description: Optional[str]
    target_url: Optional[str]
    domain_name: Optional[str]
    lang_list: List[str] = []

    class Config:
        from_attributes = True
