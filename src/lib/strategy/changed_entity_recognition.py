from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
import re
import json
import warnings
from typing import List, Tuple
from sentence_transformers import SentenceTransformer, util
from pprint import pprint
from ..data import TestCase, Conversation

from .strategy_base import Strategy
from .logger import get_logger

logger = get_logger("entity_recognition")

warnings.filterwarnings("ignore")

class EntityRecognition(Strategy):
    def __init__(self, name: str = "entity_recognition", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.lemm = WordNetLemmatizer()
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def extract_entity_pairs(self, text: str) -> List[Tuple[str, str]]:
        """
        Extracts (entity, ner_tag) pairs from loosely structured dict-like strings.
        """
        text = text.replace("```", "").strip()

        pattern = re.compile(
            r"""\{\s*['"]?entity['"]?\s*:\s*['"]?([^,'"}\n]+)['"]?\s*,\s*['"]?ner_tag['"]?\s*:\s*['"]?([^,'"}\n]+)['"]?\s*\}""",
            re.IGNORECASE
        )
        matches = pattern.findall(text)

        return [(entity.strip().lower(), tag.strip().upper()) for entity, tag in matches]

    def ner_recognition(self, expected_str: str, response_str: str) -> tuple:
        """
        Computes and returns only the F1 score between expected and predicted entity-tag strings.
        """
        expected_pairs = set(self.extract_entity_pairs(expected_str))
        predicted_pairs = set(self.extract_entity_pairs(response_str))

        return self.scoring(*self.semantic_matching(expected_pairs, predicted_pairs)), self.scoring(*self.exact_matching(expected_pairs, predicted_pairs))
    
    def exact_matching(self, expected_pairs : set, predicted_pairs : set) -> tuple:
        tp = len(expected_pairs & predicted_pairs) 
        fp = len(predicted_pairs - expected_pairs)
        fn = len(expected_pairs - predicted_pairs)
        return tp, fp, fn

    def semantic_matching(self, expected_pairs : set, predicted_pairs : set, vec_model : bool = True) -> tuple:
        fp = set([x for x in predicted_pairs if x[0] not in [y[0] for y in expected_pairs]])
        fn = set([x for x in expected_pairs if x[0] not in [y[0] for y in predicted_pairs]])
        ex = list(expected_pairs - fn)
        pr = list(predicted_pairs - fp)
        ex.sort()
        pr.sort()
        fp = list(fp)
        tp = []
        for en1, en2 in zip(ex, pr):
            syn_score = self.synonym_score(self.lemm.lemmatize(en1[1]), self.lemm.lemmatize(en2[1]))
            vec_score = self.vec_similarity(self.lemm.lemmatize(en1[1]), self.lemm.lemmatize(en2[1])) if vec_model else 0
            total_score = (syn_score + vec_score)/2 if vec_model else syn_score
            if(total_score > 0.7):
                tp.append(en1)
            else:
                fp.append(en1)
        return len(tp), len(fp), len(fn)

    def synonym_score(self, w1 : str, w2 : str) -> float:
        synsets1 = wn.synsets(w1.lower())
        synsets2 = wn.synsets(w2.lower())
        return max([s1.wup_similarity(s2) for s1 in synsets1 for s2 in synsets2 if s1.wup_similarity(s2)])
        
        # return any(s1.wup_similarity(s2) and s1.wup_similarity(s2) > 0.9 for s1 in synsets1 for s2 in synsets2)
    
    def vec_similarity(self, w1 : str, w2 : str) -> float:
        words = [w1, w2]
        embeddings = self.model.encode(words, convert_to_tensor=True, normalize_embeddings=True)
        similarity = util.cos_sim(embeddings, embeddings).detach()[0][1].item()
        return similarity
        
    def scoring(self, tp : float, fp : float, fn : float) -> float:
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        return round(f1, 4)

    def evaluate(self, testcase:TestCase, conversation:Conversation) -> float:
        """
        Evaluates the agent response against expected and returns only the F1 score.
        """
        result =  self.ner_recognition(expected_str=testcase.response.response_text, response_str=conversation.agent_response)
        logger.info(f"Result: {result}")
        return result
        
# Example usage
# expected_response = """
# {'entity' :  weeder ,  'ner_tag' :  TOOL },
# { 'entity' :  floods ,  'ner_tag' :  DISASTER},
# { 'entity' :  dibbler ,  'ner_tag' :  TOOL },  
# { 'entity' :  saplings ,  'ner_tag' :  PLANT_STAGE },  
# { 'entity' :  cutworm ,  'ner_tag' :  PEST },  
# { 'entity' :  beetles ,  'ner_tag' :  PEST }
# """
# agent_response = """
# Here are the agricultural entities extracted from the text: 
# {'entity': 'weeder', 'ner_tag': 'Tool'}\n
# {'entity': 'dibbler', 'ner_tag': 'Instrument'}\n
# {'entity': 'seedlings', 'ner_tag': 'Crop'}\n
# {'entity': 'cutworm', 'ner_tag': 'Insect'}\n
# {'entity': 'beetles', 'ner_tag': 'Pest'}
# """

# ner_eval = EntityRecognition()
# res = ner_eval.ner_recognition(expected_response, agent_response)
# pprint(f"expected_resp : {expected_response}, agent_resp : {agent_response}")
# print(f"current_score: {res[0]}, prev_score : {res[1]}")