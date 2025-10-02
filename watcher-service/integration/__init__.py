"""
Integration with external services
"""

from .logger_client import send_metadata_to_logger, test_logger_connection

__all__ = [
    'send_metadata_to_logger',
    'test_logger_connection'
]