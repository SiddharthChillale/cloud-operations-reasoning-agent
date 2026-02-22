import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(log_dir: str | None = None) -> logging.Logger:
    log_dir = log_dir or os.getenv("LOG_DIR", "logs")
    log_level_str = os.getenv("LOG_LEVEL", "INFO")
    log_max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))
    log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    rotating_handler = RotatingFileHandler(
        log_file,
        maxBytes=log_max_bytes,
        backupCount=log_backup_count,
    )
    rotating_handler.setLevel(log_level)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    rotating_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(rotating_handler)
    root_logger.addHandler(stream_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
