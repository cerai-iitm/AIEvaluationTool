
import time
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from logger import get_logger
from utils import *

logger = get_logger("webapp_driver")

def get_ui_response_webapp():
    return {"ui": "Web Application Chat Interface", "features": ["smart-compose", "modular-layout"]}

def login_webapp(driver, app_name: str) -> bool:
    match app_name.lower():
        case "cpgrams":
            try:
                login_cfg = load_xpaths()["applications"]["cpgrams"]["LoginPage"]
                logout_cfg = load_xpaths()["applications"]["cpgrams"]["LogoutPage"]
                cred_cfg = load_creds()["applications"]["cpgrams"]

                if is_logged_in(driver, profile_element=logout_cfg["profile_element"]):
                    logger.info(f"Already logged in to {app_name.upper()}")
                    return True

                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, login_cfg["email_input_element"]))).send_keys(cred_cfg["username"])
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, login_cfg["password_input_element"]))).send_keys(cred_cfg["password"])
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, login_cfg["login_button_element"]))).click()
                return True
            except Exception as e:
                logger.error(f"CPGRAMS login failed: {e}")
                return False

        case "openweb-ui":
            try:
                login_cfg = load_xpaths()["applications"]["openweb-ui"]["LoginPage"]
                logout_cfg = load_xpaths()["applications"]["openweb-ui"]["LogoutPage"]
                cred_cfg = load_creds()["applications"]["openweb-ui"]

                if is_logged_in(driver, profile_element=logout_cfg["profile_element"]):
                    logger.info(f"Already logged in to {app_name.upper()}")
                    return True

                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, login_cfg["email_input_element"]))).send_keys(cred_cfg["username"])
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, login_cfg["password_input_element"]))).send_keys(cred_cfg["password"])
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, login_cfg["login_button_element"]))).click()
                return True
            except Exception as e:
                logger.error(f"OpenWeb UI login failed: {e}")
                return False

        case _:
            raise ValueError(f"Unsupported application: {app_name}")

def logout_webapp(driver, app_name: str) -> bool:
    match app_name.lower():
        case "cpgrams":
            try:
                logout_cfg = load_xpaths()["applications"]["cpgrams"]["LogoutPage"]
                if not is_logged_in(driver, profile_element=logout_cfg["profile_element"]):
                    logger.info(f"Already logged out of {app_name}")
                    return True

                safe_click(driver, logout_cfg["profile_element"])
                safe_click(driver, logout_cfg["logout_button_element"])
                driver.quit()
                return True
            except Exception as e:
                logger.error(f"CPGRAMS logout failed: {e}")
                return False

        case "openweb-ui":
            try:
                logout_cfg = load_xpaths()["applications"]["openweb-ui"]["LogoutPage"]
                if not is_logged_in(driver, profile_element=logout_cfg["profile_element"]):
                    logger.info(f"Already logged out of {app_name}")
                    return True
                
                safe_click(driver, logout_cfg["profile_element"])
                safe_click(driver, logout_cfg["logout_button_element"])
                driver.quit()
                return True
            except Exception as e:
                logger.error(f"OpenWeb-UI logout failed: {e}")
                return False

        case _:
            raise ValueError(f"Unsupported application: {app_name}")


def search_llm(driver: webdriver.Chrome) -> bool:
    """
    Searching for the local models in OpenUI interface
    """ 
    app_name = load_config().get("application_name")
    agent_name = load_config().get("agent_name")
    cfg = load_xpaths()["applications"]["openweb-ui"]["ChatPage"]

    try:
        if login_webapp(driver=driver, app_name=app_name):
            logger.info(f"Launched the OpenUI Interface")
            button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, cfg["model_selection_element"]))
            )
            button.send_keys(Keys.RETURN)

            time.sleep(2)
            logger.info(f"Searching for the '{agent_name}' in Ollama Server")
            model_searching = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.ID, cfg["model_name_entry_element"]))
            )
            model_searching.send_keys(agent_name)
            model_searching.send_keys(Keys.RETURN)
            logger.info(f"'{agent_name}' selected for Interaction")
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Could not find model '{agent_name}': \n{e}")
        return False


def send_message(driver, app_name: str, prompt: str, max_retries: int = 3) -> str:
    match app_name.lower():
        case "cpgrams":
            cfg = load_xpaths()["applications"]["cpgrams"]["ChatPage"]
            for attempt in range(max_retries):
                try:
                    if not check_and_recover_connection():
                        return "[Failed: Internet unavailable]"

                    chat_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, cfg["prompt_input_box_element"]))
                    )
                    chat_input.clear()
                    chat_input.send_keys(prompt)
                    chat_input.send_keys(Keys.ENTER)

                    WebDriverWait(driver, 50).until(
                        lambda d: len(d.find_elements(By.XPATH, cfg["agent_response_element"])) > 0
                    )
                    time.sleep(3)
                    messages = driver.find_elements(By.XPATH, cfg["agent_response_element"])
                    return messages[-1].text.strip() if messages else "[No response]"
                except Exception as e:
                    logger.warning(f"Retry {attempt+1}/{max_retries} failed: {e}")
            return "[Error: Max retries exceeded]"

        case "openweb-ui":
            cfg = load_xpaths()["applications"]["openweb-ui"]["ChatPage"]
            for attempt in range(max_retries):
                try:
                    if not check_and_recover_connection():
                        return "[Failed: Internet Connection]"

                    chat_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, cfg['prompt_input_box_element']))
                    )
                    chat_input.clear()
                    chat_input.send_keys(prompt)
                    time.sleep(2)
                    chat_input.send_keys(Keys.ENTER)

                    time.sleep(20)

                    WebDriverWait(driver, 50).until(
                        lambda d: len(d.find_elements(By.XPATH, cfg["agent_response_element"])) > 0
                    )
                    time.sleep(3)
                    messages = driver.find_elements(By.XPATH, cfg["agent_response_element"])
                    return messages[-1].text.strip() if messages else "[No response]"
                except Exception as e:
                    logger.warning(f"Retry {attempt+1}/{max_retries} failed: {e}")
            return "[Error: Max retries exceeded]"

        case _:
            raise ValueError(f"Unsupported application: {app_name}")

def send_prompt(app_name: str, chat_id: int, prompt_list: List[str], mode: str = "single_window") -> list[dict]:
    results = []
    driver = get_driver(app_name)
    logout_cfg = load_xpaths()["applications"]["openweb-ui"]["LogoutPage"]

    if not is_logged_in(driver, profile_element=logout_cfg["profile_element"]):
        login_ok = login_webapp(driver, app_name)
    else:
        login_ok = True
    for prompt in prompt_list:
        result = {"chat_id": chat_id, "prompt": prompt, "response": "Not available"}
        if login_ok:
            result["response"] = send_message(driver, app_name, prompt)
        results.append(result)

    return results

def close_webapp(app_name: str):
    global cached_driver
    if cached_driver is not None:
        try:
            cached_driver.quit()
            cached_driver.close()
            logger.info(f"Closed session for {app_name}")
        except Exception as e:
            logger.warning(f"Error while closing driver for {app_name}: {e}")
        finally:
            # Kill leftover chrome processes tied to this profile
            profile_path = os.path.expanduser("~") + "/test_profile"
            close_chrome_with_profile(profile_path)
            cached_driver = None
    else:
        logger.info(f"No active driver to close for {app_name}")
  
