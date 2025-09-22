# webapp.py

import os
import time
import json
import socket
import psutil
from typing import List
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
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
from logger import get_logger

logger = get_logger("webapp_driver")

global cached_driver
cached_driver = None


def load_config():
    with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as file:
        return json.load(file)


def get_ui_response():
    return {"ui": "Web Application Chat Interface", "features": ["smart-compose", "modular-layout"]}


# -------------------------------
# Connectivity Helpers
# -------------------------------
def check_and_recover_connection() -> bool:
    config = load_config()
    if not is_connected(
        host=config.get("default_host"),
        port=config.get("default_port"),
        timeout=config.get("default_timeout")
    ):
        logger.warning("Internet connection lost.")
        return retry_on_internet()
    logger.info("Device is connected to the internet.")
    return True


def is_connected(host: str, port: int, timeout: int) -> bool:
    config = load_config()
    host = config.get("default_host")
    port = config.get("default_port")
    timeout = config.get("default_timeout")
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        logger.error(f"Network down: {ex}")
        return False


def retry_on_internet(max_attempts=5, initial_delay=3, max_delay=60) -> bool:
    config = load_config()
    delay = initial_delay
    logger.info("Checking internet connectivity...")
    for attempt in range(1, max_attempts + 1):
        if is_connected(
            host=config.get("default_host"),
            port=config.get("default_port"),
            timeout=config.get("default_timeout")
        ):
            logger.info("Device is connected to the internet.")
            return True
        logger.warning(f"Attempt {attempt}/{max_attempts}. Retrying in {delay}s...")
        time.sleep(delay)
        delay = min(delay * 2, max_delay)
    logger.error("Device remains disconnected after all retry attempts.")
    return False


# -------------------------------
# WebApp Login / Logout
# -------------------------------
def login_webapp():
    status: bool = False
    try:
        if not check_and_recover_connection():
            return status
        logger.info("Opening WebApp Chat Interface...")

        # profile_folder_path = os.path.expanduser('~') + "/webapp_profile"
        # opts = Options()
        # opts.add_argument("--no-sandbox")
        # opts.add_argument("--start-maximized")
        # opts.add_argument(f"user-data-dir={profile_folder_path}")
        # opts.add_experimental_option("excludeSwitches", ["enable-logging"])

        # service = Service(ChromeDriverManager().install())
        # driver = webdriver.Chrome(service=service, options=opts)
        # driver.get(load_config().get("application_url"))

        logger.info("WebApp chat interface opened successfully.")
        return True
    except Exception as e:
        logger.error(f"Error initializing WebApp interface: {e}")
        return False


def safe_click(driver, selector: str, retries: int = 3, wait_time: int = 10) -> bool:
    if selector.strip().startswith('/') or selector.strip().startswith('('):
        by_type = By.XPATH
    else:
        by_type = By.CSS_SELECTOR

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


def logout_webapp():
    try:
        profile_folder_path = os.path.expanduser('~') + "/whatsapp_profile"
        opts = Options()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--start-maximized")
        opts.add_argument(f"user-data-dir={profile_folder_path}")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)

        driver.get(load_config().get("application_url"))
        logger.info("Logout sequence placeholder. Adjust selectors if logout exists.")

        time.sleep(0.5)
        driver.quit()
        logger.info("Browser session closed after logout.")
        return True
    except Exception as e:
        logger.error(f"Error during WebApp logout: {e}")
        return False


# -------------------------------
# Session Management Helpers
# -------------------------------
def is_profile_in_use(profile_path):
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if 'chrome' in proc.info['name'].lower():
                if proc.info['cmdline'] is None:
                    continue
                cmdline = ' '.join(proc.info['cmdline'])
                if f"user-data-dir={profile_path}" in cmdline:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def close_chrome_with_profile(profile_path):
    closed_any = False
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if 'chrome' in proc.info['name'].lower():
                if proc.info['cmdline'] is None:
                    continue
                cmdline = ' '.join(proc.info['cmdline'])
                if f"user-data-dir={profile_path}" in cmdline:
                    proc.kill()
                    closed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return closed_any


