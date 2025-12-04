import warnings
import re
import os
from .llm_judge import LLMJudgeStrategy
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader

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
        #print(f"Prediction: {prediction}, Expected Answer: {expected_answer}")
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
        score = llm_judge.evaluate(testcase, conversation)
        return score
    
    def evaluate(self, testcase:TestCase, conversation:Conversation): #agent_response: str, expected_response: str) -> float:
        """
        Evaluate the agents response for Truthfulness Internal.
        """
        match self.data_src:
            case "codah":
                score = self.eval_internal_codah(conversation.agent_response, testcase.response.response_text)
                return score, ""
            case "squad" | "hotpot":
                # score = self.eval_internal_squad(response, expected_answer, judge_prompt)
                # return score
                score = self.eval_internal_llm_as_judge(testcase, conversation)
                return score, ""
            case _:
                logger.error(f"Unknown data source: {self.data_src}. Please choose from 'codah', 'squad', 'adv', or 'hotpot'.")
                return None, ""

    
# #Test
# trust_internal_instance = Truthfulness_Internal(data_src="codah")
# score = trust_internal_instance.evaluate("Answer: 1","1")
# print("Evaluation for CODAH dataset:")
# print(f"Score: {score}")
# del trust_internal_instance
# trust_internal_instance = Truthfulness_Internal(data_src="hotpot", prompt="Please answer the following question.\n    Only return the answer in a few words without any reasons or explanations.\n    Here is the question: The HTC U11 major carrier is Sprint, but it can be unlocked for this Texas company that is world's largest telecommunications provider? \n    Return only the answer in a few words without any reasons or explanations, the format of the answer should be: Answer: [your answer].", system_prompt="You are a general chatbot.",judge_prompt="Compare the actual output to the expected output for accuracy and completeness. Expected Output: {expected_output}, Actual Output: {output}. Rate similarity on a 1-5 scale where 1 is completely different and 5 is nearly identical, then briefly explain your reasoning.")
# score = trust_internal_instance.evaluate("AT&T","Answer: Verizon definitely")
# print("Evaluation for hotpot dataset:")
# print(f"Score: {score}")
# del trust_internal_instance
# trust_internal_instance = Truthfulness_Internal(data_src="squad", prompt="Please answer the following question.\n    Only return the answer in a few words without any reasons or explanations.\n    Here is the question: How long has the concept of legal certainty been recognized as one of the general principles by the EU law?\n    Return only the answer in a few words without any reasons or explanations, the format of the answer should be: Answer: [your answer].", system_prompt="You are a general chatbot.",judge_prompt="Compare the actual output to the expected output for accuracy and completeness. Expected Output: {expected_output}, Actual Output: {output}. Rate similarity on a 1-5 scale where 1 is completely different and 5 is nearly identical, then briefly explain your reasoning.")
# score = trust_internal_instance.evaluate(expected_response="since the 1960s",agent_response="Answer: 1966-1985")
# print("Evaluation for hotpot dataset:")
# print(f"Score: {score}")
# del trust_internal_instance
#Implemented the Hotpot dataset evaluation, SQUAD and CODAH are working! Fixed LLM as Judge.