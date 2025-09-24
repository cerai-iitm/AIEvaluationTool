# cpgrams.py

import time
import json
import socket
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from logger import get_logger
import os

from typing import List

logger = get_logger("cpgrams_driver")

global cached_driver
cached_driver = None

# -------------------------------
# Configuration
# -------------------------------
def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

def get_ui_response():
    return {"ui": "CPGRAMS Chat Interface", "features": ["smart-compose", "modular-layout"]}

# -------------------------------
# Connectivity Helpers
# -------------------------------
def check_and_recover_connection() -> bool:
    """
    Check internet and attempt reconnection if disconnected.
    """
    config = load_config()
    if not is_connected(config.get("default_host"), config.get("default_port"), config.get("default_timeout")):
        logger.warning("Internet connection lost.")
        return retry_on_internet()
    else:
        logger.info("Device is connected to the internet.")
        return True


def is_connected(host: str, port: int, timeout: int) -> bool:
    """
    Check whether the device is connected to internet or not.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        logger.error(f"Network down: {ex}")
        return False


def retry_on_internet(max_attempts=5, initial_delay=3, max_delay=60) -> bool:
    """
    Retry internet reconnection using exponential backoff.
    """
    config = load_config()
    delay = initial_delay
    logger.info("Checking internet connectivity...")
    for attempt in range(1, max_attempts + 1):
        if is_connected(config.get("default_host"), config.get("default_port"), config.get("default_timeout")):
            logger.info("Device is connected to the internet.")
            return True
        logger.warning(f"Attempt {attempt}/{max_attempts} failed. Retrying in {delay}s...")
        time.sleep(delay)
        delay = min(delay * 2, max_delay)
    logger.error("Device remains disconnected after all retry attempts.")
    return False

# Is logged in function can be added here if needed
def is_logged_in(driver: webdriver.Chrome) -> bool:
    try:
        # Example: check for profile icon or dashboard element
        profile_element_xpath = "//div[.//div[@class='font-semibold' and text()='Subodh Kumar Singh']]"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, profile_element_xpath))
        )
        return True
    except Exception:
        return False

# Session Management Helpers

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


# CPGRAMS Login / Logout
def login_webapp_cpgrams(driver: webdriver.Chrome) -> bool:
    """
    Attempts login and verifies success by checking post-login element.
    """
    try:
        if not check_and_recover_connection():
            return False

        logger.info("Logging in CPGRAMS Chat Interface...")

        email_xpath = "//input[@id='email']"
        password_xpath = "//input[@id='password']"
        login_button_xpath = "//button[normalize-space(.)='Sign In']"

        email = "email"
        password = "password"

        # Check for post-login success
        if is_logged_in(driver):
            logger.info("Already logged in to CPGRAMS chat interface.")
            return True
        else:
            logger.info("Not logged in, proceeding with login.")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, email_xpath))).send_keys(email)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, password_xpath))).send_keys(password)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, login_button_xpath))).click()

            logger.info("CPGRAMS chat interface Logged in successfully.")
        return True

    except Exception as e:
        logger.error(f"Login failed or not confirmed: {e}")
        return False

    
def logout_webapp_cpgrams(driver: webdriver.Chrome) -> bool:
    """
    Closes the CPGRAMS Web chat interface.
    """

    profile_element_xpath = "//div[.//div[@class='font-semibold' and text()='Subodh Kumar Singh']]" 
    logout_button_xpath = "//button[.//span[normalize-space(text())='Logout']]"

    try:
        if driver:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, profile_element_xpath))).click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, logout_button_xpath))).click()
            time.sleep(0.5)
            driver.quit()
            logger.info("CPGRAMS Chat Interface Logged out and closed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error closing WebApp interface: {e}")
        return False

# -------------------------------
# Web Automation Helpers
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
                By.XPATH, "//div[@class='select-text']/p"
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
                    "//div[@class='select-text']/p"
                )) > previous_count
            )

            time.sleep(5)  # let DOM stabilize

            # Fetch latest message
            bot_messages = driver.find_elements(
                By.XPATH, "//div[@class='select-text']/p"
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
# Main Function
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
                chat_found = login_webapp_cpgrams(driver=driver)
            
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
            close(driver)
            cached_driver = None  # Clear cached driver on close
    else:
        raise ValueError("Invalid mode: choose 'single_window'.")
    return results
    

def close(driver: webdriver.Chrome):
    """
    Close the browser session.
    """
    try:
        driver.quit()
        logger.info("Browser session closed.")
    except Exception as e:
        logger.warning(f"Error closing browser: {e}")
