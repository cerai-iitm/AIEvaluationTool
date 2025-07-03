from strategy_base import Strategy

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

# This module calculate error rate using the interaction log
class ComputeErrorRate(Strategy):
    def __init__(self, name: str = "compute_error_rate", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)

    def compute_error_rate_from_log(file_path: str):
        error_count = 0
        total_lines = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                total_lines += 1
                if "ERROR" in line.upper():
                    error_count += 1

        logger.info(f"Total ERROR lines: {error_count}")
        return error_count

    def evaluate(self, file_path: str) -> int:
        """
        Calculate error rate using the interaction log file

        :param filepath - The log file captured during the interacting with AI Agents
        :return : A value representing the number of errors
        """
        error_count = self.compute_error_rate_from_log(file_path)
        return error_count

        # if total_interactions:
        #     error_rate_interaction = error_count / total_interactions
        #     logger.info(f"Error Rate per Interaction: {error_rate_interaction:.2%}")

        # if total_time_seconds:
        #     error_rate_time = error_count / total_time_seconds
        #     logger.info(f"Error Rate per Second: {error_rate_time:.4f} errors/sec")

        # if not total_interactions and not total_time_seconds:
        #     logger.warning("Provide total_interactions or total_time_seconds to compute error rate.")

    # Testing
    # log_file = "whatsapp_driver.log"
    # print(compute_error_rate_from_log(log_file))

strategy = ComputeErrorRate()
file_path = "whatsapp_driver.log"
score = strategy.evaluate(file_path=file_path)
print(f"Error Rate: {score}")
