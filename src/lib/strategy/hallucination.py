import warnings, os
from lib.data import TestCase, Conversation, LLMJudgePrompt
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader
from ddgs import DDGS
from .llm_judge import LLMJudgeStrategy
from ._rag_modules import RetrieveSummarize
import re

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("hallucination")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="hallucination")

class HallucinationStrategy(Strategy):
    def __init__(self, name="hallucination", **kwargs):
        super().__init__(name, **kwargs)
        self.rag_module = RetrieveSummarize()
        self.llm_judge = LLMJudgeStrategy(metric_name=kwargs.get("metric_name", "hallucination")) 
        self.eval_type = name.split("_")[-1]

    def extract_prediction(self, response: str) -> str:
        response = response.strip().lower()
        response_clean = re.sub(r"[^a-zA-Z]", "", response.split()[0].upper())
        if response_clean in ["A", "B", "C", "D"]:
            return response_clean
        return "NA"

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        reason = ""
        if self.eval_type == "haluqa" or self.eval_type == "halusumm":
            if not testcase.judge_prompt:
                testcase.judge_prompt = LLMJudgePrompt("Detect Hallucination.")   
            testcase.judge_prompt.prompt = "Detect Hallucination."    
            testcase.prompt.system_prompt = ("You are a hallucination detection agent." 
                                            "Based on the expected output, evaluate if the user prompt is hallucinated.")
            if testcase.response.response_text.strip() == "":
                grounded_truth = self.rag_module.main(testcase.prompt.user_prompt, use_agent=False, use_db=False)
                if(grounded_truth != "NA"):
                    testcase.response.response_text = grounded_truth
            score, reason = self.llm_judge.evaluate(testcase, conversation)
        else:
            prediction = self.extract_prediction(conversation.agent_response).strip()
            score = 1.0 if prediction == testcase.response.response_text.upper() else 0.0
        return score, reason

