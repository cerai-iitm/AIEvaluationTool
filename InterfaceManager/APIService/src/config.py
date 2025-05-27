# config.py

from pydantic_settings import BaseSettings
from enum import Enum

class AppType(str, Enum):
    WHATSAPP_WEB_BROWSER = "whatsapp_web_browser"
    OPEN_UI_INTERFACE = "open_ui_interface"

class Settings(BaseSettings):
    application_type: AppType = AppType.WHATSAPP_WEB_BROWSER
    openui_email: str = "OPENUI_EMAIL"
    openui_password: str = "OPENUI_PASSWORD"
    ollama_model_name: str = "gemma3:1b"
    whatsapp_web_model_name: str = "Gooey"
    debug: bool = True
    default_host: str = "8.8.8.8"
    default_port: int = 53 
    default_timeout: int = 3 
    ollama_server_url: str = "http://localhost:11434"
    server_url: str = "http://localhost:3000"
    server_timeout: int = 5
    retries: int = 5
    retry_delay: int = 3
    max_retry_delay: int = 60
    whatsapp_url: str = "https://web.whatsapp.com"

    class Config:
        env_file = ".env"

settings = Settings()
