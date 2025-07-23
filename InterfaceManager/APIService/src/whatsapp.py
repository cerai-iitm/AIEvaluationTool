# whatsapp.py

import os
import time
import json
import socket
import subprocess
import tempfile
import psutil
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

from typing import List

logger = get_logger("whatsapp_driver")

def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

def get_ui_response():
    return {"ui": "Whatsapp Web Chat Interface", "features": ["smart-compose", "modular-layout"]}

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
    Checking whether the device is connected to internet or not 
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
    try:
        if not check_and_recover_connection():
            return status
        logger.info("Initiating WhatsApp Web Login process..")
        
        #temp_dir = tempfile.gettempdir()
        #folder_name = "whatsapp_profile"
        #profile_folder_path = os.path.join(temp_dir, folder_name)
        profile_folder_path = os.path.expanduser('~') + "/whatsapp_profile"
        opts = Options()
        opts.add_argument("--no-sandbox"); 
        opts.add_argument("--start-maximized")
        opts.add_argument(f"user-data-dir={profile_folder_path}")         
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        driver.get(load_config().get("whatsapp_url"))
        status = True
        logger.info("Whatapp web login successful")
        return status
    except Exception as e:
            logger.error(f"Error initializing WhatsApp Web interface: {e}")

# retry safe click logout helper
def safe_click(driver, selector: str, retries: int = 3, wait_time: int = 10) -> bool:
    """Safely clicks an element located by either XPath or CSS selector."""
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

        if not safe_click(driver, profile_btn):
            logger.warning("Profile button not found. Possibly already logged out.")
            return True
            
        if not safe_click(driver, sign_out_btn):
            logger.warning("Sign-out option not found. Possibly already logged out.")
            return True

        if not safe_click(driver, log_out_btn):
            logger.warning("Final logout button not found. Possibly already logged out.")
            return True

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
        #temp_dir = tempfile.gettempdir()
        #folder_name = "whatsapp_profile"
        #profile_folder_path = os.path.join(temp_dir, folder_name)
        profile_folder_path = os.path.expanduser('~') + "/whatsapp_profile"
        opts = Options()
        opts.add_argument("--no-sandbox") 
        opts.add_argument("--start-maximized")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument(f"user-data-dir={profile_folder_path}")         
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)

        logout_status = initiate_logout(driver=driver)
        time.sleep(0.5)
        driver.quit()
        logger.info("Browser session closed.")
        return logout_status

    except Exception as e:
        logger.error(f"Error during Whatsapp Web logout: {e}")
        return False

def search_llm(driver: webdriver.Chrome) -> bool:
    """
    Search for the particular LLM in whatsapp web application
    """
    config = load_config()
    llm_name = config.get("agent_name")

    try:
        # time.sleep(120)
        logger.info(f"Searching for contact: {llm_name}")
        search_input_xpath = '//div[@aria-label="Search input textbox" and @contenteditable="true"]'
        search_box = WebDriverWait(driver, 10).until(
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


def split_message(message, max_length=1000):
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]

def extract_text(msg_element):
    try:
        time.sleep(10)
        elements = msg_element.find_elements(By.CLASS_NAME, 'copyable-text')
        for element in elements:
            print(element.text)
        return " ".join(el.text for el in elements if el.text.strip() != "")
    except:
        return ""

def is_profile_in_use(profile_path):
    """Check if any Chrome process is using the given user-data-dir."""
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if 'chrome' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'])
                if f"user-data-dir={profile_path}" in cmdline:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def close_chrome_with_profile(profile_path):
    """Kill any Chrome process using the specified user-data-dir."""
    closed_any = False
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if 'chrome' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'])
                if f"user-data-dir={profile_path}" in cmdline:
                    proc.kill()
                    closed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return closed_any

