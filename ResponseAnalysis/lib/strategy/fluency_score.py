from utils import SarvamModel
from strategy_base import Strategy
import numpy as np
from nltk.tokenize import sent_tokenize
from typing import Optional

class IndianLanguageFluencyScorer(Strategy):
    def __init__(self, model=None, name="indian_lang_fluency", **kwargs):
        super().__init__(name, **kwargs)
        self.model = SarvamModel() if model is None else model

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def evaluate(self, agent_response: str, expected_response: Optional[str]=None) -> float:
        sentences = sent_tokenize(agent_response)
        if len(sentences) < 2:
            return 1.0
        sims = []
        for i in range(len(sentences) - 1):
            emb1 = self.model.get_mean_pooled_embedding(sentences[i]).numpy()
            emb2 = self.model.get_mean_pooled_embedding(sentences[i + 1]).numpy()
            sim = self.cosine_similarity(emb1, emb2)
            sims.append(sim)
        avg_sim = float(np.mean(sims))
        return round(avg_sim, 4)

'''if __name__ == "__main__":
    scorer = IndianLanguageFluencyScorer()
    test_sentence = "यह एक उदाहरण वाक्य है। यह दूसरा वाक्य है।"
    score = scorer.evaluate(test_sentence)
    print(f"Fluency score for test sentence: {score}")
    print("Tokenizer vocab size:", len(scorer.model.tokenizer))'''




