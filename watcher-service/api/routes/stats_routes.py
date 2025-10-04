"""
API endpoints for statistics
"""

import logging
import requests
from flask import Blueprint, jsonify, current_app

logger = logging.getLogger(__name__)

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get service statistics

    Returns:
        JSON: File processing statistics
    """
    try:
        config = current_app.config['WATCHER_CONFIG']
        stats = current_app.config['WATCHER_STATS']

        return jsonify(stats.to_dict(config)), 200

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/stats/reset', methods=['POST'])
def reset_stats():
    """
    Reset statistics

    Returns:
        JSON: Reset result
    """
    try:
        stats = current_app.config['WATCHER_STATS']

        stats.total_processed = 0
        stats.today_processed = 0
        stats.failed = 0

        logger.info("Statistics reset")
        return jsonify({
            'status': 'success',
            'message': 'Statistics reset'
        }), 200

    except Exception as e:
        logger.error(f"Failed to reset stats: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/test-connection', methods=['GET'])
def test_connection():
    """
    Test connection to Logger Service

    Returns:
        JSON: Connection test result
    """

    try:
        config = current_app.config['WATCHER_CONFIG']
        # logger_url = config['logger_service']['url'].replace('/log', '/health')
        logger_url = config['logger_service']['url'].rsplit('/log', 1)[0] + '/health'

        response = requests.get(logger_url, timeout=5)

        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Logger Service is reachable',
                'response': response.json()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Logger returned status {response.status_code}'
            }), 502

    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Connection timeout'
        }), 504

    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'Cannot connect to Logger Service'
        }), 503

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500