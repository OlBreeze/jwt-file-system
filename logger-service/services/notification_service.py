"""Notification service (Email and Syslog)"""
import os
import smtplib
import socket
import logging
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_email_notification(config, subject, message, app_logger=None):
    """
    Sends an email notification.

    Args:
        config: Application configuration
        subject: Email subject
        message: Message text
        app_logger: Logger for debugging (optional)
    """
    log = app_logger or logger

    if not config['notifications']['email']['enabled']:
        log.debug("Email notifications disabled")
        return

    try:
        email_config = config['notifications']['email']

        msg = MIMEText(message)
        msg['Subject'] = f"[Logger Service] {subject}"
        msg['From'] = email_config['from']
        msg['To'] = email_config['to']

        with smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port']) as server:
            if email_config.get('use_tls', True):
                server.starttls()

            password = email_config.get('password') or os.getenv('EMAIL_PASSWORD')
            if password:
                server.login(email_config['from'], password)

            server.send_message(msg)

        log.debug(f"📧 Email sent: {subject}")

    except Exception as e:
        log.error(f"❌ Failed to send email: {e}")


def send_syslog_notification(config, level, message, app_logger=None):
    """
    Sends a syslog notification.

    Args:
        config: Application configuration
        level: Severity level (0-7)
               0 = Emergency, 3 = Error, 4 = Warning, 6 = Info
        message: Message text
        app_logger: Logger for debugging (optional)
    """
    log = app_logger or logger

    if not config['notifications']['syslog']['enabled']:
        log.debug("Syslog notifications disabled")
        return

    try:
        syslog_config = config['notifications']['syslog']

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Формат syslog: <priority>timestamp hostname tag: message
        # priority = facility * 8 + severity
        # facility 16 = local use 0
        priority = 16 * 8 + level
        syslog_msg = f"<{priority}>logger-service: {message}"

        sock.sendto(
            syslog_msg.encode('utf-8'),
            (syslog_config['host'], syslog_config['port'])
        )

        sock.close()
        log.debug(f"📡 Syslog sent: {message[:50]}...")

    except Exception as e:
        log.error(f"❌ Failed to send syslog: {e}")


# Constants for syslog levels (for convenience)
class SyslogLevel:
    """RFC 5424 Syslog Severity Levels"""
    EMERGENCY = 0  # System is unusable
    ALERT = 1  # Action must be taken immediately
    CRITICAL = 2  # Critical conditions
    ERROR = 3  # Error conditions
    WARNING = 4  # Warning conditions
    NOTICE = 5  # Normal but significant condition
    INFO = 6  # Informational messages
    DEBUG = 7  # Debug-level messages