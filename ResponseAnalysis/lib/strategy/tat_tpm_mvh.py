from strategy_base import Strategy
from typing import Optional
from datetime import datetime
import re
import math
from logger import get_logger

logger = get_logger("tat_tpm_mvh")

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
        self.log_file_path = kwargs.get("InterfaceManager\APIService\src\logs\whatsapp_driver.log", "whatsapp_driver.log")
        self.prompt_keyword = "Sending prompt to the bot"
        self.response_keyword = "Received response from WhatsApp"
        self.time_period_minutes = kwargs.get("time_period_minutes", 1)

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
                logger.info(f"Computed TAT: {tat} seconds")
                prompt_time = None

        if not tat_list:
            logger.info("No transactions found for TAT.")
            return 0.0

        average_tat = sum(tat_list) / len(tat_list)
        logger.info(f"Average Turn Around Time: {average_tat:.2f} seconds")
        logger.info("Completed Turn Around Time evaluation strategy")
        return average_tat

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
        prompt_time = None

        for line in log_lines:
            if self.prompt_keyword in line:
                prompt_time = self.extract_timestamp(line)

            elif self.response_keyword in line and prompt_time:
                response_time = self.extract_timestamp(line)
                prompt_times.append(prompt_time)
                response_times.append(response_time)
                prompt_time = None

        if not prompt_times or not response_times:
            logger.info("No transactions found for TPM.")
            return 0.0

        total_duration_seconds = (max(response_times) - min(prompt_times)).total_seconds()
        total_transactions = len(response_times)

        if total_duration_seconds == 0:
            return float(total_transactions)

        transactions_per_minute = (total_transactions / total_duration_seconds) * 60
        logger.info(f"Transactions Per Minute: {transactions_per_minute:.2f}")
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
        prompt_time = None

        for line in log_lines:
            if self.prompt_keyword in line:
                prompt_time = self.extract_timestamp(line)

            elif self.response_keyword in line and prompt_time:
                response_time = self.extract_timestamp(line)
                prompt_times.append(prompt_time)
                response_times.append(response_time)
                prompt_time = None

        if not prompt_times or not response_times:
            logger.info("No transactions found for Message Volume Handling.")
            return 0.0

        total_duration_seconds = (max(response_times) - min(prompt_times)).total_seconds()
        total_transactions = len(response_times)

        if total_duration_seconds == 0:
            return float(total_transactions)

        actual_log_duration_minutes = total_duration_seconds / 60

        if self.time_period_minutes > actual_log_duration_minutes:
            logger.warning(f"Provided time period {self.time_period_minutes} min exceeds log duration {actual_log_duration_minutes:.2f} min. Adjusting to log duration.")
            self.time_period_minutes = math.ceil(actual_log_duration_minutes)

        messages_per_time_period = (total_transactions / total_duration_seconds) * (60 * self.time_period_minutes)
        logger.info(f"Message Volume Handling: {messages_per_time_period:.2f} messages per {self.time_period_minutes} minute(s)")
        logger.info("Completed Message Volume Handling evaluation strategy")

        return math.floor(messages_per_time_period)

    def evaluate(self, agent_response: str, expected_response: Optional[str] = None) -> float:
        """
        Evaluates the selected metric based on log file data.

        Parameters:
        - agent_response (str): Not used in this evaluation.
        - expected_response (str, optional): Not used in this evaluation.

        Returns:
        - float: Calculated metric value.
        """
        log_lines = self.parse_log_file()

        match self.__metric_name:
            case "turn_around_time":
                return self.average_tat(log_lines)

            case "transactions_per_minute":
                return self.transactions_per_minute(log_lines)

            case "message_volume_handling":
                return self.message_volume_handling(log_lines)

            case _:
                raise ValueError(f"Unknown metric name: {self.__metric_name}")

        return 0.0

#test
#from tat_tpm_mvh import TAT_TPM_MVH
#
#tat_metric = TAT_TPM_MVH(metric_name="turn_around_time", log_file_path="whatsapp_driver.log")
#tat_score = tat_metric.evaluate("", "")
#print(f"Turn Around Time: {tat_score:.2f} seconds")
#
#tpm_metric = TAT_TPM_MVH(metric_name="transactions_per_minute", log_file_path="whatsapp_driver.log")
#tpm_score = tpm_metric.evaluate("", "")
#print(f"Transactions Per Minute: {tpm_score} transactions/min")
#
#mvh_metric = TAT_TPM_MVH(metric_name="message_volume_handling", log_file_path="whatsapp_driver.log", time_period_minutes=10)
#mvh_score = mvh_metric.evaluate("", "")
#print(f"Message Volume Handling: {mvh_score} messages in mentioned time period ")


