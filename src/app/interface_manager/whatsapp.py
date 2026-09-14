import threading
from typing import Optional
from selenium import webdriver
from logger import get_logger
from utils import (
    DriverManager,
    load_config,
    get_session_config,
    login_app,
    logout_app,
    search_entity,
    send_message_whatsapp,
    resolve_node_vnc_address,
)

logger = get_logger("whatsapp_driver")

# WhatsApp Web caps linked devices to a handful per phone number, so unlike
# the web-target DriverManager registry, concurrent WhatsApp sessions must be
# bounded to a small pool of pre-logged-in profiles. Extend this list (one
# entry per QR-logged-in WhatsApp account) to raise the concurrency ceiling.
WHATSAPP_PROFILE_POOL = ["test_profile"]

_pool_semaphore = threading.Semaphore(len(WHATSAPP_PROFILE_POOL))
_free_slots = list(WHATSAPP_PROFILE_POOL)
_session_to_slot: dict[str, str] = {}
_slots_lock = threading.Lock()

_driver_managers: dict[str, DriverManager] = {}
_driver_managers_lock = threading.Lock()


def _acquire_slot(session_key: str) -> str:
    """Assigns a pool profile slot to this session, queueing if all are busy."""
    with _slots_lock:
        existing = _session_to_slot.get(session_key)
        if existing:
            return existing

    _pool_semaphore.acquire()
    with _slots_lock:
        slot = _free_slots.pop()
        _session_to_slot[session_key] = slot
    logger.info(f"WhatsApp session '{session_key}' assigned pool slot '{slot}'")
    return slot


def _release_slot(session_key: str):
    with _slots_lock:
        slot = _session_to_slot.pop(session_key, None)
        if slot:
            _free_slots.append(slot)
    if slot:
        _pool_semaphore.release()
        logger.info(f"WhatsApp session '{session_key}' released pool slot '{slot}'")


def get_driver_manager(slot: str) -> DriverManager:
    with _driver_managers_lock:
        dm = _driver_managers.get(slot)
        if dm is None:
            remote_url, _vnc_slot = selenium_pool.acquire(slot)
            dm = DriverManager(profile_name=slot, remote_url=remote_url)
            _driver_managers[slot] = dm
        return dm


def get_ui_response_whatsapp():
    return {"ui": "Whatsapp Web Chat Interface", "features": ["smart-compose", "modular-layout"]}


def login_whatsapp(session_key: str = "default") -> webdriver.Chrome | None:
    """Login to WhatsApp Web using DriverManager and generic login_app.

    `session_key` (the run_id) selects the pooled browser session — every
    test case in a run reuses the same session, so the QR-code scan only
    has to happen once per run, not once per test case.

    NOTE: WhatsApp Web only allows a WhatsApp account to be linked as a
    device on a small, fixed number of browsers at once (WhatsApp's own
    linked-devices limit). Pooling sessions here does not bypass that —
    true concurrency for WHATSAPP_WEB is capped by WhatsApp itself, not by
    this code — but reusing one session per run keeps concurrent RUNS
    within that limit instead of burning a slot per test case.
    """
    cfg = load_config()
    url = cfg.get("whatsapp_url")
    slot = _acquire_slot(session_key) if session_key else WHATSAPP_PROFILE_POOL[0]
    try:
        driver = driver_manager.get_driver(session_key, "WhatsApp Web", url)
        login_app(driver, "whatsapp_web")
        return driver
    except Exception as e:
        logger.error(f"WhatsApp Web login failed: {e}")
        return None


def logout_whatsapp(driver: Optional[webdriver.Chrome] = None) -> bool:
    """Logout from WhatsApp Web using generic logout_app."""
    if driver is None:
        logger.info("No active WhatsApp Web driver to logout.")
        return True
    return logout_app(driver, "whatsapp_web")


def search_llm(driver: webdriver.Chrome) -> bool:
    """Search for the configured contact (LLM) in WhatsApp Web using generic search_entity."""
    return search_entity(driver, "whatsapp_web")


def send_whatsapp_message(driver: webdriver.Chrome, prompt: str) -> str:
    """Send a message to WhatsApp Web using generic send_message."""
    return send_message_whatsapp(driver, prompt)


def send_prompt_whatsapp(chat_id: int, prompt_list: list[str], session_key: str = None) -> list[dict]:
    """Send multiple prompts to WhatsApp Web and collect responses.

    `session_key` (typically the run_id) selects the pooled browser
    session; falls back to `chat_id` if not given, for backward
    compatibility.
    """
    results = []
    key = session_key if session_key is not None else str(chat_id)
    driver = login_whatsapp(key)
    if not driver:
        logger.error("Could not initialize WhatsApp Web driver.")
        return [{"chat_id": chat_id, "prompt": p, "response": "No response received"} for p in prompt_list]

    try:
        if not search_llm(driver):
            logger.error("Could not open chat with LLM contact.")
            return [{"chat_id": chat_id, "prompt": p, "response": "No response received"} for p in prompt_list]

        for prompt in prompt_list:
            response = send_whatsapp_message(driver, prompt)
            results.append({"chat_id": chat_id, "prompt": prompt, "response": response})

    finally:
        pass  # keep driver alive for reuse

    return results


def get_view_path(session_key: str) -> str | None:
    """
    Return the noVNC live-view path for the pooled session belonging to
    `session_key` (the run_id), or None if no session is currently running
    for it.

    Routes directly to the chrome-node running the session rather than
    through the Grid hub's Referer-dependent live-view proxy.
    """
    session_id = driver_manager.get_session_id(session_key)
    if not session_id:
        return None
    target = resolve_node_vnc_address(session_id)
    if not target:
        return None
    return f"/vnc-proxy/{target}/"


def close_whatsapp(driver: webdriver.Chrome | None = None, session_key: str = "default"):
    """Close WhatsApp Web session gracefully."""
    try:
        if driver:
            driver.quit()
            logger.info("Driver quit successfully.")
        driver_manager.quit(session_key)
        logger.info("WhatsApp Web session closed successfully.")
    except Exception as e:
        logger.error(f"Error closing WhatsApp Web session: {e}")
