from strategy import get_class, map_name_to_class
from typing import Optional
# import numpy as np
# import os
from .logger import get_logger
from ..data import TestCase, Conversation
from .strategy_base import Strategy

logger = get_logger("strategy_implementor")

class StrategyImplementor:

    def __init__(self, strategy_name:str, **kwargs):
        self.strategy_name = strategy_name
        self.metric_name = kwargs.get("metric_name")
        self.kwargs = kwargs
    
    def execute(self, testcase:Optional[TestCase], conversation:Optional[Conversation]):
        score = 0
        try:
            obj : Strategy = get_class(map_name_to_class(self.strategy_name))()
            score = obj.evaluate(testcase, conversation)
        except Exception as e:
            print(f"[ERROR] : {e}")
        return score