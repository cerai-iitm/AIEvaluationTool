from typing import List, Optional

from config.settings import settings
from database.fastapi_deps import _get_db
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError, jwt
from schemas.metric import (
    MetricCreateV2,
    MetricDetailResponse,
    MetricListResponse,
    MetricUpdateV2,
)
from sqlalchemy.exc import IntegrityError
from utils.activity_logger import log_activity

from lib.orm.DB import DB
from lib.orm.tables import Metrics, Domains, TestRunDetails
from sqlalchemy.orm import joinedload

metric_router = APIRouter(prefix="/api/v2/metrics")


def _get_username_from_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload.get("user_name")
    except JWTError:
        return None


@metric_router.get(
    "", 
    response_model=List[MetricListResponse],
    summary="List all metrics (v2)",
)
def list_metrics(db: DB = Depends(_get_db)):
    with db.Session() as session:
        metrics = (
            session.query(Metrics)
            .options(joinedload(Metrics.domain))
            .all()
        )
        
        if not metrics:
            return []
        
        return [
            MetricListResponse(
                metric_id=metric.metric_id,
                metric_name=metric.metric_name,
                metric_description=metric.metric_description,
                metric_source=metric.metric_source,
                domain_name=metric.domain.domain_name if metric.domain else "",
                metric_benchmark=metric.metric_benchmark,
            )
            for metric in metrics
        ]


@metric_router.get(
    "/{metric_id}",
    response_model=MetricDetailResponse,
    summary="Get a metric by ID (v2)",
)
def get_metric(metric_id: int, db: DB = Depends(_get_db)):
    with db.Session() as session:
        metric = (
            session.query(Metrics)
            .options(joinedload(Metrics.domain))
            .filter(Metrics.metric_id == metric_id)
            .first()
        )
        
        if metric is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
            )
        
        return MetricDetailResponse(
            metric_id=metric.metric_id,
            metric_name=metric.metric_name,
            metric_description=metric.metric_description,
            metric_source=metric.metric_source,
            domain_name=metric.domain.domain_name if metric.domain else "",
            metric_benchmark=metric.metric_benchmark,
        )


@metric_router.post(
    "/create",
    response_model=MetricDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new metric (v2)",
)
def create_metric(
    payload: MetricCreateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    with db.Session() as session:
        try:
            # Get next available ID
            existing_ids = [row[0] for row in session.query(Metrics.metric_id).order_by(Metrics.metric_id).all()]
            next_id = 1
            for id in existing_ids:
                if id != next_id:
                    break
                next_id += 1
            
            # Get or create domain
            domain = session.query(Domains).filter(Domains.domain_name == payload.domain_name).first()
            if domain is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Domain '{payload.domain_name}' not found",
                )
            
            # Create metric
            new_metric = Metrics(
                metric_name=payload.metric_name,
                metric_description=payload.metric_description,
                metric_source=payload.metric_source,
                domain_id=domain.domain_id,
                metric_benchmark=payload.metric_benchmark,
            )
            session.add(new_metric)
            session.commit()
            session.refresh(new_metric)
            
            # Log activity
            username = _get_username_from_token(authorization)
            if username:
                log_activity(
                    username=username,
                    entity_type="Metric",
                    entity_id=str(new_metric.metric_id),
                    operation="create",
                    note=f"Metric - {new_metric.metric_name} created",
                    user_note=payload.notes,
                )
            
            return MetricDetailResponse(
                metric_id=new_metric.metric_id,
                metric_name=new_metric.metric_name,
                metric_description=new_metric.metric_description,
                metric_source=new_metric.metric_source,
                domain_name=payload.domain_name,
                metric_benchmark=new_metric.metric_benchmark,
            )
            
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A metric with the same name already exists.",
            )
        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}",
            )


@metric_router.put(
    "/update/{metric_id}",
    response_model=MetricDetailResponse,
    summary="Update a metric (v2)",
)
def update_metric(
    metric_id: int,
    payload: MetricUpdateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    with db.Session() as session:
        try:
            metric = (
                session.query(Metrics)
                .options(joinedload(Metrics.domain))
                .filter(Metrics.metric_id == metric_id)
                .first()
            )
            
            if metric is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
                )

            original_name = metric.metric_name
            original_description = metric.metric_description
            original_source = metric.metric_source
            original_domain_name = metric.domain.domain_name if metric.domain else None
            original_benchmark = metric.metric_benchmark

            # Update metric name if provided
            if payload.metric_name is not None and payload.metric_name != original_name:
                # Check for duplicate name
                existing = session.query(Metrics).filter(
                    Metrics.metric_name == payload.metric_name,
                    Metrics.metric_id != metric_id
                ).first()
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="A metric with this name already exists.",
                    )
                metric.metric_name = payload.metric_name

            # Update description if provided
            if payload.metric_description is not None:
                metric.metric_description = payload.metric_description

            # Update source if provided
            if payload.metric_source is not None:
                metric.metric_source = payload.metric_source

            # Update domain if provided
            if payload.domain_name is not None:
                domain = session.query(Domains).filter(Domains.domain_name == payload.domain_name).first()
                if domain is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Domain '{payload.domain_name}' not found",
                    )
                metric.domain_id = domain.domain_id

            # Update benchmark if provided
            if payload.metric_benchmark is not None:
                metric.metric_benchmark = payload.metric_benchmark

            session.commit()
            session.refresh(metric)

            username = _get_username_from_token(authorization)
            if not username:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

            # Track changes
            changes = []
            if payload.metric_name and original_name != payload.metric_name:
                changes.append(f"Name changed from '{original_name}' to '{payload.metric_name}'")
            if payload.metric_description and original_description != payload.metric_description:
                changes.append("Description changed")
            if payload.metric_source and original_source != payload.metric_source:
                changes.append("Source changed")
            if payload.domain_name and original_domain_name != payload.domain_name:
                changes.append(f"Domain changed from '{original_domain_name}' to '{payload.domain_name}'")
            if payload.metric_benchmark and original_benchmark != payload.metric_benchmark:
                changes.append("Benchmark changed")

            note = f"Metric - {metric.metric_name} updated"
            if changes:
                note += f" : {', '.join(changes)}"
            else:
                note += " (no changes detected)"

            log_activity(
                username=username,
                entity_type="Metric",
                entity_id=str(metric.metric_id),
                operation="update",
                note=note,
                user_note=payload.user_note,
            )

            # Get updated domain name
            session.refresh(metric)
            updated_domain_name = metric.domain.domain_name if metric.domain else ""
            
            return MetricDetailResponse(
                metric_id=metric.metric_id,
                metric_name=metric.metric_name,
                metric_description=metric.metric_description,
                metric_source=metric.metric_source,
                domain_name=updated_domain_name,
                metric_benchmark=metric.metric_benchmark,
            )

        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}",
            )


@metric_router.delete(
    "/delete/{metric_id}",
    summary="Delete a metric (v2)",
)
def delete_metric(
    metric_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    with db.Session() as session:
        metric = session.query(Metrics).filter(Metrics.metric_id == metric_id).first()
        if metric is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
            )

        # Check if metric is used in any test run detail
        test_run_with_metric = session.query(TestRunDetails).filter(TestRunDetails.metric_id == metric_id).first()
        if test_run_with_metric:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Metric is used in one or more test runs. Cannot delete.",
            )

        metric_name = metric.metric_name
        session.delete(metric)
        session.commit()

        username = _get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="Metric",
                entity_id=str(metric_id),
                operation="delete",
                note=f"Metric - {metric_name} deleted",
                user_note=None,
            )

        return {"message": "Metric deleted successfully"}
