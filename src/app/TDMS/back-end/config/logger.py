import logging
import os
from logging.handlers import RotatingFileHandler

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("AIEvaluationTool")

def get_logger_verbosity(verbosity: int) -> int:
    verbosity_levels = {
        5: logging.DEBUG,  # Verbose output
        4: logging.INFO,   # Default output
        3: logging.WARNING,  # Warning output
        2: logging.ERROR,    # Error output
        1: logging.CRITICAL,  # Critical output
        0: logging.NOTSET,    # No output
    }
    return verbosity_levels.get(verbosity, logging.NOTSET)

def get_logger(name: str, loglevel = logging.DEBUG, logFile=False) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(loglevel)

    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(loglevel)
    ch_formatter = logging.Formatter("%(asctime)s|%(name)s|%(levelname)s|%(funcName)s|%(message)s")
    ch.setFormatter(ch_formatter)

    # enable file logging only if it is asked for.
    if logFile:
        logdir = os.environ.get("LOG_DIR", "logs")
        os.makedirs(logdir, exist_ok=True)

        # File handler (rotates at 1MB, keeps 5 files)
        fh = RotatingFileHandler(os.path.join(logdir, f"{name}.log"), maxBytes=1_000_000, backupCount=5)
        fh.setLevel(loglevel)
        fh_formatter = logging.Formatter("%(asctime)s|%(name)s|%(levelname)s|%(funcName)s|%(message)s")
        fh.setFormatter(fh_formatter)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(ch)
        if logFile:
            logger.addHandler(fh)

    logger.propagate = False
    return logger