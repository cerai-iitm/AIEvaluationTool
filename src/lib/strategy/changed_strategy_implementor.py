from ._lazy_loader import LazyLoader
from typing import Optional
# import numpy as np
# import os
from .logger import get_logger
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
import re
from itertools import combinations
from .utils import average_dicts

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
            cls_name = self.find_class_name(self.strategy_name)
            if cls_name is not None:
                obj : Strategy = self.ll.get_class(cls_name)(name=self.strategy_name)
                score = obj.evaluate(testcase, conversation)
        except Exception as e:
            print(f"[ERROR] : {e}")
        return score
    
    def find_class_name(self, given_name:str):
        words = re.split(r"[_]+", given_name)
        for i in range(len(words)):
            for combo in combinations(words, i+1):
                possible_name = "_".join(list(combo))
                cls_name = self.ll.map_name_to_class(possible_name)
                if cls_name:
                    return cls_name
        return None