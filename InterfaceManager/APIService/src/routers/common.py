# routers/common.py

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from logger import get_logger
from whatsapp import login_whatsapp, logout_whatsapp, send_prompt_whatsapp
from openui import login_openui, logout_openui, send_prompt_openui
import json

from pydantic import BaseModel

router = APIRouter()

logger = get_logger("main")

class PromptCreate(BaseModel):
    prompt_str: str

def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

@router.get("/login")
def login():
    config = load_config()
    application_type = config.get("application_type")

    if application_type == "WHATSAPP_WEB":
        logger.info("Received login request for Whatsapp Web Application.")
        result = login_whatsapp()
        return JSONResponse(content=result)
    elif application_type == "OPENUI_INTERFACE":
        logger.info("Received login request for OpenUI Application.")
        result = login_openui(driver=None)
        return JSONResponse(content=result)
    else:
        result = "Application not found"
        return JSONResponse(content=result)

@router.get("/logout")
def logout():
    config = load_config()
    application_type = config.get("application_type")
    if application_type == "WHATSAPP_WEB":
        logger.info("Received logout request for Whatsapp Web Application.")
        result = logout_whatsapp()
        return JSONResponse(content=result)
    elif application_type == "OPENUI_INTERFACE":
        logger.info("Received logout request for OpenUI Application.")
        result = logout_openui()
        return JSONResponse(content=result)
    else:
        result = "Application not found"
        return JSONResponse(content=result)

@router.post("/chat")
async def chat(prompt: PromptCreate):
    config = load_config()
    application_type = config.get("application_type")
    if application_type == "WHATSAPP_WEB":
        logger.info("Received prompt request for Whatsapp Web Application.")
        result = send_prompt_whatsapp(prompt=prompt.prompt_str)
        return JSONResponse(content={"response": result})
    elif application_type == "OPENUI_INTERFACE":
        logger.info("Received prompt request for OpenUI Application.")
        result = send_prompt_openui(prompt=prompt.prompt_str)
        return JSONResponse(content={"response": result})
    else:
        result = "Application not found"
        return JSONResponse(content=result)

@router.get("/config")
def get_config():
    with open('config.json', 'r') as file:
        return json.load(file)