import logging
import warnings
import requests
import time
from typing import Optional, List, Dict, Any, Type
from langdetect import detect
from googletrans import Translator
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import os
import torch
import requests
import asyncio
from typing import Any, Dict, List, Type, Optional

from opik.evaluation.metrics import GEval

from opik.evaluation.models import OpikBaseModel


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
    :param target_lang: The target language code (default is English)
    :return: The translated text in english
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
        {"role": "system", "content": f"Translate    the text below to {target_lang}."},
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

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)




try:
    from opik.evaluation.models import OpikBaseModel
except ImportError:
    OpikBaseModel = object


class CustomOllamaModel(OpikBaseModel):
    def __init__(self, model_name: str, base_url: str = "http://172.31.99.190:11434"):
        super().__init__(model_name)
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/chat"

    def generate_string(self, input: str, response_format: Optional[Type] = None, **kwargs: Any) -> str:
        messages = [{"role": "user", "content": f'{input} /nothink'}]
        response = self.generate_provider_response(messages, **kwargs)
    
        return response["choices"][0]["message"]["content"]

    def generate_provider_response(self, messages: List[Dict[str, Any]], **kwargs: Any) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
        }
        for k, v in kwargs.items():
            if isinstance(v, (str, int, float, bool, list, dict, type(None))):
                payload[k] = v
        try:
            logger.info(f"[Ollama] Sending request to {self.api_url}...")
            response = requests.post(self.api_url, json=payload, timeout=60,)
            response.raise_for_status()
            raw = response.json()
            logger.debug(f"[Ollama] Raw content: {raw}")
            content_text = raw.get("message", {}).get("content", "") 
            logger.info(content_text)
            final_response={
                "choices": [
                    {
                        "message": {
                            "content": content_text
                        }
                    }
                ]
            }
            logger.info(final_response)
            return final_response
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"[Ollama] HTTP error occurred: {http_err.response.text}", exc_info=True)
            raise
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"[Ollama] Connection error occurred: {conn_err}", exc_info=True)
            raise
        except requests.exceptions.Timeout as timeout_err:
            logger.error(f"[Ollama] Timeout occurred: {timeout_err}", exc_info=True)
            raise
        except requests.exceptions.RequestException as req_err:
            logger.error(f"[Ollama] Request failed: {req_err}", exc_info=True)
            raise
        except ValueError as parse_err:
            logger.error(f"[Ollama] Failed to parse response JSON: {parse_err}", exc_info=True)
            raise
        

    async def agenerate_string(self, input: str, response_format: Optional[Type] = None, **kwargs: Any) -> str:
        import asyncio
        return await asyncio.to_thread(self.generate_string, input, response_format, **kwargs)

    async def agenerate_provider_response(self, messages: List[Dict[str, Any]], **kwargs: Any) -> Any:
        import asyncio
        return await asyncio.to_thread(self.generate_provider_response, messages, **kwargs)

class SarvamModel:
    def __init__(self, model_id: str = "sarvamai/sarvam-2b-v0.5"):
        self.model_id = model_id
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)

        if torch.cuda.is_available():
            logger.info("Using GPU for hosting SarvamModel")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, torch_dtype=torch.float16, device_map="auto"
            )
        else:
            logger.info("Using CPU for hosting SarvamModel")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, torch_dtype=torch.float32
            ).to("cpu")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def generate(self, prompt: str, max_new_tokens: int = 1024) -> str:
        """
        Generate text continuation from a given prompt.
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        inputs = {k: v for k, v in inputs.items() if k in ['input_ids', 'attention_mask']}
        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def get_mean_pooled_embedding(self, text: str) -> torch.Tensor:
        """
        Return mean pooled embedding from last hidden state.
        """
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            last_hidden = outputs.hidden_states[-1] 
            embedding = last_hidden.mean(dim=1).squeeze()
        return embedding.cpu()
