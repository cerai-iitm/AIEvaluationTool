from strategy_base import Strategy
from typing import Optional
import warnings
import re
from logger import get_logger
from uptime import uptime
import time


logger = get_logger("uptime")

warnings.filterwarnings("ignore")

# This module implements "Robustness Adversarial Instruction" strategy to analyze the agent response.
class UptimeCalculation(Strategy):
    def __init__(self, name: str = "uptime_calculation", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.__threshold = kwargs.get("threshold") #in seconds

    def calculate_uptime(self):
        a = uptime()
        return a
    
    def evaluate(self, agent_response: Optional[str] = None, expected_response: Optional[str] = None):
        """
        Evaluate the uptime of the application
        """
        start_time = time.time()
        z=[]
        print("Threshold",self.__threshold)
        while time.time() - start_time < self.__threshold: 
            a = self.calculate_uptime()
            print(a)
            time.sleep(10)
            z.append(a)
            if a == "None":
                break
        if len(z) == int(self.__threshold/10):
            return 1
        else:
            logger.info("The application broke or uptime cannot be determined.")
            return 0
    
# #Test
# upt_instance = UptimeCalculation(threshold=100)
# score = upt_instance.evaluate()
# print(f"Score: {score}")
# del upt_instance
# ## Uptime is working!