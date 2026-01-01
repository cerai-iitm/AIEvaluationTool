from datetime import datetime
import warnings
import os
from lib.data import TestCase, Conversation
from .utils_new import FileLoader
from .strategy_base import Strategy
from .logger import get_logger

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("compute_mtbf")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="compute_mtbf")

# this module compute mean time between failures from the log file generated during interaction with AI agents
class Compute_MTBF(Strategy):
    def __init__(self, name: str = "compute_mtbf", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.file_path = dflt_vals.file_path

    def extract_failure_timestamps(self, log_path, keyword="ERROR"):
        """
        Extracts timestamps of log entries containing a specified keyword from a log file

        :param log_path(str) - Path to the log file
        :param keyword (str, optional) - The keyword to search for in log lines. Defaults to "ERROR"
        :return List[datetime] - A list of 'datetime' objects corresponding to the timestamps of matched log entries.
        """
        timestamps = []
        with open(log_path, 'r', encoding='utf-8') as file:
            for line in file:
                if f"[{keyword}]" in line:
                    try:
                        first_bracket = line.find("[") + 1
                        second_bracket = line.find("]")
                        ts_str = line[first_bracket:second_bracket].strip()
                        
                        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")
                        timestamps.append(ts)
                    except Exception as e:
                        logger.info(f"Skipping line: {line.strip()} -> Error: {e}")
        return timestamps

    def calculate_mtbf_from_timestamps(self, timestamps):
        """
        Calculates the Mean Time Between Failures (MTBF) from a list of failure timestamps

        :param timestamps (List[datetime]) - A list of 'datetime' objects representing failure times, ordered chronologicallly.
        :return MTBF (float) - Mean Time Between Failures in hours, uptimes (List[float]) - List of time intervals between failures, in hours.
        """
        if len(timestamps) < 2:
            raise ValueError("At least two failure timestamps are needed to compute MTBF.")

        uptimes = [
            (timestamps[i] - timestamps[i - 1]).total_seconds() / 3600
            for i in range(1, len(timestamps))
        ]
        mtbf = sum(uptimes) / len(uptimes)
        logger.info(f"Mean Time Between Failure (MTBF) in hrs: {mtbf}")
        return mtbf, uptimes

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        """
        Calculate Mean Time Between Failures (MTBF) using the interaction log file

        :param filepath - The log file captured during the interacting with AI Agents
        :return : A time representing the mean time between failures.
        """
        if not self.file_path:
            raise ValueError("file_path is not provided in strategy kwargs.")
        timestamps = self.extract_failure_timestamps(self.file_path)
        mtbf_time, uptime = self.calculate_mtbf_from_timestamps(timestamps)
        return mtbf_time, f"Uptime : {uptime}"

# Example usage
# file_path = "data/whatsapp_driver.log"
# mtbf = Compute_MTBF(file_path=log_file)

