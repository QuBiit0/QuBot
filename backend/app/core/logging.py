"""
Logging utilities for Qubot
"""

import logging
import sys


def get_logger(name: str, level: int | None = None) -> logging.Logger:
    """
    Get a logger with the specified name and level.

    Args:
        name: The name of the logger (typically __name__)
        level: The logging level (defaults to INFO)

    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)

    if level is None:
        level = logging.INFO

    logger.setLevel(level)

    # Avoid adding handlers if they already exist
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
