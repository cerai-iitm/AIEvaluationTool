import requests
import os 
import warnings
from typing import Optional
import numpy as np
import Levenshtein
import stanza
from langdetect import detect
from zss import Node, simple_distance
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader, OllamaConnect

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("indian_lang_grammatical_check")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="indian_lang_grammatical_check")

class IndianLangGrammaticalCheck(Strategy):
    def __init__(self, model=None, tokenizer=None, name="indian_lang_grammatical_check", **kwargs):
        super().__init__(name, **kwargs)
        self.gpu_url=os.getenv("GPU_URL")
        self.nlp = None

        if not self.gpu_url:
            logger.warning("GPU_URL is not set in environment.")
        else:
            logger.info("GPU_URL is loaded from environment.")
    
    def detect_lang(self, original:str, corrected:str):
        lang1, lang2 = detect(original), detect(corrected)
        try:
            assert(lang1 == lang2)
        except:
            logger.debug("The corrected language is not the same as the original. Scores might get affected.")
        try:
            self.nlp = stanza.Pipeline(lang1, processors="tokenize, pos, lemma, depparse")
        except:
            try:
                stanza.download(lang1)
                self.nlp = stanza.Pipeline(lang1, processors="tokenize, pos, lemma, depparse")
            except:
                logger.debug(f"Language parser not available for {lang1}. Defaulting to Levenshtein distance for score calculation.")

    def build_tree(self, sent):
        nodes = {word.id : Node(f"{word.text}/{word.upos}") for word in sent.words}
        root = None
        for word in sent.words:
            if word.head == 0:
                root = nodes[word.id]
            else:
                parent = nodes[word.head]
                parent.addkid(nodes[word.id])
        return root

    def get_parse_tree(self, text:str):
        if(isinstance(self.nlp, stanza.Pipeline)):
            doc = self.nlp(text)
            sentence = doc.sentences[0]
            return self.build_tree(sentence)
        else:
            logger.debug("Using Levenshtein distance.")
            return None

    def tree_similarity(self, original:str, corrected:str, use_ted=True):

        def count_nodes(node):
            if node is None:
                return 0
            total = 1
            for child in node.children:
                total += count_nodes(child)
            return total

        # if(use_ted):
        self.detect_lang(original, corrected)
        ori_tree, corr_tree = self.get_parse_tree(original), self.get_parse_tree(corrected)
        score_ted = None
        if(ori_tree is not None and corr_tree is not None):
            ted = simple_distance(ori_tree, corr_tree)
            ori_tree_len, corr_tree_len = count_nodes(ori_tree), count_nodes(corr_tree)
            max_dist = max(ori_tree_len, corr_tree_len)
            score_ted = 1 - (ted / max_dist)

        # else:
        ted = Levenshtein.distance(original, corrected)
        max_dist = max(len(original), len(corrected))
        score_lev = 1 - (ted / max_dist)
        
        sim = (score_lev + score_ted) / 2 if score_ted is not None else score_lev
        return sim
    
    def embed(self, text:str):
        response = np.array(requests.post(f"{self.gpu_url}/hidden", params={"text" : text}).json()["hidden"], dtype=np.float32)
        return response
    
    def cosine(self, a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
    
    def make_corrections(self, prompt:str):
        corrections = OllamaConnect.prompt_model(prompt, dflt_vals.reqd_flds, model_names=dflt_vals.model_names, options=dflt_vals.options)
        if len(corrections) > 0: 
            return [corr["corrected"] for corr in corrections]
        else:
            return []
    
    def weighted_f1(self, scores:list, weights:list = [0.8, 0.2]): # weights  = [for vector sim, for avg_edit_dist]
        weights = [w / sum(weights) for w in weights] # normalizing so the weights sum to 1
        return 1 / sum(wt / score for wt, score in zip(weights, scores))
    
    def reason_for_score(self, agent_response:str, score:float):
        if(dflt_vals.model_reason):
            try:
                return OllamaConnect.get_reason(agent_response, " ".join(self.name.split("_")), score)
            except:
                logger.error(f"Could not fetch the reason for score. \n Make sure Ollama is running with the specified model, OR change the model_reason to false for {self.name} in data/defaults.json")
                return ""
        else:
            match score:
                case s if s < 0.4:
                    return "Very high grammatical inconsistency."
                case s if 0.4 <= s <= 0.8:
                    return "Minor grammatical inconsistencies in the sentences."
                case s if 0.8 < s <= 1.0:
                    return "Well structured and understanable sentences."
                case s if s < 0 or s > 1.0:
                    return ""

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        prompt = dflt_vals.prompt.format(sent=conversation.agent_response)
        corr_sents = self.make_corrections(prompt)
        scores = []
        final_score = 0.0
        rsn = ""
        if len(corr_sents) > 0:
            for final in corr_sents:
                # we are taking the embedding for both the sentences using the initial layer of the LLM which captures morpheme and strctural information
                a1, b1 = self.embed(conversation.agent_response), self.embed(final)
                sim = self.cosine(a1, b1)
                ted_sim = self.tree_similarity(conversation.agent_response, final, use_ted=dflt_vals.use_ted)
                # harmonic mean between the lev distance and the structural vector similarity score
                score = self.weighted_f1([sim, ted_sim])
                scores.append(score)
            final_score = round(float(np.mean(scores)), 3)
            logger.info(f"Grammatical consistency score for the input is : {final_score}")
            rsn = self.reason_for_score(conversation.agent_response, final_score)
        else:
            logger.error(f"Could not receive corrections for the sentence using the user provided models. Returning 0 score.")
        return final_score, rsn
