import math
import os
import sys
import re
import json
from typing import Optional,List,Literal
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime
import randomname
from lib.utils import get_logger, get_logger_verbosity
from configuration.paths import (
    ROOT_CONFIG_PATH as interface_manager_config,
    wb,
)
import tempfile

from lib.data import Run
from lib.interface_manager import InterfaceManagerClient
from schemas import TestRunFullResponse, TestRunSummaryResponse, TestRunDetailsResponse,TestRunResponse, NewTestRun, FilterResponse, EvaluationItemResponse, RunEvaluationSummaryResponse
from fastapi.responses import FileResponse
from tasks.test_run_tasks import execute_testcases
from utils.port import ensure_interface_manager_port_running, reset_frontend_disconnect_state

logger = get_logger(__name__)

GAP_THRESHOLD_MS = 5000

def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)

def _resolve_interface_manager_base_url() -> str:
    with open(interface_manager_config, "r") as f:
        config = json.load(f)

    if config.get("interface_manager", {}).get("docker"):
        return config.get("interface_manager", {}).get(
            "base_url", "http://interface-manager:8000"
        )
    return "http://localhost:8000"


def get_execution_view_service(db, run_id: int):
    """
    Return the noVNC live-view path for the run's pooled Selenium session,
    so the frontend can show a per-run view instead of one shared static
    link. All test cases in a run share one session/node (pooled by
    run_id), so this path stays stable for the whole run.
    """
    try:
        run = db.get_run_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        target_obj = db.get_target_by_name(run.target)
        application_type_map = {"WhatsApp": "WHATSAPP_WEB", "WebApp": "WEBAPP", "API": "API"}
        application_type = application_type_map.get(getattr(target_obj, "target_type", None))
        if application_type not in ("WHATSAPP_WEB", "WEBAPP"):
            raise HTTPException(
                status_code=400,
                detail=f"No live view available for target type '{getattr(target_obj, 'target_type', None)}'",
            )

        client = InterfaceManagerClient(
            base_url=_resolve_interface_manager_base_url(),
            application_type=application_type,
        )
        try:
            response = client.view(run_id)
        except RuntimeError as e:
            raise HTTPException(status_code=404, detail=str(e))

        return response.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"get_execution_view_service failed for run_id={run_id}")
        raise HTTPException(status_code=500, detail=f"get_execution_view_service error: {e}")


def get_interface_manager_status_service():
    with open(interface_manager_config, "r") as f:
        config = json.load(f)

    return {
        "docker": _as_bool(config.get("interface_manager", {}).get("docker", False)),
    }

def _parse_timeline_timestamp(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).timestamp() * 1000
    except ValueError:
        return None

def _calculate_timeline_duration_ms(timeline) -> Optional[int]:
    timed_events = []

    for event in timeline:
        start = _parse_timeline_timestamp(getattr(event, "prompt_ts", None))
        end = _parse_timeline_timestamp(getattr(event, "response_ts", None))

        if start is None or end is None or end <= start:
            continue

        timed_events.append({
            "plan_name": getattr(event, "plan_name", "") or "",
            "start": start,
            "end": end,
        })

    if not timed_events:
        return None

    timed_events.sort(key=lambda event: event["start"])
    plan_blocks = []

    for event in timed_events:
        last_block = plan_blocks[-1] if plan_blocks else None

        if last_block and last_block["plan_name"] == event["plan_name"]:
            last_response_time = max(item["end"] for item in last_block["events"])
            if event["start"] - last_response_time < GAP_THRESHOLD_MS:
                last_block["events"].append(event)
                continue

        plan_blocks.append({
            "plan_name": event["plan_name"],
            "events": [event],
        })

    total_ms = 0
    for block in plan_blocks:
        starts = [event["start"] for event in block["events"]]
        ends = [event["end"] for event in block["events"]]
        total_ms += max(ends) - min(starts)

    return int(total_ms) if total_ms > 0 else None

