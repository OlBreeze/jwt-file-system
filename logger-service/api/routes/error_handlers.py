"""
Flask error handlers
"""

from flask import jsonify
from services.notification_service import send_email_notification


def register_error_handlers(app, config, logger):
    """
    Registers error handlers for the Flask application

    Args:
        app: Flask application
        config (dict): Application configuration
        logger: Logger object
    """

    @app.errorhandler(404)
    def not_found(error):
        """Handles 404 Not Found errors"""
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handles 500 Internal Server Error"""
        logger.error(f"Internal server error: {error}")

        # Send error notification
        send_email_notification(
            config,
            "Internal Server Error",
            f"Error: {str(error)}",
            logger
        )

        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(400)
    def bad_request(error):
        """Handles 400 Bad Request errors"""
        return jsonify({'error': 'Bad request'}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handles 401 Unauthorized errors"""
        return jsonify({'error': 'Unauthorized'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handles 403 Forbidden errors"""
        return jsonify({'error': 'Forbidden'}), 403
