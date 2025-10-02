"""
Email notifications
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_email_notification(config, subject, message):
    """
    Sends an email notification

    Args:
        config (dict): Application configuration
        subject (str): Email subject
        message (str): Message text
    """
    try:
        # Check if email notifications are enabled
        if not config.get('notifications', {}).get('email', {}).get('enabled', False):
            logger.debug("Email notifications are disabled")
            return

        email_config = config['notifications']['email']

        # Get email settings from environment or config (env takes priority)
        email_from = os.getenv('EMAIL_FROM') or email_config.get('from')
        email_to = os.getenv('EMAIL_TO') or email_config.get('to')
        email_password = os.getenv('EMAIL_PASSWORD') or email_config.get('password')
        smtp_host = os.getenv('EMAIL_SMTP_HOST') or email_config.get('smtp_host')
        smtp_port = int(os.getenv('EMAIL_SMTP_PORT', email_config.get('smtp_port', 587)))

        # Validate required fields
        if not email_from:
            logger.error("Email 'from' address not set (set EMAIL_FROM env or 'from' in config.yaml)")
            return

        if not email_to:
            logger.error("Email 'to' address not set (set EMAIL_TO env or 'to' in config.yaml)")
            return

        if not email_password:
            logger.error("Email password not set (set EMAIL_PASSWORD env variable)")
            return

        if not smtp_host:
            logger.error("SMTP host not set (set EMAIL_SMTP_HOST env or 'smtp_host' in config.yaml)")
            return

        msg = MIMEText(message)
        msg['Subject'] = f"[Watcher Service] {subject}"
        msg['From'] = email_from
        msg['To'] = email_to

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if email_config.get('use_tls', True):
                server.starttls()

            server.login(email_from, email_password)
            server.send_message(msg)

        logger.info(f"📧 Email notification sent: {subject}")

    except KeyError as e:
        logger.error(f"Configuration error - missing key: {e}")
        logger.error(f"Email config structure: {config.get('notifications', {}).get('email', {})}")
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}", exc_info=True)


def send_error_notification(config, error_type, filepath, error_message):
    """
    Sends an error notification.

    Args:
        config (dict): Application configuration
        error_type (str): Error type
        filepath (str): File path
        error_message (str): Error description
    """
    subject = f"{error_type} Error"
    message = f"""
File: {filepath}
Error: {error_message}

This is an automated notification from Watcher Service.
    """.strip()

    send_email_notification(config, subject, message)


def send_success_notification(config, filename, metadata):
    """
    Sends a notification of successful processing.

    Args:
        config (dict): Application configuration
        filename (str): File name
        metadata (dict): File metadata
    """
    subject = "File Processed Successfully"
    message = f"""
File: {filename}
Size: {metadata.get('file_size', 0)} bytes
Hash: {metadata.get('hash', 'N/A')}

File has been successfully processed and moved to the processed directory.

This is an automated notification from Watcher Service.
    """.strip()

    send_email_notification(config, subject, message)


def send_file_detected_notification(config, filename):
    """
    Sends notification when a new file is detected.

    Args:
        config (dict): Application configuration
        filename (str): File name
    """
    subject = "New File Detected"
    message = f"""
A new file has been detected and is being processed:

File: {filename}

This is an automated notification from Watcher Service.
    """.strip()

    send_email_notification(config, subject, message)


def send_processing_error_notification(config, filename, error_message):
    """
    Sends notification about file processing error.

    Args:
        config (dict): Application configuration
        filename (str): File name
        error_message (str): Error description
    """
    subject = "File Processing Error"
    message = f"""
An error occurred while processing a file:

File: {filename}
Error: {error_message}

The file has been moved to the failed directory for investigation.

This is an automated notification from Watcher Service.
    """.strip()

    send_email_notification(config, subject, message)
