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
import emoji

from logger import get_logger

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

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
        mode = load_json('config.json').get('headless', 'False')
        # to turn off headless mode - remove the below line or comment it out.
        if mode == "True":
            opts.add_argument("--headless")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])

        cfg = load_config()
        selenium_mode = str(cfg.get("selenium_mode", "local")).lower()
        remote_url = cfg.get("selenium_remote_url", "http://selenium-hub:4444/wd/hub")

        try:
            if selenium_mode == "remote":
                logger.info(f"Using Remote WebDriver at {remote_url}")
                # opts.add_argument("--user-data-dir=/home/seluser/chrome-data")
                self.driver = webdriver.Remote(
                    command_executor=remote_url,
                    options=opts
                )
            else:
                opts.add_argument(f"user-data-dir={self.profile_folder_path}")
                logger.info("Using local Chrome WebDriver")
                self.driver = webdriver.Chrome(options=opts)

            self.driver.get(url)
            logger.info(f"Driver ready for {app_name}")
            return self.driver
        except WebDriverException as e:
            logger.error(f"Failed to start Chrome for {app_name}: {e}")
            self.driver = None
            raise

        # try:
        #     # service = Service(ChromeDriverManager().install())
        #     # self.driver = webdriver.Chrome(service=service, options=opts)
        #     # @bugfix: Use the below line to load driver faster -- Balayogi 12.01.2026
        #     self.driver = webdriver.Chrome(options=opts)
        #     self.driver.get(url)
        #     logger.info(f"Driver ready for {app_name}")
        #     return self.driver
        # except WebDriverException as e:
        #     logger.error(f"Failed to start Chrome for {app_name}: {e}")
        #     self.driver = None
        #     raise

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


# Function to identify selector type
def get_selector_type(selector: str):
    selector = selector.strip()

    # XPath patterns
    if selector.startswith("//") or selector.startswith("(//") or selector.startswith(".//"):
        return By.XPATH

    # Default → CSS
    return By.CSS_SELECTOR

# --------------------------------------------------------------------
# UI Helpers
# --------------------------------------------------------------------
def is_logged_in(driver: webdriver.Chrome, send_element: str) -> bool:
    """Check if a user is logged in by verifying presence of a profile element."""
    try:
        by = get_selector_type(send_element)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((by, send_element))
        )
        return True
    except Exception as e:
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

        qr_cfg = app_cfg.get("ChatPage", {}).get("scan_qr_code_element")

        if app_name.lower() == "whatsapp" or app_name.lower() == "whatsapp web" or app_name.lower() == "whatsapp_web":
            try:
                wait_for_login = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, qr_cfg))
                )
                logger.info(f"{app_name.upper()} requires QR code login. Please scan the QR code with your mobile app.")
                time.sleep(60)
                return True
            except TimeoutException:
                logger.error(f"QR code element not found for {app_name}")
                return True

        if not login_cfg:
            logger.info(f"{app_name} has no LoginPage config → skipping login")
            return True

        # Already logged in?
        if logout_cfg and is_logged_in(driver, logout_cfg["profile_pic_element"]):
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
        print(e)
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
    contact_selection = "//span[@title='" + entity_name + "']"

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
        
        time.sleep(5)

        contact_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, contact_selection))
        )
        contact_select.click()

        logger.info(f"{app_name}: '{entity_name}' search successful")
        return True
    except Exception as e:
        logger.error(f"{app_name}: search failed for '{entity_name}': {e}")
        return False

def split_message(message, max_length=1000):
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]

# --------------------------------------------------------------------
# Detecting Emojis in Text
# --------------------------------------------------------------------
def contains_emoji(text: str) -> bool:
    """Returns True if the text contains any emoji."""
    return any(ch in emoji.EMOJI_DATA for ch in text)

def smart_send_text(driver, element, text: str):
    """
    Sends text using the most appropriate method.

    - Plain text  -> send_keys()
    - Emoji text  -> CDP Input.insertText()
    """

    element.click()

    if contains_emoji(text):
        driver.execute_cdp_cmd(
            "Input.insertText",
            {
                "text": text
            }
        )
    else:
        element.send_keys(text)

