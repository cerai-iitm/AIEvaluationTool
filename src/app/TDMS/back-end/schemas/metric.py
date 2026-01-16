from typing import Optional

from pydantic import BaseModel, Field


class MetricBase(BaseModel):
    metric_name: str = Field(..., description="The name of the metric.")
    metric_description: Optional[str] = Field(
        None, description="The description of the metric."
    )
    metric_source: Optional[str] = Field(
        None, description="The source of the metric."
    )
    domain_name: str = Field(..., description="The name of the domain.")
    metric_benchmark: Optional[str] = Field(
        None, description="The benchmark for the metric."
    )


class MetricCreateV2(MetricBase):
    notes: Optional[str] = Field(None, description="User notes for this operation.")


class MetricUpdateV2(BaseModel):
    metric_name: Optional[str] = Field(
        None, description="The new name of the metric."
    )
    metric_description: Optional[str] = Field(
        None, description="The new description of the metric."
    )
    metric_source: Optional[str] = Field(
        None, description="The new source of the metric."
    )
    domain_name: Optional[str] = Field(
        None, description="The new domain name for the metric."
    )
    metric_benchmark: Optional[str] = Field(
        None, description="The new benchmark for the metric."
    )
    user_note: Optional[str] = Field(None, description="User notes for this operation.")


class MetricListResponse(BaseModel):
    metric_id: int
    metric_name: str
    metric_description: Optional[str]
    metric_source: Optional[str]
    domain_name: str
    metric_benchmark: Optional[str]


class MetricDetailResponse(BaseModel):
    metric_id: int
    metric_name: str
    metric_description: Optional[str]
    metric_source: Optional[str]
    domain_name: str
    metric_benchmark: Optional[str]

    class Config:
        from_attributes = True
