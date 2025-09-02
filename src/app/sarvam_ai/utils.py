from langdetect import detect
from logger import get_logger
import warnings
logger = get_logger("app_utils_calls")
warnings.filterwarnings("ignore")

def language_detection(text: str) -> str:
    """
    Detect the language of the given text.
    :param text: The text to be analyzed.
    :return: The detected language code.
    """
    try:
        language =detect(text)
        logger.info(f"Detected language: {language}")
        return language
    except Exception as e:
        logger.error(f"Error in language detection: {e}")
        return "unknown"