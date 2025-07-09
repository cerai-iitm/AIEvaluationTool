from calculate_uptime import UptimeCalculation
from robustness_advGLUE import Robustness_AdvGLUE
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

    def execute(self, prompts: Optional[List[str]] = None, expected_response: Optional[List[str]] = None, agent_response: Optional[List[str]] = None, judge_prompt: Optional[List[str]] = None) -> float :
        """
        Execute the current strategy with the provided arguments.
        """
        match self.strategy_name:
            case "uptime_calculation":
                strategy = UptimeCalculation(threshold=120) # Default check for 2 mins
                return strategy.evaluate()
            case "robustness_advglue":
                net_score =[]
                for i in range(len(prompts)):
                    if i<4:
                        ind_task = "qqp"
                    elif i<8:
                        ind_task = "sst2"
                    elif i<12:
                        ind_task = "qnli"
                    else:
                        ind_task = "mnli"
                    strategy = Robustness_AdvGLUE(task=ind_task)
                    net_score.append(strategy.advglue_eval())
                
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


                            