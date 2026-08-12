from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from services.analyse import (
    check_analyse_health_service,
    get_analyse_status_service,
    start_analyse_service,
    stop_analyse_service,
)
from services.testruns import get_test_run_service

router = APIRouter()
from configuration.database import get_db

@router.get("/analyse/health")
def check_health():
    return check_analyse_health_service()

@router.get("/analyse/{RunName}")
def get_analyse(
    RunName: str,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    mode: str = Query("rerun_all"),
    detail_ids: Optional[str] = Query(None),
):
    print(f"[API] Received analysis request for run '{RunName}' with mode '{mode}'")
    try:
        return start_analyse_service(
            RunName,
            db=db,
            background_tasks=background_tasks,
            mode=mode,
            selected_detail_ids=detail_ids,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyse/{RunName}/details")
def get_analyse_details(RunName: str, db = Depends(get_db), mode: str = Query("rerun_all")):
    print(f"[API] Received analysis details request for run '{RunName}' with mode '{mode}'")
    try:
        # Get the run details with the same filtering logic as start_analyse_service
        run = db.get_run_by_name(run_name=RunName)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        run_details = db.get_all_run_details_by_run_name(run_name=RunName)
        run_details = [
            rd for rd in run_details if rd.status == "COMPLETED"
        ]

        if mode == "retry_failed":
            print("Getting only failed test cases...")
            filtered_run_details = []
            for detail in run_details:
                conversation = db.get_conversation_by_id(detail.conversation_id)
                if not conversation:
                    continue
                reason = conversation.evaluation_reason or ""
                if reason.strip() == "":
                    filtered_run_details.append(detail)
            print(f"Retry Failed: {len(filtered_run_details)} / {len(run_details)} selected")
            run_details = filtered_run_details
        
        # Return the filtered run details in the same format as GET_TEST_RUN_DETAILS
        return get_test_run_service(db, RunName)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyse/{RunName}/status")
def get_analyse_status(RunName: str):
    try:
        return get_analyse_status_service(RunName)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyse/{RunName}/stop")
def stop_analyse(RunName: str):
    try:
        return stop_analyse_service(RunName)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
