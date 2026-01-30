from typing import List, Optional

from pydantic import BaseModel, Field


class TestPlanBase(BaseModel):
    plan_name: str = Field(..., description="The name of the test plan.")
    plan_description: Optional[str] = Field(
        None, description="A description of the test plan."
    )
    metric_names: List[str] = Field(
        default_factory=list, description="List of metric names associated with the test plan."
    )


class TestPlanCreateV2(TestPlanBase):
    notes: Optional[str] = Field(None, description="User notes for this operation.")


class TestPlanUpdateV2(BaseModel):
    plan_name: Optional[str] = Field(None, description="The new name of the test plan.")
    plan_description: Optional[str] = Field(
        None, description="The new description of the test plan."
    )
    metric_names: Optional[List[str]] = Field(
        None, description="The new list of metric names."
    )
    notes: Optional[str] = Field(None, description="User notes for this operation.")


class TestPlanListResponse(BaseModel):
    plan_id: int
    plan_name: str


class TestPlanDetailResponse(BaseModel):
    plan_id: int
    plan_name: str
    plan_description: Optional[str]
    metric_names: List[str] = []

    class Config:
        from_attributes = True

