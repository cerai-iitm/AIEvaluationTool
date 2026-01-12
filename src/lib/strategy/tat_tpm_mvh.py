from datetime import datetime
import re
import os
import math
import warnings
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("tat_tpm_mvh")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="tat_tpm_mvh")

class TAT_TPM_MVH(Strategy):
    """
    This module implements:
    1. Turn Around Time (TAT)
    2. Transactions Per Minute (TPM)
    3. Message Volume Handling (MVH)
    """

    def __init__(self, name: str = "tat_tpm_mvh", **kwargs) -> None:
        """
        Initializes the TAT_TPM_MVH strategy.

        Parameters:
        - name (str): Strategy name.
        - kwargs: Additional parameters including:
            - metric_name (str): The metric to be evaluated.
            - log_file_path (str): The path to the log file to be analyzed.
            - time_period_minutes (int): Time window for the MVH metric.
        """
        super().__init__(name, kwargs=kwargs)
        self.__metric_name = kwargs.get("metric_name")
        self.log_file_path = kwargs.get("log_file_path", dflt_vals.log_file)
        self.prompt_keyword = dflt_vals.prompt_key
        self.response_keyword = dflt_vals.response_key
        self.time_period_minutes = dflt_vals.time_period
        self.start_key = dflt_vals.ready_key
        self.quit_key = dflt_vals.quit_key

    def parse_log_file(self) -> list:
        """
        Reads and parses the log file into a list of log lines.

        Returns:
        - list: List of log lines.
        """
        with open(self.log_file_path, 'r', encoding='utf-8') as file:
            return file.readlines()

    def extract_timestamp(self, log_line: str) -> datetime:
        """
        Extracts timestamp from a log line.

        Parameters:
        - log_line (str): Log entry containing a timestamp.

        Returns:
        - datetime: Extracted timestamp as a datetime object.
        """
        timestamp_match = re.match(r'\[(.*?)\]', log_line)
        return datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S,%f")

    def average_tat(self, log_lines: list) -> float:
        """
        Calculates the average Turn Around Time (TAT) from the log file.

        Parameters:
        - log_lines (list): List of log entries.

        Returns:
        - float: Average TAT in seconds.
        """
        logger.info("Starting Turn Around Time evaluation strategy")
        tat_list = []
        prompt_time = None

        for line in log_lines:
            if self.prompt_keyword in line:
                prompt_time = self.extract_timestamp(line)

            elif self.response_keyword in line and prompt_time:
                response_time = self.extract_timestamp(line)
                tat = (response_time - prompt_time).total_seconds()
                tat_list.append(tat)
                # logger.info(f"Computed TAT: {tat} seconds")
                prompt_time = None

        if not tat_list:
            logger.info("No transactions found for TAT.")
            return 0.0

        average_tat = sum(tat_list) / len(tat_list)
        logger.info(f"Average Turn Around Time: {average_tat:.2f} seconds")
        logger.info("Completed Turn Around Time evaluation strategy")
        return round(average_tat, 2)

    def transactions_per_minute(self, log_lines: list) -> float:
        """
        Calculates Transactions Per Minute (TPM) from the log file.

        Parameters:
        - log_lines (list): List of log entries.

        Returns:
        - float: TPM value rounded down to the nearest whole number.
        """
        logger.info("Starting Transactions Per Minute evaluation strategy")
        prompt_times = []
        response_times = []
        sessions = []
        current_session_start = None

        for line in log_lines:
            if self.start_key in line:
                current_session_start = self.extract_timestamp(line)
            elif self.quit_key in line and current_session_start:
                driver_quit_time = self.extract_timestamp(line)
                sessions.append((current_session_start, driver_quit_time))
                current_session_start = None

            elif self.prompt_keyword in line:
                prompt_times.append(self.extract_timestamp(line))

            elif self.response_keyword in line:
                response_times.append(self.extract_timestamp(line))

        if not sessions:
            logger.info("No driver sessions found for TPM.")
            return 0.0

        if not response_times:
            logger.info("No responses found for TPM.")
            return 0.0

        total_active_seconds = sum(
            (end - start).total_seconds()
            for start, end in sessions
            if end > start
        )

        total_transactions = len(response_times)
        transactions_per_minute = (total_transactions / total_active_seconds) * 60
        logger.info(f"Transactions Per Minute: {transactions_per_minute:.5f}")
        logger.info("Completed Transactions Per Minute evaluation strategy")
        return math.floor(transactions_per_minute)

    def message_volume_handling(self, log_lines: list) -> float:
        """
        Calculates the number of messages handled in the specified time window.

        Parameters:
        - log_lines (list): List of log entries.

        Returns:
        - float: Number of messages handled per specified time window (rounded down).
        """
        logger.info("Starting Message Volume Handling evaluation strategy")

        prompt_times = []
        response_times = []
        sessions = []
        current_session_start = None

        for line in log_lines:
            if self.start_key in line:
                current_session_start = self.extract_timestamp(line)

            elif self.quit_key in line and current_session_start:
                driver_quit_time = self.extract_timestamp(line)
                sessions.append((current_session_start, driver_quit_time))
                current_session_start = None

            elif self.prompt_keyword in line:
                prompt_times.append(self.extract_timestamp(line))

            elif self.response_keyword in line:
                response_times.append(self.extract_timestamp(line))

        if not prompt_times or not response_times:
            logger.info("No transactions found for Message Volume Handling.")
            return 0.0

        total_duration_seconds = sum(
            (end - start).total_seconds()
            for start, end in sessions
            if end > start
        )

        if total_duration_seconds <= 0:
            return 0.0

        total_transactions = len(prompt_times) + len(response_times)
        message_volume_per_minute = (total_transactions / total_duration_seconds) * (60 * self.time_period_minutes)
        logger.info(f"Message Volume Handling: {message_volume_per_minute:.5f} messages per {self.time_period_minutes} minute(s)")
        logger.info("Completed Message Volume Handling evaluation strategy")

        return math.floor(message_volume_per_minute)

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        """
        Evaluates the selected metric based on log file data.

        Parameters:
        - agent_response (str): Not used in this evaluation.
        - expected_response (str, optional): Not used in this evaluation.

        Returns:
        - float: Calculated metric value.
        """
        log_lines = self.parse_log_file()

        match self.__metric_name.lower():
            case "turn_around_time":
                result = self.average_tat(log_lines)
                return result, f"Average Turn Around Time: {result:.2f} seconds per transaction."

            case "transactions_per_minute":
                result = self.transactions_per_minute(log_lines)
                return result, f"Number of Transactions completed per minute are {result}."

            case "message_volume_handling":
                result = self.message_volume_handling(log_lines)
                return result, f"Number of Messages handled per {self.time_period_minutes} minute(s) are {result}."

            case _:
                raise ValueError(f"Unknown metric name: {self.__metric_name}")

        return 0.0, ""

# tat_metric = TAT_TPM_MVH(metric_name="Transactions_per_minute", log_file_path="app/interface_manager/logs/interface_manager.log")
# a, _ = tat_metric.evaluate(None, None)
# print(f"TAT: {a}")
# print(_)

