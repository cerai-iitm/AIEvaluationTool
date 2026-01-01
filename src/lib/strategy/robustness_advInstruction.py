import warnings
from .strategy_base import Strategy
from .similarity_match import SimilarityMatchStrategy
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader, OllamaConnect    

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("robustness_advins")

# This module implements "Robustness Adversarial Instruction" strategy to analyze the agent response.
class Robustness_AdvInstruction(Strategy):
    def __init__(self, name: str = "robustness_advins", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.similarity_checker = SimilarityMatchStrategy(metric_name="cosine_similarity")
    
    def evaluate(self,testcase:TestCase, conversation:Conversation): #agent_response: str, expected_response: str):
        """
        Evaluate the agents response for Robustness Adv Instruction using Cosine Similarity.
        """
        return self.similarity_checker.evaluate(testcase, conversation), OllamaConnect.get_reason(conversation.agent_response, " ".join(self.name.split("_")), self.similarity_checker.evaluate(testcase, conversation))
    
#Test
# rbadv_instance = Robustness_AdvInstruction()
# score = rbadv_instance.evaluate("The cat sat on the warm windowsill in the afternoon sun.","The dog lay on the cozy cushion in the morning light.")
# print(f"Score: {score}")
# del rbadv_instance
## Robustness_AdvInstruction is working!