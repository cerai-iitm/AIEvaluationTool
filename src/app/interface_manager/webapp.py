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
    resolve_node_vnc_address,
)

logger = get_logger("webapp_driver")

# Single DriverManager instance for WebApp
driver_manager = DriverManager(profile_name="test_profile")


def get_ui_response_webapp():
    return {"ui": "Web Application Chat Interface", "features": ["smart-compose", "modular-layout"]}


def login_webapp(app_name: str, chat_id: str = "default"):
    """
    Wrapper for generic login_app. `chat_id` selects which pooled
    browser session to use so concurrent runs stay isolated.
    """
    cfg = load_config()
    url = cfg.get("application_url", "UNKNOWN")
    driver = driver_manager.get_driver(chat_id, app_name, url)
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
    app_name = load_config().get("application_name", "UNKNOWN")
    agent_name = load_config().get("agent_name", "UNKNOWN")
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
    url = cfg.get("application_url", "UNKNOWN")
    app_name = app_name.lower()
    chat_cfg = load_xpaths()["applications"][app_name]["ChatPage"]

    driver = driver_manager.get_driver(chat_id, app_name, url)

    # Ensure login
    # logout_cfg = load_xpaths()["applications"][app_name]["LogoutPage"]
    # logger.info("sending xpath: ", logout_cfg["send_element"])
    login_ok = is_logged_in(driver, send_element=chat_cfg["send_button_element"]) or login_webapp(app_name, chat_id)
    logger.info("after function running xpath: ", chat_cfg["send_button_element"])
    logger.info("login_ok:", login_ok)
    for prompt in prompt_list:
        result = {"chat_id": chat_id, "prompt": prompt, "response": "[Not available]"}
        if login_ok:
            # replace new line characters to avoid UI issues
            # CPGRAMS treats prompts with new lines as new prompts.
            prompt = prompt.replace("\n", " ")
            prompt += "\n"  # Ensure prompt submission
            result["response"] = send_message_webapp(driver, app_name, prompt)
        results.append(result)

    return results


def get_view_path(chat_id: str) -> str | None:
    """
    Return the noVNC live-view path for the pooled session belonging to
    `chat_id`, or None if no session is currently running for it.

    This routes directly to the chrome-node running the session (via
    /vnc-proxy/?target=<node-ip>:7900) rather than through the Grid hub's
    own live-view proxy, which relies on Referer-header session matching
    that's unreliable behind a reverse proxy.
    """
    session_id = driver_manager.get_session_id(chat_id)
    if not session_id:
        return None
    target = resolve_node_vnc_address(session_id)
    if not target:
        return None
    # target ("ip:7900") goes in the path (not a query string) so that
    # noVNC's relative sub-resource/websocket requests from the loaded
    # page inherit it automatically.
    return f"/vnc-proxy/{target}/"


def close_webapp(app_name: str, chat_id: str = "default"):
    """
    Gracefully close the browser session for `chat_id`.
    """
    try:
        logger.info(f"Closing WebApp session for {app_name} (chat_id={chat_id})...")
        driver_manager.quit(chat_id)
        logger.info(f"Session closed for {app_name} (chat_id={chat_id})")
    except Exception as e:
        logger.warning(f"Driver quit issue for {app_name} (chat_id={chat_id}): {e}")
    return True
