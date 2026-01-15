import warnings
import os
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval
from .utils_new import FileLoader, CustomOllamaModel
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
import numpy as np

warnings.filterwarnings("ignore")
FileLoader._load_env_vars(__file__)
logger = get_logger("llm_judge")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="llm_judge")

class LLMJudgeStrategy(Strategy):
    def __init__(self, name: str = "llm_judge", **kwargs) -> None:
        super().__init__(name=name)
        
        self.metric_name = kwargs.get("metric_name", dflt_vals.metric_name)
        self.model_names = dflt_vals.model_names #os.getenv("LLM_AS_JUDGE_MODEL")
        self.base_url = os.getenv("OLLAMA_URL")
        self.models = [CustomOllamaModel(model_name=model_name, url=self.base_url) for model_name in self.model_names]
        self.eval_type = name.split("_")[-1] if len(name.split("_")) > 2 else dflt_vals.eval_type
        
        self.judge_prompt = dflt_vals.judge_prompt
        self.system_prompt = dflt_vals.sys_prompt
        self.prompt = dflt_vals.prompt

        if not self.model_names:
            logger.warning("LLM_AS_JUDGE_MODEL is not set in default values.")
        if not self.base_url:
            logger.warning("OLLAMA_URL is not set in environment.")

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        logger.debug("Evaluating agent response using LLM judge...")
        # metric is defined here instead of init because if multiple testcases belonging to different metrics are grouped together 
        # for this strategy, the judge prompt will change. So we define the metric here right before executing the testcase.

        self.metrics = [GEval(
            name= self.metric_name,
            criteria= testcase.judge_prompt.prompt if testcase.judge_prompt.prompt else self.judge_prompt,
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
            model=model
        ) for model in self.models]
        to_evaluate = LLMTestCase(
            input = testcase.prompt.user_prompt if testcase.prompt.user_prompt else self.prompt,
            actual_output=conversation.agent_response,
            expected_output=testcase.response.response_text,
            retrieval_context=[testcase.prompt.system_prompt if testcase.prompt.system_prompt else self.system_prompt]
        )

        eval_score = np.mean([metric.measure(to_evaluate) for metric in self.metrics])
        final_score = eval_score if self.eval_type == "positive" else (1 - eval_score)
        logger.info(f"Average score based on {len(self.models)} judge models : {final_score}, Reasons: {[model.score_reason for model in self.models]}")
        return final_score, "\n\n".join([f"Reason {i} : {model.score_reason['Reason']}" for i, model in enumerate(self.models)])

#/usr/share/ollama/.ollama/models/manifests
    


