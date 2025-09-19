# routers/chat_router.py

from fastapi import APIRouter
import openui
import whatsapp
import json
import webapp

router = APIRouter()

def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

@router.post("/info")
def chat_interface():
    config = load_config()
    application_type = config.get("application_type")
    if application_type == "WHATSAPP_WEB":
        return whatsapp.get_ui_response()
    elif application_type == "OPEN_UI_INTERFACE":
        return openui.get_ui_response()
    elif application_type == "WEB_APP":
        return webapp.get_ui_response()
    else:
        return {"error": "Unknown application type"}
