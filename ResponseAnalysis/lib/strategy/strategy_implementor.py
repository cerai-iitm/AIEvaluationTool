from compute_error_rate import ComputeErrorRate
from compute_mtbf import Compute_MTBF
from entity_recognition import EntityRecognition
from toxicity_detection_using_api import ToxicityDetectionUsingAPI
from fairness_preference import Fairness_Preference
from fairness_stereotype_agreement import Fairness_Stereotype_Agreement
from fairness_stereotype_query import Fairness_Stereotype_Query
from fairness_stereotype_recognition import Fairness_Stereotype_Recognition
from typing import Optional, List
from utils import extract_from_brackets, load_json, save_json
from logger import get_logger
import numpy as np

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
                score = []
                for i in range(len(agent_responses)):
                    score.append(strategy.evaluate(agent_response=agent_responses[i], expected_response=expected_responses[i]))
                    ner_score = np.mean(score)
                logger.info(f"Entity Recognition Accuracy: {ner_score:.3f}")
                return ner_score
            case "detect_toxicity_using_perspective_api":
                strategy = ToxicityDetectionUsingAPI()
                prompt_harm_score = []
                agent_response_harm_score = []
                for i in range(len(prompts)):
                    prompt_harm_score.append(strategy.evaluate(prompt=prompts[i]))
                    prompt_toxicity_score = np.mean(prompt_harm_score)
                for i in range(len(agent_responses)):
                    agent_response_harm_score.append(strategy.evaluate(agent_response=agent_responses[i]))
                    agent_response_toxicity_score = np.mean(agent_response_harm_score)
                logger.info(f"Detection of harmful inputs score: {prompt_toxicity_score:.3f}")
                logger.info(f"Inappropriate Content Detection Rate: {prompt_toxicity_score:.3f}")
                return prompt_toxicity_score, agent_response_toxicity_score
            case "fairness_stereotype_query":
                strategy = Fairness_Stereotype_Query()
                fsq_score = []
                for i in range(agent_responses):
                    fsq_score.append(strategy.evaluate(agent_response=agent_responses[i], expected_response=expected_responses[i]))
                fairness_stereotype_query_score = np.mean(fsq_score)
                logger.info(f"Fairness Stereotype Query Score: {fairness_stereotype_query_score}:.3f")
                return fairness_stereotype_query_score
            case "fairness_stereotype_agreement":
                strategy = Fairness_Stereotype_Agreement()
                fsa_score = []
                for i in range(len(prompts)):
                    fsa_score.append(strategy.evaluate(agent_response=agent_responses[i], prompt=prompts[i]))
                fairness_stereotype_agreement_score = np.mean(fsa_score)
                logger.info(f"Fairness Stereotype Agreement Score: {fairness_stereotype_agreement_score:.3f}")
                return fairness_stereotype_agreement_score
            case "fairness_preference":
                fp_score = []
                for i in range(len(prompts)):
                    eval_type = extract_from_brackets(prompts[i])
                    if eval_type == "plain":
                        strategy = Fairness_Preference(eval_type=eval_type)
                        fp_score.append(strategy.evaluate(agent_response=agent_responses[i], prompt=prompts[i]))
                    else:
                        eval_type = "force"
                        strategy = Fairness_Preference(eval_type=eval_type) 
                        fp_score.append(strategy.evaluate(agent_response=agent_responses[i], prompt=prompts[i]))
                fairness_preference_score = np.mean(fp_score)
                logger.info(f"Fairness Preference Score: {fairness_preference_score:.3f}")
                return fairness_preference_score
            case "fairness_stereotype_recognition":
                fsr_score = []
                for i in range(len(prompts)):
                    label = extract_from_brackets(prompts[i])
                    if label == "stereotype":
                        strategy = Fairness_Stereotype_Recognition(label=label)
                        fsr_score.append(strategy.evaluate(agent_response=agent_responses[i], prompt=prompts[i]))
                    elif label == "anti-stereotype":
                        strategy = Fairness_Stereotype_Recognition(label=label)
                        fsr_score.append(strategy.evaluate(agent_response=agent_responses[i], prompt=prompts[i]))
                    elif label == "unrelated":
                        strategy = Fairness_Stereotype_Recognition(label=label)                        
                        fsr_score.append(strategy.evaluate(agent_response=agent_responses[i], prompt=prompts[i]))
                    else:
                        logger.error(f"Label {label} not recognized in fairness stereotype recognition.")
                        raise ValueError(f"Label {label} not recognized in fairness stereotype recognition.")
                    
                # Calculate the average score
                fairness_stereotype_recognition_score = np.mean(fsr_score)
                logger.info(f"Fairness Stereotype Recognition Score: {fairness_stereotype_recognition_score:.3f}")
                return fairness_stereotype_recognition_score
            case _:
                logger.error(f"Strategy {self.strategy_name} not recognized.")
                raise ValueError(f"Strategy {self.strategy_name} not recognized.")
