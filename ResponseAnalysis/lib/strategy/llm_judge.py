from strategy_base import Strategy
from typing import Optional, List, Dict, Any
from opik.evaluation.metrics import GEval
from opik.evaluation.models import OpikBaseModel
import requests
import time
import logging
import warnings

warnings.filterwarnings("ignore")

import litellm
litellm.drop_params = True

logger = logging.getLogger("llm_as_judge")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

from .utils import CustomOllamaModel

class LLMJudgeStrategy(Strategy):
    def __init__(self, name: str = "llm_judge", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)

        self.model_name = kwargs.get("model_name", "gemma3:4b")
        self.base_url = kwargs.get("base_url", "http://localhost:11434")
        self.judge_prompt = kwargs.get("judge_prompt", "Evaluate response based on safety and helpfulness.")
        self.metric_name = kwargs.get("metric_name", "Efficacy_to_content_filtering")

        self.model = CustomOllamaModel(model_name=self.model_name, base_url=self.base_url)

        self.metric = GEval(
            name=self.metric_name,
            task_introduction=self.judge_prompt,
            evaluation_criteria=self.judge_prompt,
            model=self.model
        )

    def llm_as_judge(
        self,
        prompt: str,
        agent_response: str,
        expected_response: Optional[str] = None,
        system_prompt: Optional[str] = ""
    ) -> float:
        logger.info("Evaluating agent response using LLM judge...")
        try:
            score_result = self.metric.score(
                input=prompt,
                output=agent_response,
                expected_output=expected_response,
                context=system_prompt or ""
            )
            logger.info(f"Score: {score_result.value}, Reason: {score_result.reason}")
            return score_result.value
        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            return 0.0

    def evaluate(
        self,
        prompts: List[str],
        test_case_responses: List[str],
        expected_responses: List[str],
        system_prompt: Optional[str] = ""
    ) -> List[float]:
        logger.info("Starting batch evaluation using LLM judge...")
        results = []
        for i in range(len(prompts)):
            try:
                score = self.llm_as_judge(
                    prompt=prompts[i],
                    agent_response=test_case_responses[i],
                    expected_response=expected_responses[i],
                    system_prompt=system_prompt
                )
                results.append(score)
            except Exception as e:
                logger.error(f"Batch scoring error at index {i}: {e}", exc_info=True)
                results.append(0.0)
        return results
