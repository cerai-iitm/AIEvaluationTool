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

from typing import List

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

def search_llm(driver: webdriver.Chrome) -> bool:
    """
    Search for the particular LLM in whatsapp web application
    """
    config = load_config()
    llm_name = config.get("model_name")

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


def split_message(message, max_length=1000):
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]

def extract_text(msg_element):
    try:
        time.sleep(20)
        elements = msg_element.find_elements(By.CLASS_NAME, 'copyable-text')
        for element in elements:
            print(element.text)
        return " ".join(el.text for el in elements if el.text.strip() != "")
    except:
        return ""

def send_message(driver: webdriver.Chrome, prompt: str, max_retries: int = 3):
    """
    Sends a prompt to WhatsApp Web and retrieves responses after the last sent message.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            if not check_and_recover_connection():
                return "[Failed: Internet unavailable]"

            logger.info(f"Sending prompt: {prompt}")
            message_box_xpath = (
                '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div[1]/div[2]/div[1]/p'
            )
            message_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, message_box_xpath))
            )
            message_box.clear()
            message_box.click()
            chunks = split_message(prompt)

            for chunk in chunks:
                message_box.send_keys(chunk)
                message_box.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(2)
            message_box.send_keys(Keys.RETURN)

            time.sleep(30)

            wait = WebDriverWait(driver, 50)
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
                        logger.info("Received response: %s", text)
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
                time.sleep(2)
            else:
                return ["[Error during chat after retries]"]

def send_prompt_whatsapp(chat_id: int, prompt_list: List[str], mode: str = "single_window") -> list[dict]:
    results = []

    if mode == "single_window":
        current_dir = os.getcwd()
        folder_name = "whatsapp_profile"
        profile_folder_path = os.path.join(current_dir, folder_name)

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

            # Search for chat only once
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
            current_dir = os.getcwd()
            folder_name = "whatsapp_profile"
            profile_folder_path = os.path.join(current_dir, folder_name)

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

