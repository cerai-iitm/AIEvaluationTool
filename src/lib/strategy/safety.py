import warnings
import os
import requests
import json
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("safety_strategy")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="safety_strategy")

class SafetyStrategy(Strategy):
    """
    Strategy for evaluating safety-related risks in chatbot responses.
    Supports misuse detection, jailbreak attempts, and exaggerated safety behaviors.
    """

    def __init__(self, name: str = "safety_strategy", **kwargs) -> None:
        """
        Initializes the SafetyStrategy and loads the safety evaluation model.

        Parameters:
        - name (str): Name of the strategy.
        - kwargs: Additional parameters including metric_name.
        """
        super().__init__(name, kwargs=kwargs)
        self.__metric_name = kwargs.get("metric_name", dflt_vals.default_metric)
        self.gpu_url=os.getenv("GPU_URL")

        if not self.gpu_url:
            logger.warning("GPU_URL is not set in environment.")
        else:
            logger.info("GPU_URL is loaded from environment.")

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        """
        Dispatches to the appropriate safety metric based on the selected metric name.

        Parameters:
        - agent_response (str): Agent-generated response.
        - prompt (str): User's input prompt.

        Returns:
        - float: Evaluation score for the selected safety metric.
        """
        match self.__metric_name:
            case "misuse":
                logger.info("Starting misuse evaluation with ShieldGemma")
                resp = requests.post(f"{self.gpu_url}/safety_eval",params={"prompt": testcase.prompt.user_prompt,"agent_response":conversation.agent_response,"metric_name": self.__metric_name})
                json_str = resp.content.decode('utf-8')
                data = json.loads(json_str)
                logger.info(f"Misuse Score: {data['score']:.4f}")
                return data['score'], ""
            case "jailbreak":
                logger.info("Starting jailbreak evaluation with ShieldGemma")
                resp = requests.post(f"{self.gpu_url}/safety_eval",params={"prompt": testcase.prompt.user_prompt,"agent_response":conversation.agent_response,"metric_name": self.__metric_name})
                json_str = resp.content.decode('utf-8')
                data = json.loads(json_str)
                logger.info(f"Jailbreak Score: {data['score']:.4f}")
                return data['score'], ""
            case "exaggerated_safety":
                logger.info("Starting Exaggerated Safety evaluation with ShieldGemma")
                resp = requests.post(f"{self.gpu_url}/safety_eval",params={"prompt": testcase.prompt.user_prompt,"agent_response":conversation.agent_response,"metric_name": self.__metric_name})
                json_str = resp.content.decode('utf-8')
                data = json.loads(json_str)
                logger.info(f"Exaggerated Safety Score: {data['score']:.4f}")
                return data['score'], ""
            case _:
                raise ValueError(f"Unknown safety metric: {self.__metric_name}")
