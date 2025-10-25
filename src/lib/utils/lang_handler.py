# @author Sudarsun S
# @date 24/10/2025
# Library utility to detect and translate text from one language to another using Google Translate API.

from typing import Optional
from googletrans import Translator
import asyncio
from iso639 import Language

def lang_translate(text: str, target_language: str = "en") -> str:
    """
    Translate the given text to the target language using Google Translate API.
    :param text: The text to be translated.
    :param target_language: The target language code (default is 'en' for English).
    :return: Translated text.
    """
    translator = Translator()
    translation = asyncio.run(translator.translate(text, dest=target_language))
    return translation.text

def lang_detect(text: str) -> str:
    """
    Detect the language of the given text using Google Translate API.
    :param text: The text whose language is to be detected.
    :return: Detected language code.
    """
    translator = Translator()
    detection = asyncio.run(translator.detect(text))
    return detection.lang

def iso639_to_language_name(lang_code: str) -> Optional[str]:
    """
    Convert ISO 639 language code to language name.
    :param lang_code: ISO 639 language code.
    :return: Language name.
    """
    if len(lang_code) == 2:
        return Language.from_part1(lang_code).name.lower()
    elif len(lang_code) == 3:
        return Language.from_part3(lang_code).name.lower()
    
    raise ValueError(f"Invalid ISO 639 language code: {lang_code}")

def language_name_to_iso639(lang_name: str, need_part3=False) -> Optional[str]:
    """
    Convert language name to ISO 639 language code.
    :param lang_name: Language name.
    :return: ISO 639 language code (2 or 3 letters code).
    """
    lang_name = lang_name.title() # Capitalize first letter to match Language enum
    lang = Language.from_name(lang_name)
    return lang.part3 if need_part3 else lang.part1

# Test
# result = asyncio.run(lang_translate("Bonjour tout le monde", target_language="en"))
# print("Translated Text:", result)
# detected_lang = asyncio.run(lang_detect("Bonjour tout le monde"))
# print("Detected Language:", detected_lang)