# -------------------------------
# Messaging Helpers
# -------------------------------
def send_message(driver: webdriver.Chrome, prompt: str, max_retries: int = 3):
    """
    Sends a prompt to CPGRAMS Web chat interface and retrieves responses.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            if not check_and_recover_connection():
                return "[Failed: Internet unavailable]"

            logger.info(f"Sending prompt: {prompt}")

            # Get current messages before sending
            previous_messages = driver.find_elements(
                By.XPATH, "//div[@class='leading-relaxed text-sm']/p"
            )
            previous_count = len(previous_messages)

            # Send prompt
            chat_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//textarea[@placeholder='Type your query here or press mic button for audio communication']"
                ))
            )
            chat_input.clear()
            chat_input.send_keys(prompt)
            chat_input.send_keys(Keys.ENTER)

            # Wait until a new message appears
            WebDriverWait(driver, 50).until(
                lambda d: len(d.find_elements(
                    By.XPATH,
                    "//div[@class='leading-relaxed text-sm']/p"
                )) > previous_count
            )

            time.sleep(5)  # let DOM stabilize

            # Fetch latest message
            bot_messages = driver.find_elements(
                By.XPATH, "//div[@class='leading-relaxed text-sm']/p"
            )
            new_response = bot_messages[-1].text.strip() if bot_messages else "[No response received]"

            logger.info(f"Response: {new_response}")
            return new_response

        except Exception as e:
            attempt += 1
            logger.error(f"Chat attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(0.5)
            else:
                return "[Error during chat after retries]"

# -------------------------------
# Prompt sending interface
# -------------------------------
def send_prompt_cpgrams(chat_id: int, prompt_list: List[str], mode: str = "single_window") -> list[dict]:
    global cached_driver
    results = []

    if mode == "single_window":
        profile_folder_path = os.path.expanduser('~') + "/whatsapp_profile"
        logger.info(f"Using profile folder: {profile_folder_path}")

        if is_profile_in_use(profile_folder_path) and cached_driver is not None:
            driver = cached_driver
            logger.info("Reusing existing Chrome session.")
        else:
            if cached_driver is None:
                logger.error("Chrome with this session is already running, but driver outdated.  Restarting Chrome with the same profile.")
                close_chrome_with_profile(profile_folder_path)
            else:
                logger.info("No Automated Chrome instance. Safe to launch a new one.")

            opts = Options()
            opts.add_argument("--no-sandbox")
            #opts.add_argument("--headless")  # Uncomment for headless operation
            opts.add_argument(f"user-data-dir={profile_folder_path}")
            opts.add_experimental_option("excludeSwitches", ["enable-logging"])

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=opts)
            driver.get(load_config().get("application_url"))
            cached_driver = driver  # Cache the driver for reuse
            
        try:
            chat_found = False
            while chat_found is False:
                logger.debug("Waiting for chat to be found...")
                time.sleep(0.5)
                chat_found = login_webapp()
            
            for i, prompt in enumerate(prompt_list):
                result = {"chat_id": chat_id, "prompt": prompt, "response": "Not available"}
                try:
                    if chat_found:
                        response_str = send_message(driver=driver, prompt=prompt)
                        result["response"] = str(response_str)
                    else:
                        result["response"] = "Chat not found"
                except Exception as e:
                    logger.error(f"Prompt failed for chat '{chat_id}': {e}")
                    result['response'] = f"Error: {e}"
                
                results.append(result)
            
        finally:
            pass
    else:
        raise ValueError("Invalid mode: choose 'single_window'.")
    return results


def close_webapp():
    global cached_driver
    if cached_driver is not None:
        try:
            cached_driver.quit()
            logger.info("Closing WebApp session...")
            cached_driver = None
            profile_folder_path = os.path.expanduser('~') + "/whatsapp_profile"
            close_chrome_with_profile(profile_folder_path)
        except Exception as e:
            logger.error(f"Error closing WebApp session: {e}")
    else:
        logger.warning("No active WebApp session to close.")
        profile_folder_path = os.path.expanduser('~') + "/whatsapp_profile"
        close_chrome_with_profile(profile_folder_path)


def close(driver: webdriver.Chrome):
    try:
        driver.quit()
        logger.info("Browser session closed.")
    except Exception as e:
        logger.warning(f"Error closing browser: {e}")
