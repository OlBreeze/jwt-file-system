"""
API endpoints for working with logs
"""

import logging
from pathlib import Path
from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)


def create_logs_bp(config, app_logger):
    """
    Creates a blueprint for logs routes

    Args:
        config (dict): Application configuration
        app_logger: Logger object

    Returns:
        Blueprint
    """
    logs_bp = Blueprint('logs', __name__)

    @logs_bp.route('/api/logs/recent', methods=['GET'])
    def get_recent_logs():
        """Retrieve the most recent service log entries"""

        try:
            log_file = Path(config['logging']['file'])

            if not log_file.exists():
                return jsonify([]), 200

            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-50:]  # Последние 50 строк

            logs = []
            for line in lines:
                parts = line.split(' - ')
                if len(parts) >= 3:
                    logs.append({
                        'timestamp': parts[0],
                        'level': parts[2].strip(),
                        'message': ' - '.join(parts[3:]).strip()
                    })

            return jsonify(logs), 200

        except Exception as e:
            app_logger.error(f"Failed to get recent logs: {e}")
            return jsonify({'error': str(e)}), 500

    return logs_bp