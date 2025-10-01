from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from logger import get_logger
from whatsapp import (
    login_whatsapp,
    logout_whatsapp,
    send_prompt_whatsapp,
    close_whatsapp,
    get_ui_response_whatsapp,
)
from webapp import (
    login_webapp,
    logout_webapp,
    send_prompt,
    close_webapp,
    get_ui_response_webapp,
)
from utils import load_config
from typing import List
from pydantic import BaseModel
import json

router = APIRouter()
logger = get_logger("main")


class PromptCreate(BaseModel):
    chat_id: int
    prompt_list: List[str]


# -------------------------------
# Helpers
# -------------------------------
def get_app_info():
    config = load_config()
    return config.get("application_type"), config.get("application_name")


# -------------------------------
# Login
# -------------------------------
@router.get("/login")
def login():
    app_type, app_name = get_app_info()

    if app_type == "WHATSAPP_WEB":
        logger.info("Login request: WhatsApp Web")
        result = login_whatsapp()
        return JSONResponse(content={"result": bool(result)})

    if app_type == "WEBAPP":
        logger.info(f"Login request: WebApp {app_name}")
        result = login_webapp(app_name)
        return JSONResponse(content={"result": bool(result)})

    return JSONResponse(content={"error": "Unsupported application type"})


# -------------------------------
# Logout
# -------------------------------
@router.get("/logout")
def logout():
    app_type, app_name = get_app_info()

    if app_type == "WHATSAPP_WEB":
        logger.info("Logout request: WhatsApp Web")
        result = logout_whatsapp()
        return JSONResponse(content={"result": bool(result)})

    if app_type == "WEBAPP":
        logger.info(f"Logout request: WebApp {app_name}")
        result = logout_webapp(app_name)
        return JSONResponse(content={"result": bool(result)})

    return JSONResponse(content={"error": "Unsupported application type"})


# -------------------------------
# Chat
# -------------------------------
@router.post("/chat")
async def chat(prompt: PromptCreate):
    app_type, app_name = get_app_info()

    if app_type == "WHATSAPP_WEB":
        logger.info("Chat request: WhatsApp Web")
        result = send_prompt_whatsapp(chat_id=prompt.chat_id, prompt_list=prompt.prompt_list)
        return JSONResponse(content={"response": result})

    if app_type == "WEBAPP":
        logger.info(f"Chat request: WebApp {app_name}")
        result = send_prompt(app_name=app_name, chat_id=prompt.chat_id, prompt_list=prompt.prompt_list)
        return JSONResponse(content={"response": result})

    return JSONResponse(content={"error": "Unsupported application type"})


# -------------------------------
# Close
# -------------------------------
@router.get("/close")
def close():
    app_type, app_name = get_app_info()

    if app_type == "WHATSAPP_WEB":
        logger.info("Close request: WhatsApp Web")
        close_whatsapp()
        return JSONResponse(content={"message": "WhatsApp Web closed successfully"})

    if app_type == "WEBAPP":
        logger.info(f"Close request: WebApp {app_name}")
        close_webapp(app_name)
        return JSONResponse(content={"message": f"Closed WebApp {app_name}"})

    return JSONResponse(content={"error": "Unsupported application type"})


# -------------------------------
# Info
# -------------------------------
@router.post("/info")
def chat_interface():
    app_type, _ = get_app_info()

    if app_type == "WHATSAPP_WEB":
        return get_ui_response_whatsapp()
    if app_type == "WEBAPP":
        return get_ui_response_webapp()

    return {"error": "Unsupported application type"}


# -------------------------------
# Config
# -------------------------------
@router.get("/config")
def get_config():
    with open("config.json", "r") as file:
        return json.load(file)


@router.post("/config")
async def update_config(request: Request):
    try:
        new_config = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        with open("config.json", "w") as file:
            json.dump(new_config, file, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config: {e}")

    return {"message": "Config updated successfully"}
