from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database.fastapi_deps import _get_db
from lib.orm.DB import DB
from lib.orm.tables import Metrics
from schemas.metric import MetricResponse



metric_router = APIRouter(prefix="/api/v2/metrics")


@metric_router.get(
    "", 
    response_model=List[MetricResponse],
    summary="List all metrics"
)
def list_metrics(db: DB = Depends(_get_db)):
    with db.Session() as session:
        metrics = session.query(Metrics).all()
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Metrics not found"
            )
        
        
        return [
            MetricResponse(
                metric_id = metric.metric_id,
                metric_name = getattr(metric, 'metric_name'),
                metric_description = getattr(metric, 'metric_description'),
                metric_source = getattr(metric, 'metric_source'),
                domain_name = metric.domain.domain_name,
                metric_benchmark = getattr(metric, 'metric_benchmark')
            )
            for metric in metrics
        ]