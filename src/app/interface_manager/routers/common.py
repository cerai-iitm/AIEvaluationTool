from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from logger import get_logger
from whatsapp import login_whatsapp, logout_whatsapp, send_prompt_whatsapp, close_whatsapp, get_ui_response_whatsapp
from webapp_new import send_prompt, login_webapp, logout_webapp, close_webapp, get_ui_response_webapp
import json
from typing import List
import os
from pydantic import BaseModel

router = APIRouter()
logger = get_logger("main")


class PromptCreate(BaseModel):
    chat_id: int
    prompt_list: List[str]


def load_config():
    with open(os.path.join(os.path.dirname(__file__), "../config.json"), "r") as file:
        return json.load(file)


# -------------------------------
# Login
# -------------------------------
@router.get("/login")
def login():
    config = load_config()
    application_type = config.get("application_type")
    application_name = config.get("application_name")

    match application_type:
        case "WHATSAPP_WEB":
            logger.info("Received login request for Whatsapp Web Application.")
            result = login_whatsapp()
            return JSONResponse(content=result)

        case "WEBAPP":
            logger.info(f"Received login request for Web App: {application_name}")
            result = login_webapp(driver=None ,app_name=application_name)
            return JSONResponse(content={"result": result})

        case _:
            return JSONResponse(content={"error": "Application not found"})


# -------------------------------
# Logout
# -------------------------------
@router.get("/logout")
def logout():
    config = load_config()
    application_type = config.get("application_type")
    application_name = config.get("application_name")

    match application_type:
        case "WHATSAPP_WEB":
            logger.info("Received logout request for Whatsapp Web Application.")
            result = logout_whatsapp()
            return JSONResponse(content=result)

        case "WEBAPP":
            logger.info(f"Received logout request for Web App: {application_name}")
            result = logout_webapp(driver=None, app_name=application_name)
            return JSONResponse(content={"result": result})

        case _:
            return JSONResponse(content={"error": "Application not found"})


# -------------------------------
# Chat
# -------------------------------
@router.post("/chat")
async def chat(prompt: PromptCreate):
    config = load_config()
    application_type = config.get("application_type")
    application_name = config.get("application_name")

    match application_type:
        case "WHATSAPP_WEB":
            logger.info(f"Received prompt for {application_type}")
            result = send_prompt_whatsapp(chat_id=prompt.chat_id, prompt_list=prompt.prompt_list)
            return JSONResponse(content={"response": result})

        case "WEBAPP":
            logger.info(f"Received prompt request for Web App: {application_name}")
            result = send_prompt(app_name=application_name, chat_id=prompt.chat_id, prompt_list=prompt.prompt_list)
            return JSONResponse(content={"response": result})

        case _:
            return JSONResponse(content={"error": "Application not found"})


# -------------------------------
# Close
# -------------------------------
@router.get("/close")
def close():
    config = load_config()
    application_type = config.get("application_type")
    application_name = config.get("application_name")

    match application_type:
        case "WHATSAPP_WEB":
            logger.info("Received close request for Whatsapp Web Application.")
            close_whatsapp()
            return JSONResponse(content={"message": "Whatsapp Web closed successfully"})

        case "WEBAPP":
            logger.info(f"Received close request for Web App: {application_name}")
            close_webapp(app_name=application_name)
            return JSONResponse(content={"message": f"Closed Web App {application_name}"})

        case _:
            return JSONResponse(content={"error": "Application not found"})


@router.post("/info")
def chat_interface():
    config = load_config()
    application_type = config.get("application_type")

    match application_type:
        case "WHATSAPP_WEB":
            return get_ui_response_whatsapp()
        case "WEBAPP":
            return get_ui_response_webapp()
        case _:
            return {"error": "Unknown application type"}

# -------------------------------
# Config API
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
