# routers/common.py

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from logger import get_logger
from whatsapp import login_whatsapp, logout_whatsapp, send_prompt_whatsapp
from openui import login_openui, logout_openui, send_prompt_openui
from cpgrams import send_prompt_cpgrams
import json
from typing import List

from pydantic import BaseModel

router = APIRouter()

logger = get_logger("main")

class PromptCreate(BaseModel):
    chat_id: int
    prompt_list: List[str]

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
    elif application_type == "OPENUI":
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
    elif application_type == "OPENUI":
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
        logger.info(f"Received prompt for {application_type}")
        result = send_prompt_whatsapp(chat_id=prompt.chat_id, prompt_list=prompt.prompt_list)
        return JSONResponse(content={"response": result})
    elif application_type == "OPENUI":
        logger.info("Received prompt request for OpenUI Application.")
        result = send_prompt_openui(chat_id=prompt.chat_id, prompt_list=prompt.prompt_list)
        return JSONResponse(content={"response": result})
    elif application_type == "WEBAPP":
        logger.info("Received prompt request for WEB Application.")
        result = send_prompt_cpgrams(chat_id=prompt.chat_id, prompt_list=prompt.prompt_list)
        return JSONResponse(content={"response": result})
    else:
        result = "Application not found"
        return JSONResponse(content=result)

@router.get("/config")
def get_config():
    with open('config.json', 'r') as file:
        return json.load(file)

@router.post("/config")
async def update_config(request: Request):
    try:
        new_config = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    try:
        with open('config.json', 'w') as file:
            json.dump(new_config, file, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config: {e}")
    response = {"message": "Config updated successfully"}
    return response