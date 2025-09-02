from .strategy_base import Strategy
from typing import Optional
from .llm_judge import LLMJudgeStrategy
from .similarity_match import SimilarityMatchStrategy

# This module implements a factory for creating strategy instances based on the strategy name.
class StrategyFactory:
    @staticmethod
    def create(strategy_name: str) -> Strategy:
        """
        Factory method to create a strategy instance based on the strategy name.
        
        :param strategy_name: The name of the strategy to create.
        :return: An instance of a Strategy subclass.
        """
        if strategy_name == "llm_judge":
            return LLMJudgeStrategy()
        elif strategy_name == "similarity_match":
            return SimilarityMatchStrategy()
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")