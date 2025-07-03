from .utils import SarvamModel
from .strategy_base import Strategy
import numpy as np
from nltk.tokenize import sent_tokenize

class IndianLanguageFluencyScorer(Strategy):
    def __init__(self, model=None, tokenizer=None, name="indian_lang_fluency", **kwargs):
        super().__init__(name, kwargs=kwargs)
        self.model = SarvamModel()
        self.tokenizer = tokenizer

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def evaluate(self, text: str) -> float:
        sentences = sent_tokenize(text)
        if len(sentences) < 2:
            return 1.0
        sims = []
        for i in range(len(sentences) - 1):
            emb1 = self.model.get_sarvam_mean_pooled_embedding(sentences[i], model=self.model, tokenizer=self.tokenizer).numpy()
            emb2 = self.model.get_sarvam_mean_pooled_embedding(sentences[i + 1], model=self.model, tokenizer=self.tokenizer).numpy()
            sim = self.cosine_similarity(emb1, emb2)
            sims.append(sim)
        avg_sim = float(np.mean(sims))
        return round(avg_sim, 4)




