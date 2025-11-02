from ._lazy_loader import LazyLoader
from typing import Optional
# import numpy as np
# import os
from .logger import get_logger
from lib.data import TestCase, Conversation
from .strategy_base import Strategy

logger = get_logger("strategy_implementor")

#only works with the "changed" strategies for now

class StrategyImplementor:

    def __init__(self, strategy_name:str, **kwargs):
        self.kwargs = kwargs
        self.strategy_name = strategy_name
        self.metric_name = kwargs.get("metric_name", None)
        self.ll = LazyLoader()
    
    def execute(self, testcase:Optional[TestCase], conversation:Optional[Conversation]):
        score = 0
        try:
            obj : Strategy = self.ll.get_class(self.ll.map_name_to_class(self.strategy_name))()
            score = obj.evaluate(testcase, conversation)
        except Exception as e:
            print(f"[ERROR] : {e}")
        return score