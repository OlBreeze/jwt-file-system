"""
Syslog notifications
"""

import logging
import socket
from datetime import datetime

logger = logging.getLogger(__name__)

# Syslog severity levels
SYSLOG_EMERGENCY = 0
SYSLOG_ALERT = 1
SYSLOG_CRITICAL = 2
SYSLOG_ERROR = 3
SYSLOG_WARNING = 4
SYSLOG_NOTICE = 5
SYSLOG_INFO = 6
SYSLOG_DEBUG = 7


def send_syslog_notification(config, level, message):
    """
    Sends a syslog notification.

    Args:
        config (dict): Application configuration
        level (int): Severity level (0-7)
        message (str): Message text
    """
    if not config['notifications']['syslog']['enabled']:
        logger.debug("Syslog notifications are disabled")
        return

    try:
        syslog_config = config['notifications']['syslog']

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Format syslog: <priority>timestamp hostname tag: message
        facility = 16  # local0
        priority = facility * 8 + level

        timestamp = datetime.now().strftime('%b %d %H:%M:%S')
        hostname = socket.gethostname()

        syslog_msg = f"<{priority}>{timestamp} {hostname} watcher-service: {message}"

        sock.sendto(
            syslog_msg.encode('utf-8'),
            (syslog_config['host'], syslog_config['port'])
        )

        sock.close()
        logger.debug(f"Syslog notification sent: {message[:50]}...")

    except Exception as e:
        logger.error(f"Failed to send syslog notification: {e}")


def send_syslog_error(config, error_message):
    """
    Sends a syslog error.

        Args:
            config (dict): Application configuration
            error_message (str): Error text
    """
    send_syslog_notification(config, SYSLOG_ERROR, error_message)


def send_syslog_info(config, info_message):
    """
    Sends an informational message to syslog.

    Args:
        config (dict): Application configuration
        info_message (str): Message text
    """
    send_syslog_notification(config, SYSLOG_INFO, info_message)


def send_syslog_warning(config, warning_message):
    """
    Sends a syslog warning.

    Args:
        config (dict): Application configuration
        warning_message (str): Warning text
    """
    send_syslog_notification(config, SYSLOG_WARNING, warning_message)

def send_syslog_success(config, filename, metadata):
    """
    Sends a syslog notification about successful file processing.

    Args:
        config (dict): Application configuration
        filename (str): File name
        metadata (dict): File metadata
    """
    message = (
        f"File processed successfully: {filename} "
        f"(size: {metadata.get('file_size', 0)} bytes, "
        f"hash: {metadata.get('hash', 'N/A')[:8]}...)"
    )
    send_syslog_notification(config, SYSLOG_INFO, message)