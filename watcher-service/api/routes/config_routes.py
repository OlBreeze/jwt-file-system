"""
API endpoints for managing configuration
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from core.config import save_config

logger = logging.getLogger(__name__)

config_bp = Blueprint('config', __name__)


@config_bp.route('/config', methods=['GET'])
def get_config():
    """
    Get the current configuration

    Returns:
        JSON: Application configuration
    """
    try:
        config = current_app.config['WATCHER_CONFIG']

        # Hide sensitive data
        safe_config = config.copy()
        if 'jwt' in safe_config and 'secret' in safe_config['jwt']:
            safe_config['jwt']['secret'] = '***hidden***'
        if 'notifications' in safe_config and 'email' in safe_config['notifications']:
            if 'password' in safe_config['notifications']['email']:
                safe_config['notifications']['email']['password'] = '***hidden***'

        return jsonify(safe_config), 200

    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        return jsonify({'error': str(e)}), 500


@config_bp.route('/config/<section>', methods=['PUT'])
def update_config(section):
    """
    Update a configuration section

    Args:
        section (str): Section name to update

    Returns:
        JSON: Update result
    """
    try:
        config = current_app.config['WATCHER_CONFIG']
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        if section not in config:
            return jsonify({'error': f'Unknown section: {section}'}), 400

        # Update section
        if isinstance(config[section], dict) and isinstance(data, dict):
            config[section].update(data)
        else:
            config[section] = data

        # Save to file
        save_config(config)

        logger.info(f"Configuration section '{section}' updated")
        return jsonify({
            'status': 'success',
            'message': f'{section} updated'
        }), 200

    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        return jsonify({'error': str(e)}), 500


@config_bp.route('/config/reload', methods=['POST'])
def reload_config():
    """
    Reload configuration from file

    Returns:
        JSON: Reload result
    """
    try:
        from core.config import load_config

        # Reload configuration
        new_config = load_config()
        current_app.config['WATCHER_CONFIG'] = new_config

        logger.info("Configuration reloaded from file")
        return jsonify({
            'status': 'success',
            'message': 'Configuration reloaded'
        }), 200

    except Exception as e:
        logger.error(f"Failed to reload config: {e}")
        return jsonify({'error': str(e)}), 500
