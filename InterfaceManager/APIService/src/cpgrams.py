# cpgrams.py

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
from logger import get_logger

from typing import List

logger = get_logger("cpgrams_driver")

def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

def get_ui_response():
    return {"ui": "CPGRAMS Chat Interface", "features": ["smart-compose", "modular-layout"]}

# helper functions
def check_and_recover_connection() -> bool:
    """
    Check internet and attempt reconnection if disconnected.
    Logs the device's connectivity status.
    """
    config = load_config()
    print(f"[DEBUG] Keys in config: {list(config.keys())}")
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

# def is_profile_in_use(profile_path):
#     """Check if any Chrome process is using the given user-data-dir."""
#     for proc in psutil.process_iter(['name', 'cmdline']):
#         try:
#             if 'chrome' in proc.info['name'].lower():
#                 cmdline = ' '.join(proc.info['cmdline'])
#                 if f"user-data-dir={profile_path}" in cmdline:
#                     return True
#         except (psutil.NoSuchProcess, psutil.AccessDenied):
#             continue
#     return False

def is_profile_in_use(profile_folder_path):
    for proc in psutil.process_iter(attrs=["cmdline"]):
        cmdline = proc.info.get("cmdline")
        if not cmdline:  # None or empty
            continue
        # Ensure it's a list before joining
        if isinstance(cmdline, (list, tuple)):
            cmdline_str = " ".join(cmdline)
        else:
            cmdline_str = str(cmdline)

        if profile_folder_path in cmdline_str:
            return True
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
    Sends a prompt to CPGRAMS Web chat interface and retrieves responses after the last sent message.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            if not check_and_recover_connection():
                return "[Failed: Internet unavailable]"
            
            logger.info(f"Sending prompt to the bot: {prompt}")

            try:
                # Get current messages before sending
                previous_messages = driver.find_elements(
                    By.XPATH,
                    "//div[@class='leading-relaxed text-sm']/p"
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

                time.sleep(10)  # Give DOM a moment to settle

                # Fetch latest message
                bot_messages = driver.find_elements(
                    By.XPATH,
                    "//div[@class='leading-relaxed text-sm']/p"
                )

                new_response = bot_messages[-1].text.strip()
                logger.info(f"Prompt: {prompt}\nResponse: {new_response}")
                if new_response:
                    return new_response
                else:
                    logger.warning("No response message found.")
                    return ["[No response received]"]

            except Exception as e:
                logger.error(f"Error while getting bot response: {str(e)}")
                return f"Error: {str(e)}"

        except Exception as e:
            attempt += 1
            logger.error(f"Chat attempt {attempt} failed: {e}")
            if attempt < max_retries:
                logger.info("Retrying chat...")
                time.sleep(0.3)
            else:
                return ["[Error during chat after retries]"]

def open_chat_interface() -> bool:
    """
    Opens and verifies CPGRAMS chat interface using Selenium driver.
    """
    try:
        if not check_and_recover_connection():
            return False

        logger.info("Initiating CPGRAMS web interface process..")
        logger.info("CPGRAMS web chat interface opened successfully")
        return True

    except Exception as e:
        logger.error(f"Error initializing CPGRAMS web chat interface: {e}")
        return False
    

def send_prompt_cpgrams(chat_id: int, prompt_list: List[str], mode: str = "single_window") -> list[dict]:
    results = []

    if mode == "single_window":
        #temp_dir = tempfile.gettempdir()
        #folder_name = "whatsapp_profile"
        #profile_folder_path = os.path.join(temp_dir, folder_name)

        profile_folder_path = os.path.expanduser('~') + "/web_profile"  # For testing purposes
        logger.info(f"Using profile folder: {profile_folder_path}")

        if is_profile_in_use(profile_folder_path):
            logger.info("Chrome with this session is already running. Attempting to close it...")
            if close_chrome_with_profile(profile_folder_path):
                logger.info("Successfully closed the Chrome instance using this session.")
                time.sleep(2)  # Wait for processes to terminate
            else:
                logger.error("Failed to close. Possibly due to permission or timing issues.")
                time.sleep(2)  # Wait before retrying
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
            driver.get(load_config().get("application_url"))
            time.sleep(5)

            chat_found = open_chat_interface()
            print(chat_found)
            
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

            profile_folder_path = os.path.expanduser('~') + "/web_profile"
            
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
                driver.get(load_config().get("application_url"))
                time.sleep(5)

                result = {"chat_id": chat_id, "prompt": prompt, "response": "Not available"}

                try:
                    if open_chat_interface(driver):
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

