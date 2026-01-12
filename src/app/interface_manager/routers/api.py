from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
import os

# Reuse existing implementations from common where appropriate
from . import common

router = APIRouter(prefix="/api")


def _config_path() -> str:
    return os.path.join(os.path.dirname(__file__), "../config.json")


@router.post("/login")
def api_login():
    return common.login()


@router.post("/logout")
def api_logout():
    return common.logout()


@router.get("/config")
def api_get_config():
    # Delegate to common.get_config, which reads workspace-level config
    return common.get_config()


@router.post("/config")
async def api_update_config(request: Request):
    # Delegate to common.update_config to keep single source of truth
    return await common.update_config(request)


@router.get("/evaluations")
def list_evaluations(limit: int = 20, offset: int = 0):
    """
    Placeholder for fetching evaluation data. Currently returns a static payload.
    Integrate with real storage later (DB or file-based reports).
    """
    try:
        # Example minimal structure for frontend consumption
        items = [
            {"id": 1, "name": "Sample Eval", "status": "completed"},
        ]
        return {"items": items[offset:offset + limit], "total": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


