# from utils import SarvamModel
import numpy as np
from nltk.tokenize import sent_tokenize
from typing import Optional
# import nltk
import requests
import os
from dotenv import load_dotenv
from os.path import join, dirname
import json

from .strategy_base import Strategy
from .logger import get_logger

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# nltk.download('punkt')
logger = get_logger("fleuncy_score")

class IndianLanguageFluencyScorer(Strategy):
    def __init__(self, name="indian_lang_fluency", **kwargs):
        super().__init__(name, **kwargs)
        self.gpu_url=os.getenv("GPU_URL")
        if not self.gpu_url:
            logger.warning("GPU_URL is not set in environment.")
        else:
            logger.info("GPU_URL is loaded from environment.")

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def evaluate(self, agent_response: str, expected_response: Optional[str]=None) -> float:
        sentences = sent_tokenize(agent_response)
        if len(sentences) < 2:
            return 1.0
        sims = []
        for i in range(len(sentences) - 1):
            emb1 = requests.post(f"{self.gpu_url}/embedding",params={"text": sentences[i]})
            emb2 = requests.post(f"{self.gpu_url}/embedding",params={"text": sentences[i+1]})

            json_str = emb1.content.decode('utf-8')
            data = json.loads(json_str)
            emb1 = data['embedding']

            json_str = emb2.content.decode('utf-8')
            data = json.loads(json_str)
            emb2 = data['embedding']

            # emb1 = self.model.get_mean_pooled_embedding(sentences[i]).numpy()
            # emb2 = self.model.get_mean_pooled_embedding(sentences[i + 1]).numpy()
            sim = self.cosine_similarity(emb1, emb2)
            sims.append(sim)
        avg_sim = float(np.mean(sims))
        return round(avg_sim, 4)

# if __name__ == "__main__":
#     scorer = IndianLanguageFluencyScorer()
#     test_sentence = "यह एक उदाहरण वाक्य है। यह दूसरा वाक्य है।"
#     score = scorer.evaluate(test_sentence)
#     print(f"Fluency score for test sentence: {score}")
    # print("Tokenizer vocab size:", len(scorer.tokenizer))




