"""
API endpoints for statistics
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)


def create_stats_bp(config, app_logger):
    """
    Creates a blueprint for stats routes

    Args:
        config (dict): Application configuration
        app_logger: Logger object

    Returns:
        Blueprint
    """
    stats_bp = Blueprint('stats', __name__)

    @stats_bp.route('/api/stats', methods=['GET'])
    def get_stats():
        """Retrieve service statistics"""
        try:
            logs_dir = Path(config['storage']['logs_directory'])

            if not logs_dir.exists():
                return jsonify({
                    'total_logs': 0,
                    'today_logs': 0,
                    'storage_mb': 0
                }), 200

            log_files = list(logs_dir.glob('*.txt'))
            total_logs = len(log_files)

            # Count today’s logs
            today = datetime.now(timezone.utc).date()
            today_logs = sum(
                1 for f in log_files
                if datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).date() == today
            )

            # Calculate storage used
            storage_bytes = sum(f.stat().st_size for f in log_files)
            storage_mb = storage_bytes / (1024 * 1024)

            return jsonify({
                'total_logs': total_logs,
                'today_logs': today_logs,
                'storage_mb': round(storage_mb, 2)
            }), 200

        except Exception as e:
            app_logger.error(f"Failed to get stats: {e}")
            return jsonify({'error': str(e)}), 500

    return stats_bp