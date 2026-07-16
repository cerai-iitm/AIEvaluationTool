import os
import sys
from typing import Optional, List,Literal
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from schemas import (
    ContinueRunRequest,
    FilterResponse,
    NewTestRun,
    TestRunFullResponse,
    TestRunResponse,
    TestRunSummaryResponse,
    TimelineEvent,
)
from services.testruns import (
    RunEvaluationSummaryResponse,
    continue_run_service,
    continue_run_with_plan_service,
    delete_test_run_service,
    download_evaluation_report_service,
    get_all_test_runs_service,
    get_interface_manager_status_service,
    get_metrics_by_plan_service,
    get_run_evaluation_summary_service,
    get_test_run_service,
    get_test_run_summary_service,
    get_test_run_timeline_service,
    start_run_service,
)
from configuration.database import get_db

router = APIRouter()

@router.get("/interface-manager/status")
def get_interface_manager_status():
    try:
        return get_interface_manager_status_service()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-run")
def start_run(data: NewTestRun, background_tasks: BackgroundTasks, db=Depends(get_db)):
    try:
        return start_run_service(db=db, data=data, background_tasks=background_tasks)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continue-run")
def continue_run(data: ContinueRunRequest, db=Depends(get_db)):
    try:
        return continue_run_service(db=db, run_name=data.run_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continue-run-with-plan")
def continue_run_with_plan(
    data: NewTestRun, background_tasks: BackgroundTasks, db=Depends(get_db)
):
    try:
        return continue_run_with_plan_service(
            db=db, data=data, background_tasks=background_tasks
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/test-runs/{run_name}",
    response_model=TestRunFullResponse
)
def get_test_run(
    run_name: str,
    metric: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db = Depends(get_db)
):
    try:
        return get_test_run_service(db, run_name, metric, status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/test-runs/{run_name}")
def delete_test_run(run_name: str, db=Depends(get_db)):
    try:
        return delete_test_run_service(db=db, run_name=run_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/get_all_test_runs",
    response_model=List[TestRunResponse],
)
def get_all_test_runs(
    domain: Optional[str] = Query(None),
    target: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: Literal["end_ts", "start_ts"] = Query("end_ts"),
    order: Literal["asc", "desc"] = Query("desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db=Depends(get_db),
):
    try:
        return get_all_test_runs_service(
            db=db,
            domain=domain,
            target=target,
            status=status,
            sort_by=sort_by,
            order=order,
            page=page, 
            page_size=page_size
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/get_metrics_by_plan/{plan_name}", response_model=list[FilterResponse])
def get_metrics_by_plan(plan_name: str, db=Depends(get_db)):
    try:
        return get_metrics_by_plan_service(db=db, plan_name=plan_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))        
    
@router.get("/test-runs/{run_name}/timeline", response_model=list[TimelineEvent])
def get_test_run_timeline(run_name: str, db=Depends(get_db)):
    try:
        return get_test_run_timeline_service(db=db, run_name=run_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-runs/{run_name}/evaluation-summary", response_model=RunEvaluationSummaryResponse)
def get_run_evaluation_summary(run_name: str, db=Depends(get_db)):
    try:
        return get_run_evaluation_summary_service(db=db, run_name=run_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-runs/{run_name}/evaluation-report")
def download_evaluation_report(run_name: str, db=Depends(get_db)):
    try:
        return download_evaluation_report_service(db=db, run_name=run_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))        
    
@router.get("/test-runs/{run_name}/summary", response_model=TestRunSummaryResponse)
def get_test_run_summary(run_name: str, db=Depends(get_db)):
    try:
        return get_test_run_summary_service(db=db, run_name=run_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    
