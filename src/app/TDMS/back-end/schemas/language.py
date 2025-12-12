from typing import Optional

from pydantic import BaseModel, Field


class LanguageBase(BaseModel):
    lang_name: str = Field(..., description="The name of the language.")


class LanguageCreateV2(LanguageBase):
    pass


class LanguageUpdateV2(BaseModel):
    lang_name: Optional[str] = Field(None, description="The new name of the language.")


class LanguageListResponse(BaseModel):
    lang_id: int
    lang_name: str


class LanguageDetailResponse(BaseModel):
    lang_id: int
    lang_name: str

    class Config:
        from_attributes = True

#-----------------------------------------
class ResponseModel(BaseModel):
    text: str
    type: str


class Language_v2(BaseModel):
    lang_name: str
    response: ResponseModel