"""
API routes
"""

from .config_routes import config_bp
from .stats_routes import stats_bp
from .files_routes import files_bp
from .logs_routes import logs_bp

__all__ = [
    'config_bp',
    'stats_bp',
    'files_bp',
    'logs_bp'
]