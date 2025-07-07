from typing import Optional
import logging
import warnings

warnings.filterwarnings("ignore")

from utils import CustomOllamaModel
from opik.evaluation.metrics import GEval
from strategy_base import Strategy

# Setup logger
logger = logging.getLogger("llm_as_judge")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class LLMJudgeStrategy(Strategy):
    def __init__(
        self,
        judge_prompt: str,
        metric_name: str,
        model_name: str = "gemma3:4b",
        base_url: str = "http://172.31.99.190:11434",
        name: str = "llm_judge"
    ) -> None:
        super().__init__(name=name)

        self.judge_prompt = judge_prompt
        self.metric_name = metric_name
        self.model_name = model_name
        self.base_url = base_url


        self.model = CustomOllamaModel(model_name=self.model_name, base_url=self.base_url)

    
        self.metric = GEval(
            name=self.metric_name,
            task_introduction=self.judge_prompt,
            evaluation_criteria=self.judge_prompt,
            model=self.model
        )

    def evaluate(self, agent_response: str, expected_response: Optional[str] = None) -> float:
        logger.info("Evaluating agent response using LLM judge...")
        try:
            score_result = self.metric.score(
                input=self.judge_prompt,
                output=agent_response,
                expected_output=expected_response,
                context=""
            )
            logger.info(f"Score: {score_result.value}, Reason: {score_result.reason}")
            return score_result.value
        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            return 0.0

'''if __name__ == "__main__":
    judge = LLMJudgeStrategy(
        judge_prompt="Evaluate the agent response for factual correctness and clarity.",
        metric_name="CorrectnessScore"
    )

    agent_response = "The sun revolves around the Earth."
    expected_response = "The Earth revolves around the sun."

    score = judge.evaluate(agent_response, expected_response)
    print(f"Score: {score}")'''

