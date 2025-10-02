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
    if not config['notifications']['email']['enabled']:
        logger.debug("Email notifications are disabled")
        return

    try:
        email_config = config['notifications']['email']

        msg = MIMEText(message)
        msg['Subject'] = f"[Watcher Service] {subject}"
        msg['From'] = email_config['from']
        msg['To'] = email_config['to']

        with smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port']) as server:
            if email_config.get('use_tls', True):
                server.starttls()

            password = email_config.get('password') or os.getenv('EMAIL_PASSWORD')
            if password:
                server.login(email_config['from'], password)

            server.send_message(msg)

        logger.debug(f"Email notification sent: {subject}")

    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")


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