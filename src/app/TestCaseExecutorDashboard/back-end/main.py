import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, WebSocket, BackgroundTasks,WebSocketDisconnect, Request
from fastapi.responses import FileResponse
from services.ws_manager import ws_manager 
from openpyxl import Workbook, load_workbook
import threading
from typing import Optional, List,Literal
import tempfile
import socket
import psutil
import os
import re
from urllib.parse import urlparse
# import mysql.connector
import json
import uvicorn
import asyncio
# from mysql.connector import Error
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import sys
import randomname
from collections import defaultdict
from schemas import TestRunResponse,TestRunDetailsResponse,FilterResponse,AllFiltersResponse,TestRunSummaryResponse,TestRunFullResponse,RunEvaluationSummaryResponse,EvaluationItemResponse,ConversationResponse,TestCaseResponse,FullConversationResponse, TimelineEvent,NewTestRun,ContinueRunRequest
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import datetime
from datetime import datetime
from lib.orm import DB
from lib.data import Target, Run, RunDetail, Conversation

from lib.orm.tables import TestRuns
from lib.interface_manager import InterfaceManagerClient  # Import the InterfaceManagerClient from the lib directory
from configuration.database import get_db
from configuration.database import db
from configuration.paths import (
    ROOT_CONFIG_PATH as interface_manager_config,
    profile_path,
)
from apis.testruns import router as testruns_router
from apis.filters import router as filters_router
from apis.analyse import router as analyse_router
from apis.conversations import router as conversations_router
from apis.report import router as report_router

from utils.port import check_service, ensure_interface_manager_port_running, stop_interface_manager, watch_chrome_and_kill_im, watch_im_process,on_frontend_disconnect

from middleware.auth import AuthMiddleware

# db_url = (
#             f"mysql+mysqlconnector://"
#             f"{os.getenv('DB_USER')}:"
#             f"{os.getenv('DB_PASSWORD')}@"
#             f"{os.getenv('DB_HOST')}:"
#             f"{os.getenv('DB_PORT')}/"
#             f"{os.getenv('DB_NAME')}"
#         )


## Configure DB and port connection  (using config.json for flexibility)

config_path = os.path.join(Path(__file__).resolve().parents[5], "config.json")
try:
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}


port_config = config.get("port", {})
BACKEND_PORT = int(port_config.get("back-end", 7000))


# Resolve project root (this file → importer → app → src → project_root)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))

if not os.path.exists(interface_manager_config):
    raise RuntimeError(
        f"Interface Manager config.json not found at {interface_manager_config}"
    )

back_end_root=os.path.abspath(os.path.join(os.path.dirname(__file__)))


template_path = os.path.join(
    back_end_root,
    "templates",
    "Reports.xlsx"
)

wb = load_workbook(template_path)

app = FastAPI()

app.add_middleware(AuthMiddleware)

raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
cors_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
if not cors_origins:
    cors_origins = [
        "*",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(testruns_router)
app.include_router(filters_router)
app.include_router(analyse_router)
app.include_router(conversations_router)
app.include_router(report_router)


@app.on_event("startup")
async def _start_ws_pubsub_listener():
    # Every replica must run this so WebSocket broadcasts published by
    # whichever replica is running a background task (test run/analysis)
    # reach clients connected to this replica too. See services/ws_manager.py.
    await ws_manager.start_pubsub_listener()

def load_config():
    with open(config_path , "r") as f:
        return json.load(f)

@app.websocket("/ws/test-run")
async def websocket_endpoint(websocket: WebSocket):
    
    await ws_manager.connect(websocket)
    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=15)
            except asyncio.TimeoutError:
                await ws_manager.send_one(websocket, {"type": "HEARTBEAT"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        if ws_manager.is_empty():
            on_frontend_disconnect(interface_manager_config)
    except Exception:
        ws_manager.disconnect(websocket)
        
        if ws_manager.is_empty():
            on_frontend_disconnect(interface_manager_config)
         
@app.get(
    "/testcases/{testcase_name}",
    response_model=TestCaseResponse
)
def get_conversation(testcase_name: str, plan_name: Optional[str] = None):
    
    testcase = db.get_testcase_by_name(testcase_name)
    if not testcase:
        raise HTTPException(status_code=404, detail="Testcase not found")
    if plan_name:
        plan_testcases = db.get_testcases_by_testplan(plan_name)
        if not any(case.name == testcase_name for case in plan_testcases):
            raise HTTPException(
                status_code=400,
                detail=f"Test case '{testcase_name}' does not belong to test plan '{plan_name}'",
            )
    return TestCaseResponse(
        user_prompt=testcase.prompt.user_prompt,
        system_prompt=testcase.prompt.system_prompt
    )


@app.get("/targets/{target_name}/metadata")
def get_target_metadata(target_name: str):

    clean_target_name = re.sub(
        r"\s*\(.*?\)", 
        "", 
        target_name
    ).strip()

    target = db.get_target_by_name(clean_target_name)

    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    return {
        "domains": (
            [target.target_domain]
            if isinstance(target.target_domain, str)
            else target.target_domain
        ),
        "languages": target.target_languages or []
    }

@app.get("/__dev/config")
def dev_config():
    if not os.getenv("DEV_CONFIG_ENABLED"):
        print("Dev config is disabled.")
        raise HTTPException(status_code=404)
        
    print("Accessed dev config endpoint")
    return load_config()
    
@app.post("/__dev/config")
async def update_config(request: Request):
    

    data = await request.json()

    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)

    return {"message": "Config updated"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=True
    )
