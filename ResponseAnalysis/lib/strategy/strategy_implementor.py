from truth_external import Truthfulness_External
from truth_internal import Truthfulness_Internal
from transliterated_strategies import TransliteratedStrategy
from calculate_uptime import UptimeCalculation
from robustness_advGLUE import Robustness_AdvGLUE
from typing import Optional, List
import numpy as np
from robustness_advInstruction import Robustness_AdvInstruction
from robustness_ood import Robustness_OutOfDomain
from logger import get_logger
from compute_error_rate import ComputeErrorRate
from compute_mtbf import Compute_MTBF
from entity_recognition import EntityRecognition
from toxicity_detection_using_api import ToxicityDetectionUsingAPI
from fairness_preference import Fairness_Preference
from fairness_stereotype_agreement import Fairness_Stereotype_Agreement
from fairness_stereotype_query import Fairness_Stereotype_Query
from fairness_stereotype_recognition import Fairness_Stereotype_Recognition
from llm_judge import LLMJudgeStrategy
from indian_lang_grammatical_check import IndianLangGrammaticalCheck
from fluency_score import IndianLanguageFluencyScorer
import os
from hallucination import HallucinationStrategy
from privacy import PrivacyStrategy
from safety import SafetyStrategy
from tat_tpm_mvh import TAT_TPM_MVH
from bias_detection import BiasDetection
from similarity_match import SimilarityMatchStrategy
from grammatical_strategy import GrammaticalStrategy
from language_strategies_async import LanguageStrategiesAsync
from language_strategies_sync import LanguageStrategiesSync
import asyncio
from lexical_diversity_calc import LexicalDiversity
from toxicity import Toxicity
from efficacy_of_content_filtering import ContentFiltering
from utils import extract_from_uds, RtA, average_dicts

logger = get_logger("strategy_implementor")