def _has_failed_cases(db, details) -> bool:
    for d in details:
        if getattr(d, "status", None) != "COMPLETED":
            continue

        conversation_id = getattr(d, "conversation_id", None)
        if not conversation_id:
            continue

        conv = db.get_conversation_by_id(conversation_id)
        if not conv:
            continue

        evaluation_reason = conv.evaluation_reason or ""
        if not evaluation_reason.strip():
            return True
    return False

def start_run_service(db, data: NewTestRun, background_tasks: BackgroundTasks):
    reset_frontend_disconnect_state()
    ensure_interface_manager_port_running(interface_manager_config)
    if data.testPlan:
        logger.info("Starting new test run...")
        target = data.target
        target = re.sub(r"\s*\(.*?\)", "", target)

        plan_name = data.testPlan
        test_case_ids = list(dict.fromkeys(
            testcase_name.strip()
            for testcase_name in (data.testCaseIds or ([data.testCaseId] if data.testCaseId else []))
            if testcase_name and testcase_name.strip()
        ))
        metric_name = data.metric
        domain_name = data.domain if data.domain else None
        lang_name = [data.language] if data.language else None
        
        provided_run_name = data.runName.strip() if data.runName else None
        if test_case_ids and metric_name:
            raise HTTPException(
                status_code=400,
                detail="Provide either 'testCaseId' or 'metric', not both.",
            )
        try:
            max_test_cases = int(data.maxTestCases)
            
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="maxTestCases must be a valid number",
            )
        if max_test_cases < 1:
            raise HTTPException(
                status_code=400,
                detail="maxTestCases must be at least 1",
            )

        if provided_run_name:
            run_name = provided_run_name
        else:
            run_name = randomname.generate("v/*", "adj/*", "n/*", "ip/*").replace(
                "/", "-"
            )
        start_time = datetime.now().isoformat()
        run = Run(target=target, run_name=run_name, start_ts=start_time)
        run_id = db.add_or_update_testrun(run)
        logger.info(f"Starting run: {run_name} with run id {run_id}")

        if plan_name is None:
            logger.error(f"No test plan found with name {plan_name}.")
            return
        logger.info(f"Starting run with Test Plan: {plan_name}")

        if test_case_ids:
            testcases = []
            for test_case_id in test_case_ids:
                testcase = db.get_testcase_by_name(test_case_id)
                if not testcase:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Test case ID '{test_case_id}' does not exist",
                    )
                testcases.append(testcase)
            total_testcases = len(testcases)
            logger.info(f"Length of testcases: {len(testcases)}")
            

            run.status = "RUNNING"
            db.add_or_update_testrun(run=run)
            background_tasks.add_task(
                execute_testcases,
                run_name,
                run_id,
                plan_name,
                target,
                testcases,
                run,
            )

        elif metric_name:
            is_metric_in_plan = db.is_metric_in_testplan(
                metric_name=metric_name, plan_name=plan_name
            )
            if not is_metric_in_plan:
                return
            testcases = db.get_testcases_by_metric(
                metric_name=metric_name,
                n=max_test_cases,
                lang_names=lang_name,
                domain_name=domain_name,
            )
            if not testcases:
                raise HTTPException(
                    status_code=404,
                    detail=f"No Test cases found",
                )
                
            total_testcases = len(testcases)
            run.status = "RUNNING"
            db.add_or_update_testrun(run=run)
            background_tasks.add_task(
                execute_testcases,
                run_name,
                run_id,
                plan_name,
                target,
                testcases,
                run,
            )

        else:
            
            testcases = db.get_testcases_by_testplan(
                plan_name=plan_name,
                n=max_test_cases,
                lang_names=lang_name,
                domain_name=domain_name,
            )
            
            if not testcases:
                raise HTTPException(
                    status_code=404,
                    detail=f"No Test cases found",
                )
                
            total_testcases = len(testcases)
            run.status = "RUNNING"
            db.add_or_update_testrun(run=run)
            background_tasks.add_task(
                execute_testcases,
                run_name,
                run_id,
                plan_name,
                target,
                testcases,
                run,
            )

        return {
            "status": "success",
            "runId": run_id,
            "runName": run_name,
            "testPlanName": plan_name,
            "metricName": metric_name,
            "target": target,
            "totalTestCases": total_testcases,
        }

    return "Test Plan ID is mandatory"


