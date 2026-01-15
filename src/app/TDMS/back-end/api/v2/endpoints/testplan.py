from typing import List, Optional

from config.settings import settings
from database.fastapi_deps import _get_db
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError, jwt
from schemas.testplan import (
    TestPlanCreateV2,
    TestPlanDetailResponse,
    TestPlanListResponse,
    TestPlanUpdateV2,
)
from sqlalchemy.exc import IntegrityError
from utils.activity_logger import log_activity

from lib.orm.DB import DB
from lib.orm.tables import TestPlans, Metrics
from sqlalchemy.orm import joinedload

testplan_router = APIRouter(prefix="/api/v2/testplans")


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


@testplan_router.get(
    "",
    response_model=List[TestPlanDetailResponse],
    summary="List all test plans (v2)",
)
def list_testplans(db: DB = Depends(_get_db)):
    with db.Session() as session:
        plans = (
            session.query(TestPlans)
            .options(joinedload(TestPlans.metrics))
            .all()
        )
        
        result = []
        for plan in plans:
            metric_names = [metric.metric_name for metric in plan.metrics] if plan.metrics else []
            result.append(
                TestPlanDetailResponse(
                    plan_id=plan.plan_id,
                    plan_name=plan.plan_name,
                    plan_description=plan.plan_description,
                    metric_names=metric_names,
                )
            )
        return result


@testplan_router.get(
    "/{plan_id}",
    response_model=TestPlanDetailResponse,
    summary="Get a test plan by ID (v2)",
)
def get_testplan(plan_id: int, db: DB = Depends(_get_db)):
    with db.Session() as session:
        plan = (
            session.query(TestPlans)
            .options(joinedload(TestPlans.metrics))
            .filter(TestPlans.plan_id == plan_id)
            .first()
        )
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Test plan not found"
            )
        
        metric_names = [metric.metric_name for metric in plan.metrics] if plan.metrics else []
        return TestPlanDetailResponse(
            plan_id=plan.plan_id,
            plan_name=plan.plan_name,
            plan_description=plan.plan_description,
            metric_names=metric_names,
        )


@testplan_router.post(
    "/create",
    response_model=TestPlanDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new test plan (v2)",
)
def create_testplan(
    payload: TestPlanCreateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    with db.Session() as session:
        try:
            # Get next available ID
            existing_ids = [row[0] for row in session.query(TestPlans.plan_id).order_by(TestPlans.plan_id).all()]
            next_id = 1
            for id in existing_ids:
                if id != next_id:
                    break
                next_id += 1
            
            # Create test plan
            new_plan = TestPlans(
                plan_name=payload.plan_name,
                plan_description=payload.plan_description,
            )
            session.add(new_plan)
            session.flush()  # Flush to get the plan_id
            
            # Add metrics if provided
            if payload.metric_names:
                for metric_name in payload.metric_names:
                    metric = session.query(Metrics).filter(Metrics.metric_name == metric_name).first()
                    if metric:
                        new_plan.metrics.append(metric)
            
            session.commit()
            session.refresh(new_plan)
            
            # Log activity
            username = _get_username_from_token(authorization)
            if username:
                log_activity(
                    username=username,
                    entity_type="TestPlan",
                    entity_id=str(new_plan.plan_id),
                    operation="create",
                    note=f"Test Plan - {new_plan.plan_name} created",
                    user_note=payload.notes,
                )
            
            # Get metric names for response
            metric_names = [metric.metric_name for metric in new_plan.metrics] if new_plan.metrics else []
            
            return TestPlanDetailResponse(
                plan_id=new_plan.plan_id,
                plan_name=new_plan.plan_name,
                plan_description=new_plan.plan_description,
                metric_names=metric_names,
            )
            
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A test plan with the same name already exists.",
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}",
            )


@testplan_router.put(
    "/update/{plan_id}",
    response_model=TestPlanDetailResponse,
    summary="Update a test plan (v2)",
)
def update_testplan(
    plan_id: int,
    payload: TestPlanUpdateV2,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    with db.Session() as session:
        try:
            plan = (
                session.query(TestPlans)
                .options(joinedload(TestPlans.metrics))
                .filter(TestPlans.plan_id == plan_id)
                .first()
            )
            
            if plan is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Test plan not found"
                )

            original_name = plan.plan_name
            original_description = plan.plan_description
            original_metric_names = sorted([m.metric_name for m in plan.metrics]) if plan.metrics else []

            # Update plan name if provided
            if payload.plan_name is not None and payload.plan_name != original_name:
                # Check for duplicate name
                existing = session.query(TestPlans).filter(
                    TestPlans.plan_name == payload.plan_name,
                    TestPlans.plan_id != plan_id
                ).first()
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="A test plan with this name already exists.",
                    )
                plan.plan_name = payload.plan_name

            # Update description if provided
            if payload.plan_description is not None:
                plan.plan_description = payload.plan_description

            # Update metrics if provided
            if payload.metric_names is not None:
                # Clear existing metrics
                plan.metrics.clear()
                # Add new metrics
                for metric_name in payload.metric_names:
                    metric = session.query(Metrics).filter(Metrics.metric_name == metric_name).first()
                    if metric:
                        plan.metrics.append(metric)

            session.commit()
            session.refresh(plan)

            username = _get_username_from_token(authorization)
            if not username:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

            # Track changes
            changes = []
            if payload.plan_name and original_name != payload.plan_name:
                changes.append(f"Name changed from '{original_name}' to '{payload.plan_name}'")
            if payload.plan_description and original_description != payload.plan_description:
                changes.append("Description changed")
            if payload.metric_names is not None:
                updated_metric_names = sorted(payload.metric_names)
                if original_metric_names != updated_metric_names:
                    changes.append("Metrics changed")

            note = f"Test Plan - {plan.plan_name} updated"
            if changes:
                note += f" : {', '.join(changes)}"
            else:
                note += " (no changes detected)"

            log_activity(
                username=username,
                entity_type="TestPlan",
                entity_id=str(plan.plan_id),
                operation="update",
                note=note,
                user_note=payload.notes,
            )

            metric_names = [metric.metric_name for metric in plan.metrics] if plan.metrics else []
            return TestPlanDetailResponse(
                plan_id=plan.plan_id,
                plan_name=plan.plan_name,
                plan_description=plan.plan_description,
                metric_names=metric_names,
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


@testplan_router.delete(
    "/delete/{plan_id}",
    summary="Delete a test plan (v2)",
)
def delete_testplan(
    plan_id: int,
    db: DB = Depends(_get_db),
    authorization: Optional[str] = Header(None),
):
    with db.Session() as session:
        plan = session.query(TestPlans).filter(TestPlans.plan_id == plan_id).first()
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Test plan not found"
            )

        plan_name = plan.plan_name
        session.delete(plan)
        session.commit()

        username = _get_username_from_token(authorization)
        if username:
            log_activity(
                username=username,
                entity_type="TestPlan",
                entity_id=str(plan_id),
                operation="delete",
                note=f"Test Plan - {plan_name} deleted",
                user_note=None,
            )

        return {"message": "Test plan deleted successfully"}


@testplan_router.get(
    "/metrics/all",
    response_model=List[str],
    summary="Get all available metric names",
)
def get_all_metrics(db: DB = Depends(_get_db)):
    with db.Session() as session:
        metrics = session.query(Metrics).all()
        return [metric.metric_name for metric in metrics]

