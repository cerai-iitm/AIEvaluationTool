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
from utils import *

logger = get_logger("whatsapp_driver")


def get_ui_response_whatsapp():
    return {"ui": "Whatsapp Web Chat Interface", "features": ["smart-compose", "modular-layout"]}

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
        logger.info(f"Searching for contact: {llm_name}")
        search_input_xpath = '//div[@aria-label="Search input textbox" and @contenteditable="true"]'
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, search_input_xpath))
        )
        search_box.click()
        # @bugfix -- sudar 02.08.2025
        # clear the box before typing a new string.
        search_box.clear()
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

def send_message(driver: webdriver.Chrome, prompt: str, max_retries: int = 3):
    """
    Sends a prompt to WhatsApp Web and retrieves responses after the last sent message.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            if not check_and_recover_connection():
                return "Failed: Internet unavailable"
            
            logger.info(f"Sending prompt to the bot: {prompt}")
            # @bugfix.  The XPath has changed! -- Sudar 02.08.2025
            #message_box_xpath = '//div[@aria-label="Type a message" and @contenteditable="true"]'
            message_box_xpath = '//div[@aria-placeholder="Type a message" and @contenteditable="true"]'
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

                old_response_texts = response_texts.copy()
                response_texts = []
                for msg in responses:
                    try:
                        text_elem = msg.find_element(By.CSS_SELECTOR, "span.selectable-text")
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

def send_prompt_whatsapp(chat_id: int, prompt_list: List[str], mode: str = "single_window") -> list[dict]:
    global cached_driver
    results = []

    if mode == "single_window":
        profile_folder_path = os.path.expanduser('~') + "/whatsapp_profile"  # For testing purposes
        logger.info(f"Using profile folder: {profile_folder_path}")

        if is_profile_in_use(profile_folder_path) and cached_driver is not None:
            driver = cached_driver
            logger.info("Chrome with this session is already running. Reusing the session.")
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
            driver.get(load_config().get("whatsapp_url"))
            cached_driver = driver  # Cache the driver for reuse
        
        try:
            chat_found = False
            while chat_found is False:
                logger.debug("Waiting for chat to be found...")
                time.sleep(0.5)
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
            pass
            #driver.quit()
    else:
        raise ValueError("Invalid mode: choose 'single_window'.")

    return results

def close_whatsapp():
    """
    Close the WhatsApp Web session.
    """
    global cached_driver
    if cached_driver is not None:
        try:
            cached_driver.quit()
            logger.info("Closing WhatsApp Web session...")
            logger.info("WhatsApp Web session closed successfully.")
            cached_driver = None  # Clear the cached driver
            profile_folder_path = os.path.expanduser('~') + "/whatsapp_profile"
            close_chrome_with_profile(profile_folder_path)
        except Exception as e:
            logger.error(f"Error closing WhatsApp Web session: {e}")
    else:
        logger.warning("No active WhatsApp Web session to close.")
        profile_folder_path = os.path.expanduser('~') + "/whatsapp_profile"
        close_chrome_with_profile(profile_folder_path)

def close(driver: webdriver.Chrome):
    """
    Close the browser session.
    """
    try:
        driver.quit()
        logger.info("Browser session closed.")
    except Exception as e:
        logger.warning(f"Error closing browser: {e}")