def continue_run_service(db, run_name: str):
    run = db.get_run_by_name(run_name)

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    details = db.get_run_details_by_run_id(run.run_id)
    
    return {"run": run, "details": details}


def continue_run_with_plan_service(db, data: NewTestRun, background_tasks: BackgroundTasks):
    reset_frontend_disconnect_state()
    ensure_interface_manager_port_running(interface_manager_config)
    run = db.get_run_by_name(data.runName)

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status == "COMPLETED":
        run.status = "RUNNING"
        run.end_ts = None
        db.add_or_update_testrun(run=run, override=True)

    run_id = run.run_id
    run_name = run.run_name

    plan_name = data.testPlan
    metric_name = data.metric
    testcase_ids = list(dict.fromkeys(
        testcase_name.strip()
        for testcase_name in (data.testCaseIds or ([data.testCaseId] if data.testCaseId else []))
        if testcase_name and testcase_name.strip()
    ))
    if testcase_ids and metric_name:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'testCaseId' or 'metric', not both.",
        )

    if not plan_name:
        raise HTTPException(status_code=400, detail="Test Plan is required")

    try:
        max_test_cases = int(data.maxTestCases)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid maxTestCases")
    if max_test_cases < 1:
        raise HTTPException(status_code=400, detail="maxTestCases must be at least 1")

    if metric_name:
        testcases = db.get_testcases_by_metric(
            metric_name=metric_name,
            n=max_test_cases,
            lang_names=data.language,
            domain_name=data.domain,
        )
    elif testcase_ids:
        testcases = []
        for testcase_id in testcase_ids:
            testcase = db.get_testcase_by_name(testcase_id)
            if not testcase:
                raise HTTPException(
                    status_code=404,
                    detail=f"Test case ID '{testcase_id}' does not exist",
                )
            testcases.append(testcase)
    else:
        testcases = db.get_testcases_by_testplan(
            plan_name=plan_name,
            n=max_test_cases,
            lang_names=data.language,
            domain_name=data.domain,
        )

    if not testcases:
        raise HTTPException(status_code=400, detail="No testcases found")

    background_tasks.add_task(
        execute_testcases,
        run_name,
        run_id,
        plan_name,
        run.target,
        testcases,
        run,
    )

    return {
        "status": "continued",
        "runId": run_id,
        "runName": run_name,
        "addedPlan": plan_name,
        "plan_name":plan_name,
        "metric_name":metric_name,
        "totalTestCases": len(testcases),
    }

