import logging
from datetime import datetime


def setup_logger(name: str, log_dir: str = ".") -> logging.Logger:
    log_file = f"tui_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(f"{log_dir}/{log_file}"),
        ],
    )
    logger = logging.getLogger(name)
    return logger