def send_message_whatsapp(driver: webdriver.Chrome, prompt: str):
    """
    Sends a prompt to WhatsApp Web and retrieves the agent's full response
    after the last sent message, waiting until the response is stable.
    """
    attempt = 0
    max_retries: int = 3
    app_name = load_config().get("application_type")
    app_cfg = load_xpaths()["applications"][app_name.lower()]
    chat_cfg = app_cfg["ChatPage"]

    # Tunables
    POLL_INTERVAL = 2          # seconds between polls
    MAX_WAIT = 60              # total seconds to wait for a response
    STABLE_CYCLES_REQUIRED = 4 # consecutive unchanged polls => ~8s quiet

    while attempt < max_retries:
        try:
            if not check_and_recover_connection():
                logger.warning("No internet connection available.")
                return "No response received"

            logger.info(f"Sending prompt to the bot: {prompt}")

            message_box_xpath = chat_cfg["prompt_input_box_element"]
            message_box = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, message_box_xpath))
            )
            message_box.clear()
            message_box.click()

            chunks = split_message(prompt)
            for i, chunk in enumerate(chunks):
                smart_send_text(driver, message_box, chunk)
                if i != len(chunks) - 1:
                    message_box.send_keys(Keys.SHIFT, Keys.ENTER)
            message_box.send_keys(Keys.RETURN)

            message_in = chat_cfg["message_in_element"]
            message_out = chat_cfg["message_out_element"]
            selectable_text = chat_cfg["agent_response_element"]

            last_seen_response = ""
            last_seen_count = -1
            stable_count = 0
            wait_time = 0
            start = time.time()

            while wait_time <= MAX_WAIT:
                time.sleep(POLL_INTERVAL)
                wait_time += POLL_INTERVAL

                wait = WebDriverWait(driver, 30)

                # All messages in order (incoming + outgoing)
                all_messages = wait.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, f"{message_in} | {message_out}")
                    )
                )

                logger.info(
                    "Total message containers: %d",
                    len(all_messages)
                )

                outgoing_msgs = driver.find_elements(By.XPATH, message_out)

                logger.info(
                    "Outgoing messages: %d",
                    len(outgoing_msgs)
                )

                if not outgoing_msgs:
                    raise Exception("No outgoing messages found.")

                last_outgoing = outgoing_msgs[-1]

                # Find the index of our last sent message
                try:
                    last_index = max(
                        i for i, msg in enumerate(all_messages)
                        if msg == last_outgoing
                    )
                except ValueError:
                    raise Exception(
                        "Last outgoing message not found in all_messages list."
                    )

                # Everything after our last outgoing message
                responses_after = all_messages[last_index + 1:]
                logger.info(
                    "Messages after last outgoing: %d", len(responses_after)
                )

                # message_in_element already restricts all_messages to genuine
                # incoming bubbles, so everything after our last outgoing
                # message is already a real incoming response.
                responses = responses_after

                logger.info("Incoming responses found: %d", len(responses))

                # Extract and combine text from every incoming bubble, in order
                response_texts = []
                for msg in responses:
                    try:
                        text_elems = msg.find_elements(
                            By.XPATH,
                            selectable_text
                        )

                        parts = []

                        for elem in text_elems:
                            txt = elem.text.strip()

                            if txt:
                                parts.append(txt)

                        text = "\n".join(parts)

                        logger.info(
                            "Found %d text elements, extracted: %s",
                            len(text_elems),
                            text
                        )

                        if text:
                            response_texts.append(text)

                    except Exception as e:
                        logger.debug(
                            "Could not read response message: %s",
                            e
                        )

                full_text = "\n".join(response_texts)
                current_count = len(response_texts)

                logger.info(
                    f"(Waited:{int(time.time() - start)}) "
                    f"Received: {full_text}"
                )

                # Stable only if BOTH the text and the number of bubbles
                # are unchanged since the last poll.
                if (full_text == last_seen_response
                        and current_count == last_seen_count):
                    stable_count += 1
                else:
                    stable_count = 0
                    last_seen_response = full_text
                    last_seen_count = current_count

                if full_text and stable_count >= STABLE_CYCLES_REQUIRED:
                    logger.info("Response stabilized. Returning final response.")
                    return full_text

            # Timeout fallback
            if last_seen_response:
                logger.info("Returning last collected response after timeout.")
                return last_seen_response

            logger.warning("No response message received from whatsapp.")
            return "No response received"

        except Exception as e:
            attempt += 1
            logger.error(f"Chat attempt {attempt} failed: {e}")
            if attempt < max_retries:
                logger.info("Retrying chat...")
                time.sleep(0.3)
            else:
                logger.error("Max chat retries reached. Aborting.")
                return "No response received"

