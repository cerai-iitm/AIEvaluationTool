from typing import Optional

from pydantic import BaseModel, Field

class MetricResponse(BaseModel):
    metric_id: int
    metric_name: str
    metric_description: Optional[str]
    metric_source: Optional[str]
    domain_name: str
    metric_benchmark: Optional[str]