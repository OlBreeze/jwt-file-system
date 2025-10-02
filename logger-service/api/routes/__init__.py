"""
API routes
"""

from .config_routes import create_config_bp
from .stats_routes import create_stats_bp
from .logs_routes import create_logs_bp
from .log_endpoint import create_log_bp

__all__ = [
    'create_config_bp',
    'create_stats_bp',
    'create_logs_bp',
    'create_log_bp'
]