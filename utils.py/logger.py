import logging
import os
from datetime import datetime


def setup_logger(
    name: str,
    log_dir: str = "logs",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Create and configure a logger.

    Args:
        name (str): Logger name (usually __name__)
        log_dir (str): Directory to store log files
        level (int): Logging level

    Returns:
        logging.Logger: Configured logger instance
    """

    # Create logs directory if not exists
    os.makedirs(log_dir, exist_ok=True)

    # Create log file name with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{timestamp}.log")

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Avoid duplicate logs

    # Prevent duplicate handlers if already added
    if not logger.handlers:

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
