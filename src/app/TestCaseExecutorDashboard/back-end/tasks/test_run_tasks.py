import asyncio
import json
import threading
from datetime import datetime

from configuration.database import db
from configuration.paths import (
    ROOT_CONFIG_PATH as config_path,
    profile_path,
)
from lib.data import Conversation, RunDetail
from lib.interface_manager import InterfaceManagerClient
from services.ws_manager import ws_manager
from utils.port import (
    is_frontend_disconnect_requested,
    set_active_stop_watcher,
    watch_im_process,
)
from lib.utils import get_logger, get_logger_verbosity

logger = get_logger(__name__)

def is_error_response(response_text: str) -> bool:
    error_indicators = [
        "chat not found",
        "[error: max retries exceeded]",
        "[error: connection refused]",
        "no response received",
    ]
    text = (response_text or "").lower()
    return (not text.strip()) or any(ind in text for ind in error_indicators)

def extract_agent_response(response_payload) -> str:
    """
    Normalize interface-manager payloads across channels.
    Supported shapes:
    - {"response": [{"response": "plain text"}]}
    - {"response": [{"response": {"type": "text", "content": "plain text"}}]}
    - direct string payloads
    """
    if isinstance(response_payload, str):
        return response_payload.strip()

    if isinstance(response_payload, dict):
        payload_type = response_payload.get("type")
        if payload_type == "text":
            return (response_payload.get("content") or "").strip()
        if payload_type == "audio":
            return (response_payload.get("file") or "").strip()
        # Backward-compatible fallback where text is nested under "response"
        nested = response_payload.get("response")
        if isinstance(nested, str):
            return nested.strip()
        return ""

    if isinstance(response_payload, list) and response_payload:
        first = response_payload[0]
        if isinstance(first, dict):
            return extract_agent_response(first.get("response"))
        if isinstance(first, str):
            return first.strip()

    return ""

with open(config_path, "r") as f:
    config_read = json.load(f)

# Added logic for dynamic interface manager URL and selenium mode based on config
if config_read.get('interface_manager', {}).get('docker'):
    interface_manager_url = config_read.get("interface_manager", {}).get(
        "base_url", "http://interface-manager:8000"
    )
    selenium_mode = config_read.get("selenium_mode", {}).get(
        "selenium_mode", "remote"
    )
else:
    interface_manager_url = "http://localhost:8000"
    selenium_mode = config_read.get("selenium_mode", {}).get(
        "selenium_mode", "local"
    )

# Optional: keeping this if still needed elsewhere
interface_manager_config = config_read.get("interface_manager", {})

async def step(ws_payload, delay=0.1):
    await ws_manager.send_all(ws_payload)
    await asyncio.sleep(delay)