def handle_farmerchat(driver, prompt):

    cfg = load_xpaths()["applications"]["farmerchat"]["ChatPage"]

    iframe_selector = cfg["shadow_root_element"]
    textarea_selector = cfg["prompt_input_box_element"]
    response_selector = cfg["agent_response_element"]
    audio_selector = cfg["audio_message_element"]
    mic_selector = cfg["mic_button_element"]
    send_selector = cfg["send_button_element"]

    shadow_host = get_shadow_host(driver, iframe_selector)

    textarea = driver.execute_script("""
        const host = arguments[0];
        return host.shadowRoot.querySelector(arguments[1]);
    """, shadow_host, textarea_selector)

    if not textarea:
        raise RuntimeError("Prompt input box not found")
    
    # To clear text area
    textarea.send_keys(Keys.CONTROL + "a")
    textarea.send_keys(Keys.DELETE)
    
    initial_count = driver.execute_script("""
        const host = arguments[0];
        return host.shadowRoot.querySelectorAll(arguments[1]).length;
    """, shadow_host, response_selector)

    smart_send_text(driver, textarea, prompt)
    textarea.send_keys(Keys.RETURN)

    time.sleep(10)
    
    text = wait_for_new_shadow_text(driver, shadow_host, response_selector, initial_count)

    return {
        "type": "text",
        "content": text
    }

def handle_bodhan_ai(driver, prompt):
   cfg = load_xpaths()["applications"]["bodhan-ai"]["ChatPage"]

   prompt_xpath = cfg["prompt_input_box_element"]
   response_xpath = cfg["agent_response_element"]

   if not prompt_xpath or not response_xpath:
       raise RuntimeError("Prompt input box or response XPath not configured.")

   wait = WebDriverWait(driver, 30)

   def get_textarea():
       return wait.until(
           EC.element_to_be_clickable((By.XPATH, prompt_xpath))
       )

   def get_response_text():
       elements = driver.find_elements(By.XPATH, response_xpath)
       return "\n".join(
           e.text.strip()
           for e in elements
           if e.text.strip()
       )

   # Current response before sending prompt
   previous_response = get_response_text()

   # Retry in case React replaces the textarea
   for _ in range(3):
       try:
           textarea = get_textarea()

           textarea.click()
           textarea.send_keys(Keys.CONTROL, "a")
           textarea.send_keys(Keys.DELETE)

           textarea = get_textarea()
           smart_send_text(driver, textarea, prompt)

           textarea = get_textarea()
           textarea.send_keys(Keys.ENTER)

           break

       except StaleElementReferenceException:
           time.sleep(0.5)
   else:
       raise RuntimeError("Textarea became stale repeatedly.")

   # Wait until response starts changing
   try:
       wait.until(
           lambda d: get_response_text() != previous_response
       )
   except TimeoutException:
       raise RuntimeError("No response received from Bodhan AI.")

   # Wait until streaming finishes
   last_text = ""
   stable_count = 0
   timeout = time.time() + 120

   while time.time() < timeout:
       try:
           current_text = get_response_text()

           if current_text == last_text and current_text:
               stable_count += 1
           else:
               stable_count = 0
               last_text = current_text

           # 4 consecutive stable reads (~2 seconds)
           if stable_count >= 4:
               break

           time.sleep(0.5)

       except StaleElementReferenceException:
           continue

   return {
       "type": "text",
       "content": last_text.strip()
   }


APP_HANDLERS = {
    "farmerchat": handle_farmerchat,
    "bodhan-ai": handle_bodhan_ai
}

