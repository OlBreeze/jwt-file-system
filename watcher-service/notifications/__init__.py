"""
Notifications
"""

from .email_sender import (
    send_email_notification,
    send_error_notification,
    send_success_notification
)
from .syslog_sender import (
    send_syslog_notification,
    send_syslog_error,
    send_syslog_info,
    send_syslog_warning,
    send_syslog_success,
    SYSLOG_ERROR,
    SYSLOG_INFO,
    SYSLOG_WARNING
)

__all__ = [
    'send_email_notification',
    'send_error_notification',
    'send_success_notification',
    'send_syslog_notification',
    'send_syslog_error',
    'send_syslog_info',
    'send_syslog_warning',
    'send_syslog_success',
    'SYSLOG_ERROR',
    'SYSLOG_INFO',
    'SYSLOG_WARNING'
]