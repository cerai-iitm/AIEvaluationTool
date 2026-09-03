from fastapi import BackgroundTasks, HTTPException, logger
from lib.strategy.strategy_implementor import StrategyImplementor
from datetime import datetime
import asyncio
import json
import os
import requests
from lib.utils import get_logger, get_logger_verbosity
logger = get_logger(__name__)
from services.ws_manager import ws_manager
from services.redis_client import redis_client

ollama_port = os.getenv("OLLAMA_URL")
gpu_url = os.getenv("GPU_URL")

# Analysis job progress used to be a per-process in-memory dict, which
# broke as soon as app-backend ran as multiple replicas: the replica that
# started (and is running) a job could differ from the replica serving a
# given browser's status poll/WebSocket, so that replica's dict simply had
# no entry for the job — a permanently "stuck" UI even though the job was
# genuinely progressing/completing elsewhere. Storing it in Redis instead
# makes it visible to every replica regardless of which one is running the
# background task.
ANALYSIS_JOB_KEY_PREFIX = "analysis_job:"
ANALYSIS_JOB_TTL_SECONDS = 24 * 60 * 60  # jobs are transient; avoid unbounded growth

ollama_url = os.getenv("OLLAMA_URL")
NO_FAILED_TESTCASES_MESSAGE = "No failed testcases found"

def check_analyse_health_service():
    try:
        response = requests.get(ollama_url, timeout=3)
        if response.status_code < 400:
            return {"status": "ok"}
        raise HTTPException(status_code=503, detail="Ollama is not healthy")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Ollama is not reachable")

# def check_service(url: str, name: str):
#     try:
#         response = requests.get(url, timeout=3)
#         print(f"Health check for {name} service at {url} returned status code {response.status_code}")
#         if response.status_code < 400:
#             return f"{name} service is reachable at {url}"
#         if response.status_code >= 400:
#             raise HTTPException(
#                 status_code=503,
#                 detail=f"{name} service is not healthy at {url}"
#             )
#     except requests.exceptions.RequestException:
#         raise HTTPException(
#             status_code=503,
#             detail=f"{name} service is not reachable at {url}"
#         )
    
def _job_key(run_name: str) -> str:
    return f"{ANALYSIS_JOB_KEY_PREFIX}{run_name}"


def _get_analysis_job(run_name: str) -> dict:
    try:
        raw = redis_client.get(_job_key(run_name))
    except Exception as e:
        logger.warning(f"Redis read failed for analysis job '{run_name}': {e}")
        return {}
    return json.loads(raw) if raw else {}


def _set_analysis_job(run_name: str, **updates):
    current = _get_analysis_job(run_name)
    current.update(updates)
    try:
        redis_client.set(_job_key(run_name), json.dumps(current), ex=ANALYSIS_JOB_TTL_SECONDS)
    except Exception as e:
        logger.warning(f"Redis write failed for analysis job '{run_name}': {e}")
    return current


def get_analyse_status_service(run_name: str):
    state = _get_analysis_job(run_name)
    if not state:
        return {"run_name": run_name, "status": "IDLE"}
    return {"run_name": run_name, **state}


def stop_analyse_service(run_name: str):
    state = _get_analysis_job(run_name)
    if not state or state.get("status") not in ("RUNNING", "STOPPING"):
        raise HTTPException(status_code=409, detail="This analysis is not active")
    _set_analysis_job(run_name, status="STOPPING", stop_requested=True)
    logger.info(f"Stop requested for analysis '{run_name}'")
    return {"run_name": run_name, "status": "stopping"}


def _analysis_stop_requested(run_name: str) -> bool:
    return bool(_get_analysis_job(run_name).get("stop_requested"))


def _is_retry_failed_candidate(db, detail) -> bool:
    if getattr(detail, "status", None) != "COMPLETED":
        return False

    conversation_id = getattr(detail, "conversation_id", None)
    if not conversation_id:
        return False

    conversation = db.get_conversation_by_id(conversation_id)
    if not conversation:
        return False

    reason = getattr(conversation, "evaluation_reason", None) or ""
    return reason.strip() == ""


def _parse_selected_detail_ids(selected_detail_ids):
    if not selected_detail_ids:
        return set()
    try:
        return {int(value) for value in selected_detail_ids.split(",") if value.strip()}
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="detail_ids must be comma-separated integers")


