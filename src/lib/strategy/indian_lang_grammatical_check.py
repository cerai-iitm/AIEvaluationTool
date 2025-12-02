import requests
import os 
import warnings
from typing import Optional
import numpy as np
import json
from ollama import Client
import Levenshtein
import stanza
from langdetect import detect
from zss import Node, simple_distance
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("indian_lang_grammatical_check")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="indian_lang_grammatical_check")

class IndianLangGrammaticalCheck(Strategy):
    def __init__(self, model=None, tokenizer=None, name="indian_lang_grammatical_check", **kwargs):
        super().__init__(name, **kwargs)
        self.gpu_url=os.getenv("GPU_URL")
        self.ollama_url = os.getenv("OLLAMA_URL")
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
            ori_tree_len = count_nodes(ori_tree)
            corr_tree_len = count_nodes(corr_tree)
            max_dist = max(ori_tree_len, corr_tree_len)
            score_ted = 1 - (ted / max_dist)

        # else:
        ted = Levenshtein.distance(original, corrected)
        max_dist = max(len(original), len(corrected))
        score_lev = 1 - (ted / max_dist)
        
        sim = (score_lev + score_ted) / 2 if score_ted is not None else score_lev
        return sim

    def make_prompt(self, sent:str):
        text = dflt_vals.prompt.format(sent=sent)
        return text
    
    def ollama_connect(self, model_name:str, text:str):
        ollama_client = Client(host=self.ollama_url)
        try:
            """
            We are making a strong assumption that the model we provide will return a 
            grammatically correct response based on the input text.
            """
            response = ollama_client.chat(
                model = model_name,
                messages = [
                    {
                        "role" : "user",
                        "content" : f"{text} /nothink",
                    }
                ],
                format="json",
                options= {
                    "temperature": 0.3,
                    "top_p": 0.5,
                    "repeat_penalty": 1.2
                }
            )
        except Exception as e:
            logger.error(f"Could not communicate with the {model_name}. Make sure the model is downloaded and running.")
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
    
    def make_corrections(self, prompt:str):
        model_names = dflt_vals.model_names
        corrections = []
        tries = dflt_vals.n_tries
        while(corrections == [] and tries > 0):
            for model_name in model_names:
                corr_dict = self.ollama_connect(model_name, prompt)
                if(self.has_correct_format(corr_dict)):
                    corrections.append(corr_dict)
            tries -= 1
        if len(corrections) > 0: 
            return [corr["correct"] for corr in corrections]
        else:
            return []
    
    def weighted_f1(self, scores:list, weights:list = [0.8, 0.2]): # weights  = [for vector sim, for avg_edit_dist]
        weights = [w / sum(weights) for w in weights] # normalizing so the weights sum to 1
        return 1 / sum(wt / score for wt, score in zip(weights, scores))

    def evaluate(self, testcase:TestCase, conversation:Conversation): #testcase:TestCase, conversation:Conversation):#agent_response:str, expected:Optional[str]=None):
        prompt = self.make_prompt(conversation.agent_response)
        corr_sents = self.make_corrections(prompt)
        print(corr_sents)
        print(conversation.agent_response)
        scores = []
        if len(corr_sents) > 0:
            for final in corr_sents:
                # we are taking the embedding for both the sentences using the initial layer of the LLM which captures morpheme and strctural information
                a1, b1 = self.embed(conversation.agent_response), self.embed(final)
                sim = self.cosine(a1, b1)
                ted_sim = self.tree_similarity(conversation.agent_response, final, use_ted=dflt_vals.use_ted)
                print(sim)
                print(ted_sim)
                # harmonic mean between the lev distance and the structural vector similarity score
                # score =  2 * sim * ted_sim / (sim + ted_sim + 1e-12)
                score = self.weighted_f1([sim, ted_sim])
                scores.append(score)
            final_score = round(float(np.mean(scores)), 3)
            logger.info(f"Grammatical consistency score for the input is : {final_score}")
            return final_score
        else:
            final_score = 0.0
            logger.error("Could not receive corrections for the sentence using the user provided models. Returning 0 score.")
        return final_score

# if __name__ == "__main__":
#     checker = IndianLangGrammaticalCheck()
#     sent = "நான் இன்று ரொம்ப மகிழ்ச்சி இருக்கு ஆனா என் மனசுல ஏதோ சில ஒத்துக்காத மாதிரி எண்ணம் வருது அது எப்படி சரியா சொல்லுவது நான் ஒண்ணும் நன்றா நினைக்க முடியலே, அதனால கொஞ்சம் எல்லாம் குழப்பம் போல இருக்கு."
#     score = checker.evaluate(sent)
#     print(score)
