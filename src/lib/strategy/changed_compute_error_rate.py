from typing import Optional
import warnings
from lib.data import TestCase, Conversation
from .utils_new import FileLoader
from .strategy_base import Strategy
from .logger import get_logger
from .strategy_base import Strategy

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("compute_error_rate")

# This module calculate error rate using the interaction log
class ComputeErrorRate(Strategy):
    def __init__(self, name: str = "compute_error_rate", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.file_path = kwargs.get("file_path")

    def compute_error_rate_from_log(self, file_path: str) -> int:
        error_count = 0
        total_lines = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                total_lines += 1
                if "ERROR" in line.upper():
                    error_count += 1

        logger.info(f"Total ERROR lines: {error_count}")
        return error_count

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        """
        Calculate error rate using the interaction log file

        :param filepath - The log file captured during the interacting with AI Agents
        :return : A value representing the number of errors
        """
        if not self.file_path:
            raise ValueError("file_path is not provided in strategy kwargs.")
        return self.compute_error_rate_from_log(self.file_path)

# log_file = "data/whatsapp_driver.log"
# error_rate = ComputeErrorRate(file_path=log_file)
# score = error_rate.evaluate()
# print(f"Error Rate: {score}")
# computer error rate working