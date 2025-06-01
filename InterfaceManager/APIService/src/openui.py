# openui.py

import time
import json
import socket
import requests
from selenium import webdriver
from typing import Optional
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.chrome.options import Options
from logger import get_logger
from typing import List

logger = get_logger("openui_driver")

driver: Optional[WebDriver] = None  # Global driver instance

def get_ui_response():
    return {"ui": "OpenUI Interface", "features": ["smart-compose", "modular-layout"]}

def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

# helper functions
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

def is_server_running(url: str, timeout: int) -> bool:
    '''
    Checking whether the server is running or not
    '''
    config = load_config()

    url = config.get("server_url")
    timeout = config.get("server_timeout")
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
    config = load_config()

    url = config.get("server_url")
    retries = retries if retries is not None else config.get("retries")
    delay = delay if delay is not None else config.get("retry_delay")
    max_delay = max_delay if max_delay is not None else config.get("max_retry_delay")

    current_delay = delay
    for attempt in range(1, retries + 1):
        if is_server_running(url=url, timeout=config.get("default_timeout")):
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
    config = load_config()

    status: bool = False
    try:
        logger.info("Initiating OpenUI Login process..")
        EMAIL = config.get("openui_email")
        PASSWORD = config.get("openui_password")

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
    config = load_config()
    driver = driver
    status: bool = False
    try:
        if not wait_for_server(url=config.get("ollama_server_url"), retries=5, delay=3, max_delay=10):
            logger.error("Ollama server is not reachable after multiple attempts")
            raise ConnectionError("Ollama server is not reachable after multiple attempts.")

        if driver is None:
            driver = webdriver.Chrome()
            driver.get(config.get("server_url"))

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
        
        if not safe_click(driver, profile_btn):
            logger.error("Failed to click profile button.")
            return False

        if not safe_click(driver, sign_out_btn):
            logger.error("Failed to click sign-out button.")
            return False

        WebDriverWait(driver, 5).until(EC.url_contains("/auth"))
        logger.info(f"Logout successful. Current URL: {driver.current_url}")
        return True
    except TimeoutException:
        logger.warning(f"Logout click sequence completed but no redirect detected. Current URL: {driver.current_url}")
        return True  
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

def search_llm(driver: webdriver.Chrome) -> bool:
    """
    Searching for the local models in OpenUI interface
    """ 
    llm_name = load_config().get("model_name")
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
    config = load_config()
    attempt = 0
    while attempt < max_retries:
        try:
            if not is_server_running(url=config.get("ollama_server_url"), timeout=config.get("server_timeout")):
                return "[Failed: Server unavailable]"
            
            logger.info(f"Sending prompt")
            
            message_box_xpath = '//*[@id="chat-input"]/p'
            message_box = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, message_box_xpath))
            )
            message_box.click()
            message_box.send_keys(prompt)
            time.sleep(2)
            message_box.send_keys(Keys.RETURN)
            
            time.sleep(15)
            
            wait = WebDriverWait(driver, 50)
            element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="response-content-container"]')))
            
            if element:
                response = element.text
                logger.info(f"Received response: {response}")
                return response
        except Exception as e:
            logger.error(f"Error during chat: {e}")
            return "[Error during chat]"
        
def send_prompt_openui(chat_id: int, prompt_list: List[str], mode: str = "single_window") -> list[dict]:
    """
    Send prompt and receive response from Ollama Server using OpenUI Interface
    """
    results = []

    if mode == "single_window":
        opts = Options()
        opts.add_argument("--start-maximized")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)

        try:
            driver.get(load_config().get("server_url"))
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
            opts = Options()
            opts.add_argument("--start-maximized")
            opts.add_experimental_option("excludeSwitches", ["enable-logging"])

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=opts)

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=opts)
            
            try:
                driver.get(load_config().get("server_url"))
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
    Close the browser automation
    """
    driver.close()
    logger.info("Browser closed")

    