class StrategyImplementor:
    """
    StrategyImplementor class that implements the strategy pattern.
    It allows for dynamic selection of strategies at runtime.
    """

    
    def __init__(self, strategy_name: str, **kwargs):
        self.strategy_name = strategy_name
        self.__metric_name = kwargs.get("metric_name")
        
    def execute(self, prompts: Optional[List[str]] = None, expected_responses: Optional[List[str]] = None, agent_responses: Optional[List[str]] = None, system_prompts: Optional[List[str]] = None, judge_prompts: Optional[List[str]] = None) -> float :
        """
        Execute the current strategy with the provided arguments.
        """
        scores = []
        match self.strategy_name:
            case "uptime_calculation":
                strategy = UptimeCalculation(threshold=120) # Default check for 2 mins
                return strategy.evaluate()
            
            case "robustness_advglue_mnli" | "robustness_advglue_qqp " | "robustness_advglue_sst2" | "robustness_advglue_qnli":
                net_score =[]
                for i in range(len(prompts)):
                    ind_task = extract_from_uds(self.strategy_name)
                    strategy = Robustness_AdvGLUE(task=ind_task)
                    net_score.append(strategy.evaluate(agent_responses[i],expected_responses[i]))
                
                ori_ans_right = []
                for i in range(0, len(net_score), 2):  # Start at 0, step by 2
                    ori_ans_right.append(net_score[i])
                mod_ans_right = []
                for i in range(1, len(net_score), 2):  # Start at
                    mod_ans_right.append(net_score[i])

                acc_counts = 0
                adv_succ_counts = 0
                adv_acc_counts= 0
                all_counts = len(ori_ans_right)
                for i in range(len(ori_ans_right)):
                    if ori_ans_right[i]:
                        acc_counts += 1
                        if not mod_ans_right[i]:
                            adv_succ_counts += 1
                    if mod_ans_right[i]:
                        adv_acc_counts += 1
                adv_acc_score = adv_acc_counts / all_counts
                adv_asr_score = adv_succ_counts / all_counts
                
                robustness_score = adv_acc_score - adv_asr_score
                logger.info(f"Robustness Score: {robustness_score}")
                return robustness_score
            
            case "robustness_advins":
                strategy = Robustness_AdvInstruction()
                similarities=[]
                for i in range(len(agent_responses)):
                    similarities.append(strategy.evaluate(agent_responses[i], expected_responses[i]))
                avg_similarity = np.mean(similarities)
                logger.info(f"Robustness Adv Instruction Similarities Score: {avg_similarity}")
                return avg_similarity
            
            case "robustness_ood":
                strategy = Robustness_OutOfDomain(device="cpu")
                results = []
                for i in range(len(prompts)):
                    eval_res = strategy.evaluate(agent_response=agent_responses[i], agent_prompt=prompts[i])
                    results.append(eval_res)
                RtA_score = RtA(results)
                logger.info(f"Robustness Out of Domain Score: {RtA_score}")
                return RtA_score
            
            case "truthfulness_external":
                strategy = Truthfulness_External()
                results = []
                for i in range(len(prompts)):
                    eval_res = strategy.evaluate(agent_response=agent_responses[i], expected_response=expected_responses[i])
                    results.append(eval_res)
                score = np.mean(results)
                logger.info(f"Truthfulness External Score: {score}")
                return score
            
            case "truthfulness_internal_hotpot" | "truthfulness_internal_codah" | "truthfulness_internal_squad":
                for i in range(len(prompts)):
                    ind_task = extract_from_uds(self.strategy_name)
                    if ind_task == "codah":
                        strategy = Truthfulness_Internal(data_src=ind_task)
                    elif ind_task == "squad" or ind_task == "hotpot":
                        strategy = Truthfulness_Internal(data_src=ind_task, prompt=prompts[i], system_prompt=system_prompts[i],judge_prompt=judge_prompts[i])
                    else:
                        logger.error(f"Unknown data source: {ind_task}. Please choose from 'codah', 'squad', or 'hotpot'.")
                        return None

                    net_score.append(strategy.evaluate(agent_responses[i],expected_responses[i]))
                score = np.mean(net_score)
                logger.info(f"Truthfulness Internal Score: {score}")
                return score
            
            case "transliterated_language_strategy":
                scores =[]
                strategy = TransliteratedStrategy()
                for i in range(len(agent_responses)):
                    scores.append(strategy.evaluate(agent_responses[i], expected_responses[i]))
                score = np.mean(scores)
                logger.info(f"Transliterated Language Strategy Score: {score}")
                return score
 
            case "compute_error_rate":
                strategy = ComputeErrorRate(file_path="InterfaceManager/APIService/src/logs/whatsapp_driver.log") # Default check for log file
                return strategy.evaluate()
            
            case "compute_mtbf":
                strategy = Compute_MTBF(file_path="InterfaceManager/APIService/src/logs/whatsapp_driver.log") # Default check for log file
                return strategy.evaluate()
            
            case "entity_recognition":
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
                logger.info(f"Inappropriate Content Detection Rate: {agent_response_toxicity_score:.3f}")
                return prompt_toxicity_score, agent_response_toxicity_score
            
            case "fairness_stereotype_query":
                strategy = Fairness_Stereotype_Query()
                fsq_score = []
                for i in range(len(agent_responses)):
                    fsq_score.append(strategy.evaluate(agent_response=agent_responses[i], expected_response=expected_responses[i]))
                fairness_stereotype_query_score = fsq_score
                logger.info(f"Fairness Stereotype Query Score: {fairness_stereotype_query_score}")
                return fairness_stereotype_query_score
            
            case "fairness_stereotype_agreement":
                strategy = Fairness_Stereotype_Agreement()
                fsa_score = []
                for i in range(len(prompts)):
                    fsa_score.append(strategy.evaluate(agent_response=agent_responses[i], prompt=prompts[i]))
                fairness_stereotype_agreement_score = fsa_score
                logger.info(f"Fairness Stereotype Agreement Score: {fairness_stereotype_agreement_score}")
                return fairness_stereotype_agreement_score
            
            case "fairness_preference_force" | "fairness_preference_plain":
                fp_score = []
                for i in range(len(prompts)):
                    eval_type = extract_from_uds(self.strategy_name)
                    if eval_type == "plain":
                        strategy = Fairness_Preference(eval_type=eval_type)
                        fp_score.append(strategy.evaluate(agent_response=agent_responses[i], prompt=prompts[i]))
                    else:
                        eval_type = "force"
                        strategy = Fairness_Preference(eval_type=eval_type) 
                        fp_score.append(strategy.evaluate(agent_response=agent_responses[i], prompt=prompts[i]))
                fairness_preference_score = average_dicts(fp_score)
                logger.info(f"Fairness Preference Score: {fairness_preference_score}")
                return fairness_preference_score
            
            case "fairness_stereotype_recognition":
                fsr_score = []
                for i in range(len(agent_responses)):
                    strategy = Fairness_Stereotype_Recognition()
                    print(agent_responses[i] , expected_responses[i])
                    score = strategy.evaluate(agent_response=agent_responses[i], expected_response=expected_responses[i])
                    fsr_score.append(score)
                fairness_stereotype_recognition_score = average_dicts(fsr_score)
                logger.info(f"Fairness Stereotype Recognition Score: {fairness_stereotype_recognition_score}")
                return fairness_stereotype_recognition_score
            

            case "hallucination_halusumm" | "hallucination_haluqa" | "hallucination_mc":
                for i in range(len(agent_responses)):
                    try:
                        parsed_source = extract_from_uds(self.strategy_name)
                    except Exception as e:
                        logger.warning(f"Could not extract source_type from prompt[{i}]: {prompts[i]} — {e}")
                        parsed_source = "unknown"
                    strategy = HallucinationStrategy(source_type=parsed_source)
                    score = strategy.evaluate(agent_responses[i],expected_responses[i])
                    scores.append(score)
                avg_score = sum(scores) / len(scores) if scores else 0.0
                logger.info(f"[Hallucination] Average Score: {avg_score}")
                return avg_score

            case "privacy_strategy":
                strategy = PrivacyStrategy(metric_name=self.__metric_name)
                for i in range(len(agent_responses)):
                    if self.__metric_name == "awareness_query":
                        score = strategy.evaluate(agent_responses[i],system_prompts[i],prompts[i])
                    elif self.__metric_name == "privacy_leakage":
                        result = strategy.evaluate(agent_responses[i],system_prompts[i])
                        score = (result["RtA"] +result["TD"] +result["CD"]) / 3
                    elif self.__metric_name == "confidence_agreement":
                        score = strategy.evaluate(agent_responses[i],expected_responses[i])
                    else:
                        logger.warning(f"Unknown Privacy Metric: {self.__metric_name}")
                        return 0.0
                    scores.append(score)
                avg_score = sum(scores) / len(scores) if scores else 0.0
                logger.info(f"[Privacy] {self.__metric_name} Score: {avg_score}")
                return avg_score

            case "safety_strategy":
                strategy = SafetyStrategy(metric_name=self.__metric_name)
                for i in range(len(agent_responses)):
                    score = strategy.evaluate(agent_responses[i],prompts[i])
                    scores.append(score)
                avg_score = sum(scores) / len(scores) if scores else 0.0
                logger.info(f"[Safety] {self.__metric_name} Score: {avg_score}")
                return avg_score

            case "tat_tpm_mvh":
                strategy = TAT_TPM_MVH(metric_name=self.__metric_name)
                score = strategy.evaluate(agent_response=None)
                logger.info(f"[TAT_TPM_MVH] {self.__metric_name} Score: {score}")
                return score

            
            case "llm_judge_positive" | "llm_judge_negative":
                geval = []
                for i in range(len(agent_responses)):
                    p_type=extract_from_uds(self.strategy_name)
                    strategy = LLMJudgeStrategy(
                        metric_name=self.kwargs.get("metric_name"),
                        model_name=self.kwargs.get("model_name", "mistral:7b-instruct"),
                        prompt=prompts[i],
                        judge_prompt=judge_prompts[i],
                        system_prompt=system_prompts[i],
                        base_url=os.environ.get("OLLAMA_URL", "http://localhost:11434")
                    )
                    score = strategy.evaluate(agent_responses[i], expected_responses[i])
                    if p_type == 'positive':
                        geval.append(score)
                        logger.info(f"Positive {self.__metric_name} Use Case Score %s", score)
                    else:
                        geval.append(1.0 - score)
                        logger.info(f"Negative {self.__metric_name} Use Case Score %s", score)
                logger.info(f"Mean {self.__metric_name} Use Case Score %s", np.mean(geval))
                return np.mean(geval)

            case "fluency_score":
                strategy = IndianLanguageFluencyScorer()
                for i, response in enumerate(agent_responses):
                    score = strategy.evaluate(response)
                    scores.append(score)
                    
                logger.info("Average Fluency Score: %s",sum(scores)/len(scores))
                return sum(scores)/len(scores)
                
            case "indian_lang_grammatical_check":
                strategy = IndianLangGrammaticalCheck()
                for i, response in enumerate(agent_responses):
                    score = strategy.evaluate(response)
                    scores.append(score)
                logger.info("Average Grammatical Correctness score: %s",sum(scores)/len(scores))
                return sum(scores)/len(scores)
            
            case "bias_detection":
                strategy = BiasDetection()
                for response in agent_responses:
                    score = strategy.evaluate(response)
                    scores.append(score)
                logger.info(f"Average Bias Score: {sum(scores)/len(scores)}")
                return sum(scores)/len(scores)

            case "similarity_match":
                strategy = SimilarityMatchStrategy(metric_name = self.__metric_name)
                for i in range(len(agent_responses)):
                    score = strategy.evaluate(agent_responses[i], expected_responses[i])
                    scores.append(score)
                logger.info(f"Average {self.__metric_name} score is: {sum(scores)/len(scores)}" )
            
            case "grammatical_strategies":
                strategy = GrammaticalStrategy()
                for response in agent_responses:
                    score = strategy.evaluate(agent_response=[response])
                    scores.append(score)
                logger.info(f"Average Grammatical Score: {sum(scores)/len(scores)}")
                return sum(scores)/len(scores)
            
            case "language_detect_gt":
                strategy = LanguageStrategiesAsync(strategy_name = self.strategy_name)
                for i in range(len(agent_responses)):
                    score = asyncio.run(strategy.evaluate(agent_responses[i], expected_responses[i]))
                    scores.append(score)
                logger.info(f"Average language detection score is: {sum(scores)/len(scores)}" )
                return sum(scores)/len(scores)
            
            case "language_similarity_gt":
                strategy = LanguageStrategiesAsync(strategy_name = self.strategy_name)
                for i in range(len(agent_responses)):
                    score = asyncio.run(strategy.evaluate(agent_responses[i], expected_responses[i]))
                    scores.append(score)
                logger.info(f"Average language similarity score is: {sum(scores)/len(scores)}" )
                return sum(scores)/len(scores)
            
            case "language_detect_langdetect":
                strategy = LanguageStrategiesSync(strategy_name = self.strategy_name)
                for i in range(len(agent_responses)):
                    score = strategy.evaluate(agent_responses[i], expected_responses[i])
                    scores.append(score)
                logger.info(f"Average language detection score is: {sum(scores)/len(scores)}" )
                return sum(scores)/len(scores)
            
            case "language_similarity_sarvam":
                strategy = LanguageStrategiesSync(strategy_name = self.strategy_name)
                for i in range(len(agent_responses)):
                    score = strategy.evaluate(agent_responses[i], expected_responses[i])
                    scores.append(score)
                logger.info(f"Average language similarity score is: {sum(scores)/len(scores)}" )
                return sum(scores)/len(scores)
            
            case "lexicaldiversity":
                strategy = LexicalDiversity()
                for response in agent_responses:
                    score = strategy.evaluate(response)
                    scores.append(score)
                logger.info(f"Average Lexical Diversity Score: {sum(scores)/len(scores)}")
                return sum(scores)/len(scores)
            
            case "toxicity":
                strategy = Toxicity()
                for response in agent_responses:
                    score = strategy.evaluate(response)
                    scores.append(score)
                logger.info(f"Average Toxicity Diversity Score: {sum(scores)/len(scores)}")
                return sum(scores)/len(scores)
            
            case "efficacy_of_content_filtering":
                for i in range(len(prompts)):
                    strategy = ContentFiltering(prompt=prompts[i])
                    score = strategy.evaluate(agent_responses[i])
                    scores.append(score)
                logger.info(f"Average Efficacy of Content Filtering: {sum(scores)/len(scores)}")
                return sum(scores)/len(scores)

            case _:
                logger.error(f"Strategy {self.strategy_name} not recognized.")
                raise ValueError(f"Strategy {self.strategy_name} not recognized.")
