import os
import time
import json
import socket
import psutil
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
    InvalidElementStateException
)
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import traceback

from logger import get_logger


logger = get_logger("interface_manager")


# --------------------------------------------------------------------
# Driver Management
# --------------------------------------------------------------------
class DriverManager:
    """
    Manage a Selenium Chrome WebDriver instance with profile isolation.
    Ensures reuse if alive, otherwise restarts with clean profile.
    """

    def __init__(self, profile_name: str = "test_profile"):
        self.profile_folder_path = os.path.join(os.path.expanduser("~"), profile_name)
        self.driver: webdriver.Chrome | None = None

    def get_driver(self, app_name: str, url: str) -> webdriver.Chrome:
        """
        Returns a cached driver if alive, otherwise creates a new one.
        """
        if self.driver and self._is_alive():
            logger.info(f"Reusing existing Chrome session for {app_name}")
            return self.driver

        self.close_chrome_with_profile()

        logger.info(f"Launching {app_name} at {url}")
        opts = Options()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--start-maximized")
        opts.add_argument(f"user-data-dir={self.profile_folder_path}")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=opts)
            self.driver.get(url)
            logger.info(f"Driver ready for {app_name}")
            return self.driver
        except WebDriverException as e:
            logger.error(f"Failed to start Chrome for {app_name}: {e}")
            self.driver = None
            raise

    def _is_alive(self) -> bool:
        """Check if the cached driver is still valid."""
        try:
            _ = self.driver.title
            return True
        except Exception:
            return False

    def close_chrome_with_profile(self) -> bool:
        """Kill any Chrome process using this profile."""
        closed_any = False
        for proc in psutil.process_iter(["name", "cmdline"]):
            try:
                if "chrome" in (proc.info["name"] or "").lower():
                    cmdline = " ".join(proc.info["cmdline"] or [])
                    if f"user-data-dir={self.profile_folder_path}" in cmdline:
                        proc.kill()
                        closed_any = True
                        logger.info(f"Killed Chrome with profile {self.profile_folder_path}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return closed_any

    def quit(self):
        """Cleanly quit the driver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Driver quit successfully")
            except Exception as e:
                logger.warning(f"Error while quitting driver: {e}")
            finally:
                self.driver = None


# --------------------------------------------------------------------
# Config Loaders
# --------------------------------------------------------------------
def load_config() -> dict:
    with open(os.path.join(os.path.dirname(__file__), "config.json"), "r") as file:
        return json.load(file)


def load_xpaths() -> dict:
    with open(os.path.join(os.path.dirname(__file__), "xpaths.json"), "r") as file:
        return json.load(file)


def load_creds() -> dict:
    with open(os.path.join(os.path.dirname(__file__), "credentials.json"), "r") as file:
        return json.load(file)


# --------------------------------------------------------------------
# Connectivity Helpers
# --------------------------------------------------------------------
# --------------------------------------------------------------------
# Connectivity Helpers (Improved)
# --------------------------------------------------------------------
import requests

def is_connected(test_url: str = "https://www.google.com", timeout: int = 5) -> bool:
    """Check internet connectivity using HTTPS GET (more reliable than raw sockets)."""
    try:
        r = requests.get(test_url, timeout=timeout)
        return r.status_code == 200
    except requests.RequestException as ex:
        logger.error(f"HTTP connectivity check failed: {ex}")
        return False


def check_selenium_internet(driver, test_url: str = "https://www.google.com") -> bool:
    """Validate connectivity from inside the Selenium browser itself."""
    try:
        driver.get(test_url)
        title = driver.title or ""
        return "Google" in title or "google" in title.lower()
    except Exception as e:
        logger.error(f"Selenium browser connectivity check failed: {e}")
        return False


def check_and_recover_connection(driver=None) -> bool:
    """
    Unified connectivity check:
    1. Try Python requests.
    2. If Selenium driver provided, try inside the browser.
    3. Retry with exponential backoff.
    """
    if is_connected():
        logger.info("Device is connected to the internet (requests).")
        return True

    if driver and check_selenium_internet(driver):
        logger.info("Device has internet via Selenium browser.")
        return True

    delay, max_attempts, max_delay = 3, 5, 60
    for attempt in range(1, max_attempts + 1):
        logger.warning(f"Connectivity lost. Attempt {attempt}/{max_attempts} - retrying in {delay}s...")
        time.sleep(delay)

        if is_connected():
            logger.info("Recovered connectivity (requests).")
            return True
        if driver and check_selenium_internet(driver):
            logger.info("Recovered connectivity via Selenium browser.")
            return True

        delay = min(delay * 2, max_delay)

    logger.error("Device remains disconnected after all retry attempts.")
    return False


def retry_on_internet(max_attempts: int = 5, initial_delay: int = 3, max_delay: int = 60) -> bool:
    """Retry internet connectivity check with backoff."""
    delay = initial_delay
    logger.info("Checking internet connectivity...")
    for attempt in range(1, max_attempts + 1):
        if is_connected():
            logger.info("Device is connected to the internet.")
            return True
        logger.warning(f"Attempt {attempt}/{max_attempts}. Retrying in {delay}s...")
        time.sleep(delay)
        delay = min(delay * 2, max_delay)
    logger.error("Device remains disconnected after all retry attempts.")
    return False


# --------------------------------------------------------------------
# UI Helpers
# --------------------------------------------------------------------
def is_logged_in(driver: webdriver.Chrome, profile_element: str) -> bool:
    """Check if a user is logged in by verifying presence of a profile element."""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, profile_element))
        )
        return True
    except Exception:
        return False


def safe_click(driver: webdriver.Chrome, selector: str, retries: int = 3, wait_time: int = 10) -> bool:
    """Safely click an element with retries and wait conditions."""
    by_type = By.XPATH if selector.strip().startswith(("/", "(")) else By.CSS_SELECTOR

    for attempt in range(retries):
        try:
            logger.debug(f"Attempt {attempt + 1}: Locating element ({by_type}) {selector}")
            element = WebDriverWait(driver, wait_time).until(
                EC.element_to_be_clickable((by_type, selector))
            )
            element.click()
            logger.debug(f"Clicked element ({by_type}) {selector}")
            return True
        except (StaleElementReferenceException, TimeoutException) as e:
            logger.warning(f"Retrying due to {type(e).__name__} for selector {selector}")
            time.sleep(1)
        except WebDriverException as e:
            logger.error(f"WebDriver error during click: {e}")
            break
    return False


# --------------------------------------------------------------------
# Server Helpers
# --------------------------------------------------------------------
def is_server_running(url: str | None = None, timeout: int | None = None) -> bool:
    """Check if a server is reachable and responding."""
    config = load_config()
    url = url or config.get("server_url")
    timeout = timeout or config.get("server_timeout")

    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"Server unreachable at {url}: {e}")
        return False


def wait_for_server(
    url: str | None = None,
    retries: int | None = None,
    delay: int | None = None,
    max_delay: int | None = None,
    on_retry_callback=None,
) -> bool:
    """Retry until server responds or attempts exhausted."""
    config = load_config()

    url = url or config.get("server_url")
    retries = retries if retries is not None else config.get("retries", 5)
    delay = delay if delay is not None else config.get("retry_delay", 3)
    max_delay = max_delay if max_delay is not None else config.get("max_retry_delay", 60)

    current_delay = delay
    for attempt in range(1, retries + 1):
        if is_server_running(url=url, timeout=config.get("default_timeout", 10)):
            logger.info(f"Server at {url} is up.")
            return True

        logger.warning(f"Attempt {attempt}/{retries}: Server not responding. Retrying in {current_delay}s...")
        if on_retry_callback:
            on_retry_callback(attempt, retries, current_delay)

        time.sleep(current_delay)
        current_delay = min(current_delay * 2, max_delay)

    logger.error(f"Server at {url} is not reachable after {retries} attempts.")
    return False

# --------------------------------------------------------------------
# Generic App Helpers (Login / Logout / Search / Send Message)
# --------------------------------------------------------------------
def login_app(driver: webdriver.Chrome, app_name: str) -> bool:
    """
    Generic login flow for apps that define a LoginPage in xpaths.json.
    Uses credentials.json for username/password.
    """
    try:
        app_cfg = load_xpaths()["applications"][app_name.lower()]
        login_cfg = app_cfg.get("LoginPage")
        logout_cfg = app_cfg.get("LogoutPage")
        cred_cfg = load_creds()["applications"].get(app_name.lower(), {})

        if not login_cfg:
            logger.info(f"{app_name} has no LoginPage config → skipping login")
            return True

        # Already logged in?
        if logout_cfg and is_logged_in(driver, logout_cfg.get("profile_element", "")):
            logger.info(f"Already logged in to {app_name.upper()}")
            return True

        # Perform login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, login_cfg["email_input_element"]))
        ).send_keys(cred_cfg["username"])

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, login_cfg["password_input_element"]))
        ).send_keys(cred_cfg["password"])

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, login_cfg["login_button_element"]))
        ).click()

        logger.info(f"Login successful for {app_name.upper()}")
        return True

    except Exception as e:
        logger.error(f"{app_name.upper()} login failed: {e}")
        return False


def logout_app(driver: webdriver.Chrome, app_name: str) -> bool:
    """
    Generic logout flow for apps that define a LogoutPage in xpaths.json.
    """
    try:
        app_cfg = load_xpaths()["applications"][app_name.lower()]
        logout_cfg = app_cfg.get("LogoutPage") or app_cfg.get("ChatPage")

        if not logout_cfg:
            logger.info(f"{app_name} has no LogoutPage config → skipping logout")
            return True

        safe_click(driver, logout_cfg["profile_element"])
        safe_click(driver, logout_cfg["logout_button_element"])

        logger.info(f"Logout successful for {app_name.upper()}")
        return True
    except Exception as e:
        logger.error(f"{app_name.upper()} logout failed: {e}")
        return False


def search_entity(driver: webdriver.Chrome, app_name: str) -> bool:
    """
    Generic search (contact, model, etc.) based on ChatPage config.
    Uses agent_name from config.json.
    """
    cfg = load_config()
    app_cfg = load_xpaths()["applications"][app_name.lower()]
    chat_cfg = app_cfg["ChatPage"]
    entity_name = cfg.get("agent_name")

    try:
        search_input_xpath = chat_cfg.get("contact_search_element") or chat_cfg.get("model_name_entry_element")
        if not search_input_xpath:
            logger.info(f"{app_name} has no search element → skipping search")
            return True

        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, search_input_xpath))
        )
        search_box.clear()
        search_box.send_keys(entity_name)
        search_box.send_keys(Keys.RETURN)

        logger.info(f"{app_name}: '{entity_name}' search successful")
        return True
    except Exception as e:
        logger.error(f"{app_name}: search failed for '{entity_name}': {e}")
        return False

def split_message(message, max_length=1000):
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]

def send_message_whatsapp(driver: webdriver.Chrome, prompt: str):
    """
    Sends a prompt to WhatsApp Web and retrieves responses after the last sent message.
    """
    attempt = 0
    max_retries: int = 3
    app_name = load_config().get("application_type")
    app_cfg = load_xpaths()["applications"][app_name.lower()]
    chat_cfg = app_cfg["ChatPage"]

    while attempt < max_retries:
        try:
            if not check_and_recover_connection():
                return "Failed: Internet unavailable"
            
            logger.info(f"Sending prompt to the bot: {prompt}")
            # @bugfix.  The XPath has changed! -- Sudar 02.08.2025
            #message_box_xpath = '//div[@aria-label="Type a message" and @contenteditable="true"]'
            message_box_xpath = chat_cfg["prompt_input_box_element"]
            message_box = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, message_box_xpath))
            )
            message_box.clear()
            message_box.click()
            chunks = split_message(prompt)
            
            for chunk in chunks:
                message_box.send_keys(chunk)
                message_box.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(0.5)
            message_box.send_keys(Keys.RETURN)

            #time.sleep(5)  # Wait for the message to be sent and responses to arrive
            old_response_texts = []
            response_texts = []

            # setup the wait time counter.
            wait_time = 0 # seconds

            # wait for the responses from the agent for a maximum of 30 seconds
            while "".join(old_response_texts) != "".join(response_texts) or len(response_texts) == 0:
                if wait_time > 30:
                    logger.warning("No new responses received after 30 seconds. Exiting response retrieval loop.")
                    break
                time.sleep(2)  # Wait for responses to appear
                wait_time += 2

                wait = WebDriverWait(driver, 30)
                message_in = chat_cfg["message_in_element"]
                message_out = chat_cfg["message_out_element"]
                all_messages = wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, f"{message_in}, {message_out}")
                    )
                )
                
                outgoing_msgs = driver.find_elements(By.CSS_SELECTOR, message_out)
                if not outgoing_msgs:
                    raise Exception("No outgoing messages found.")

                last_outgoing = outgoing_msgs[-1]

                try:
                    last_index = next(
                        i for i, msg in enumerate(all_messages) if msg == last_outgoing
                    )
                except StopIteration:
                    raise Exception(
                        "Last outgoing message not found in all_messages list."
                    )

                responses_after = all_messages[last_index + 1:]
                responses = [
                    msg
                    for msg in responses_after
                    if "message-in" in str(msg.get_attribute("class"))
                ]

                old_response_texts = response_texts.copy()
                response_texts = []
                selectable_text = chat_cfg["agent_response_element"]
                for msg in responses:
                    try:
                        text_elem = msg.find_element(By.CSS_SELECTOR, selectable_text)
                        text = text_elem.text.strip()
                        if text:
                            response_texts.append(text)
                            logger.info(f"(Waited:{wait_time}) Received response from WhatsApp: %s", text)
                    except Exception as e:
                        logger.debug("Could not read response message: %s", e)
                        continue

            if response_texts:
                combined_response = " ".join(response_texts)
                return combined_response
            else:
                logger.warning("No response message found.")
                return ["No response received"]

        except Exception as e:
            attempt += 1
            logger.error(f"Chat attempt {attempt} failed: {e}")
            if attempt < max_retries:
                logger.info("Retrying chat...")
                time.sleep(0.3)
            else:
                return ["Error during chat after retries"]

def send_message_webapp(
    driver: webdriver.Chrome,
    app_name: str,
    prompt: str,
    max_retries: int = 3,
    response_timeout: float = 30.0,
    stability_window: float = 1.5,
    poll_interval: float = 0.5,
    send_button_xpath: str | None = None,  # optional: prefer click if UI uses a send button
) -> str:
    """
    Robust send-and-wait that detects both appended responses and in-place updates.
    Returns only the single final response message (most-recent changed/added element).
    """

    app_cfg = load_xpaths()["applications"][app_name.lower()]
    chat_cfg = app_cfg["ChatPage"]

    input_xpath    = chat_cfg.get("prompt_input_box_element")
    response_xpath = chat_cfg.get("agent_response_element")

    if not input_xpath or not response_xpath:
        logger.error(f"{app_name} ChatPage config incomplete: {chat_cfg}")
        return "[Error: Invalid ChatPage config]"

    # --- helpers (ensure interactable, clear, type) ---
    def _ensure_input_interactable(timeout=10):
        box = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, input_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", box)
        for _ in range(4):
            try:
                box.click()
                return box
            except (WebDriverException, InvalidElementStateException):
                try:
                    driver.execute_script("arguments[0].focus();", box)
                except Exception:
                    pass
                time.sleep(0.2)
        try:
            ActionChains(driver).move_to_element(box).click().perform()
            return box
        except Exception as e:
            raise TimeoutException(f"Input element not interactable: {e}")

    def _clear_input(box) -> bool:
        try:
            box.clear()
            time.sleep(0.08)
            val = (box.get_attribute("value") or "").strip()
            contenteditable = box.get_attribute("contenteditable")
            inner = ""
            if contenteditable == "true" or not val:
                inner = (box.get_attribute("innerText") or box.get_attribute("textContent") or "").strip()
            if val == "" and (contenteditable != "true" or inner == ""):
                return True
        except Exception:
            pass
        # JS fallback
        try:
            driver.execute_script(
                "arguments[0].value = ''; arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                box,
            )
            time.sleep(0.06)
            val = (box.get_attribute("value") or "").strip()
            inner = (box.get_attribute("innerText") or box.get_attribute("textContent") or "").strip()
            if val == "" and inner == "":
                return True
        except Exception:
            pass
        try:
            driver.execute_script(
                "arguments[0].innerText = ''; arguments[0].textContent = ''; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));",
                box,
            )
            time.sleep(0.06)
            inner = (box.get_attribute("innerText") or box.get_attribute("textContent") or "").strip()
            if inner == "":
                return True
        except Exception:
            pass
        logger.debug("Unable to fully clear input element prior to sending.")
        return False

    def _type_into_input(box, text):
        try:
            for chunk in split_message(text):
                box.send_keys(chunk)
                box.send_keys(Keys.SHIFT + Keys.RETURN)
                time.sleep(0.15)
            # final Enter -- if UI has a send button we will click it instead later
            box.send_keys(Keys.RETURN)
            return
        except (InvalidElementStateException, WebDriverException) as e:
            logger.debug(f"send_keys failed, falling back to JS. Error: {e}")
            try:
                set_js = (
                    "arguments[0].value = arguments[1];"
                    "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));"
                )
                driver.execute_script(set_js, box, text)
                ActionChains(driver).move_to_element(box).send_keys(Keys.RETURN).perform()
                return
            except Exception as e2:
                logger.error(f"Fallback JS typing failed: {e2}")
                raise

    # --- element snapshot helpers (index-aware) ---
    def _snapshot_texts() -> list[str]:
        """Return current list of element texts (stripped) for all matched response elements."""
        try:
            elems = driver.find_elements(By.XPATH, response_xpath)
        except Exception:
            return []
        texts = []
        for el in elems:
            try:
                texts.append((el.text or "").strip())
            except StaleElementReferenceException:
                texts.append("")  # conservative fallback
        return texts

    def _find_changed_index(pre_list: list[str], cur_list: list[str]) -> int | None:
        """
        Return the index of the first changed element (text differs) OR index of first appended element.
        If nothing changed, return None.
        """
        # appended?
        if len(cur_list) > len(pre_list):
            return len(cur_list) - 1
        # changed in-place?
        common = min(len(pre_list), len(cur_list))
        for i in range(common):
            if pre_list[i] != cur_list[i]:
                return i
        return None

    def _wait_for_change_and_stability(pre_snapshot: list[str]) -> str | None:
        """
        Wait until a change is detected (append or in-place update) and then wait for it to stabilize.
        Returns the stable text of the changed/added element, or None on timeout.
        """
        start_time = time.time()
        # Phase 1: wait for any change
        changed_index = None
        cur_snapshot = pre_snapshot
        while time.time() - start_time < response_timeout:
            cur_snapshot = _snapshot_texts()
            changed_index = _find_changed_index(pre_snapshot, cur_snapshot)
            if changed_index is not None:
                logger.debug(f"[{app_name}] Detected change at index {changed_index} (pre_count={len(pre_snapshot)} cur_count={len(cur_snapshot)})")
                break
            time.sleep(poll_interval)

        if changed_index is None:
            return None

        # Phase 2: wait for stability of that element's text
        last_text = cur_snapshot[changed_index] if changed_index < len(cur_snapshot) else ""
        last_change = time.time()
        while time.time() - start_time < response_timeout:
            time.sleep(poll_interval)
            cur_snapshot = _snapshot_texts()
            # if changed_index disappeared, try to treat last element as the target
            if changed_index >= len(cur_snapshot):
                # element removed? return most-recent last element if present
                if cur_snapshot:
                    candidate = cur_snapshot[-1]
                else:
                    candidate = last_text
            else:
                candidate = cur_snapshot[changed_index]

            if candidate != last_text:
                last_text = candidate
                last_change = time.time()
                logger.debug(f"[{app_name}] Change detected; waiting for stability. New text len={len(last_text)}")
                continue

            # unchanged since last poll -> check stability window
            if time.time() - last_change >= stability_window:
                return last_text.strip()
        # timed out, return last seen
        return last_text.strip()

    # -------------- main retry loop -------------- #
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            if not check_and_recover_connection(driver):
                return "[Failed: Internet unavailable]"

            logger.info(f"[{app_name}] Attempt {attempt}: preparing to send prompt.")

            # Baseline snapshot BEFORE sending (index-aware)
            pre_snapshot = _snapshot_texts()
            logger.debug(f"[{app_name}] pre_snapshot count={len(pre_snapshot)}; preview={pre_snapshot[-1] if pre_snapshot else None}")

            # Ensure input is interactable and cleared before every attempt
            box = _ensure_input_interactable(timeout=12)
            cleared = _clear_input(box)
            if not cleared:
                logger.debug(f"[{app_name}] input not verified cleared (attempt {attempt}); proceeding anyway.")

            # Type the prompt (primary) and optionally click send-button if provided
            _type_into_input(box, prompt)
            if send_button_xpath:
                try:
                    btn = driver.find_element(By.XPATH, send_button_xpath)
                    if btn.is_displayed() and btn.is_enabled():
                        btn.click()
                        logger.debug(f"[{app_name}] Clicked send button.")
                except Exception as e:
                    logger.debug(f"[{app_name}] send_button click failed: {e}")

            # Wait for any change (append or update) and for it to stabilize
            final_text = _wait_for_change_and_stability(pre_snapshot)
            if final_text:
                logger.info(f"[{app_name}] Received final response (len={len(final_text)})")
                return final_text

            logger.warning(f"[{app_name}] No new response after {response_timeout}s (attempt {attempt}).")

        except Exception as e:
            last_exception = e
            logger.exception(f"[{app_name}] attempt {attempt}/{max_retries} raised exception: {e}")
            # save minimal debug info (counts + last exception)
            try:
                cur_count = len(driver.find_elements(By.XPATH, response_xpath))
            except Exception:
                cur_count = -1
            logger.error(f"[{app_name}] Debug: response_xpath matches {cur_count} elements")
            # (optional) save screenshot / page source here if you want deeper debug

        # small backoff before retry
        if attempt < max_retries:
            time.sleep(1.2)

    # final failure
    if last_exception:
        logger.error(f"[{app_name}] Last exception before giving up: {traceback.format_exception_only(type(last_exception), last_exception)}")
    return "[Error: Max retries exceeded]"