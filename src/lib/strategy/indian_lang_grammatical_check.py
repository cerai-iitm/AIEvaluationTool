import requests
import difflib
import os 
import re
import warnings
from typing import Optional
import numpy as np
import json
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader
import regex
from ollama import Client
import Levenshtein

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("indian_lang_grammatical_check")

class IndianLangGrammaticalCheck(Strategy):
    def __init__(self, model=None, tokenizer=None, name="indian_lang_grammatical_check", **kwargs):
        super().__init__(name, **kwargs)
        self.gpu_url=os.getenv("GPU_URL")
        self.ollama_url = os.getenv("OLLAMA_URL")

        if not self.gpu_url:
            logger.warning("GPU_URL is not set in environment.")
        else:
            logger.info("GPU_URL is loaded from environment.")

        
    def make_prompt(self, sent:str):
        text = f'''
        <|system|>
        Correct the grammar of the input sentences. 
        Return the corrected sentences in the same language as the input.

        <|user|>
        {sent}

        <|assistant|>      
        '''
        return text
    
    def ollama_connect(self, text:str):
        ollama_client = Client(host=self.ollama_url)
        response = ollama_client.chat(
            model = "qwen2.5:14b",
            messages = [
                {
                    "role" : "user",
                    "content" : f"{text} /nothink",
                }
            ],
            format="json"
        )
        return response.message.content

    def embed(self, text:str):
        return json.loads(requests.post(f"{self.gpu_url}/embedding", params={"input_text" : text}).content.decode('utf-8'))
        
    def evaluate(self, agent_response:str, expected:Optional[str]=None):
        prompting = self.make_prompt(agent_response)
        full_correct = list(json.loads(self.ollama_connect(prompting)).values())
        final_op = full_correct[0] if len(full_correct) < 2 else full_correct[1]
        a , b = self.embed(agent_response), self.embed(final_op)
        sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        dist = Levenshtein.distance(agent_response, full_correct)
        max_dist = max(len(final_op), len(agent_response))
        score = 0.5 * (1 - (dist / max_dist)) + 0.5 * sim
        print(score)

if __name__ == "__main__":
    checker = IndianLangGrammaticalCheck()
    sent = "मैं कल स्कूल जाता हूँ था लेकिन दोस्त नहीं आया थे।"
    score = checker.evaluate(sent)