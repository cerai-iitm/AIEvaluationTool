import os
import warnings
from lib.data import TestCase, Conversation
from .utils_new import FileLoader, OllamaConnect
from .strategy_base import Strategy
from .logger import get_logger
from pathlib import Path

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("compute_error_rate")
project_root = Path(__file__).parents[3]
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="compute_error_rate")

# This module calculate error rate using the interaction log
class ComputeErrorRate(Strategy):
    def __init__(self, name: str = "compute_error_rate", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.file_path = project_root / Path(dflt_vals.file_path)
        self.metric_name = kwargs.get("metric_name", name)

    def compute_error_rate_from_log(self, file_path: str) -> tuple[float, int, int]:
        error_count = 0
        total_lines = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                total_lines += 1
                if "ERROR" in line.upper():
                    error_count += 1

        error_rate = error_count / total_lines if total_lines else 0.0
        logger.info(f"Total ERROR lines: {error_count} / {total_lines} (rate: {error_rate})")
        return error_rate, error_count, total_lines

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        """
        Calculate error rate using the interaction log file

        :param filepath - The log file captured during the interacting with AI Agents
        :return : A value representing the fraction of log lines that are errors
        """
        if not self.file_path:
            raise ValueError("file_path is not set in defaults.json.")
        error_rate, error_count, total_lines = self.compute_error_rate_from_log(self.file_path)
        reason = f"The error rate in the log file is {error_rate:.4f} ({error_count} of {total_lines} lines)."
        if dflt_vals.model_reason:
            try:
                reason = OllamaConnect.get_reason(conversation.agent_response, error_rate, metric_name=self.metric_name)
            except Exception as e:
                logger.error(f"Could not fetch the reason for score from Ollama, falling back to the deterministic reason: {e}")
        return error_rate, reason

# log_file = "data/whatsapp_driver.log"
# error_rate = ComputeErrorRate(file_path=log_file)