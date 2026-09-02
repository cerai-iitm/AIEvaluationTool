from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from whatsapp import (
    login_whatsapp,
    logout_whatsapp,
    send_prompt_whatsapp,
    close_whatsapp,
    get_ui_response_whatsapp,
    get_driver_for_session as get_whatsapp_driver_for_session,
    get_vnc_slot as get_whatsapp_vnc_slot,
)
from webapp import (
    login_webapp,
    logout_webapp,
    send_prompt,
    close_webapp,
    get_ui_response_webapp,
    get_driver_for_session as get_webapp_driver_for_session,
    get_vnc_slot as get_webapp_vnc_slot,
)

from logger import get_logger
from utils import load_config, get_session_config, set_session_config, SeleniumPoolExhausted
from context import APIRuntimeContext
from api_handler import handle_api_chat
from pydantic import BaseModel
import json
import os

router = APIRouter()
logger = get_logger("main")
config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")

# old one
# class PromptCreate(BaseModel):
#     chat_id: int
#     prompt_list: List[str]

# new one
class PromptCreate(BaseModel):
    chat_id: int
    prompt_list: List[str]
    api_context: Optional[Dict[str, Any]] = None
    session_key: Optional[str] = None


# -------------------------------
# Helpers
# -------------------------------
def get_app_info(session_key: Optional[str] = None):
    config = get_session_config(session_key)
    return config.get("application_type"), config.get("application_name")


# -------------------------------
# Login
# -------------------------------
@router.get("/login")
def login(session_key: Optional[str] = Query(None)):
    app_type, app_name = get_app_info(session_key)

    try:
        if app_type == "WHATSAPP_WEB":
            logger.info("Login request: WhatsApp Web")
            result = login_whatsapp(session_key)
            return JSONResponse(content={"result": bool(result)})

        if str.upper(app_type) == "WEBAPP":
            logger.info(f"Login request: WebApp {app_name}")
            result = login_webapp(app_name, session_key)
            return JSONResponse(content={"result": bool(result)})
    except SeleniumPoolExhausted as e:
        raise HTTPException(status_code=503, detail=str(e))

    return JSONResponse(content={"error": "Unsupported application type"})


# -------------------------------
# Logout
# -------------------------------
@router.get("/logout")
def logout(session_key: Optional[str] = Query(None)):
    app_type, app_name = get_app_info(session_key)

    if app_type == "WHATSAPP_WEB":
        logger.info(f"Logout request: WhatsApp Web (session_key={session_key})")
        driver = get_whatsapp_driver_for_session(session_key)
        result = logout_whatsapp(driver)
        return JSONResponse(content={"result": bool(result)})

    if str.upper(app_type) == "WEBAPP":
        logger.info(f"Logout request: WebApp {app_name} (session_key={session_key})")
        driver = get_webapp_driver_for_session(session_key)
        result = logout_webapp(driver, app_name)
        return JSONResponse(content={"result": bool(result)})

    return JSONResponse(content={"error": "Unsupported application type"})


# -------------------------------
# Chat
# -------------------------------
# Old one
# @router.post("/chat")
# async def chat(prompt: PromptCreate):
#     app_type, app_name = get_app_info()

#     if app_type == "WHATSAPP_WEB":
#         logger.info("Chat request: WhatsApp Web")
#         result = send_prompt_whatsapp(chat_id=prompt.chat_id, prompt_list=prompt.prompt_list)
#         return JSONResponse(content={"response": result})

#     if str.upper(app_type) == "WEBAPP":
#         logger.info(f"Chat request: WebApp {app_name}")
#         result = send_prompt(app_name=app_name, chat_id=prompt.chat_id, prompt_list=prompt.prompt_list)
#         return JSONResponse(content={"response": result})

#     return JSONResponse(content={"error": "Unsupported application type"})

