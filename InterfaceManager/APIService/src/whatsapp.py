# whatsapp.py

import os
import time
import json
import socket
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException
)
from logger import get_logger

logger = get_logger("whatsapp_driver")

def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

def get_ui_response():
    return {"ui": "Whatsapp Web Chat Interface", "features": ["smart-compose", "modular-layout"]}

def run_batch_file(bat_file_path: str) -> int:
    """
    Executes a .bat file for whatsapp web qr scan
    """
    try:
        result = subprocess.run([bat_file_path], shell=True)
        return result.returncode
    except Exception:
        return -1

# helper functions
def check_and_recover_connection() -> bool:
    """
    Check internet and attempt reconnection if disconnected.
    Logs the device's connectivity status.
    """
    config = load_config()
    if not is_connected(host=config.get("default_host"), port=config.get("default_port"), timeout=config.get("default_timeout")):
        logger.warning("Internet connection lost.")
        return retry_on_internet()
    else:
        logger.info("Device is connected to the internet.")
        return True

def is_connected(host: str, port: int, timeout: int) -> bool:
    '''
    Checking whether the device is connected to internet of not 
    '''
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
    """
    Retry internet reconnection using exponential backoff.
    Logs when the device is disconnected and when reconnection is successful.
    """
    config = load_config()
    delay = initial_delay
    logger.info("Checking internet connectivity...")
    for attempt in range(1, max_attempts + 1):
        if is_connected(host=config.get("default_host"), port=config.get("default_port"), timeout=config.get("default_timeout")):
            logger.info("Device is connected to the internet.")
            return True
        logger.warning(f"Device not connected. Attempt {attempt}/{max_attempts}. Retrying in {delay}s...")
        time.sleep(delay)
        delay = min(delay * 2, max_delay)
    logger.error("Device remains disconnected after all retry attempts.")
    return False

def login_whatsapp():
    """
    Login to whatsapp using batch file
    """
    status: bool = False
    login_batch_file = "login_whatsapp.bat"
    try:
        if not check_and_recover_connection():
            return status
        logger.info("Initiating WhatsApp Web Login process..")
        response_code = run_batch_file(login_batch_file)
        if response_code == 0:
            status = True
            logger.info("Whatapp web login successful")
        return status
    except Exception as e:
            logger.error(f"Error initializing WhatsApp Web interface: {e}")

# retry safe click logout helper
def safe_click(driver, selector: str, retries: int = 3, wait_time: int = 10) -> bool:
    """Safely clicks an element located by either XPath or CSS selector."""
    # Determine selector type
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

# logout helper
def initiate_logout(driver: webdriver.Chrome) -> bool:
    """
    Initiates logout process in whatsapp
    """
    config = load_config()
    try:
        logger.info("Initiating Whatsapp Web Logout process...")
        driver.get(config.get("whatsapp_url"))

        profile_btn = 'button[aria-label="Settings"][role="button"][data-tab="2"]'
        sign_out_btn = '//span[text()="Log out"]'
        log_out_btn = '//button[.//div[text()="Log out"]]'

        # Check presence of profile button
        if not safe_click(driver, profile_btn):
            logger.warning("Profile button not found. Possibly already logged out.")
            return True

        # Check presence of sign out option
        if not safe_click(driver, sign_out_btn):
            logger.warning("Sign-out option not found. Possibly already logged out.")
            return True

        # Final logout confirmation
        if not safe_click(driver, log_out_btn):
            logger.warning("Final logout button not found. Possibly already logged out.")
            return True

        # Wait for a possible redirect or confirmation
        WebDriverWait(driver, 2)
        logger.info(f"Logout successful. Current URL: {driver.current_url}")
        return True

    except TimeoutException:
        logger.warning(f"Logout steps completed but no redirect detected. Current URL: {driver.current_url}")
        return True
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return False

