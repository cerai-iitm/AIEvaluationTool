from strategy_base import Strategy
from typing import Optional
import logging
from datetime import datetime
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("analyzer_log.log")
    ]
)

logger = logging.getLogger(__name__)

class TurnAroundTimeMetric(Strategy):
    """
    This module implements the Turn Around Time (TAT) and Transactions Per Minute (TPM) metric strategy.
    It calculates:
    1. Turn Around Time: The time between sending a prompt and receiving the first response.
    2. Transactions Per Minute: The number of completed prompt-response pairs per minute.
    """

    def __init__(self, name: str = "turn_around_time", **kwargs) -> None:
        """
        Initialize the TurnAroundTimeMetric strategy.

        :param name: Name of the strategy.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(name, kwargs=kwargs)
        self.log_file_path = kwargs.get("log_file_path", "whatsapp_driver.log")
        self.prompt_keyword = "Sending prompt to the bot"
        self.response_keyword = "Received response from WhatsApp"

    def parse_log_file(self) -> list:
        """
        Reads the log file and returns the list of log lines.

        :return: List of log entries.
        """
        with open(self.log_file_path, 'r', encoding='utf-8') as file:
            return file.readlines()

    def extract_timestamp(self, log_line: str) -> datetime:
        """
        Extracts the timestamp from a log line.

        :param log_line: A log entry.
        :return: The extracted timestamp.
        """
        timestamp_match = re.match(r'\[(.*?)\]', log_line)
        return datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S,%f")

    def compute_tat(self, log_lines: list) -> list:
        """
        Identifies prompt-response pairs and computes their Turn Around Time (TAT).

        :param log_lines: List of log entries.
        :return: List of TATs in seconds for each prompt-response pair.
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

        logger.info("Completed Turn Around Time evaluation strategy")
        return tat_list

    def calculate_average_tat(self, tat_list: list) -> float:
        """
        Calculates the average Turn Around Time (TAT).

        :param tat_list: List of individual TATs.
        :return: Average TAT in seconds.
        """
        if not tat_list:
            return 0.0
        return sum(tat_list) / len(tat_list)

    def compute_transactions_per_minute(self, log_lines: list) -> float:
        """
        Computes the number of transactions (prompt-response pairs) per minute.

        :param log_lines: List of log entries.
        :return: Transactions per minute.
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
            logger.info("No transactions found.")
            return 0.0

        total_duration_seconds = (max(response_times) - min(prompt_times)).total_seconds()
        total_transactions = len(response_times)

        if total_duration_seconds == 0:
            return float(total_transactions)

        transactions_per_minute = (total_transactions / total_duration_seconds) * 60
        logger.info(f"Transactions Per Minute: {transactions_per_minute:.2f}")
        logger.info("Completed Transactions Per Minute evaluation strategy")
        return transactions_per_minute

    def evaluate(self, agent_response: str, expected_response: Optional[str] = None) -> float:
        """
        Evaluate the Turn Around Time (TAT) from the log file.

        :param agent_response: Not used for this strategy.
        :param expected_response: Not used for this strategy.
        :return: Average TAT in seconds.
        """
        log_lines = self.parse_log_file()
        tat_list = self.compute_tat(log_lines)
        average_tat = self.calculate_average_tat(tat_list)

        logger.info(f"Average Turn Around Time: {average_tat:.2f} seconds")
        return average_tat

    def calculate_transactions_per_minute(self) -> float:
        """
        Calculates the Transactions Per Minute (TPM) from the log file.

        :return: Transactions per minute.
        """
        log_lines = self.parse_log_file()
        return self.compute_transactions_per_minute(log_lines)

# test 
from tat_tpm import TurnAroundTimeMetric
tat_metric = TurnAroundTimeMetric(log_file_path="whatsapp_driver.log")

avg_tat = tat_metric.evaluate("", "")
print(f"Average Turn Around Time: {avg_tat:.2f} seconds")

tpm = tat_metric.calculate_transactions_per_minute()
print(f"Transactions Per Minute: {tpm:.2f}")
