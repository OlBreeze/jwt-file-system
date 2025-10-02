"""
API endpoints for working with logs
"""

import logging
from pathlib import Path
from flask import Blueprint, jsonify, request, current_app

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__)


@logs_bp.route('/logs/recent', methods=['GET'])
def get_recent_logs():
    """
    Get the latest log entries

    Query params:
        lines (int): Number of lines (default 50)

    Returns:
        JSON: Array of logs
    """
    try:
        config = current_app.config['WATCHER_CONFIG']
        log_file = Path(config['logging']['file'])

        # We get the number of lines parameter
        lines_count = request.args.get('lines', default=50, type=int)

        if not log_file.exists():
            return jsonify([]), 200

        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-lines_count:]

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
        logger.error(f"Failed to get recent logs: {e}")
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/logs/search', methods=['GET'])
def search_logs():
    """
    Search logs

    Query params:
        query (str): Search bar
        level (str): Filter by level (INFO, ERROR, WARNING, DEBUG)

    Returns:
        JSON: Log entries found
    """
    try:
        config = current_app.config['WATCHER_CONFIG']
        log_file = Path(config['logging']['file'])

        search_query = request.args.get('query', '').lower()
        level_filter = request.args.get('level', '').upper()

        if not log_file.exists():
            return jsonify([]), 200

        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.split(' - ')
                if len(parts) >= 3:
                    level = parts[2].strip()
                    message = ' - '.join(parts[3:]).strip()

                    # Applying filters
                    if level_filter and level != level_filter:
                        continue

                    if search_query and search_query not in line.lower():
                        continue

                    logs.append({
                        'timestamp': parts[0],
                        'level': level,
                        'message': message
                    })

        # Returning the last 100 results
        return jsonify(logs[-100:]), 200

    except Exception as e:
        logger.error(f"Failed to search logs: {e}")
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/logs/download', methods=['GET'])
def download_logs():
    """
    Download log file

    Returns:
        File: Log file
    """
    try:
        config = current_app.config['WATCHER_CONFIG']
        log_file = Path(config['logging']['file'])

        if not log_file.exists():
            return jsonify({'error': 'Log file not found'}), 404

        from flask import send_file
        return send_file(
            log_file,
            as_attachment=True,
            download_name='watcher_service.log',
            mimetype='text/plain'
        )

    except Exception as e:
        logger.error(f"Failed to download logs: {e}")
        return jsonify({'error': str(e)}), 500