# new one
# Deliberately a plain `def`, not `async def`: the branches below block for
# up to ~60s inside Selenium calls and never await anything, so declaring
# this async would serialize every concurrent request on the single event
# loop. FastAPI/Starlette runs a sync `def` route in its thread pool instead,
# which is what actually lets concurrent runs' /chat calls proceed in parallel.
@router.post("/chat")
def chat(prompt: PromptCreate):
    app_type, app_name = get_app_info(prompt.session_key)

    # ------------------------------------------------
    # WhatsApp Web (unchanged)
    # ------------------------------------------------
    if app_type == "WHATSAPP_WEB":
        logger.info("Chat request: WhatsApp Web")
        try:
            result = send_prompt_whatsapp(
                chat_id=prompt.chat_id,
                prompt_list=prompt.prompt_list,
                session_key=prompt.session_key,
            )
        except SeleniumPoolExhausted as e:
            raise HTTPException(status_code=503, detail=str(e))
        return JSONResponse(content={"response": result})

    # ------------------------------------------------
    # WebApp (unchanged)
    # ------------------------------------------------
    if str.upper(app_type) == "WEBAPP":
        logger.info(f"Chat request: WebApp {app_name}")
        try:
            result = send_prompt(
                app_name=app_name,
                chat_id=prompt.chat_id,
                prompt_list=prompt.prompt_list,
                session_key=prompt.session_key,
            )
        except SeleniumPoolExhausted as e:
            raise HTTPException(status_code=503, detail=str(e))
        return JSONResponse(content={"response": result})

    # ------------------------------------------------
    # API (NEW + IMPORTANT)
    # ------------------------------------------------
    if str.upper(app_type) == "API":
        logger.info("Chat request: API")

        if not prompt.api_context:
            raise HTTPException(
                status_code=400,
                detail="api_context is required for API application type",
            )

        # Build runtime context
        ctx = APIRuntimeContext.from_dict(prompt.api_context)

        # Execute API call (this is where logs happen)
        result = handle_api_chat(
            ctx=ctx,
            payload={
                "chat_id": prompt.chat_id,
                "prompt_list": prompt.prompt_list,
            },
        )

        return JSONResponse(content=result)

    # ------------------------------------------------
    # Unsupported
    # ------------------------------------------------
    return JSONResponse(content={"error": "Unsupported application type"})


# -------------------------------
# Close
# -------------------------------
@router.get("/close")
def close(session_key: Optional[str] = Query(None)):
    app_type, app_name = get_app_info(session_key)

    if app_type == "WHATSAPP_WEB":
        logger.info(f"Close request: WhatsApp Web (session_key={session_key})")
        close_whatsapp(session_key=session_key)
        return JSONResponse(content={"message": "WhatsApp Web closed successfully"})

    if str.upper(app_type) == "WEBAPP":
        logger.info(f"Close request: WebApp {app_name} (session_key={session_key})")
        close_webapp(app_name, session_key=session_key)
        return JSONResponse(content={"message": f"Closed WebApp {app_name}"})

    return JSONResponse(content={"error": "Unsupported application type"})


# -------------------------------
# Info
# -------------------------------
@router.post("/info")
def chat_interface(session_key: Optional[str] = Query(None)):
    app_type, _ = get_app_info(session_key)

    if app_type == "WHATSAPP_WEB":
        return get_ui_response_whatsapp()
    if str.upper(app_type) == "WEBAPP":
        return get_ui_response_webapp()

    return {"error": "Unsupported application type"}


# -------------------------------
# Selenium live-view slot
# -------------------------------
@router.get("/selenium-slot")
def selenium_slot(session_key: Optional[str] = Query(None)):
    """
    The browser-pool slot assigned to this session's live view, if a driver
    has been started for it. Frontend can build the noVNC URL from this as
    /selenium/<slot>/.
    """
    app_type, _ = get_app_info(session_key)

    if app_type == "WHATSAPP_WEB":
        slot = get_whatsapp_vnc_slot(session_key)
    elif str.upper(app_type) == "WEBAPP":
        slot = get_webapp_vnc_slot(session_key)
    else:
        slot = None

    return JSONResponse(content={"slot": slot, "path": f"/selenium/{slot}/" if slot else None})


# -------------------------------
# Config
# -------------------------------
@router.get("/config")
def get_config(session_key: Optional[str] = Query(None)):
    if session_key:
        return get_session_config(session_key)
    with open(config_path, "r") as file:
        return json.load(file)


@router.post("/config")
async def update_config(request: Request, session_key: Optional[str] = Query(None)):
    try:
        new_config = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if session_key:
        set_session_config(session_key, new_config)
        return {"message": "Session config updated successfully"}

    try:
        with open(config_path, "w") as file:
            json.dump(new_config, file, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config: {e}")

    return {"message": "Config updated successfully"}
