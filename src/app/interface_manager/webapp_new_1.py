import time
from typing import List
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from logger import get_logger
from utils import (
    DriverManager,
    load_config,
    load_xpaths,
    is_logged_in,
    login_app,
    logout_app,
    send_message_webapp,
)

logger = get_logger("webapp_driver")

# Single DriverManager instance for WebApp
driver_manager = DriverManager(profile_name="test_profile")


def get_ui_response_webapp():
    return {"ui": "Web Application Chat Interface", "features": ["smart-compose", "modular-layout"]}


def login_webapp(app_name: str):
    """
    Wrapper for generic login_app.
    """
    cfg = load_config()
    url = cfg.get("application_url")
    driver = driver_manager.get_driver(app_name, url)
    return login_app(driver, app_name)


def logout_webapp(driver, app_name: str):
    """
    Wrapper for generic logout_app.
    """
    return logout_app(driver, app_name)


def search_llm(driver):
    """
    Specific: OpenWeb-UI model search.
    """
    app_name = load_config().get("application_name")
    agent_name = load_config().get("agent_name")
    cfg = load_xpaths()["applications"]["openweb-ui"]["ChatPage"]

    try:
        if login_webapp(app_name):
            logger.info("Launched the OpenWeb-UI Interface")

            button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, cfg["model_selection_element"]))
            )
            button.send_keys(Keys.RETURN)

            time.sleep(2)
            logger.info(f"Searching for model '{agent_name}'")
            model_searching = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.ID, cfg["model_name_entry_element"]))
            )
            model_searching.send_keys(agent_name)
            model_searching.send_keys(Keys.RETURN)
            logger.info(f"'{agent_name}' selected for interaction")
            return True
        return False
    except Exception as e:
        logger.error(f"Could not find model '{agent_name}': {e}")
        return False


def send_prompt(app_name: str, chat_id: int, prompt_list: List[str]) -> list[dict]:
    """
    Send prompt(s) to a web application interface and collect responses.
    """
    results = []
    cfg = load_config()
    url = cfg.get("application_url")
    app_name = app_name.lower()

    driver = driver_manager.get_driver(app_name, url)

    # Ensure login
    logout_cfg = load_xpaths()["applications"][app_name]["LogoutPage"]
    login_ok = is_logged_in(driver, profile_element=logout_cfg["profile_element"]) or login_webapp(app_name)

    for prompt in prompt_list:
        result = {"chat_id": chat_id, "prompt": prompt, "response": "[Not available]"}
        if login_ok:
            result["response"] = send_message_webapp(driver, app_name, prompt)
        results.append(result)

    return results


def close_webapp(app_name: str):
    """
    Gracefully close the browser session.
    """
    try:
        logger.info(f"Closing WebApp session for {app_name}...")
        driver_manager.quit()
        logger.info(f"Session closed for {app_name}")
    except Exception as e:
        logger.warning(f"Driver quit issue for {app_name}: {e}")
    return True
