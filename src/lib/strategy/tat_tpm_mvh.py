import os
import warnings
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader
from pathlib import Path

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("tat_tpm_mvh")
project_root = Path(__file__).parents[3]
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="tat_tpm_mvh")

class TAT_TPM_MVH(Strategy):
    """
    This module implements, from the run's own recorded conversation timestamps
    (not a shared interaction log, which measured driver-session uptime rather
    than actual evaluation throughput):
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
            - time_period_minutes (int): Time window for the MVH metric.
        """
        super().__init__(name, kwargs=kwargs)
        self.__metric_name = kwargs.get("metric_name")
        self.db = FileLoader._build_db(project_root)
        self.time_period_minutes = dflt_vals.time_period

    def average_tat(self, stats: dict) -> float:
        """
        Calculates the average Turn Around Time (TAT) across the run's requests.

        Returns:
        - float: Average TAT in seconds.
        """
        logger.info("Starting Turn Around Time evaluation strategy")
        tats = stats["tats"]
        if not tats:
            logger.info("No transactions found for TAT.")
            return 0.0

        average_tat = sum(tats) / len(tats)
        logger.info(f"Average Turn Around Time: {average_tat:.2f} seconds")
        return round(average_tat, 2)

    def transactions_per_minute(self, stats: dict) -> float:
        """
        Calculates Transactions Per Minute (TPM): successful requests over the
        run's actual duration, the same way throughput is measured by tools
        like JMeter/Locust/k6.

        Returns:
        - float: TPM value rounded down to the nearest whole number.
        """
        logger.info("Starting Transactions Per Minute evaluation strategy")
        start_ts, end_ts = stats["start_ts"], stats["end_ts"]
        if start_ts is None or end_ts is None:
            logger.info("No evaluation window found for TPM.")
            return 0.0

        duration_minutes = (end_ts - start_ts).total_seconds() / 60
        if duration_minutes <= 0:
            logger.info("Evaluation window has zero or negative duration for TPM.")
            return 0.0

        tpm = stats["successful_requests"] / duration_minutes
        logger.info(f"Transactions Per Minute: {tpm:.5f}")
        return float(int(tpm))

    def message_volume_handling(self, stats: dict) -> float:
        """
        Calculates the number of messages (prompts + responses) handled per the
        configured time window, over the run's actual duration.

        Returns:
        - float: Number of messages handled per specified time window (rounded down).
        """
        logger.info("Starting Message Volume Handling evaluation strategy")
        start_ts, end_ts = stats["start_ts"], stats["end_ts"]
        if start_ts is None or end_ts is None:
            logger.info("No evaluation window found for Message Volume Handling.")
            return 0.0

        duration_minutes = (end_ts - start_ts).total_seconds() / 60
        if duration_minutes <= 0:
            logger.info("Evaluation window has zero or negative duration for Message Volume Handling.")
            return 0.0

        total_messages = len(stats["prompt_times"]) + len(stats["response_times"])
        mvh = (total_messages / duration_minutes) * self.time_period_minutes
        logger.info(f"Message Volume Handling: {mvh:.5f} messages per {self.time_period_minutes} minute(s)")
        return float(int(mvh))

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        """
        Evaluates the selected metric from the test run's own recorded conversation
        timestamps (the run this conversation belongs to).

        Returns:
        - float: Calculated metric value.
        """
        run_detail = self.db.get_run_detail_by_id(conversation.run_detail_id)
        if run_detail is None:
            raise ValueError(f"Could not resolve the test run for run_detail_id={conversation.run_detail_id}.")

        stats = FileLoader._collect_run_stats(self.db, run_detail.run_name)

        match self.__metric_name.lower():
            case "turn_around_time":
                result = self.average_tat(stats)
                return float(int(result)), f"Average Turn Around Time: {result:.2f} seconds per transaction."

            case "transactions_per_minute":
                result = self.transactions_per_minute(stats)
                return float(int(result)), f"Number of Transactions completed per minute are {result}."

            case "message_volume_handling":
                result = self.message_volume_handling(stats)
                return float(int(result)), f"Number of Messages handled per {self.time_period_minutes} minute(s) are {result}."

            case _:
                raise ValueError(f"Unknown metric name: {self.__metric_name}")

# tat_metric = TAT_TPM_MVH(metric_name="Transactions_per_minute")
# a, _ = tat_metric.evaluate(None, conversation)
# print(f"TAT: {a}")
# print(_)
