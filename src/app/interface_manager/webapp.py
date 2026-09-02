import threading
import time
from typing import List, Optional
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from logger import get_logger
from utils import (
    DriverManager,
    load_config,
    get_session_config,
    load_xpaths,
    is_logged_in,
    login_app,
    logout_app,
    send_message_webapp,
    selenium_pool,
    SeleniumPoolExhausted,
)

logger = get_logger("webapp_driver")

# One DriverManager (and one Chrome session) per concurrent run, keyed by
# session_key (the caller's run_id). This isolates concurrent runs' browser
# automation instead of racing all of them through a single shared Chrome tab.
# Each DriverManager is also assigned its own selenium-browser-N container
# from the shared pool, so a run's live view (/selenium/<slot>/) shows only
# that run instead of overlapping with other concurrent runs.
_driver_managers: dict[str, DriverManager] = {}
_driver_managers_lock = threading.Lock()


def get_driver_manager(session_key: Optional[str] = None) -> DriverManager:
    key = session_key or "default"
    with _driver_managers_lock:
        dm = _driver_managers.get(key)
        if dm is None:
            remote_url, _vnc_slot = selenium_pool.acquire(key)
            dm = DriverManager(profile_name=f"session_{key}", remote_url=remote_url)
            _driver_managers[key] = dm
        return dm


def get_vnc_slot(session_key: Optional[str] = None) -> Optional[str]:
    """The pool slot (matching /selenium/<slot>/) assigned to this session, if any."""
    key = session_key or "default"
    return selenium_pool.vnc_slot(key)


def get_ui_response_webapp():
    return {"ui": "Web Application Chat Interface", "features": ["smart-compose", "modular-layout"]}


def get_driver_for_session(session_key: Optional[str] = None):
    """
    Returns this session's already-running driver, if one exists, without
    launching a new browser session. Used by /logout so it doesn't spin up
    a fresh Chrome instance just to immediately log it out.
    """
    key = session_key or "default"
    with _driver_managers_lock:
        dm = _driver_managers.get(key)
    return dm.driver if dm else None


def login_webapp(app_name: str, session_key: Optional[str] = None):
    """
    Wrapper for generic login_app.
    """
    cfg = get_session_config(session_key)
    url = cfg.get("application_url", "UNKNOWN")
    driver = get_driver_manager(session_key).get_driver(app_name, url)
    return login_app(driver, app_name)


def logout_webapp(driver, app_name: str):
    """
    Wrapper for generic logout_app.
    """
    if driver is None:
        logger.info(f"No active WebApp session for {app_name} to logout.")
        return True
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


def send_prompt(app_name: str, chat_id: int, prompt_list: List[str], session_key: Optional[str] = None) -> list[dict]:
    """
    Send prompt(s) to a web application interface and collect responses.
    """
    results = []
    cfg = get_session_config(session_key)
    url = cfg.get("application_url", "UNKNOWN")
    app_name = app_name.lower()
    chat_cfg = load_xpaths()["applications"][app_name]["ChatPage"]

    driver = get_driver_manager(session_key).get_driver(app_name, url)

    # Ensure login
    # logout_cfg = load_xpaths()["applications"][app_name]["LogoutPage"]
    # logger.info("sending xpath: ", logout_cfg["send_element"])
    login_ok = is_logged_in(driver, send_element=chat_cfg["send_button_element"]) or login_webapp(app_name, session_key)
    logger.info(f"after function running xpath: {chat_cfg['send_button_element']}")
    logger.info(f"login_ok: {login_ok}")
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


def close_webapp(app_name: str, session_key: Optional[str] = None):
    """
    Gracefully close the browser session. If session_key is given, closes
    only that run's own driver; otherwise closes every tracked session
    (used only for a full service shutdown, not per-run cleanup).
    """
    try:
        logger.info(f"Closing WebApp session for {app_name} (session_key={session_key})...")
        if session_key is not None:
            with _driver_managers_lock:
                dm = _driver_managers.pop(session_key, None)
            if dm is not None:
                dm.quit()
            selenium_pool.release(session_key)
        else:
            with _driver_managers_lock:
                keys = list(_driver_managers.keys())
                managers = list(_driver_managers.values())
                _driver_managers.clear()
            for dm in managers:
                dm.quit()
            for key in keys:
                selenium_pool.release(key)
        logger.info(f"Session closed for {app_name}")
    except Exception as e:
        logger.warning(f"Driver quit issue for {app_name}: {e}")
    return True
