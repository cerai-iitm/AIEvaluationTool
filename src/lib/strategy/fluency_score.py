import numpy as np
import requests
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import gaussian_kde
from .utils_new import FileLoader, OllamaConnect
import warnings
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
import math

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("fluency_score")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="fluency_score")

class IndianLanguageFluencyScorer(Strategy):
    def __init__(self, name:str="fluency_score", **kwargs):
        super().__init__(name, kwargs=kwargs)
        self.name__ = name #self.name is a property of the base class, so the naming should be different
        self.gpu_url=os.getenv("GPU_URL")
        self.ex_dir = os.getenv("EXAMPLES_DIR")
        self.dist_file = dflt_vals.dist_file
        self.epsilon = dflt_vals.epsilon

    def run_examples(self):
        if(not FileLoader._check_if_present(__file__, self.ex_dir, f"{self.dist_file}_{dflt_vals.type}.json")):
            examples = FileLoader._load_file_content(__file__, self.ex_dir, strategy_name=self.name__)
            score_dist = {}
            if len(examples) > 0:
                for k, v in examples.items():
                    if(isinstance(v, list)):                        
                        for para in v:
                            if k in score_dist:
                                score_dist[k].append(self.get_score(para["agent_response"], type=dflt_vals.type))
                            else:
                                score_dist[k] = [self.get_score(para["agent_response"], dflt_vals.type)]
                FileLoader._save_values(__file__, score_dist, self.ex_dir, f"{self.dist_file}_{dflt_vals.type}.json")
            else:
                logger.error("No examples to generate the distributions.")
        else:
            score_dist = FileLoader._load_file_content(__file__, self.ex_dir, f"{self.dist_file}_{dflt_vals.type}.json")
        return score_dist

    def get_score(self, text:str, type:str):
        if type == "perplexity":
            response = requests.post(f"{self.gpu_url}/perplexity", params={"text" : text})
            score = json.loads(response.content.decode('utf-8'))["perplexity"]
        else:
            response = requests.post(f"{self.gpu_url}/slor", params={"text" : text})
            score = json.loads(response.content.decode('utf-8'))["SLOR"]
        return score
    
    def save_res_as_img(self, results:dict, path:str):
        for k , v in results.items():
            sns.kdeplot(v, label=k, fill=True)
        plt.title("Perplexity for fluent and non fluent indic language paragraphs.")
        plt.xlabel('Value')
        plt.ylabel('Density')
        plt.legend()
        plt.savefig(path)
        plt.clf()

    def reason_for_score(self, agent_response:str, score:float):
        if(dflt_vals.model_reason):
            try:
                return OllamaConnect.get_reason(agent_response, " ".join(self.name.split("_")), score)
            except:
                logger.error(f"Could not fetch the reason for score. \n Make sure Ollama is running with the specified model, OR change the model_reason to false for {self.name} in data/defaults.json")
                return ""
        else:
            match score:
                case s if s < 0.3:
                    return "Highly unstructured wording and sentences."
                case s if 0.3 <= s <= 0.6:
                    return "Not completely structured sentences."
                case s if 0.6 < s <= 1.0:
                    return "Very fluent sentences."
                case s if s < 0 or s > 1.0:
                    return ""
    
    def evaluate(self, testcase:TestCase, conversation:Conversation, save_dist_img=False):
        score = self.get_score(conversation.agent_response, dflt_vals.type)
        ex_results = self.run_examples()
        final_score = 0.0
        rsn = ""
        if(len(ex_results) == 2): # needs examples for both fluent and non fluent
            probs = {}
            for k, v in ex_results.items():
                dist = gaussian_kde(v)
                interval = np.linspace(score-self.epsilon, score+self.epsilon, 500)
                dist_int = dist(interval) # kde applied to the interval
                probs[k] = np.trapezoid(dist_int, interval)

            if(save_dist_img):
                self.save_res_as_img(ex_results, os.path.join(os.path.dirname(__file__), f"{os.getenv('IMAGES_DIR')}/{dflt_vals.type}_dist.png"))
            
            probs_as_lst = list(probs.values())
            # if the differnce is positive the value is closer to fluent dist than non fluent
            log_ratio = math.log(max(probs_as_lst[0], 1e-40)) - math.log(max(probs_as_lst[1], 1e-40))
            final_score = 1 / (1 + math.exp(-log_ratio)) # sigmoid function for the difference in log values
            logger.info(f"Fluency Score: {final_score}")
            final_score = round(final_score, 3)
            rsn = self.reason_for_score(conversation.agent_response, final_score)
        else:
            logger.error(f"Distributions not generated in the absence of examples. Add examples for {self.name} in data/examples. Returning a 0 score.")
        return final_score, rsn
        