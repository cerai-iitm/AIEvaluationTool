from compute_error_rate import ComputeErrorRate
from compute_mtbf import Compute_MTBF
from entity_recognition import EntityRecognition
from toxicity_detection_using_api import ToxicityDetectionUsingAPI
from fairness_preference import Fairness_Preference
from fairness_stereotype_agreement import Fairness_Stereotype_Agreement
from fairness_stereotype_query import Fairness_Stereotype_Query
from fairness_stereotype_recognition import Fairness_Stereotype_Recognition
from typing import Optional, List
from logger import get_logger
logger = get_logger("strategy_implementor")

class StrategyImplementor:
    """
    StrategyImplementor class that implements the strategy pattern.
    It allows for dynamic selection of strategies at runtime.
    """

    def __init__(self, strategy_name: str, **kwargs):
        self.strategy_name = strategy_name

    def execute(self, prompts: Optional[List[str]] = None, expected_responses: Optional[List[str]] = None, agent_responses: Optional[List[str]] = None, judge_prompt: Optional[List[str]] = None) -> float :
        """
        Execute the current strategy with the provided arguments.
        """
        match self.strategy_name:
            case "compute_error_rate":
                strategy = ComputeErrorRate(file_path="logs/whatsapp_driver.log") # Default check for log file
                return strategy.evaluate()
            case "compute_mtbf":
                strategy = Compute_MTBF(file_path="logs/whatsapp_drivr.log") # Default check for log file
                return strategy.evaluate()
            case "entity_recogonition":
                strategy = EntityRecognition()
                score = 0
                for i in range(len(agent_responses)):
                    score += strategy.evaluate(agent_response=agent_responses[i], expected_response=expected_responses[i])
                    ner_score = score / len(agent_responses)
                logger.info(f"Entity Recognition Accuracy: {ner_score}")
                return ner_score
            case "detect_toxicity_using_perspective_api":
                strategy = ToxicityDetectionUsingAPI()
                prompt_harm_score = 0
                agent_response_harm_score = 0
                for i in range(len(prompts)):
                    prompt_harm_score += strategy.evaluate(prompt=prompts[i])
                    prompt_toxicity_score = prompt_harm_score / len(prompts)
                for i in range(len(agent_responses)):
                    agent_response_harm_score += strategy.evaluate(agent_response=agent_responses[i])
                    agent_response_toxicity_score = agent_response_harm_score / len(agent_responses)
                logger.info(f"Detection of harmful inputs score: {prompt_toxicity_score}")
                logger.info(f"Inappropriate Content Detection Rate: {prompt_toxicity_score}")
                return prompt_toxicity_score, agent_response_toxicity_score
            case "fairness_stereotype_query":
                strategy = Fairness_Stereotype_Query()
                fsq_score = 0
                for i in range(agent_responses):
                    fsq_score += strategy.evaluate(agent_response=agent_responses[i], expected_response=expected_responses[i])
                fairness_stereotype_query_score = fsq_score / len(agent_responses)
                logger.info(f"Fairness Stereotype Query Score: {fairness_stereotype_query_score}")
                return fairness_stereotype_query_score
            case "fairness_stereotype_agreement":
                strategy = Fairness_Stereotype_Agreement()
                fsa_score = 0
                for i in range(len(prompts)):
                    fsa_score += strategy.evaluate(agent_response=agent_responses[i], prompt=prompts[i])
                fairness_stereotype_agreement_score = fsa_score / len(prompts)
                logger.info(f"Fairness Stereotype Agreement Score: {fairness_stereotype_agreement_score}")
                return fairness_stereotype_agreement_score

# testing 
s = StrategyImplementor(strategy_name="entity_recognition")

expected_responses = []
agent_responses = []

s.execute(expected_response=expected_responses, agent_response=agent_responses)
