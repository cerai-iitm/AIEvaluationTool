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
    selenium_pool,
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


def get_vnc_slot(session_key: Optional[str] = None) -> Optional[str]:
    """The pool slot (matching /selenium/<slot>/) assigned to this session, if any."""
    with _slots_lock:
        slot = _session_to_slot.get(session_key) if session_key else WHATSAPP_PROFILE_POOL[0]
    return selenium_pool.vnc_slot(slot) if slot else None


def get_driver_for_session(session_key: Optional[str] = None) -> webdriver.Chrome | None:
    """
    Returns this session's already-assigned driver, if any, without
    acquiring a pool slot or launching a new browser session. Used by
    /logout so it doesn't queue for/spin up a fresh session just to
    immediately log it out.
    """
    with _slots_lock:
        slot = _session_to_slot.get(session_key) if session_key else WHATSAPP_PROFILE_POOL[0]
    if not slot:
        return None
    with _driver_managers_lock:
        dm = _driver_managers.get(slot)
    return dm.driver if dm else None


def login_whatsapp(session_key: Optional[str] = None) -> webdriver.Chrome | None:
    """Login to WhatsApp Web using DriverManager and generic login_app."""
    cfg = get_session_config(session_key)
    url = cfg.get("whatsapp_url")
    slot = _acquire_slot(session_key) if session_key else WHATSAPP_PROFILE_POOL[0]
    try:
        driver = get_driver_manager(slot).get_driver("WhatsApp Web", url)
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


def send_prompt_whatsapp(chat_id: int, prompt_list: list[str], session_key: Optional[str] = None) -> list[dict]:
    """Send multiple prompts to WhatsApp Web and collect responses."""
    results = []
    driver = login_whatsapp(session_key)
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


def close_whatsapp(driver: webdriver.Chrome | None = None, session_key: Optional[str] = None):
    """
    Close WhatsApp Web session gracefully and release its pool slot so a
    queued session can proceed. If session_key is omitted, closes every
    tracked session (used only for a full service shutdown).
    """
    try:
        if driver:
            driver.quit()
            logger.info("Driver quit successfully.")

        if session_key is not None:
            with _slots_lock:
                slot = _session_to_slot.get(session_key)
            if slot is not None:
                with _driver_managers_lock:
                    dm = _driver_managers.pop(slot, None)
                if dm is not None:
                    dm.quit()
                selenium_pool.release(slot)
            _release_slot(session_key)
        else:
            with _driver_managers_lock:
                slots = list(_driver_managers.keys())
                managers = list(_driver_managers.values())
                _driver_managers.clear()
            for dm in managers:
                dm.quit()
            for slot in slots:
                selenium_pool.release(slot)
            with _slots_lock:
                pending_keys = list(_session_to_slot)
            for key in pending_keys:
                _release_slot(key)

        logger.info(f"WhatsApp Web session closed successfully (session_key={session_key}).")
    except Exception as e:
        logger.error(f"Error closing WhatsApp Web session: {e}")
