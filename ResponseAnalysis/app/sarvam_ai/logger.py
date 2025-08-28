# @author: Sudarsun S
# @date: 2025-07-24
# @description: This module provides a logger utility for the application.

import logging
import os
from logging.handlers import RotatingFileHandler

def get_logger(name: str, loglevel = logging.DEBUG) -> logging.Logger:
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
        logger.addHandler(fh)

    logger.propagate = False
    return logger
