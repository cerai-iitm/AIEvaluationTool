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

from typing import List

logger = get_logger("cpgrams_driver")

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


def open_chat_interface(driver: webdriver.Chrome) -> bool:
    """
    Opens and verifies CPGRAMS chat interface.
    """
    try:
        if not check_and_recover_connection():
            return False
        logger.info("CPGRAMS web chat interface opened successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing chat interface: {e}")
        return False


# -------------------------------
# Main Function
# -------------------------------
def send_prompt_cpgrams(chat_id: int, prompt_list: List[str], mode: str = "single_window") -> list[dict]:
    """
    Send a list of prompts to the CPGRAMS chat interface.
    No session profiles are used.
    """
    results = []

    def launch_driver():
        opts = Options()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--start-maximized")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=opts)

    if mode == "single_window":
        driver = launch_driver()
        try:
            driver.get(load_config().get("application_url"))
            time.sleep(3)

            chat_found = open_chat_interface(driver)
            for prompt in prompt_list:
                result = {"chat_id": chat_id, "prompt": prompt, "response": "Not available"}
                if chat_found:
                    result["response"] = send_message(driver, prompt)
                else:
                    result["response"] = "Chat not found"
                results.append(result)
        finally:
            driver.quit()

    elif mode == "multi_window":
        for prompt in prompt_list:
            driver = launch_driver()
            try:
                driver.get(load_config().get("application_url"))
                time.sleep(3)

                result = {"chat_id": chat_id, "prompt": prompt, "response": "Not available"}
                if open_chat_interface(driver):
                    result["response"] = send_message(driver, prompt)
                else:
                    result["response"] = "Chat not found"
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
