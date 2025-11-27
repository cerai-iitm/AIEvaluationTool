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
from .llm_judge import LLMJudgeStrategy

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
        text = f"""
            <|system|>
            You are a grammar-correction assistant.  
            If the input paragraph is already grammatically correct, return it unchanged.  
            Otherwise, correct the grammar while keeping the original language.  
            Do not translate the text into any other language.
            Return no additional information — only a dictionary of the form:
            {{"correct": "<corrected paragraph>"}}

            <|user|>
            {sent}

            <|assistant|>
            """
        return text
    
    def ollama_connect(self, model_name:str, text:str):
        ollama_client = Client(host=self.ollama_url)
        try:
            response = ollama_client.chat(
                model = model_name,
                messages = [
                    {
                        "role" : "user",
                        "content" : f"{text} /nothink",
                    }
                ],
                format="json"
            )
        except Exception as e:
            return {}
        try:
            final = response.message.content
            return json.loads(final)
        except:
            return {} 
    
    def embed(self, text:str):
        response = np.array(requests.post(f"{self.gpu_url}/hidden", params={"text" : text}).json()["hidden"], dtype=np.float32)
        return response
    
    def cosine(self, a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
    
    def has_correct_format(self, obj):
        return (isinstance(obj, dict) and "correct" in obj and isinstance(obj.get("correct"), str))

    def evaluate(self, agent_response:str, expected:Optional[str]=None):
        prompting = self.make_prompt(agent_response)
        model_names = ["qwen3:32b"]
        corrections = []
        while(corrections == []):
            for model_name in model_names:
                corr_dict = self.ollama_connect(model_name, prompting)
                if(self.has_correct_format(corr_dict)):
                    corrections.append(corr_dict)
        final_ops = [corr["correct"] for corr in corrections]
        print(final_ops)
        print(agent_response)
        scores = []
        for final in final_ops:
            a1, b1 = self.embed(agent_response), self.embed(final)
            sim = self.cosine(a1, b1)
            dist = Levenshtein.distance(agent_response, final)
            max_dist = max(len(final), len(agent_response))
            lev_sim = 1 - (dist / max_dist)
            print(sim)
            print(lev_sim)
            # harmonic mean between the lev distance and the semantic similarity score
            score =  2 * sim * lev_sim / (sim + lev_sim + 1e-12)
            scores.append(score)
        return np.mean(scores)

if __name__ == "__main__":
    checker = IndianLangGrammaticalCheck()
    sent = "నేను రేపు ఇంటికి వెళ్తుంది కానీ నువ్వు వచ్చాను అని అన్నావు."
    score = checker.evaluate(sent)
    print(score)
