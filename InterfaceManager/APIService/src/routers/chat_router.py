# routers/chat_router.py

from fastapi import APIRouter
import openui
import whatsapp
import json
import cpgrams

router = APIRouter()

def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

@router.post("/info")
def chat_interface():
    config = load_config()
    application_type = config.get("application_type")
    if application_type == "WHATSAPP_WEB_BROWSER":
        return whatsapp.get_ui_response()
    elif application_type == "OPEN_UI_INTERFACE":
        return openui.get_ui_response()
    elif application_type == "WEBAPP":
        return cpgrams.get_ui_response()
    else:
        return {"error": "Unknown application type"}
