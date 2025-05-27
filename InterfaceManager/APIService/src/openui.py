# openui.py

import os
import time
import socket
import requests
from datetime import datetime
from config import settings
from selenium import webdriver
from typing import Optional
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.chrome.options import Options
from logger import get_logger

logger = get_logger("openui_driver")

driver: Optional[WebDriver] = None  # Global driver instance

def get_ui_response():
    return {"ui": "OpenUI Interface", "features": ["smart-compose", "modular-layout"]}

# helper functions
def is_connected(host: str, port: int, timeout: int) -> bool:
    '''
    Checking whether the device is connected to internet of not 
    '''
    host = settings.default_host
    port = settings.default_port
    timeout = settings.default_timeout
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        logger.error(f"Network down: {ex}")
        return False

def is_server_running(url: str, timeout: int=settings.server_timeout) -> bool:
    '''
    Checking whether the server is running or not
    '''
    url = settings.server_url
    timeout = settings.server_timeout
    try:
        response = requests.get(url)
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"Server unreachable at {url}: {e}")
        return False

def wait_for_server(url: str, retries: int, delay: int, max_delay=None, on_retry_callback=None) -> bool:
    '''
    Retry the automation function if server is down or a runtime exception occurs.
    '''
    url = settings.server_url
    retries = retries if retries is not None else settings.retries
    delay = delay if delay is not None else settings.retry_delay
    max_delay = max_delay if max_delay is not None else settings.max_retry_delay

    current_delay = delay
    for attempt in range(1, retries + 1):
        if is_server_running(url=url):
            logger.info(f"Server at {url} is up.")
            return True
        logger.warning(f"Attempt {attempt}/{retries}: Server not responding. Retrying in {current_delay}s...")

        if on_retry_callback:
            on_retry_callback(attempt, retries, current_delay)

        time.sleep(current_delay)
        current_delay = min(current_delay * 2, max_delay)

    logger.error(f"Server at {url} is not reachable after {retries} attempts.")
    return False

# login helper
def initiate_login(driver: webdriver.Chrome) -> bool:
    """
    Login initiation using email and password stored in environment variable
    """
    status: bool = False
    try:
        logger.info("Initiating OpenUI Login process..")
        EMAIL = settings.openui_email
        PASSWORD = settings.openui_password

        """
        Sending email and password to the site for login
        """
        logger.info("Entering Email and Password to access OpenUI")
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_input.send_keys(EMAIL)

        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_input.send_keys(PASSWORD)
        sign_in_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//button[@type="submit" and text()="Sign in"]'))
        )
        sign_in_btn.send_keys(Keys.RETURN)
        logger.info("Login Successful")        
        status = True
    except Exception as e:
        logger.error(f"Login failed: {e}")
    return status

def login_openui(driver: Optional[WebDriver]= None) -> bool:
    """
    Login with OpenUI using Selenium automation
    """
    driver = driver
    status: bool = False
    try:
        if not wait_for_server(url=settings.ollama_server_url, retries=5, delay=3, max_delay=10):
            logger.error("Ollama server is not reachable after multiple attempts")
            raise ConnectionError("Ollama server is not reachable after multiple attempts.")

        if driver is None:
            driver = webdriver.Chrome()
            driver.get(settings.server_url)

        if initiate_login(driver):
            status = True

    except Exception as e:
        logger.error(f"Error opening OpenUI Browse Interface: {e}")
    return status

# retry safe click logout helper
def safe_click(driver, selector: str, retries: int = 3, wait_time: int = 10) -> bool:
    """
    Safely clicks an element located by either XPath or CSS selector.
    """
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
    Logout via UI interactions.
    """
    try:
        logger.info("Initiating OpenUI Logout process...")

        profile_btn = 'button[aria-label="User Menu"]'
        sign_out_btn = '//button[.//div[text()="Sign Out"]]'
        
        # Click profile button
        if not safe_click(driver, profile_btn):
            logger.error("Failed to click profile button.")
            return False

        # Click sign out button
        if not safe_click(driver, sign_out_btn):
            logger.error("Failed to click sign-out button.")
            return False

        # Optional: wait until redirected or URL change
        WebDriverWait(driver, 5).until(EC.url_contains("/auth"))
        logger.info(f"Logout successful. Current URL: {driver.current_url}")
        return True
    except TimeoutException:
        logger.warning(f"Logout click sequence completed but no redirect detected. Current URL: {driver.current_url}")
        return True  # Still return True if actions succeeded but URL check failed
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return False

def logout_openui() -> bool:
    """
    Log out and close browser.
    """
    global driver
    try:
        if driver is None:
            logger.error("No active browser session.")
            return False

        logout_status = initiate_logout(driver)
        time.sleep(2)  
        driver.quit()
        logger.info("Browser session closed.")
        return logout_status
    except Exception as e:
        logger.error(f"Error during OpenUI logout: {e}")
        return False
    finally:
        driver = None

def search_llm(driver: webdriver.Chrome, llm_name: str) -> bool:
    """
    Searching for the local models in OpenUI interface
    """ 
    try:
        if login_openui(driver):
            logger.info(f"Launched the OpenUI Interface")
            model_selection_xpath = '//*[@id="model-selector-0-button"]'
            button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, model_selection_xpath))
            )
            button.send_keys(Keys.RETURN)

            time.sleep(2)
            logger.info(f"Searching for the '{llm_name}' in Ollama Server")
            model_searching = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.ID, "model-search-input"))
            )
            model_searching.send_keys(llm_name)
            model_searching.send_keys(Keys.RETURN)
            logger.info(f"'{llm_name}' selected for Interaction")
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Could not find model '{llm_name}': \n{e}")
        return False

def send_message(driver: webdriver.Chrome, prompt: str, max_retries: int=3):
    """
    Send prompt to the Ollama model using OpenUI Interface
    """
    attempt = 0
    while attempt < max_retries:
        try:
            if not is_server_running(url=settings.ollama_server_url, timeout=settings.server_timeout):
                return "[Failed: Server unavailable]"
            
            logger.info(f"Sending prompt: {prompt}")
            # Locate the message input box
            message_box_xpath = '//*[@id="chat-input"]/p'
            message_box = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, message_box_xpath))
            )
            message_box.click()
            message_box.send_keys(prompt)
            message_box.send_keys(Keys.RETURN)

            # Wait and capture latest incoming message
            time.sleep(15)
            
            elements = driver.find_elements(By.CSS_SELECTOR, "div#response-content-container")
            if elements:
                response = elements[-1].text  # Get the last element
                logger.info(f"Received response: {response}")
                return response
        except Exception as e:
            logger.error(f"Error during chat: {e}")
            return "[Error during chat]"
        
def send_prompt_openui(prompt: str) -> dict:
    """
    Send prompt and receive response from Ollama Server using OpenUI Interface
    """
    llm_name: str=settings.ollama_model_name
    # start_time = None 
    # end_time = None
    response_json = {
        "prompt": prompt,
        "response": "Not available"
    }

    try:
        if not is_server_running(url=settings.ollama_server_url, timeout=settings.server_timeout):
            return response_json
        
        opts = Options()
        opts.add_argument('--start-maximized')
        driver = webdriver.Chrome(options=opts)
        driver.get(settings.server_url)

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
    Close the browser automation
    """
    driver.close()
    logger.info("Browser closed")

    