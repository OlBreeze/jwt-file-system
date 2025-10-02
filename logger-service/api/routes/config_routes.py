"""
API endpoints for configuration management
"""

import logging
import yaml
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template

logger = logging.getLogger(__name__)


def create_config_bp(config, app_logger):
    """
    Creates a blueprint for config routes

    Args:
        config (dict): Configuration
        app_logger: Logger объект

    Returns:
        Blueprint
    """
    config_bp = Blueprint('config', __name__)

    @config_bp.route('/', methods=['GET'])
    def index():
        """Web UI homepage"""
        try:
            return render_template('config.html')
        except Exception as e:
            app_logger.debug(f"Template not found: {e}")
            return jsonify({
                'service': 'logger-service',
                'message': 'Web UI not available. Create templates/config.html to enable.',
                'endpoints': {
                    'health': '/health',
                    'log': '/log (POST)',
                    'config': '/api/config (GET)',
                    'update_config': '/api/config/<section> (PUT)',
                    'stats': '/api/stats (GET)',
                    'recent_logs': '/api/logs/recent (GET)'
                }
            }), 200

    @config_bp.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        from datetime import datetime, timezone

        return jsonify({
            'status': 'healthy',
            'service': config['service']['name'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200

    @config_bp.route('/api/config', methods=['GET'])
    def get_config():
        """Get the current configuration"""
        # Hiding sensitive data
        safe_config = config.copy()
        if 'jwt' in safe_config and 'secret' in safe_config['jwt']:
            safe_config['jwt']['secret'] = '***hidden***'
        if 'notifications' in safe_config:
            if 'email' in safe_config['notifications']:
                if 'password' in safe_config['notifications']['email']:
                    safe_config['notifications']['email']['password'] = '***hidden***'

        return jsonify(safe_config), 200

    @config_bp.route('/api/config/<section>', methods=['PUT'])
    def update_config(section):
        """Update configuration section"""
        try:
            data = request.get_json()

            if not data:
                return jsonify({'error': 'No data provided'}), 400

            if section not in config:
                return jsonify({'error': f'Unknown section: {section}'}), 400

            # Updating the section in memory
            if isinstance(config[section], dict) and isinstance(data, dict):
                config[section].update(data)
            else:
                config[section] = data

            # Save to file
            config_path = Path(__file__).parent.parent.parent / 'config.yaml'
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

            app_logger.info(f"Configuration section '{section}' updated")
            return jsonify({
                'status': 'success',
                'message': f'{section} updated'
            }), 200

        except Exception as e:
            app_logger.error(f"Failed to update config: {e}")
            return jsonify({'error': str(e)}), 500

    return config_bp