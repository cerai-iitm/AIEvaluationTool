# routers/common.py

from fastapi import APIRouter
from config import settings
from fastapi.responses import JSONResponse
from logger import get_logger
from whatsapp import login_whatsapp, logout_whatsapp, send_prompt_whatsapp
from openui import login_openui, logout_openui, send_prompt_openui

from pydantic import BaseModel

router = APIRouter()

logger = get_logger("main")

class PromptCreate(BaseModel):
    prompt_str: str

@router.get("/login")
def login():
    if settings.application_type == settings.application_type.WHATSAPP_WEB_BROWSER:
        logger.info("Received login request for Whatsapp Web Application.")
        result = login_whatsapp()
        return JSONResponse(content=result)
    elif settings.application_type == settings.application_type.OPEN_UI_INTERFACE:
        logger.info("Received login request for OpenUI Application.")
        result = login_openui(driver=None)
        return JSONResponse(content=result)
    else:
        result = "Application not found"
        return JSONResponse(content=result)

@router.get("/logout")
def logout():
    if settings.application_type == settings.application_type.WHATSAPP_WEB_BROWSER:
        logger.info("Received logout request for Whatsapp Web Application.")
        result = logout_whatsapp()
        return JSONResponse(content=result)
    elif settings.application_type == settings.application_type.OPEN_UI_INTERFACE:
        logger.info("Received logout request for OpenUI Application.")
        result = logout_openui()
        return JSONResponse(content=result)
    else:
        result = "Application not found"
        return JSONResponse(content=result)

@router.post("/chat")
async def chat(prompt: PromptCreate):
    if settings.application_type == settings.application_type.WHATSAPP_WEB_BROWSER:
        logger.info("Received prompt request for Whatsapp Web Application.")
        result = send_prompt_whatsapp(prompt=prompt.prompt_str)
        return JSONResponse(content={"response": result})
    elif settings.application_type == settings.application_type.OPEN_UI_INTERFACE:
        logger.info("Received prompt request for OpenUI Application.")
        result = send_prompt_openui(prompt=prompt.prompt_str)
        return JSONResponse(content={"response": result})
    else:
        result = "Application not found"
        return JSONResponse(content=result)

@router.get("/config")
def get_config():
    return {
        "application_type": settings.application_type,
        "debug": settings.debug,
        "default_host": settings.default_host,
        "default_port": settings.default_port,
        "default_timeout": settings.default_timeout,
        "ollama_server_url": settings.ollama_server_url,
        "server_url": settings.server_url,
        "server_timeout": settings.server_timeout,
        "retries": settings.retries,
        "retry_delay": settings.retry_delay,
        "max_retry_delay": settings.max_retry_delay,
        "whatsapp_url": settings.whatsapp_url
    }