async def execute_testcases(
    run_name,
    run_id,
    plan_name,
    target,
    testcases,
    run,
):
    logger.info(f"🚀 Background execution started for run {run_id}")

    client = None
    try:
        
        stop_watcher = threading.Event()
        set_active_stop_watcher(stop_watcher)

        def stop_requested() -> bool:
            return is_frontend_disconnect_requested(stop_watcher)

        async def finish_aborted_run(rundetail=None):
            logger.info(f"Frontend disconnected; aborting run {run_id}")
            stop_watcher.set()
            if rundetail is not None:
                rundetail.status = "FAILED"
                db.add_or_update_testrun_detail(rundetail)
            run.end_ts = datetime.now().isoformat()
            run.status = "FAILED"
            db.add_or_update_testrun(run=run)
            await ws_manager.send_all(
                {
                    "type": "RUN_FINISHED",
                    "runId": run_id,
                    "status": "FAILED",
                    "error": "Frontend disconnected",
                }
            )

        if interface_manager_config.get("docker"):
            logger.info("Docker mode detected; skipping local Chrome process watcher")
        else:
            watcher_thread = threading.Thread(
                target=watch_im_process,
                args=(config_path, profile_path, stop_watcher),
                daemon=True,
            )
            watcher_thread.start()

        if stop_requested():
            await finish_aborted_run()
            return

        agent_name = target
        application_name = target
        target_obj = db.get_target_by_name(target)
        application_url = target_obj.target_url
        APPLICATION_TYPE_MAP = {
            "WhatsApp": "WHATSAPP_WEB",
            "WebApp": "WEBAPP",
            "API": "API",
        }
        
        if target_obj.target_type not in APPLICATION_TYPE_MAP:
            raise ValueError(f"Unsupported target_type: {target_obj.target_type}")

        application_type = APPLICATION_TYPE_MAP[target_obj.target_type]

        base_url = interface_manager_url

        client = InterfaceManagerClient(
            base_url=base_url,
            application_type=application_type,
            agent_name=agent_name,
        )
        await ws_manager.send_all(
            {"type": "RUN_STARTED", "runId": run_id, "total": len(testcases)}
        )

        if stop_requested():
            await finish_aborted_run()
            return

        try:
            client.sync_config(
                {
                    "application_name": application_name,
                    "application_type": application_type,
                    "agent_name": agent_name,
                    "application_url": application_url,
                    "selenium_mode": selenium_mode
                }
            )
            client.apply_server_config()
        except Exception as e:
            if stop_requested():
                await finish_aborted_run()
                return
            logger.error(f"Interface manager setup failed for run {run_id}: {e}")
            run.status = "FAILED"
            run.end_ts = datetime.now().isoformat()
            db.add_or_update_testrun(run=run)
            await ws_manager.send_all(
                {
                    "type": "RUN_FINISHED",
                    "runId": run_id,
                    "status": "FAILED",
                    "error": str(e),
                }
            )
            return

        logger.info("⏳ Waiting for WhatsApp to be ready...")

        logger.info("✅ Starting testcase loop!")
        for index, testcase in enumerate(testcases, start=1):
            rundetail = None
            try:
                if stop_requested():
                    await finish_aborted_run()
                    return

                rundetail = RunDetail(
                    run_name=run_name,
                    plan_name=plan_name,
                    metric_name=testcase.metric,
                    testcase_name=testcase.name,
                )
                rundetail_id = db.add_or_update_testrun_detail(rundetail)
                # For continue runs, always rerun test cases regardless of previous status
                # Commented out the status check to force rerun
                # run_status = db.get_status_by_run_detail_id(run_detail_id=rundetail_id)
                # if run_status is not None and run_status == "COMPLETED":
                #     print(
                #         f"Run detail for testcase {testcase.name} (ID: {testcase.testcase_id}) is already completed. Skipping execution."
                #     )
                #     continue

                message_to_agent = testcase.prompt.user_prompt or ""
                if testcase.prompt.system_prompt:
                    message_to_agent = testcase.prompt.system_prompt + " " + message_to_agent

                conv = Conversation(
                    target=target,
                    run_detail_id=rundetail_id,
                    testcase=testcase.name,
                )
                conv_id = db.add_or_update_conversation(conversation=conv)
                logger.info(f"A new conversation is created with ID: {conv_id}")

                rundetail.status = "RUNNING"
                db.add_or_update_testrun_detail(rundetail)
                conv.prompt_ts = datetime.now().isoformat()
                db.add_or_update_conversation(conversation=conv)

                await step(
                    {
                        "type": "STEP_UPDATE",
                        "runId": run_id,
                        "testcaseIndex": index,
                        "step": 1,
                        "status": "DONE",
                    }
                )
                await ws_manager.send_all(
                    {
                        "type": "STEP_UPDATE",
                        "runId": run_id,
                        "testcaseIndex": index,
                        "step": 2,
                        "status": "RUNNING",
                    }
                )
                step2_start = datetime.now()
                if stop_requested():
                    await finish_aborted_run(rundetail)
                    return

                response_from_agent = await asyncio.to_thread(
                    client.chat,
                    chat_id=testcase.testcase_id,
                    prompt_list=[message_to_agent],
                )
                if stop_requested():
                    await finish_aborted_run(rundetail)
                    return

                step2_duration = (datetime.now() - step2_start).total_seconds()
                if step2_duration < 2:
                    logger.error(
                        f"Step 2 completed too fast ({step2_duration:.2f}s) — marking as FAILED"
                    )
                    await step(
                        {
                            "type": "STEP_UPDATE",
                            "runId": run_id,
                            "testcaseIndex": index,
                            "step": 2,
                            "status": "FAILED",
                        }
                    )
                    rundetail.status = "FAILED"
                    db.add_or_update_testrun_detail(rundetail)
                    continue
                await step(
                    {
                        "type": "STEP_UPDATE",
                        "runId": run_id,
                        "testcaseIndex": index,
                        "step": 2,
                        "status": "DONE",
                    }
                )
                
                data = response_from_agent.json().get("response")
                agent_response = extract_agent_response(data)

                if is_error_response(agent_response):
                    logger.error(
                        f"No response received from the agent for test case {testcase.testcase_id}."
                    )
                    rundetail.status = "FAILED"
                    db.add_or_update_testrun_detail(rundetail)
                    continue

                conv.response_ts = datetime.now().isoformat()
                conv.agent_response = agent_response
                db.add_or_update_conversation(conversation=conv)

                await step(
                    {
                        "type": "STEP_UPDATE",
                        "runId": run_id,
                        "testcaseIndex": index,
                        "step": 3,
                        "status": "DONE",
                    }
                )
                await step(
                    {
                        "type": "STEP_UPDATE",
                        "runId": run_id,
                        "testcaseIndex": index,
                        "step": 4,
                        "status": "DONE",
                    }
                )
                await step(
                    {"type": "TESTCASE_FINISHED", "runId": run_id, "current": index}
                )
                rundetail.status = "COMPLETED"
                db.add_or_update_testrun_detail(rundetail)
            except Exception as e:
                if stop_requested():
                    await finish_aborted_run(rundetail)
                    return
                logger.error(
                    f"Testcase execution failed for run {run_id}, testcase index {index}: {e}"
                )
                if rundetail is not None:
                    rundetail.status = "FAILED"
                    db.add_or_update_testrun_detail(rundetail)
                continue

        stop_watcher.set()
        run.end_ts = datetime.now().isoformat()
        run.status = "COMPLETED"

        db.add_or_update_testrun(run=run)
        await ws_manager.send_all(
            {"type": "RUN_FINISHED", "runId": run_id, "status": "COMPLETED"}
        )
        logger.info(f"🏁 Background execution finished for run {run_id}")

    except Exception as e:
        logger.error(f"Background execution failed for run {run_id}: {e}")
        run.status = "FAILED"
        run.end_ts = datetime.now().isoformat()
        db.add_or_update_testrun(run=run)
        try:
            await ws_manager.send_all(
                {
                    "type": "RUN_FINISHED",
                    "runId": run_id,
                    "status": "FAILED",
                    "error": str(e),
                }
            )
        except Exception as ws_error:
            logger.error(f"Failed to push RUN_FINISHED for failed run {run_id}: {ws_error}")
    finally:
        set_active_stop_watcher(None)
        if client is not None:
            try:
                client.close()
            except Exception as close_error:
                logger.error(f"Client close failed (IM already dead): {close_error}")
