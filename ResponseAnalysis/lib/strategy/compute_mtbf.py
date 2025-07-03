from strategy_base import Strategy

from datetime import datetime
import logging
import warnings

logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  
        logging.FileHandler("analyzer_log.log")  
    ]
)

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore")

# this module compute mean time between failures from the log file generated during interaction with AI agents
class Compute_MTBF(Strategy):
    def __init__(self, name: str = "compute_mtbf", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)

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

    def evaluate(self, file_path: str) -> float:
        """
        Calculate Mean Time Between Failures (MTBF) using the interaction log file

        :param filepath - The log file captured during the interacting with AI Agents
        :return : A time representing the mean time between failures.
        """
        timestamps = self.extract_failure_timestamps(file_path)
        mtbf_time, uptime = self.calculate_mtbf_from_timestamps(timestamps)
        return mtbf_time, uptime

# Example usage
# strategy = Compute_MTBF()
# file_path = "Data/whatsapp_driver.log"
# mtbf_time = strategy.evaluate(file_path=file_path)
# print(f"Mean time Between Failure (in Hrs): {mtbf_time}")

# # example usage
# log_file_path = "whatsapp_driver.log" 
# failures = extract_failure_timestamps(log_file_path)

# if failures:
#     mtbf, uptimes = calculate_mtbf_from_timestamps(failures)
#     logger.info(f"MTBF: {mtbf:.2f} hours")
# else:
#     logger.debug("No ERROR events found.")