def _filter_run_details(run_details, mode: str, selected_detail_ids, db):
    if mode == "retry_failed":
        return [detail for detail in run_details if _is_retry_failed_candidate(db, detail)]
    if mode == "selected":
        selected_ids = _parse_selected_detail_ids(selected_detail_ids)
        if not selected_ids:
            raise HTTPException(status_code=400, detail="Select at least one test case")
        return [
            detail
            for detail in run_details
            if getattr(detail, "detail_id", None) in selected_ids
        ]
    if mode != "rerun_all":
        raise HTTPException(status_code=400, detail=f"Unsupported analysis mode: {mode}")
    return run_details


def start_analyse_service(
    run_name: str,
    db,
    background_tasks: BackgroundTasks,
    mode: str = "rerun_all",
    selected_detail_ids=None,
):
    logger.info(f"[SERVICE] Starting analysis service for run '{run_name}' with mode '{mode}'")
    try:
        run = db.get_run_by_name(run_name=run_name)
        if not run:
            logger.error(f"Run with name '{run_name}' not found.")
            raise HTTPException(
                status_code=404,
                detail=f"Run with name '{run_name}' not found."
            )
        if run.status != "COMPLETED":
            logger.error(f"Run '{run_name}' is not completed. Current status: {run.status}")
            raise HTTPException(
                status_code=400,
                detail=f"Run '{run_name}' is not completed. Current status: {run.status}"
            )

        existing = _get_analysis_job(run_name)
        if existing and existing.get("status") == "RUNNING":
            return {"run_name": run_name, "status": "running"}

        run_details = db.get_all_run_details_by_run_name(run_name=run.run_name)
        run_details = [
            rd for rd in run_details if rd.status == "COMPLETED"
        ]

        if mode in ("retry_failed", "selected"):
            logger.info("Running only failed test cases...")
            filtered_run_details = _filter_run_details(
                run_details, mode, selected_detail_ids, db
            )
            logger.info(f"Filtered Run Details: {filtered_run_details}")
            logger.info(f"Retry Failed: {len(filtered_run_details)} / {len(run_details)} selected")
            run_details = filtered_run_details
            if not run_details:
                logger.info("No failed test cases to retry")
                message = (
                    NO_FAILED_TESTCASES_MESSAGE
                    if mode == "retry_failed"
                    else "None of the selected test cases can be re-executed"
                )
                raise HTTPException(status_code=400, detail=message)
        total_items = len(run_details) if run_details else 0
        _set_analysis_job(
            run_name,
            status="RUNNING",
            current=0,
            total=total_items,
            analysis_start_ts=datetime.now().isoformat(),
            analysis_end_ts=None,
            analysis_duration_seconds=None,
            last_update=None,
            stop_requested=False,
        )

        background_tasks.add_task(
            run_analyse_background_service,
            run_name,
            db,
            mode,
            selected_detail_ids,
        )
        return {
            "run_name": run_name,
            "status": "started",
            "total": total_items,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _safe_ws_send(message: dict):
    """
    Best-effort WebSocket broadcast.
    Analysis must not crash if a client disconnects or send fails.
    """
    try:
        await ws_manager.send_all(message)
    except Exception as e:
        try:
            logger.error(f"WebSocket send failed: {e}")
        except Exception:
            pass


async def _run_in_thread(fn, *args, **kwargs):
    """
    Run blocking/sync work off the event loop.
    This also avoids `asyncio.run()` failures inside strategies when we're already in an async context.
    """
    to_thread = getattr(asyncio, "to_thread", None)
    if callable(to_thread):
        return await to_thread(fn, *args, **kwargs)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


def _stringify_error(e: Exception) -> str:
    try:
        msg = str(e)
        return msg if msg else e.__class__.__name__
    except Exception:
        return "Unknown error"


async def run_analyse_background_service(
    run_name: str, db, mode: str = "rerun_all", selected_detail_ids=None
):
    analysis_start_ts = datetime.now()
    try:
        await _safe_ws_send({
            "type": "ANALYSIS_STARTED",
            "runName": run_name,
            "analysisStartTs": analysis_start_ts.isoformat(),
        })

        run = db.get_run_by_name(run_name=run_name)
        if not run:
            raise HTTPException(
                status_code=404,
                detail=f"Run with name '{run_name}' not found."
            )
        
        run_details = db.get_all_run_details_by_run_name(run_name=run.run_name)
        run_details = [
            rd for rd in run_details if rd.status == "COMPLETED"
        ]
        
        if mode in ("retry_failed", "selected"):
            logger.info("Running only failed test cases...")
            filtered_run_details = _filter_run_details(
                run_details, mode, selected_detail_ids, db
            )
            logger.info(f"Retry Failed: {len(filtered_run_details)} / {len(run_details)} selected")
            run_details = filtered_run_details
            if not run_details:
                logger.info("No failed test cases to retry")
                raise ValueError(NO_FAILED_TESTCASES_MESSAGE)
        if not run_details:
            logger.error(f"No run details found for run '{run_name}'.")
            raise HTTPException(
                status_code=404,
                detail=f"No run details found for run '{run_name}'."
            )
        total_items = len(run_details)
        _set_analysis_job(run_name, total=total_items)

        completed = 0
        failed = 0

        for detail in sorted(run_details, key=lambda d: getattr(d, "detail_id", 0) or 0):
            if _analysis_stop_requested(run_name):
                break

            testcase_name = getattr(detail, "testcase_name", None)
            metric_name = getattr(detail, "metric_name", None)
            detail_id = getattr(detail, "detail_id", None)
            conversation_id = getattr(detail, "conversation_id", None)
            logger.info(f"[LOOP START] detail_id={detail_id} testcase={testcase_name} conversation_id={conversation_id}")
            # Always attempt to resolve strategy; missing strategy becomes a per-testcase failure.
            logger.info(f"[PRE-TRY] status={getattr(detail, 'status', None)}  conversation_id={conversation_id}")
            strategy_name = None
            try:
                strategy_name = db.get_testcase_strategy_name(testcase_name=testcase_name)
            except Exception:
                strategy_name = None

            status = "COMPLETED"
            score = None
            error = None
            conversation = None
            stopped_during_detail = False

            try:
                # Validate detail readiness for analysis, but never abort the whole loop.
                if getattr(detail, "status", None) != "COMPLETED":
                    raise ValueError(
                        f"Test case has failed"
                    )

                if not testcase_name:
                    raise ValueError(f"Missing testcase name for detail ID {detail_id}.")

                if not metric_name:
                    raise ValueError(f"Missing metric name for testcase '{testcase_name}' (detail ID {detail_id}).")

                if not strategy_name:
                    raise ValueError(f"Strategy not found for testcase '{testcase_name}' (detail ID {detail_id}).")

                testcase = db.get_testcase_by_name(testcase_name)
                if not testcase:
                    raise ValueError(f"Testcase '{testcase_name}' not found (detail ID {detail_id}).")

                if not getattr(testcase, "prompt", None) or not getattr(testcase.prompt, "user_prompt", None):
                    raise ValueError(f"User prompt not found for testcase '{testcase_name}' (detail ID {detail_id}).")

                if not conversation_id:
                    raise ValueError(f"Conversation ID not found for testcase '{testcase_name}' (detail ID {detail_id}).")

                conversation = db.get_conversation_by_id(conversation_id)
                logger.info(f"[DEBUG] detail_id={detail_id} testcase={testcase_name} conversation={conversation} agent_response={repr(getattr(conversation, 'agent_response', 'NO_CONV'))}")

                if not conversation:
                    raise ValueError(
                        f"Conversation with ID '{conversation_id}' not found for testcase '{testcase_name}' (detail ID {detail_id})."
                    )

                if not conversation.agent_response:
                    raise ValueError(
                        f"NO_AGENT_RESPONSE: No agent response recorded for testcase '{testcase_name}' (detail ID: {detail_id})."
                    )    
                agent_response = getattr(conversation, "agent_response", None)
                logger.info(f"Evaluating testcase='{testcase_name}' conversation_id='{conversation_id}' detail_id={detail_id} | agent_response value: {repr(agent_response)}")
                
                # Check for agent response immediately after getting conversation
                if not agent_response or str(agent_response).strip() == "":
                    logger.info(f"[NO_AGENT_RESPONSE] testcase='{testcase_name}' conversation_id='{conversation_id}' detail_id={detail_id} | agent_response value: {repr(agent_response)}")
                    raise ValueError(
                        f"NO_AGENT_RESPONSE: No response received from model for testcase '{testcase_name}' (conversation ID: {conversation_id}, detail ID: {detail_id})."
                    )

                def _eval_sync():
                    impl = StrategyImplementor()
                    impl.set_metric_strategy(strategy_name=strategy_name, metric_name=metric_name)
                    return impl.execute(testcase=testcase, conversation=conversation)

                raw_score, reason = await _run_in_thread(_eval_sync)
                if _analysis_stop_requested(run_name):
                    stopped_during_detail = True
                    break
                score = float(raw_score) if raw_score is not None else None
                if not reason or str(reason).strip() == "":
                    raise ValueError(
                        f"Failed to analyse"
                    )
                # Persist evaluation to conversation (best effort)
                conversation.evaluation_score = raw_score
                conversation.evaluation_reason = reason
                conversation.evaluation_ts = datetime.now().isoformat()
                db.add_or_update_conversation(conversation=conversation, override=True)
            except Exception as e:
                status = "FAILED"
                failed += 1
                error = _stringify_error(e)
                score = None
                # Best-effort: persist failure reason to conversation (if available)
                try:
                    if conversation is None and conversation_id:
                        conversation = db.get_conversation_by_id(conversation_id)
                    if conversation is not None:
                        # Set score to None when there's an error
                        conversation.evaluation_score = None
                        conversation.evaluation_reason = ""
                        conversation.evaluation_ts = datetime.now().isoformat()
                        db.add_or_update_conversation(conversation=conversation, override=True)
                except Exception:
                    pass
            finally:
                if not stopped_during_detail:
                    completed += 1
                    progress_payload = {
                        "type": "ANALYSIS_PROGRESS",
                        "runName": run_name,
                        "current": completed,
                        "total": total_items,
                        "testcaseName": testcase_name,
                        "metricName": metric_name,
                        "strategyName": strategy_name,
                        "detailId": detail_id,
                        "status": status,
                        "score": score,
                    }
                    if error:
                        progress_payload["error"] = error

                    _set_analysis_job(
                        run_name,
                        current=completed,
                        last_update=progress_payload,
                    )
                    await _safe_ws_send(progress_payload)

        if _analysis_stop_requested(run_name):
            analysis_end_ts = datetime.now()
            duration_seconds = int((analysis_end_ts - analysis_start_ts).total_seconds())
            _set_analysis_job(
                run_name,
                status="STOPPED",
                analysis_start_ts=analysis_start_ts.isoformat(),
                analysis_end_ts=analysis_end_ts.isoformat(),
                analysis_duration_seconds=duration_seconds,
                stop_requested=False,
            )
            await _safe_ws_send({
                "type": "ANALYSIS_STOPPED",
                "runName": run_name,
                "analysisStartTs": analysis_start_ts.isoformat(),
                "analysisEndTs": analysis_end_ts.isoformat(),
                "analysisDurationSeconds": duration_seconds,
                "current": completed,
                "total": total_items,
            })
            return

        analysis_end_ts = datetime.now()
        duration_seconds = int((analysis_end_ts - analysis_start_ts).total_seconds())
        _set_analysis_job(
            run_name,
            status="COMPLETED",
            analysis_start_ts=analysis_start_ts.isoformat(),
            analysis_end_ts=analysis_end_ts.isoformat(),
            analysis_duration_seconds=duration_seconds,
            failed=failed,
        )
        await _safe_ws_send({
            "type": "ANALYSIS_FINISHED",
            "runName": run_name,
            "analysisStartTs": analysis_start_ts.isoformat(),
            "analysisEndTs": analysis_end_ts.isoformat(),
            "analysisDurationSeconds": duration_seconds,
            "current": total_items,
            "total": total_items,
            "failed": failed,
        })
    except Exception as e:
        _set_analysis_job(
            run_name,
            status="FAILED",
            analysis_end_ts=datetime.now().isoformat(),
            error=str(e),
        )
        await _safe_ws_send({
            "type": "ANALYSIS_FAILED",
            "runName": run_name,
            "error": str(e),
        })