def get_test_run_service(db, run_name: str, metric: Optional[str] = None, status: Optional[str] = None):
    try:
        

        run = db.get_run_by_name(run_name)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        timeline = db.get_run_timeline(run_name) or []
        duration_ms = _calculate_timeline_duration_ms(timeline)
        analysis_status="failed"   # default status
        if timeline:
            scores = []
            for e in timeline:
                if e.evaluation_score is not None:
                    scores.append(float(e.evaluation_score))
            if scores:
                analysis_status="completed"
            print(analysis_status)
            average_score = (
                round(sum(scores) / len(scores), 4)
                if scores
                else None
            )
            
        domain_name = None
        if getattr(run, "target_id", None):
            target = db.get_target_by_id(run.target_id)
            if target:
                domain_name = getattr(target, "target_domain", None)

        summary = TestRunSummaryResponse(
            run_id=run.run_id,
            run_name=run.run_name,
            target=run.target,
            domain=domain_name,
            status=run.status,
            start_ts=run.start_ts,
            end_ts=run.end_ts,
            average_score=average_score,
            analysis_status=analysis_status
        )
        logger.info(f"Run summary: {summary}")
        details = db.get_all_run_details_by_run_name(run_name)

        details_response = []
        if metric:
            details = [d for d in details if d.metric_name == metric]

        if status:
            details = [d for d in details if d.status == status]

        has_failed_cases = _has_failed_cases(db, details)

        for d in details:
            score = None
            evaluation_reason = ""
            if d.conversation_id:
                conv = db.get_conversation_by_id(d.conversation_id)
                if conv and conv.evaluation_score is not None:
                    score = float(conv.evaluation_score)
                if conv:
                    evaluation_reason = conv.evaluation_reason or ""  # ← add this

            details_response.append(
                TestRunDetailsResponse(
                    run_name=d.run_name,
                    testcase_name=d.testcase_name,
                    metric_name=d.metric_name,
                    plan_name=d.plan_name,
                    conversation_id=d.conversation_id,
                    status=d.status,
                    detail_id=d.detail_id,
                    score=score,
                    evaluation_reason=evaluation_reason,
                    has_failed_cases=has_failed_cases
                )
            )
        print(has_failed_cases)    
        return TestRunFullResponse(
            summary=summary,
            details=details_response
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def get_all_test_runs_service(
    db,
    domain: Optional[str] = None,
    target: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Literal["end_ts", "start_ts"] = "end_ts",
    order: Literal["asc", "desc"] = "desc",
    page: int = 1,
    page_size: int = 10,
) -> List[TestRunResponse]:
    try:
        runs = db.get_all_runs(domain=domain, target=target, status=status)
        total_count = len(runs)    
        response: List[TestRunResponse] = []
        reverse = order == "desc"
        runs.sort(key=lambda r: getattr(r, sort_by) or "", reverse=reverse)
        start_idx = (page - 1) * page_size
        runs = runs[start_idx : start_idx + page_size]
        
        for r in runs:
            analysis_status = "failed"   # reset for each run
            domain_name = None

            target_id = (
                r.kwargs.get("target_id")
                if hasattr(r, "kwargs") and r.kwargs
                else None
            )

            if target_id:
                target_obj = db.get_target_by_id(target_id)
                if target_obj:
                    domain_name = target_obj.target_domain
            duration_ms = None
            timeline = db.get_run_timeline(r.run_name) or []
            
            if timeline:
                duration_ms = _calculate_timeline_duration_ms(timeline)

            scores = []
            count = 0
            for e in timeline:
                
                if (e.evaluation_score is not None) and (e.evaluation_score <= 1):
                    count += 1
                    scores.append(float(e.evaluation_score))
                    
            
            if scores:
                analysis_status="completed"

            average_score = (
                round(sum(scores) / count, 4)
                if scores 
                else None
            )
            evaluation_ts = max(
                (e.evaluation_ts for e in timeline if e.evaluation_ts),
                default=None
            )
            run_details = db.get_all_run_details_by_run_name(r.run_name)
            # print("evaluation time stamp", evaluation_ts)   
            response.append(
                TestRunResponse(
                    run_id=r.run_id,
                    run_name=r.run_name,
                    target=r.target,
                    status=r.status,
                    start_ts=r.start_ts,
                    end_ts=r.end_ts,
                    domain=domain_name,
                    duration_ms=duration_ms,
                    average_score=average_score,
                    evaluation_ts=evaluation_ts,
                    analysis_status=analysis_status,
                    has_failed_cases=_has_failed_cases(db, run_details),
                    totalPages= math.ceil(total_count / page_size) if page_size else 1
                )
            )

        # # 🔹 Sorting
        # reverse = order == "desc"
        # response.sort(
        #     key=lambda x: getattr(x, sort_by) or "",
        #     reverse=reverse
        # )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))   
    
def get_metrics_by_plan_service(db, plan_name: str):
    metrics = db.get_metrics_by_testplan(plan_name)
    return [FilterResponse(filter_name=m) for m in metrics]

def get_test_run_timeline_service(db,run_name: str):
    timeline = db.get_run_timeline(run_name)
    if not timeline:
        raise HTTPException(status_code=404, detail="No timeline found")
    return timeline


def get_run_evaluation_summary_service(db, run_name: str):
    run = db.get_run_by_name(run_name)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    domain_name = None
    if getattr(run, "target_id", None):
        target = db.get_target_by_id(run.target_id)
        if target:
            domain_name = getattr(target, "target_domain", None)

    run_summary = TestRunSummaryResponse(
        run_id=run.run_id,
        run_name=run.run_name,
        target=run.target,
        domain=domain_name,
        status=run.status,
        start_ts=run.start_ts,
        end_ts=run.end_ts
    )

    details = db.get_all_run_details_by_run_name(run_name)
    evaluations = []

    for d in details:
        conv = db.get_conversation_by_id(d.conversation_id)
        
        if not conv:
            continue
        evaluations.append(
            EvaluationItemResponse(
                detail_id=d.detail_id,
                testcase=conv.testcase,
                agent_response=conv.agent_response,
                evaluation_score=conv.evaluation_score,
                evaluation_reason=conv.evaluation_reason,
                evaluation_ts=conv.evaluation_ts
            )
        )

    return RunEvaluationSummaryResponse(run=run_summary, evaluations=evaluations)


def download_evaluation_report_service(db, run_name: str):
    run = db.get_run_by_name(run_name)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    details = db.get_all_run_details_by_run_name(run_name)
    plan_name = details[0].plan_name if details else None

    conversation_cache = {}
    testcase_prompt_cache = {}
    for d in details:
        if d.conversation_id not in conversation_cache:
            conversation_cache[d.conversation_id] = db.get_conversation_by_id(d.conversation_id)

    ws_summary = wb["Run_Summary"]
    testcases = set()
    total_metrics = len(details)

    for conv in conversation_cache.values():
        if conv and getattr(conv, "testcase", None):
            testcases.add(conv.testcase)

    ws_summary["B1"] = run.run_name
    ws_summary["B2"] = plan_name
    ws_summary["B3"] = run.status
    ws_summary["B4"] = len(testcases)
    ws_summary["B5"] = total_metrics

    ws_details = wb["Evaluation_Details"]

    for d in details:
        conv = conversation_cache.get(d.conversation_id)
        if not conv:
            continue

        metric_name = (
            getattr(d, "metric", None)
            or getattr(d, "metric_name", None)
            or getattr(conv, "metric", None)
            or getattr(conv, "metric_name", None)
        )

        testcase_name = getattr(conv, "testcase", None)

        if testcase_name not in testcase_prompt_cache:
            testcase = db.get_testcase_by_name(testcase_name)
            if not testcase or not getattr(testcase, "prompt", None):
                testcase_prompt_cache[testcase_name] = {"user_prompt": None, "system_prompt": None}
            else:
                testcase_prompt_cache[testcase_name] = {
                    "user_prompt": getattr(testcase.prompt, "user_prompt", None),
                    "system_prompt": getattr(testcase.prompt, "system_prompt", None),
                }

        prompts = testcase_prompt_cache[testcase_name]
        ws_details.append([
            d.detail_id,
            getattr(conv, "testcase", None),
            metric_name,
            getattr(conv, "evaluation_score", None),
            getattr(conv, "evaluation_reason", None),
            getattr(conv, "evaluation_ts", None),
            getattr(conv, "agent_response", None),
            prompts["user_prompt"],
            prompts["system_prompt"],
        ])

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(tmp_file.name)
    tmp_file.close()

    return FileResponse(
        tmp_file.name,
        filename=f"{run_name}_evaluation_report.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def get_test_run_summary_service(db, run_name: str):
    run = db.get_run_by_name(run_name)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    domain_name = None
    if getattr(run, "target_id", None):
        target = db.get_target_by_id(run.target_id)
        if target:
            domain_name = getattr(target, "target_domain", None)

    return TestRunSummaryResponse(
        run_id=run.run_id,
        run_name=run.run_name,
        target=run.target,
        domain=domain_name,
        status=run.status,
        start_ts=run.start_ts,
        end_ts=run.end_ts
    )


def delete_test_run_service(db, run_name: str):
    run = db.get_run_by_name(run_name)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    deleted = db.delete_run_by_name(run_name)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete run")

    return {
        "status": "success",
        "message": f"Run '{run_name}' deleted successfully",
        "run_name": run_name,
    }

# def start_run_service(db, data: NewTestRun, background_tasks: BackgroundTasks):    
#     ensure_interface_manager_running(interface_manager_config)
#     if data.testPlan:
#         ### Initialising the form variables
#         print("Starting new test run...")
#         target = data.target
#         target = re.sub(r"\s*\(.*?\)", "", target)

        
#         plan_name = data.testPlan
#         test_case_id = data.testCaseId
#         metric_name = data.metric 
#         domain_name = data.domain if data.domain else None
#         lang_name = data.language if data.language else None
#         provided_run_name = data.runName.strip() if data.runName else None
#         if test_case_id and metric_name:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Provide either 'testCaseId' or 'metric', not both."
#             )
#         try:
#             max_test_cases = int(data.maxTestCases)
#             print(max_test_cases)
#         except (TypeError, ValueError):
#             raise HTTPException(
#                 status_code=400,
#                 detail="maxTestCases must be a valid number"
#             )
#         ## Create a random name for the run and generating run id

#         if provided_run_name:
#             run_name = provided_run_name
#         else:
#             run_name = randomname.generate('v/*','adj/*','n/*','ip/*')
#         start_time = datetime.now().isoformat()
#         run = Run(target=target, run_name=run_name, start_ts=start_time)
#         run_id = db.add_or_update_testrun(run)
#         print(f"Starting run: {run_name} with run id {run_id}")

        
#         # plan_name = db.get_testplan_name(plan_id=test_plan_id)
        
#         if plan_name is None:
#             print(f"No test plan found with name {plan_name}.")
#             return
#         print(f"Starting run with Test Plan: {plan_name}")

#         if test_case_id:
#             testcases = db.get_testcase_by_name(test_case_id)
#             if not testcases:
#                 raise HTTPException(
#                     status_code=500,
#                     detail=f"Test case ID '{test_case_id}' does not exist"
#                 )
#             # is_valid = db.is_testcase_in_testplan(
#             #     test_case_id=test_case_id,
#             #     plan_name=plan_name
#             # )

#             # if not is_valid:
#             #     raise HTTPException(
#             #         status_code=400,
#             #         detail=f"Test case '{test_case_id}' is not mapped to test plan '{plan_name}'"
#             #     )
#             testcases = [testcases]
#             total_testcases = len(testcases)
#             print(f"Length of testcases: {len(testcases)}")
#             print(type(testcases))
            
#             run.status = "RUNNING"
#             db.add_or_update_testrun(run=run)
            
            
#             background_tasks.add_task(
#                 execute_testcases,
#                 run_name,
#                 run_id,
#                 plan_name,
#                 target,
                
#                 testcases,
#                 run
#             )

#         elif metric_name:
#             # metric_name = db.get_metric_name(metric_id=metric_id)  
#             is_metric_in_plan = db.is_metric_in_testplan(metric_name=metric_name, plan_name=plan_name)  
#             if not is_metric_in_plan:
#                 return
#             testcases = db.get_testcases_by_metric(
#                 metric_name=metric_name,
#                 n=max_test_cases,
#                 lang_names=lang_name,
#                 domain_name=domain_name
#             ) 
#             if not testcases:
#                 print("No Test cases Found")
#                 return
#             #     ## Get the metric from the provided ID 
#             total_testcases = len(testcases)
#             # metric = db.get_metric_by_id(metric_id=metric_id)
#             # if metric is None:
#             #     print("No Metric Found")
#             #     return
#             run.status = "RUNNING"
#             db.add_or_update_testrun(run=run)
#             background_tasks.add_task(
#                 execute_testcases,
#                 run_name,
#                 run_id,
#                 plan_name,
#                 target,
                
#                 testcases,
#                 run
#             )
#             # agent_name = target
#             # application_name = target
#             # application_url = "https://web.whatsapp.com"
#             # application_type = "WHATSAPP_WEB"
#             # print("started syncing")
#             # client = InterfaceManagerClient(base_url="http://localhost:8000" ,application_type=application_type, agent_name=agent_name)
#             # client.sync_config({
#             #         "application_name": application_name,
#             #         "application_type": application_type,
#             #         "agent_name": agent_name,
#             #         "application_url": application_url
#             #     })
#             # client.apply_server_config()
#             # for testcase in testcases:
#             #     rundetail = RunDetail(run_name=run_name, plan_name=plan_name, metric_name=testcase.metric, testcase_name=testcase.name)
#             #     rundetail_id = db.add_or_update_testrun_detail(rundetail)
#             #     run_status = db.get_status_by_run_detail_id(run_detail_id=rundetail_id)
#             #     if run_status is not None and run_status == "COMPLETED":
#             #         print(f"Run detail for testcase {testcase.name} (ID: {testcase.testcase_id}) is already completed. Skipping execution.")
#             #         continue
#             #     message_to_agent = testcase.prompt.user_prompt if testcase.prompt.user_prompt else ""
#             #     if testcase.prompt.system_prompt:
#             #         message_to_agent = testcase.prompt.system_prompt + " " + message_to_agent

#             #     conv = Conversation(target=target, 
#             #                         run_detail_id=rundetail_id, 
#             #                         testcase=testcase.name)
#             #     conv_id = db.add_or_update_conversation(conversation=conv)
#             #     print(f"A new conversation is created with ID: {conv_id}")
#             #     rundetail.status = "RUNNING"
#             #     db.add_or_update_testrun_detail(rundetail)
#             #     # print("completed")
                
#             #     conv.prompt_ts = datetime.now().isoformat()
#             #     db.add_or_update_conversation(conversation=conv)
#             #     print("prompt time added")    
#             #     response_from_agent = client.chat(chat_id = testcase.testcase_id, prompt_list=[message_to_agent])
#             #     agent_response = response_from_agent.json().get("response", "")
#             #     if len(agent_response) == 0 or agent_response[0]['response'] == "Chat not found":
#             #         print(f"No response received from the agent for test case {testcase.testcase_id}.")
#             #         rundetail.status = "FAILED"
#             #         db.add_or_update_testrun_detail(rundetail)
#             #         continue
#             #     conv.response_ts = datetime.now().isoformat()
#             #     print("Response time added") 
#             #     conv.agent_response = agent_response[0]['response']
#             #     db.add_or_update_conversation(conversation=conv)
#             #     rundetail.status = "COMPLETED"
#             #     db.add_or_update_testrun_detail(rundetail)
#             #     print("completed Response time")
            
#         # 🔹 Get testcases count (NO execution here)

#         else:
#             testcases = db.get_testcases_by_testplan(plan_name=plan_name, n=max_test_cases, lang_names=lang_name, domain_name=domain_name)
#             if not testcases:
#                 print("No Test cases Found")
#                 return
#             total_testcases = len(testcases)   
#             run.status = "RUNNING"
#             db.add_or_update_testrun(run=run)
#             background_tasks.add_task(
#                 execute_testcases,
#                 run_name,
#                 run_id,
#                 plan_name,
#                 target,
                
#                 testcases,
#                 run
#             )
        
#         return {
#             "status": "success",
#             "runId": run_id,
#             "runName": run_name,
#             "testPlanName": plan_name,
#             "metricName": metric_name,
#             "target": target,
#             "totalTestCases": total_testcases,
            
#         }
        
#     else:
#         return("Test Plan ID is mandatory")