def send_message(driver: webdriver.Chrome, prompt: str, max_retries: int = 3):
    """
    Sends a prompt to WhatsApp Web and retrieves responses after the last sent message.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            if not check_and_recover_connection():
                return "[Failed: Internet unavailable]"
            
            logger.info(f"Sending prompt to the bot: {prompt}")
            # message_box_xpath = (
            #     '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div[1]/div[2]/div[1]/p'
            # )

            message_box_xpath = '//div[@aria-label="Type a message" and @contenteditable="true"]'
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

            time.sleep(30)

            wait = WebDriverWait(driver, 10)
            all_messages = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.message-in, div.message-out")
                )
            )

            outgoing_msgs = driver.find_elements(By.CSS_SELECTOR, "div.message-out")
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

            response_texts = []
            for msg in responses:
                try:
                    text_elem = msg.find_element(By.CSS_SELECTOR, "span.selectable-text")
                    text = text_elem.text.strip()
                    if text:
                        response_texts.append(text)
                        logger.info("Received response from WhatsApp: %s", text)
                except Exception as e:
                    logger.debug("Could not read response message: %s", e)
                    continue

            if response_texts:
                combined_response = " ".join(response_texts)
                return combined_response
            else:
                logger.warning("No response message found.")
                return ["[No response received]"]

        except Exception as e:
            attempt += 1
            logger.error(f"Chat attempt {attempt} failed: {e}")
            if attempt < max_retries:
                logger.info("Retrying chat...")
                time.sleep(0.3)
            else:
                return ["[Error during chat after retries]"]

def send_prompt_whatsapp(chat_id: int, prompt_list: List[str], mode: str = "single_window") -> list[dict]:
    results = []

    if mode == "single_window":
        #temp_dir = tempfile.gettempdir()
        #folder_name = "whatsapp_profile"
        #profile_folder_path = os.path.join(temp_dir, folder_name)

        profile_folder_path = os.path.expanduser('~') + "/whatsapp_profile"  # For testing purposes
        logger.info(f"Using profile folder: {profile_folder_path}")

        if is_profile_in_use(profile_folder_path):
            logger.info("Chrome with this session is already running. Attempting to close it...")
            if close_chrome_with_profile(profile_folder_path):
                logger.info("Successfully closed the Chrome instance using this session.")
            else:
                logger.error("Failed to close. Possibly due to permission or timing issues.")
        else:
            logger.info("No Chrome instance is using the session. Safe to launch a new one.")

        opts = Options()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--start-maximized")
        opts.add_argument(f"user-data-dir={profile_folder_path}")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        
        try:
            driver.get(load_config().get("whatsapp_url"))
            time.sleep(5)

            chat_found = search_llm(driver=driver)
            
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
            driver.quit()

    elif mode == "multi_window":
        for i, prompt in enumerate(prompt_list):
            #temp_dir = tempfile.gettempdir()
            #folder_name = "whatsapp_profile"
            #profile_folder_path = os.path.join(temp_dir, folder_name)

            profile_folder_path = os.path.expanduser('~') + "/whatsapp_profile"
            
            if is_profile_in_use(profile_folder_path):
                print("Chrome with this session is already running. Attempting to close it...")
                if close_chrome_with_profile(profile_folder_path):
                    print("Successfully closed the Chrome instance using this session.")
                else:
                    print("Failed to close. Possibly due to permission or timing issues.")
            else:
                print("No Chrome instance is using the session. Safe to launch a new one.")

            opts = Options()
            opts.add_argument("--no-sandbox")
            opts.add_argument("--start-maximized")
            opts.add_argument(f"user-data-dir={profile_folder_path}")
            opts.add_experimental_option("excludeSwitches", ["enable-logging"])

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=opts)
            
            try:
                driver.get(load_config().get("whatsapp_url"))
                time.sleep(5)

                result = {"chat_id": chat_id, "prompt": prompt, "response": "Not available"}

                try:
                    if search_llm(driver):
                        result["response"] = send_message(driver, prompt)
                    else:
                        result["response"] = "Chat not found"
                except Exception as e:
                    result["response"] = f"Error: {e}"
                
                results.append(result)
            
            finally:
                driver.quit()

    else:
        raise ValueError("Invalid mode: choose 'single_window' or 'multi_window'.")

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

