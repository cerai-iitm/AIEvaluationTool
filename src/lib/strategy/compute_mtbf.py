import json
import warnings
import os
from pathlib import Path

from lib.data import TestCase, Conversation
from lib.orm import DB
from .utils_new import FileLoader, OllamaConnect
from .strategy_base import Strategy
from .logger import get_logger

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("compute_mtbf")
project_root = Path(__file__).parents[3]
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="compute_mtbf")


def _build_db() -> DB:
    """
    Builds a standalone DB connection from config.json, mirroring
    TestCaseExecutorDashboard/back-end/configuration/database.py, so this
    strategy stays independent of the backend app package.
    """
    config_path = project_root / "config.json"
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    db_cfg = config.get("db", {})
    engine_type = db_cfg.get("engine", "sqlite").lower()

    if engine_type == "sqlite":
        db_folder = project_root / "data"
        db_path = db_folder / db_cfg.get("file", "AIEvaluationData.db")
        db_url = f"sqlite:///{db_path}"
    elif engine_type == "mariadb":
        db_url = "mariadb+mariadbconnector://{user}:{password}@{host}:{port}/{database}".format(
            user=db_cfg.get("user"),
            password=db_cfg.get("password"),
            host=db_cfg.get("host"),
            port=db_cfg.get("port"),
            database=db_cfg.get("database"),
        )
    else:
        raise ValueError(f"Unsupported database engine: {engine_type}")

    return DB(db_url=db_url, debug=False)


# This module scores reliability from failed test-case details recorded in the DB,
# instead of parsing a shared interaction log that isn't scoped to any one run.
# Score = 1 - (failures / total requests): 1.0 when nothing failed, 0.0 when everything
# did, stable regardless of how failures happen to be spaced out over time.
class Compute_MTBF(Strategy):
    def __init__(self, name: str = "compute_mtbf", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.db = _build_db()
        self.metric_name = kwargs.get("metric_name", name)

    def _failure_stats(self, run_name: str = None):
        """
        Counts FAILED vs total test-case details, scoped to a single run when
        run_name is given, otherwise across every run in the DB.

        :return (failures, total) - failure count and total request count.
        """
        run_names = [run_name] if run_name is not None else [r.run_name for r in self.db.get_all_runs()]

        failures = 0
        total = 0
        for name in run_names:
            for detail in self.db.get_all_run_details_by_run_name(name):
                total += 1
                if detail.status == "FAILED":
                    failures += 1
        return failures, total

    def compute_run_mtbf(self, run_name: str):
        """
        Computes the reliability score using only the requests recorded within a single test run.
        """
        failures, total = self._failure_stats(run_name=run_name)
        if total == 0:
            reason = f"No test-case details recorded in run '{run_name}'."
            logger.info(reason)
            return None, reason

        score = 1 - (failures / total)
        reason = (
            f"Reliability score for run '{run_name}' is {score:.4f} "
            f"({failures} failure(s) out of {total} request(s))."
        )
        logger.info(reason)
        return score, reason

    def compute_overall_mtbf(self):
        """
        Computes the reliability score using every request recorded across all test runs.
        """
        failures, total = self._failure_stats(run_name=None)
        if total == 0:
            reason = "No test-case details recorded across all runs."
            logger.info(reason)
            return None, reason

        score = 1 - (failures / total)
        reason = (
            f"Overall reliability score across all runs is {score:.4f} "
            f"({failures} failure(s) out of {total} request(s))."
        )
        logger.info(reason)
        return score, reason

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        """
        Calculate a reliability score (1 - failure rate) across every request recorded
        in the database, not just the test run this conversation belongs to.
        """
        # Default metric
        score, reason = self.compute_overall_mtbf()
        if dflt_vals.model_reason:
            try:
                reason = OllamaConnect.get_reason(conversation.agent_response, score, metric_name=self.metric_name)
            except Exception as e:
                logger.error(f"Could not fetch the reason for score from Ollama, falling back to the deterministic reason: {e}")
        return score, reason

