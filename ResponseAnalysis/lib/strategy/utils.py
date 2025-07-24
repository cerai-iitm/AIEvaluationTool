import json
import logging
import warnings
import requests
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
from opik.evaluation.models import OpikBaseModel
from .logger import get_logger
import torch
import torch.nn as nn
import traceback
from transformers import BartTokenizer, BartForConditionalGeneration
from typing import List
import numpy as np
import re
from collections import defaultdict

logger = get_logger("utils_calls")

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

def RtA(data, key='eval_res', refusal_label="LABEL_0", return_count=False):
        """
        Calculates the ratio of items in a list of dictionaries where the specified key's value equals the refusal label.

        Args:
            data (list of dict): The list of dictionaries to check.
            key (str): The key to check in the dictionaries. Defaults to 'eval_res'.
            refusal_label (str): The label that signifies refusal to answer. Defaults to 'LABEL_0'.

        Returns:
            float: The ratio of items where the key's value is the refusal label. Returns 0 if the list is empty.
        """

        assert isinstance(data, list), "Data should be a list of dictionaries"
        assert all(isinstance(d, dict) for d in data), "All elements in data should be dictionaries"
        assert isinstance(key, str), "Key should be a string"
        assert isinstance(refusal_label, str), "Refusal label should be a string"

        count = sum(1 for item in data if item.get(key) == refusal_label)

        rta_ratio = count / len(data) if data else 0
        if return_count:
            return rta_ratio, count
        return rta_ratio

def get_key_by_value(dictionary, value):
    for key, val in dictionary.items():
        if val == value:
            return key
    return None

def extract_from_uds(txt):
    new_txt = txt.split("_")
    return new_txt[-1]


try:
    from opik.evaluation.models import OpikBaseModel
except ImportError:
    OpikBaseModel = object

class DotDict:
    """
    A class to convert a dictionary to have dot notation access.
    Allows accessing dictionary keys as attributes.
    """
    def __init__(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                setattr(self, key, self._convert(value))
       
    def _convert(self, value):
        if isinstance(value, dict):
            return DotDict(value)
        elif isinstance(value, list):
            return [self._convert(item) for item in value]
        else:
            return value


class CustomOllamaModel(OpikBaseModel):
    def __init__(self, model_name: str, base_url: str = os.getenv("OLLAMA_URL")):
        super().__init__(model_name)
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/chat"

    def generate_string(self, input: str, response_format: Optional[Type] = None, **kwargs: Any) -> Any:
        messages = [{"role": "user", "content": f'{input} /nothink'}]
        response = self.generate_provider_response(messages, **kwargs)
        #response = DotDict(response)
        return response.choices[0].message.content
        # return response["choices"][0]["message"]["content"]

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
            print(raw)
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
            final_response= DotDict(final_response)
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
    
class BARTScorer:
    def __init__(self, device='cuda:0', max_length=1024, checkpoint='facebook/bart-large-cnn'):
        # Set up model
        self.device = device
        self.max_length = max_length
        self.tokenizer = BartTokenizer.from_pretrained(checkpoint)
        self.model = BartForConditionalGeneration.from_pretrained(checkpoint)
        self.model.eval()
        self.model.to(device)

        # Set up loss
        self.loss_fct = nn.NLLLoss(reduction='none', ignore_index=self.model.config.pad_token_id)
        self.lsm = nn.LogSoftmax(dim=1)

    def load(self, path=None):
        """ Load model from paraphrase finetuning """
        if path is None:
            path = 'models/bart.pth'
        self.model.load_state_dict(torch.load(path, map_location=self.device))

    def score(self, srcs, tgts, batch_size=4):
        """ Score a batch of examples """
        score_list = []
        for i in range(0, len(srcs), batch_size):
            src_list = srcs[i: i + batch_size]
            tgt_list = tgts[i: i + batch_size]
            try:
                with torch.no_grad():
                    encoded_src = self.tokenizer(
                        src_list,
                        max_length=self.max_length,
                        truncation=True,
                        padding=True,
                        return_tensors='pt'
                    )
                    encoded_tgt = self.tokenizer(
                        tgt_list,
                        max_length=self.max_length,
                        truncation=True,
                        padding=True,
                        return_tensors='pt'
                    )
                    src_tokens = encoded_src['input_ids'].to(self.device)
                    src_mask = encoded_src['attention_mask'].to(self.device)

                    tgt_tokens = encoded_tgt['input_ids'].to(self.device)
                    tgt_mask = encoded_tgt['attention_mask']
                    tgt_len = tgt_mask.sum(dim=1).to(self.device)

                    output = self.model(
                        input_ids=src_tokens,
                        attention_mask=src_mask,
                        labels=tgt_tokens
                    )
                    logits = output.logits.view(-1, self.model.config.vocab_size)
                    loss = self.loss_fct(self.lsm(logits), tgt_tokens.view(-1))
                    loss = loss.view(tgt_tokens.shape[0], -1)
                    loss = loss.sum(dim=1) / tgt_len
                    curr_score_list = [-x.item() for x in loss]
                    score_list += curr_score_list

            except RuntimeError:
                traceback.print_exc()
                print(f'source: {src_list}')
                print(f'target: {tgt_list}')
                exit(0)
        return score_list

    def multi_ref_score(self, srcs, tgts: List[List[str]], agg="mean", batch_size=4):
        # Assert we have the same number of references
        ref_nums = [len(x) for x in tgts]
        if len(set(ref_nums)) > 1:
            raise Exception("You have different number of references per test sample.")

        ref_num = len(tgts[0])
        score_matrix = []
        for i in range(ref_num):
            curr_tgts = [x[i] for x in tgts]
            scores = self.score(srcs, curr_tgts, batch_size)
            score_matrix.append(scores)
        if agg == "mean":
            score_list = np.mean(score_matrix, axis=0)
        elif agg == "max":
            score_list = np.max(score_matrix, axis=0)
        else:
            raise NotImplementedError
        return list(score_list)

    def test(self, batch_size=3):
        """ Test """
        src_list = [
            'This is a very good idea. Although simple, but very insightful.',
            'Can I take a look?',
            'Do not trust him, he is a liar.'
        ]

        tgt_list = [
            "That's stupid.",
            "What's the problem?",
            'He is trustworthy.'
        ]

        print(self.score(src_list, tgt_list, batch_size))


def average_dicts(dict_list):
    if not dict_list:
        return {}

    totals = defaultdict(float)
    count = len(dict_list)

    for d in dict_list:
        for key, value in d.items():
            totals[key] += value

    return {key: totals[key] / count for key in totals}

def extract_score(s):
    try:
        if isinstance(s, (int, float)):
            return float(s)
        elif isinstance(s, str):
            try:
                # Extract first float-like pattern from the string
                match = re.search(r"\d+\.\d+", s)
                return float(match.group()) if match else 0
            except Exception:
                return 0
        elif isinstance(s, (list, tuple)) and s:
            return extract_score(s[0])
        elif isinstance(s, dict):
            if 'overall' in s:
                return extract_score(s['overall'])
            elif 'score' in s:
                return extract_score(s['score'])
            else:
                return 0
        else:
            return 0
    except Exception:
        return 0



