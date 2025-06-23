import logging
import warnings
from langdetect import detect
from googletrans import Translator
from transformers import AutoModelForCausalLM, AutoTokenizer

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

def sarvam_translate(text: str, target_lang: str = "en") -> str:
    """
    Helper function to translate text to a specified language using Sarvam model.
    :param text: The text to be translated.
    :param target_lang: The target language code (default is English).
    :return: The translated text.
    """
    logger.info(f"Translating text to {target_lang}: {text} using Sarvam Model")
    model_name = "sarvamai/sarvam-translate"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name).to('cuda:0')
    messages = [
        {"role": "system", "content": f"Translate the text below to {target_lang}."},
        {"role": "user", "content": text}
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # Tokenize and move input to model device
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    logger.info(f"Translating to {target_lang} ......")
    # Generate the output
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=1024,
        do_sample=True,
        temperature=0.01,
        num_return_sequences=1
    )
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
    output_text = tokenizer.decode(output_ids, skip_special_tokens=True)
    logger.info(f"Translated text: {output_text}")
    return output_text
