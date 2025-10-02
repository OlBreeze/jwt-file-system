"""
Setting up the logging system
"""

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(config):
    """
    Configures logging with file rotation

    Args:
        config (dict): Application Configuration

    Returns:
        logging.Logger: Configured logger
    """
    # Create a folder for logs if it doesn't exist.
    log_dir = Path(config['logging']['file']).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Determine the logging level
    log_level = getattr(logging, config['logging']['level'].upper(), logging.INFO)

    # Log format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(
        config['logging']['file'],
        maxBytes=config['logging']['max_size_mb'] * 1024 * 1024,
        backupCount=config['logging']['backup_count'],
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Setting up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger