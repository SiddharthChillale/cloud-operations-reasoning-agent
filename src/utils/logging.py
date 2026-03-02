import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_dir: str | None = None, log_file: str = "app.log"
) -> logging.Logger:
    log_level_str = os.getenv("LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Stream handler is always needed for CLI/TUI and Vercel logs
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # Only add file handler if NOT on Vercel
    if not os.getenv("VERCEL"):
        LOG_PATH = Path.home() / ".cora"
        log_dir = log_dir or os.getenv("LOG_DIR", str(LOG_PATH))
        log_max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))
        log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

        try:
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, log_file)

            rotating_handler = RotatingFileHandler(
                log_path,
                maxBytes=log_max_bytes,
                backupCount=log_backup_count,
            )
            rotating_handler.setLevel(logging.DEBUG)
            rotating_handler.setFormatter(formatter)
            root_logger.addHandler(rotating_handler)
        except Exception as e:
            # Fallback to only stream logging if file access fails
            print(f"Failed to setup file logging: {e}", file=sys.stderr)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
