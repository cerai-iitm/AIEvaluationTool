import warnings
import os
from lib.data import TestCase, Conversation
from lib.data.llm_judge_prompt import LLMJudgePrompt
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader
from .llm_judge import LLMJudgeStrategy

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("robustness_ood")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="robustness_ood")

# This module implements "Robustness Out of Domain" strategy to analyze the agent response.
class Robustness_OutOfDomain(Strategy):
    """
    Evaluates whether the agent stays within its system-prompt-defined domain when
    faced with an out-of-domain (OOD) user query, using an LLM-as-judge.
    """

    def __init__(self, name: str = "robustness_ood", **kwargs):
        super().__init__(name, kwargs=kwargs)
        self.metric_name = kwargs.get("metric_name", name)
        self.llm_judge = LLMJudgeStrategy(metric_name=self.metric_name)

    def evaluate(self, testcase: TestCase, conversation: Conversation):
        if not testcase.judge_prompt:
            testcase.judge_prompt = LLMJudgePrompt(dflt_vals.definition)

        logger.info("Evaluating out-of-domain robustness via LLM judge.")
        judge_score, judge_reason = self.llm_judge.evaluate(testcase, conversation)
        logger.info(f"LLM Judge Score: {judge_score:.3f}")

        return judge_score, judge_reason
