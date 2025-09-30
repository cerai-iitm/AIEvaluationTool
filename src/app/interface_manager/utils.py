
import os
import time
import json
import socket
import psutil
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
from logger import get_logger


logger = get_logger("webapp_driver")
cached_driver = None

def load_config():
    with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as file:
        return json.load(file)
    
def load_xpaths():
    with open(os.path.join(os.path.dirname(__file__), 'xpaths.json'), 'r') as file:
        return json.load(file)

def load_creds():
    with open(os.path.join(os.path.dirname(__file__), 'credentials.json'), 'r') as file:
        return json.load(file)

# -------------------------------
# Connectivity Helpers
# -------------------------------
def check_and_recover_connection() -> bool:
    if not is_connected(host="8.8.8.8", port=53, timeout=3):
        logger.warning("Internet connection lost.")
        return retry_on_internet()
    logger.info("Device is connected to the internet.")
    return True


def is_connected(host: str="8.8.8.8", port: int=53, timeout: int=3) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        logger.error(f"Network down: {ex}")
        return False


def retry_on_internet(max_attempts=5, initial_delay=3, max_delay=60) -> bool:
    delay = initial_delay
    logger.info("Checking internet connectivity...")
    for attempt in range(1, max_attempts + 1):
        if is_connected(host="8.8.8.8", port=53, timeout=3):
            logger.info("Device is connected to the internet.")
            return True
        logger.warning(f"Attempt {attempt}/{max_attempts}. Retrying in {delay}s...")
        time.sleep(delay)
        delay = min(delay * 2, max_delay)
    logger.error("Device remains disconnected after all retry attempts.")
    return False

def get_driver(app_name: str):
    global cached_driver

    cfg = load_config()
    profile_folder_path = os.path.expanduser('~') + "/test_profile"
    url = cfg.get("application_url")

    if is_profile_in_use(profile_folder_path) and cached_driver is not None:
        logger.info(f"Reusing existing Chrome session for {app_name}")
        return cached_driver

    if cached_driver is not None:
        try:
            cached_driver.quit()
        except Exception as e:
            logger.warning(f"Error closing old driver: {e}")

    close_chrome_with_profile(profile_folder_path)

    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--start-maximized")
    opts.add_argument(f"user-data-dir={profile_folder_path}")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    logger.info(f"Launching {app_name} at {url}")
    driver.get(url)

    cached_driver = driver
    return driver


def is_logged_in(driver: webdriver.Chrome, profile_element: str) -> bool:
    try:
        # Example: check for profile icon or dashboard element
        profile_element_xpath = profile_element
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, profile_element_xpath))
        )
        return True
    except Exception:
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