def logout_whatsapp():
    """
    Login from whatsapp using selenium automation
    """
    try:
        current_dir = os.getcwd()
        folder_name = "whatsapp_profile"
        profile_folder_path = os.path.join(current_dir, folder_name)
        opts = Options()
        opts.add_argument("--no-sandbox"); 
        opts.add_argument("--start-maximized")
        opts.add_argument(f"user-data-dir={profile_folder_path}")         
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])

        # Use webdriver manager to auto-resolve ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)

        logout_status = initiate_logout(driver=driver)
        time.sleep(2)
        driver.quit()
        logger.info("Browser session closed.")
        return logout_status

    except Exception as e:
        logger.error(f"Error during Whatsapp Web logout: {e}")
        return False

def search_llm(driver: webdriver.Chrome, llm_name: str) -> bool:
    """
    Search for the particular LLM in whatsapp web application
    """
    try:
        logger.info(f"Searching for contact: {llm_name}")
        search_input_xpath = '//*[@id="side"]/div[1]/div/div[2]/div/div/div/p'
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, search_input_xpath))
        )
        search_box.click()
        search_box.send_keys(llm_name)
        search_box.send_keys(Keys.RETURN)

        chat_header_xpath = f'//span[@title="{llm_name}" and .//span[text()="{llm_name}"]]'
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, chat_header_xpath))
        )
        logger.info(f"Chat with '{llm_name}' opened successfully.")
    except Exception as e:
        logger.error(f"Could not find contact '{llm_name}': {e}")
        return False
    return True

def send_message(driver: webdriver.Chrome, prompt: str, max_retries: int=3):
    """
    Sends prompts to the Whatsapp Web application 
    """
    response: str
    attempt = 0
    while attempt < max_retries:
        try:
            if not check_and_recover_connection():
                return "[Failed: Internet unavailable]"

            logger.info(f"Sending prompt: {prompt}")
            message_box_xpath = '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div[1]/div[2]/div[1]/p'
            message_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, message_box_xpath))
            )
            message_box.click()
            message_box.send_keys(prompt)
            message_box.send_keys(Keys.RETURN)

            time.sleep(20)
            messages_css = 'div[class*="copyable-text"]'
            messages = driver.find_elements(By.CSS_SELECTOR, messages_css)
            if messages:
                response = messages[-1].text
                logger.info(f"Received response: {response}")
                return response
            else:
                logger.warning("No response message found.")
                return "[No response received]"

        except Exception as e:
            attempt += 1
            logger.error(f"Chat attempt {attempt} failed: {e}")
            if attempt < max_retries:
                logger.info("Retrying chat...")
                time.sleep(2)
            else:
                return "[Error during chat after retries]"

def send_prompt_whatsapp(prompt: str) -> dict:
    """
    Send prompt and receieve response from Whatsapp Web
    """
    config = load_config()
    llm_name: str=config.get("whatsapp_web_model_name")
    # start_time = None 
    # end_time = None
    response_json = {
        "prompt": prompt,
        "response": "Not available"
    }

    try:
        current_dir = os.getcwd()
        folder_name = "whatsapp_profile"
        profile_folder_path = os.path.join(current_dir, folder_name)
        if not check_and_recover_connection():
            return response_json

        opts = Options()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--start-maximized")
        opts.add_argument(f"user-data-dir={profile_folder_path}")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        driver.get(config.get("whatsapp_url"))

        if search_llm(driver=driver, llm_name=llm_name):
            # start_time = datetime.now()
            response_str = send_message(driver=driver, prompt=prompt)
            # end_time = datetime.now()
            # response_json['start_time'] = str(start_time)
            # response_json['end_time'] = str(end_time)
            response_json["prompt"] = prompt
            response_json["response"] = str(response_str)

        close(driver=driver)

    except Exception as e:
        logger.error(f"Chat failed: {e}")

    return response_json


def close(driver: webdriver.Chrome):
    """
    Close the browser session.
    """
    try:
        driver.quit()
        logger.info("Browser session closed.")
    except Exception as e:
        logger.warning(f"Error closing browser: {e}")