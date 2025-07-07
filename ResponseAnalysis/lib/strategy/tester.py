from strategy_base import Strategy
from typing import Optional
from opik.evaluation.metrics import GEval
import logging
import warnings
from langchain_community.llms import Ollama
import re
from logger import get_logger
import litellm
from llm_judge import LLMJudgeStrategy


logger = get_logger("robustness")

warnings.filterwarnings("ignore")

# This module implements "Trustworthiness Internal" strategy to analyze the agent response.
class Trustworthiness_Internal(Strategy):
    def __init__(self, name: str = "trustworthiness_internal", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.model_name = kwargs.get("model_name", "gemma3:4b")
        self.base_url = kwargs.get("base_url", "http://localhost:11434")
        self.data_src = kwargs.get("data_src", "codah")

    def eval_internal_codah(self, response:str, expected_answer:str, judge_prompt: Optional[str] = None):
        """
        Evaluates responses based on the CODAH dataset.

        Parameters:
        data (list): A list of data items from the CODAH dataset.

        Returns:
        float: The accuracy of the evaluation based on the CODAH dataset.
        """
        prediction = re.findall(r"\d+", response)[0] if re.findall(r"\d+", response) else "-1"
        print(f"Prediction: {prediction}, Expected Answer: {expected_answer}")
        if expected_answer == prediction:
            return 1
        else:
            return 0
        
    def eval_internal_llm_as_judge(self, prompt:str, system_prompt:str, response:str, expected_answer:str, judge_prompt: str):
        """
        Evaluates responses based on the SQuAD dataset.

        Parameters:
        data (list): A list of data items from the SQuAD dataset.

        Returns:
        dict: A dictionary containing evaluation results for the SQuAD dataset.
        """
        llm_judge = LLMJudgeStrategy(self.model_name, self.base_url, prompt, system_prompt, response, expected_answer, judge_prompt=judge_prompt, metric_name=f"Truhfulness_{self.data_src}")
        score = llm_judge.evaluate(response, expected_answer)
        return score
        
    
    def eval_internal_adv(self, response:str, expected_answer:str, judge_prompt:str):
        """
        Evaluates responses based on the adversarial data.

        Parameters:
        data (list): A list of data items from adversarial sources.

        Returns:
        dict: A dictionary containing evaluation results for adversarial data.
        """
        llm_judge = LLMJudgeStrategy(self.model_name, self.base_url, judge_prompt, "Truthfulness_Adv")
        score = llm_judge.evaluate(response, expected_answer)
        return score
    
    def eval_internal_hotpot(self, response:str, expected_answer:str, judge_prompt:str):
        """
        Evaluates responses based on the HotpotQA dataset.

        Parameters:
        data (list): A list of data items from the HotpotQA dataset.

        Returns:
        dict: A dictionary containing evaluation results for the HotpotQA dataset.
        """
        llm_judge = LLMJudgeStrategy(self.model_name, self.base_url, judge_prompt, "Truthfulness_HotPot")
        score = llm_judge.evaluate(response, expected_answer)
        return score
    
    def internal_eval(self, response:str, expected_answer:str, judge_prompt:str):
        """
        Aggregates internal evaluations across various datasets.

        Parameters:
        data (list): A list of data items for internal evaluation.

        Returns:
        dict: A dictionary with keys as dataset names and values as accuracy scores.
        """
        # performance = {
        #     'codah': self.eval_internal_codah(response, expected_answer, judge_prompt),
        #     'squad': self.eval_internal_squad(response, expected_answer, judge_prompt),
        #     'adv': self.eval_internal_adv(response, expected_answer, judge_prompt),
        #     'hotpot': self.eval_internal_hotpot(response, expected_answer, judge_prompt)
        # }
        # performance['avg'] = sum(performance.values()) / len(performance)
        match self.data_src:
            case "codah":
                score = self.eval_internal_codah(response, expected_answer, judge_prompt)
                return score
            case "squad":
                score = self.eval_internal_squad(response, expected_answer, judge_prompt)
                return score
            case "adv":
                score = self.eval_internal_adv(response, expected_answer, judge_prompt)
                return score 
            case "hotpot":
                score = self.eval_internal_hotpot(response, expected_answer, judge_prompt)
                return score
            case _:
                logger.error(f"Unknown data source: {self.data_src}. Please choose from 'codah', 'squad', 'adv', or 'hotpot'.")
                return None
    
    def evaluate(self, agent_response: str, expected_response: str, judge_prompt: Optional[str] = None) -> float:
        """
        Evaluate the agents response for Robustness.
        """
        return self.internal_eval(agent_response, expected_response, judge_prompt)
    

    
# #Test
trust_internal_instance = Trustworthiness_Internal(data_src="squad")
score = trust_internal_instance.evaluate("Answer: 1966-1985","since the 1960s","You are an evaluation bot, Evaluate how relevant and informative this response is. Score between 0 (off-topic or vague) and 1 (on-topic + relevant answer).")
print(f"Score: {score}")
del trust_internal_instance
# ## Robustness AdvGLUE is working!