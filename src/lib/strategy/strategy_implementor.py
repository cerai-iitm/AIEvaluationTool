from ._lazy_loader import LazyLoader
from typing import Optional
from .logger import get_logger
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
import re
from itertools import combinations
import traceback

logger = get_logger("strategy_implementor")

class StrategyImplementor:

    # Class-level (process-wide) cache of instantiated strategy objects, keyed by
    # (strategy_name, metric_name). Several strategies load ML models in __init__,
    # and StrategyImplementor is re-created per test case, so without this cache
    # those models get reloaded from disk on every single evaluation.
    _instance_cache: dict = {}

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.ll = LazyLoader()
        self.strategy_name = None
        self.metric_name = None

    def set_metric_strategy(self, strategy_name:str, metric_name:str):
        self.strategy_name = strategy_name
        self.metric_name = metric_name

    def execute(self, testcase:Optional[TestCase], conversation:Optional[Conversation]):
        score = 0
        reason = ""
        try:
            if self.strategy_name:
                logger.info(f"Strategy name is : {self.strategy_name}")
                cls_name = self.find_class_name(self.strategy_name)
                if cls_name is not None:
                    cache_key = (self.strategy_name, self.metric_name)
                    obj : Optional[Strategy] = self._instance_cache.get(cache_key)
                    if obj is None:
                        logger.debug(f"Class has been identified...")
                        obj = self.ll.get_class(cls_name)(name=self.strategy_name, metric_name = self.metric_name)
                        self._instance_cache[cache_key] = obj
                    logger.debug(f"Object has been created and evaluation is starting...")
                    score, reason = obj.evaluate(testcase, conversation)
                    logger.info(f"Evaluation is complete...")
                else:
                    logger.error(f"The specified strategy name : {self.strategy_name} could not be found.")
        except Exception as e:
            logger.error(f"[ERROR] : {e}")
            # traceback.print_exc()
        return score, reason
    
    # this is just in case , should be removable later
    def find_class_name(self, given_name:str):
        words = re.split(r"[_]+", given_name)
        for i in range(len(words), 0, -1):
            for combo in combinations(words, i):
                possible_name = "_".join(list(combo))
                cls_name = self.ll.map_name_to_class(possible_name)
                if cls_name:
                    return cls_name
        return None