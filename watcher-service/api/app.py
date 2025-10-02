"""
Flask application for Web UI
"""

import logging
from pathlib import Path

from flask import Flask, jsonify, render_template
from .routes.config_routes import config_bp
from .routes.stats_routes import stats_bp
from .routes.files_routes import files_bp
from .routes.logs_routes import logs_bp

logger = logging.getLogger(__name__)


def create_app(config, app_logger, stats_obj):
    """
        Creates and configures a Flask application.

        Args:
            config (dict): Application configuration
            app_logger: Logger object
            stats_obj: Statistics object

        Returns:
            Flask: Configured application
    """
    base_dir = Path(__file__).parent.parent
    template_dir = base_dir / 'templates'
    static_dir = base_dir / 'static'

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir)
    )
    # app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False

    # Saving configuration in the application context
    app.config['WATCHER_CONFIG'] = config
    app.config['WATCHER_LOGGER'] = app_logger
    app.config['WATCHER_STATS'] = stats_obj

    # We are registering blueprints
    app.register_blueprint(config_bp, url_prefix='/api')
    app.register_blueprint(stats_bp, url_prefix='/api')
    app.register_blueprint(files_bp, url_prefix='/api')
    app.register_blueprint(logs_bp, url_prefix='/api')

    # Home page
    @app.route('/')
    def index():
        """Web UI homepage"""
        try:
            return render_template('config.html')
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            return jsonify({
                'service': 'watcher-service',
                'message': 'Web UI not available. Create templates/config.html to enable.',
                'endpoints': {
                    'config': '/api/config (GET)',
                    'update_config': '/api/config/<section> (PUT)',
                    'stats': '/api/stats (GET)',
                    'pending_files': '/api/files/pending (GET)',
                    'recent_logs': '/api/logs/recent (GET)',
                    'test_connection': '/api/test-connection (GET)'
                }
            }), 200

    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'watcher-service'
        }), 200

    logger.info("Flask app created successfully")

    return app