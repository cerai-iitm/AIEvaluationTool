from hallucination import HallucinationStrategy
from privacy import PrivacyStrategy
from safety import SafetyStrategy
from tat_tpm_mvh import TAT_TPM_MVH
from typing import Optional, List
from logger import get_logger

logger = get_logger("strategy_implementor")


class StrategyImplementor:
    """
    StrategyImplementor class that implements the strategy pattern.
    It allows for dynamic selection of strategies at runtime with flexible metric selection.
    """

    def __init__(self, strategy_name: str, **kwargs):
        self.strategy_name = strategy_name
        self.kwargs = kwargs

    def execute(self,
                prompts: Optional[List[str]] = None,
                expected_response: Optional[List[str]] = None,
                agent_response: Optional[List[str]] = None,
                judge_prompt: Optional[List[str]] = None,
                source_type: Optional[List[str]] = None,
                system_prompt: Optional[List[str]] = None) -> float:

        metric_name = self.kwargs.get("metric_name")

        match self.strategy_name:

            case "hallucination":
                strategy = HallucinationStrategy(**self.kwargs)
                scores = []

                for i in range(len(agent_response)):
                    score = strategy.evaluate(
                        agent_response[i],
                        expected_response[i],
                        source_type[i]
                    )
                    scores.append(score)

                avg_score = sum(scores) / len(scores) if scores else 0.0
                logger.info(f"[Hallucination] Average Score: {avg_score}")
                return avg_score

            case "privacy":
                strategy = PrivacyStrategy(metric_name=metric_name)
                scores = []

                for i in range(len(agent_response)):
                    if metric_name == "awareness_query":
                        score = strategy.evaluate(
                            agent_response[i],
                            system_prompt[i],
                            prompts[i]
                        )
                    elif metric_name == "privacy_leakage":
                        result = strategy.evaluate(
                            agent_response[i],
                            system_prompt[i]
                        )
                        score = (
                            result["RtA"] +
                            result["TD"] +
                            result["CD"]
                        ) / 3
                    elif metric_name == "confidence_agreement":
                        score = strategy.evaluate(
                            agent_response[i],
                            expected_response[i]
                        )
                    else:
                        logger.warning(f"Unknown Privacy Metric: {metric_name}")
                        return 0.0

                    scores.append(score)

                avg_score = sum(scores) / len(scores) if scores else 0.0
                logger.info(f"[Privacy] {metric_name} Score: {avg_score}")
                return avg_score

            case "safety":
                strategy = SafetyStrategy(metric_name=metric_name)
                scores = []

                for i in range(len(agent_response)):
                    score = strategy.evaluate(
                        agent_response[i],
                        prompts[i]
                    )
                    scores.append(score)

                avg_score = sum(scores) / len(scores) if scores else 0.0
                logger.info(f"[Safety] {metric_name} Score: {avg_score}")
                return avg_score

            case "tat_tpm_mvh":
                strategy = TAT_TPM_MVH(metric_name=metric_name, **self.kwargs)
                score = strategy.evaluate(agent_response=None)
                logger.info(f"[TAT_TPM_MVH] {metric_name} Score: {score}")
                return score

            case _:
                logger.warning(f"Unknown strategy: {self.strategy_name}")
                return 0.0
