import warnings
import os
from uptime import uptime
import time
from lib.data import TestCase, Conversation
from .utils_new import FileLoader
from .strategy_base import Strategy
from .logger import get_logger

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("uptime_calculation")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="uptime_calculation")

# This module implements "Robustness Adversarial Instruction" strategy to analyze the agent response.
class UptimeCalculation(Strategy):
    def __init__(self, name: str = "uptime_calculation", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.__threshold = dflt_vals.threshold

    def calculate_uptime(self):
        a = uptime()
        return a
    
    def evaluate(self, testcase:TestCase, conversation:Conversation): #agent_response: Optional[str] = None, expected_response: Optional[str] = None):
        """
        Evaluate the uptime of the application
        """
        start_time = time.time()
        z=[]
        logger.info("Threshold", self.__threshold)
        while time.time() - start_time < self.__threshold: 
            a = self.calculate_uptime()
            logger.info(a)
            time.sleep(10)
            z.append(a)
            if a == "None":
                break
        if len(z) == int(self.__threshold/10):
            return 1
        else:
            logger.error("The application broke or uptime cannot be determined.")
            return 0
    
# #Test
# upt_instance = UptimeCalculation(threshold=100)
# score = upt_instance.evaluate()
# print(f"Score: {score}")
# del upt_instance
# ## Uptime is working!