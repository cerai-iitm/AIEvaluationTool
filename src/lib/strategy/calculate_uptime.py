import json
import os
import time
import warnings
from pathlib import Path

import requests

from lib.data import TestCase, Conversation
from .utils_new import FileLoader, OllamaConnect
from .strategy_base import Strategy
from .logger import get_logger

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("uptime_calculation")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="uptime_calculation")


def _default_health_url() -> str:
    # src/lib/strategy/calculate_uptime.py -> project root
    config_path = Path(__file__).resolve().parents[3] / "config.json"
    port = "7000"
    try:
        with open(config_path, "r") as f:
            port = json.load(f).get("port", {}).get("back-end", port)
    except FileNotFoundError:
        pass
    return f"http://localhost:{port}/health"


# This module checks the backend application's /health endpoint to verify it stays up over the threshold window.
class UptimeCalculation(Strategy):
    def __init__(self, name: str = "uptime_calculation", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.__threshold = dflt_vals.threshold
        self.__health_url = os.getenv("BACKEND_HEALTH_URL", _default_health_url())
        self.metric_name = kwargs.get("metric_name", name)

    def check_health(self) -> bool:
        try:
            response = requests.get(self.__health_url, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as exc:
            logger.error(f"Health check request failed: {exc}")
            return False

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        """
        Evaluate the uptime of the application by polling its /health endpoint.
        """
        start_time = time.time()
        checks = []
        logger.info(f"Threshold : {self.__threshold}")
        while time.time() - start_time < self.__threshold:
            healthy = self.check_health()
            logger.info(f"Health check ({self.__health_url}): {'up' if healthy else 'down'}")
            checks.append(healthy)
            if not healthy:
                break
            time.sleep(10)
        if checks and all(checks) and len(checks) == int(self.__threshold / 10):
            score = 1.0
            reason = f"The application stayed healthy for {self.__threshold} seconds ({len(checks)} checks passed)."
        else:
            logger.error("The application is unhealthy or unreachable.")
            score = 0.0
            reason = "The application is unhealthy or unreachable."

        if dflt_vals.model_reason:
            try:
                reason = OllamaConnect.get_reason(conversation.agent_response, score, metric_name=self.metric_name)
            except Exception as e:
                logger.error(f"Could not fetch the reason for score from Ollama, falling back to the deterministic reason: {e}")
        return score, reason