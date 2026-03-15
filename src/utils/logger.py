import logging
import sys
import os


def get_app_logger(
    name: str = "obsidian-logger",
    level: int = logging.INFO,
    log_file: str = "logs/app.log",
) -> logging.Logger:
    """Initializes and returns a configured logger"""

    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)

    # Avoid  adding multiple handlers if the logger alreasy exits
    if not logger.handlers:
        logger.setLevel(level)

        # Format: Time - Name - Level - Message
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
