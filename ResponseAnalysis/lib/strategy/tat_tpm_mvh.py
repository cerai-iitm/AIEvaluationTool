from strategy_base import Strategy
from typing import Optional
import logging
from datetime import datetime
import re
import math

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("analyzer_log.log")
    ]
)

logger = logging.getLogger(__name__)

class TAT_TPM_MVH(Strategy):
    """
    This module implements:
    1. Turn Around Time (TAT)
    2. Transactions Per Minute (TPM)
    3. Message Volume Handling (MVH)
    """

    def __init__(self, name: str = "tat_tpm_mvh", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.__metric_name = kwargs.get("metric_name")
        self.log_file_path = kwargs.get("log_file_path", "whatsapp_driver.log")
        self.prompt_keyword = "Sending prompt to the bot"
        self.response_keyword = "Received response from WhatsApp"

    def parse_log_file(self) -> list:
        with open(self.log_file_path, 'r', encoding='utf-8') as file:
            return file.readlines()

    def extract_timestamp(self, log_line: str) -> datetime:
        timestamp_match = re.match(r'\[(.*?)\]', log_line)
        return datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S,%f")

    def average_tat(self, log_lines: list) -> float:
        """
        Computes Turn Around Time (TAT) and returns the average TAT.
        Logs individual TATs.
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

    def message_volume_handling(self, time_period_minutes: int) -> float:
        """
        Calculates the number of messages processed per user-defined time period.

        :param time_period_minutes: Time period in minutes.
        :return: Number of messages processed per the given time period.
        """
        logger.info("Starting Message Volume Handling evaluation strategy")
        log_lines = self.parse_log_file()

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

        messages_per_time_period = (total_transactions / total_duration_seconds) * (60 * time_period_minutes)
        logger.info(f"Message Volume Handling: {messages_per_time_period:.2f} messages per {time_period_minutes} minute(s)")
        logger.info("Completed Message Volume Handling evaluation strategy")

        return math.floor(messages_per_time_period)

    def evaluate(self, agent_response: str, expected_response: Optional[str] = None) -> float:
        """
        Evaluate the agent log based on the selected metric.
        Supported metrics:
            - 'turn_around_time'
            - 'transactions_per_minute'
            - 'message_volume_handling'

        :param agent_response: For this metric, not required.
        :param expected_response: For this metric, not required.
        :return: Metric score.
        """
        log_lines = self.parse_log_file()

        match self.__metric_name:
            case "turn_around_time":
                return self.average_tat(log_lines)

            case "transactions_per_minute":
                return self.transactions_per_minute(log_lines)

            case "message_volume_handling":
                time_period_minutes = self._Strategy__kwargs.get("time_period_minutes", 1)
                return self.message_volume_handling(time_period_minutes)

            case _:
                raise ValueError(f"Unknown metric name: {self.__metric_name}")

        return 0.0

from ResponseAnalysis.lib.strategy.tat_tpm_mvh import TAT_TPM_MVH

tat_metric = TAT_TPM_MVH(metric_name="turn_around_time", log_file_path="whatsapp_driver.log")
tat_score = tat_metric.evaluate("", "")
print(f"Turn Around Time: {tat_score:.2f} seconds")

tpm_metric = TAT_TPM_MVH(metric_name="transactions_per_minute", log_file_path="whatsapp_driver.log")
tpm_score = tpm_metric.evaluate("", "")
print(f"Transactions Per Minute: {tpm_score} transactions/min")

mvh_metric = TAT_TPM_MVH(metric_name="message_volume_handling", log_file_path="whatsapp_driver.log", time_period_minutes=5)
mvh_score = mvh_metric.evaluate("", "")
print(f"Message Volume Handling: {mvh_score} messages per 5 minutes")
