# routers/chat_router.py

from fastapi import APIRouter
import webapp
import whatsapp
import json
import webapp
import os, sys

router = APIRouter()

def load_config():
    path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(path, 'r') as file:
        return json.load(file)

@router.post("/info")
def chat_interface():
    config = load_config()
    application_type = config.get("application_type")
    if application_type == "WHATSAPP_WEB":
        return whatsapp.get_ui_response()
    elif application_type == "WEBAPP":
        return webapp.get_ui_response()
    else:
        return {"error": "Unknown application type"}
