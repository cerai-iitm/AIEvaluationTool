import logging
import warnings
from langdetect import detect
from googletrans import Translator

logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  
        logging.FileHandler("analyzer_log.log")  
    ]
)

logger = logging.getLogger(__name__)

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

async def google_lang_translate(text: str, target_lang: str = "en") -> str:
    """
    Helper function to translate text to english language using Google Translate.
    :param text: The text to be translated.
    :param target_lang: The target language code (default is English
    return: The translated text in english
    """
    translator = Translator()
    try:
        translation = await translator.translate(text, dest=target_lang)
        return translation.text
    except Exception as e:
        logger.error(f"Error in translation: {e}")
        return text
        
async def detect_text(text):
    """
    Helper function to translate text to a specified language.
    """
    translator = Translator()
    try:
        language = await translator.detect(text)
        return language.lang
    except Exception as e:
        logger.error(f"Error in language detection: {e}")
        return "unknown"