from selenium import webdriver
from logger import get_logger
from utils import (
    DriverManager,
    load_config,
    login_app,
    logout_app,
    search_entity,
    send_message_whatsapp,
)

logger = get_logger("whatsapp_driver")

# Single DriverManager instance for WhatsApp
driver_manager = DriverManager()


def get_ui_response_whatsapp():
    return {"ui": "Whatsapp Web Chat Interface", "features": ["smart-compose", "modular-layout"]}


def login_whatsapp() -> webdriver.Chrome | None:
    """Login to WhatsApp Web using DriverManager and generic login_app."""
    cfg = load_config()
    url = cfg.get("whatsapp_url")
    try:
        driver = driver_manager.get_driver("WhatsApp Web", url)
        login_app(driver, "whatsapp_web")
        return driver
    except Exception as e:
        logger.error(f"WhatsApp Web login failed: {e}")
        return None


def logout_whatsapp(driver: webdriver.Chrome) -> bool:
    """Logout from WhatsApp Web using generic logout_app."""
    return logout_app(driver, "whatsapp_web")


def search_llm(driver: webdriver.Chrome) -> bool:
    """Search for the configured contact (LLM) in WhatsApp Web using generic search_entity."""
    return search_entity(driver, "whatsapp_web")


def send_whatsapp_message(driver: webdriver.Chrome, prompt: str) -> str:
    """Send a message to WhatsApp Web using generic send_message."""
    return send_message_whatsapp(driver, prompt)


def send_prompt_whatsapp(chat_id: int, prompt_list: list[str]) -> list[dict]:
    """Send multiple prompts to WhatsApp Web and collect responses."""
    results = []
    driver = login_whatsapp()
    if not driver:
        logger.error("Could not initialize WhatsApp Web driver.")
        return [{"chat_id": chat_id, "prompt": p, "response": "[Driver init failed]"} for p in prompt_list]

    try:
        if not search_llm(driver):
            logger.error("Could not open chat with LLM contact.")
            return [{"chat_id": chat_id, "prompt": p, "response": "[Chat not found]"} for p in prompt_list]

        for prompt in prompt_list:
            response = send_whatsapp_message(driver, prompt)
            results.append({"chat_id": chat_id, "prompt": prompt, "response": response})

    finally:
        pass  # keep driver alive for reuse

    return results


def close_whatsapp(driver: webdriver.Chrome | None = None):
    """Close WhatsApp Web session gracefully."""
    try:
        if driver:
            driver.quit()
            logger.info("Driver quit successfully.")
        driver_manager.quit()
        logger.info("WhatsApp Web session closed successfully.")
    except Exception as e:
        logger.error(f"Error closing WhatsApp Web session: {e}")
