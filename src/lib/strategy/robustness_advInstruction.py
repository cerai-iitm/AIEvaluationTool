from typing import Optional
from opik.evaluation.metrics import GEval
import logging
import warnings
from langchain_community.llms import Ollama
import re

from .logger import get_logger
from .strategy_base import Strategy
from .similarity_match import SimilarityMatchStrategy

logger = get_logger("robustness")

warnings.filterwarnings("ignore")

# This module implements "Robustness Adversarial Instruction" strategy to analyze the agent response.
class Robustness_AdvInstruction(Strategy):
    def __init__(self, name: str = "robustness_advins", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.similarity_checker = SimilarityMatchStrategy(metric_name="cosine_similarity")
    
    def evaluate(self, agent_response: str, expected_response: str):
        """
        Evaluate the agents response for Robustness Adv Instruction using Cosine Similarity.
        """
        return self.similarity_checker.evaluate(agent_response,expected_response)
    
#Test
# rbadv_instance = Robustness_AdvInstruction()
# score = rbadv_instance.evaluate("The cat sat on the warm windowsill in the afternoon sun.","The dog lay on the cozy cushion in the morning light.")
# print(f"Score: {score}")
# del rbadv_instance
## Robustness_AdvInstruction is working!