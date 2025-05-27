# routers/chat_router.py

from fastapi import APIRouter
from config import settings, AppType
import openui
import whatsapp

router = APIRouter()

@router.post("/info")
def chat_interface():
    if settings.application_type == AppType.WHATSAPP_WEB_BROWSER:
        return whatsapp.get_ui_response()
    elif settings.application_type == AppType.OPEN_UI_INTERFACE:
        return openui.get_ui_response()
    else:
        return {"error": "Unknown application type"}
