import warnings
import re
import os
from .llm_judge import LLMJudgeStrategy
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader, OllamaConnect

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("truthfulness_internal")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="truthfulness_internal")

# This module implements "Truthfulness_Internal" strategy to analyze the agent response.
class Truthfulness_Internal(Strategy):
    def __init__(self, name: str = "truthfulness_internal", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.model_name = os.getenv("LLM_AS_JUDGE_MODEL")
        self.base_url = os.getenv("OLLAMA_URL")
        self.data_src = name.split("_")[-1] if len(name.split("_")) > 2 else dflt_vals.data_src

    def eval_internal_codah(self, response:str, expected_answer:str):
        """
        Evaluates responses based on the CODAH dataset.

        Parameters:
        data (list): A list of data items from the CODAH dataset.

        Returns:
        float: The accuracy of the evaluation based on the CODAH dataset.
        """
        prediction = re.findall(r"\d+", response)[0] if re.findall(r"\d+", response) else "-1"
        if expected_answer == prediction:
            return 1
        else:
            return 0
        
    def eval_internal_llm_as_judge(self, testcase:TestCase, conversation:Conversation):
        """
        Evaluates responses based on the SQuAD dataset.

        Parameters:
        data (list): A list of data items from the SQuAD dataset.

        Returns:
        dict: A dictionary containing evaluation results for the SQuAD dataset.
        """
        llm_judge = LLMJudgeStrategy(metric_name=f"Truthfulness_{self.data_src}")
        score, _ = llm_judge.evaluate(testcase, conversation)
        return score
    
    def evaluate(self, testcase:TestCase, conversation:Conversation):
        """
        Evaluate the agents response for Truthfulness Internal.
        """
        match self.data_src:
            case "codah":
                score = self.eval_internal_codah(conversation.agent_response, testcase.response.response_text)
                return score, OllamaConnect.get_reason(conversation.agent_response, " ".join(self.name.split("_")), score)
            case "squad" | "hotpot":
                score = self.eval_internal_llm_as_judge(testcase, conversation)
                return score, OllamaConnect.get_reason(conversation.agent_response, " ".join(self.name.split("_")), score)
            case _:
                logger.error(f"Unknown data source: {self.data_src}. Please choose from 'codah', 'squad', 'adv', or 'hotpot'.")
                return None, OllamaConnect.get_reason(conversation.agent_response, " ".join(self.name.split("_")), 0)