# Sending Message to Web applications
def send_message_webapp(
    driver,
    app_name,
    prompt=None,
    max_retries=3,
):

    app = app_name.lower()
    handler = APP_HANDLERS.get(app)

    if not handler:
        raise ValueError(f"Unsupported application: {app}")


    for attempt in range(1, max_retries + 1):

        try:
            if not check_and_recover_connection():
                return {
                    "type": "error",
                    "content": "No internet connection"
                }
            
            return handler(driver, prompt)

        except Exception as e:

            logger.warning(f"[{app}] attempt {attempt} failed: {e}")

            if attempt == max_retries:
                logger.error(f"[{app}] All {max_retries} attempts failed")
                return {
                    "type": "error",
                    "content": f"Max retries reached for {app}: {str(e)}"
                }

            time.sleep(1.5)

# ------------------------------------------------------------
# WAIT FOR TEXT RESPONSE (NORMAL DOM)
# ------------------------------------------------------------

def wait_for_text_response(driver, xpath, timeout=60, stable_time=2):

    start = time.time()
    last_text = ""
    last_change = time.time()

    while time.time() - start < timeout:

        nodes = driver.find_elements(By.XPATH, xpath)

        if nodes:
            # Collect all visible text nodes
            full_text = " ".join(
                n.text.strip() for n in nodes if n.text.strip()
            )

            if full_text and full_text != last_text:
                last_text = full_text
                last_change = time.time()
                logger.info(
                    f"(Waited:{int(time.time() - start)}) "
                    f"Received: {full_text}"
                )

            # Return only when text has stopped changing
            if last_text and (time.time() - last_change) > stable_time:
                return last_text

        time.sleep(0.5)

    raise TimeoutException("Response timeout")

# ------------------------------------------------------------
# WAIT FOR TEXT RESPONSE (SHADOW DOM)
# ------------------------------------------------------------

def wait_for_new_shadow_text(driver, shadow_host, selector, initial_count, timeout=60, stable_time=3, poll_interval=0.5):

    start = time.time()
    last_text = ""
    last_change = time.time()
    first_text_time = None 

    while time.time() - start < timeout:

        result = driver.execute_script("""
            const host = arguments[0];
            const sel = arguments[1];
            const nodes = host.shadowRoot.querySelectorAll(sel);

            return {
                count: nodes.length,
                text: nodes.length ? nodes[nodes.length-1].textContent : ""
            };
        """, shadow_host, selector)

        # Wait until a NEW message appears
        if result["count"] <= initial_count:
            time.sleep(0.2)
            continue

        text = (result["text"] or "").strip()

        if text != last_text:
            last_text = text
            last_change = time.time()
            # Log streaming progress
            logger.debug(
                f"(Waited:{int(time.time()-start)}) "
                f"Streaming: {text[:50]}..."
            )

        # Record when first text appeared
        if text and first_text_time is None:
            first_text_time = time.time()

        # Wait until minimum time passed AND text stopped changing
        if (
            text and
            first_text_time and
            (time.time() - first_text_time) > 1 and       # min 1s after first text
            (time.time() - last_change) > stable_time      # text stopped changing
        ):
            logger.info(
                f"(Waited:{int(time.time() - start)}) "
                f"Received: {text}"
            )
            return text

        time.sleep(poll_interval)   # configurable poll interval

    raise TimeoutException("New shadow response timeout")


# ------------------------------------------------------------
# SHADOW HOST DISCOVERY
# ------------------------------------------------------------

def get_shadow_host(driver, iframe_selector, host_selector=None):

    frames = driver.find_elements(By.CSS_SELECTOR, iframe_selector)

    if frames:
        driver.switch_to.frame(frames[0])

    if host_selector:
        # Target a specific shadow host by CSS selector
        host = driver.execute_script("""
            const el = document.querySelector(arguments[0]);
            return el && el.shadowRoot ? el : null;
        """, host_selector)
        logger.info(f"Shadow host found via selector: {host_selector}")
    else:
        # Fallback — first shadow host found
        host = driver.execute_script("""
            return Array.from(document.querySelectorAll('*'))
            .find(el => el.shadowRoot);
        """)
        logger.info("Shadow host found via fallback scan")

    if not host:
        raise RuntimeError("Shadow host not found")

    return host
