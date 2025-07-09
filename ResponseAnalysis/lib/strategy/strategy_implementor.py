from calculate_uptime import UptimeCalculation
from robustness_advGLUE import Robustness_AdvGLUE
from typing import Optional, List

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
                strategy = Robustness_AdvGLUE()
                return strategy.advglue_eval()