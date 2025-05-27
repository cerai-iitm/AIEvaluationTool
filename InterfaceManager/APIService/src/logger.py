# logger.py

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    ch.setFormatter(ch_formatter)

    # File handler (rotates at 1MB, keeps 5 files)
    fh = RotatingFileHandler(os.path.join(LOG_DIR, f"{name}.log"), maxBytes=1_000_000, backupCount=5)
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s - %(message)s")
    fh.setFormatter(fh_formatter)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)

    logger.propagate = False
    return logger
