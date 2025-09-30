
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
    """
    Logout from the web application via UI interactions 
    """
    match app_name.lower():
        case "cpgrams":
            try:
                logout_cfg = load_xpaths()["applications"]["cpgrams"]["LogoutPage"]
                if not is_logged_in(driver, profile_element=logout_cfg["profile_element"]):
                    logger.info(f"Already logged out of {app_name}")
                    return True

                safe_click(driver, logout_cfg["profile_element"])
                safe_click(driver, logout_cfg["logout_button_element"])
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
    """
    Send prompt to the Web Application Interface with robust checks
    """
    match app_name.lower():
        case "cpgrams":
            cfg = load_xpaths()["applications"]["cpgrams"]["ChatPage"]
            if not cfg["prompt_input_box_element"]:
                logger.error("Prompt input box XPath missing for cpgrams.")
                return "[Error: Invalid XPath]"

            for attempt in range(max_retries):
                try:
                    # logger.info(f"Sending prompt (attempt {attempt+1}/{max_retries})")
                    if not check_and_recover_connection():
                        return "[Failed: Internet unavailable]"
                    
                    logger.info(f"Prompt sending to {app_name}: {prompt}")
                    previous_messages = driver.find_elements(
                        By.XPATH, cfg["agent_response_element"]
                    )
                    previous_count = len(previous_messages)

                    # Send prompt
                    chat_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            cfg["prompt_input_box_element"]
                        ))
                    )

                    chat_input.clear()
                    chat_input.click()
                    chat_input.send_keys(prompt)
                    chat_input.send_keys(Keys.RETURN)

                    # Wait until a new message appears
                    WebDriverWait(driver, 50).until(
                        lambda d: len(d.find_elements(
                            By.XPATH,
                            cfg["agent_response_element"]
                        )) > previous_count
                    )

                    time.sleep(5)  # let DOM stabilize

                    # Fetch latest message
                    bot_messages = driver.find_elements(
                        By.XPATH, cfg["agent_response_element"]
                    )
                    response = bot_messages[-1].text.strip() if bot_messages else "[No response received]"
                    logger.info(f"Received response: {response}")
                    return response

                except Exception as e:
                    logger.warning(f"Retry {attempt+1}/{max_retries} failed: {e}")

            return "[Error: Max retries exceeded]"

        case "openweb-ui":
            cfg = load_xpaths()["applications"]["openweb-ui"]["ChatPage"]
            input_xpath = cfg.get("prompt_input_box_element")
            if not input_xpath:
                logger.error("Prompt input box XPath missing for openweb-ui.")
                return "[Error: Invalid XPath]"

            config = load_config()
            if not is_server_running(url=config.get("ollama_server_url"), timeout=config.get("server_timeout")):
                return "[Failed: Server unavailable]"

            for attempt in range(max_retries):
                try:
                    # logger.info(f"Sending prompt (attempt {attempt+1}/{max_retries})")
                    logger.info(f"Prompt sending to {app_name}: {prompt}")

                    # Wait for element to be clickable
                    message_box = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, input_xpath))
                    )

                    if message_box is None:
                        raise ValueError("Message input element resolved to None")

                    message_box.clear()
                    message_box.click()
                    message_box.send_keys(prompt)
                    time.sleep(2)
                    message_box.send_keys(Keys.RETURN)

                    # Wait for agent response
                    wait = WebDriverWait(driver, 50)
                    wait.until(EC.presence_of_element_located((By.XPATH, cfg["agent_response_element"])))

                    elements = driver.find_elements(By.XPATH, cfg["agent_response_element"])
                    if elements:
                        response = elements[-1].text.strip()
                        logger.info(f"Received response: {response}")
                        return response

                except Exception as e:
                    logger.warning(f"Retry {attempt+1}/{max_retries} failed: {e}")

            return "[Error: Max retries exceeded]"

        case _:
            raise ValueError(f"Unsupported application: {app_name}")


def send_prompt(app_name: str, chat_id: int, prompt_list: List[str], mode: str = "single_window") -> list[dict]:
    """
    Send prompt and receive response from web application interfaces
    """
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
    """
    Gracefully logs out of the application (if possible) and then shuts down the browser session completely.
    If the Selenium driver fails, Chrome processes tied to the profile folder are force-killed.
    """
    global cached_driver
    profile_folder_path = os.path.expanduser('~') + "/test_profile"

    try:
        if is_profile_in_use(profile_path=profile_folder_path):
            cached_driver.quit()
            logger.info(f"Browser session closed for {app_name}")
    except Exception as e:
        logger.warning(f"Driver quit encountered an issue: {e}")

    finally:
        cached_driver = None

    # Kill any strays still using this profile
    if close_chrome_with_profile(profile_folder_path):
        logger.info("Closed stray Chrome processes using profile.")

    return True


