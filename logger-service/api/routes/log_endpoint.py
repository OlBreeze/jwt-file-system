"""
Main endpoint for receiving file metadata
POST /log
"""

import logging
from pathlib import Path
from flask import Blueprint, request, jsonify
from api.middleware import require_jwt, validate_json
from core.log_manager import create_log_file
from services.notification_service import send_email_notification, send_syslog_notification, SyslogLevel
from utils.formatters import format_file_size

logger = logging.getLogger(__name__)


def create_log_bp(config, app_logger):
    """
    Creates a blueprint for the log endpoint

    Args:
        config (dict): Application configuration
        app_logger: Logger object

    Returns:
        Blueprint
    """
    log_bp = Blueprint('log', __name__)

    @log_bp.route('/log', methods=['POST'])
    @require_jwt(config)
    @validate_json('filename', 'created_at', 'file_size')
    def log_metadata():
        """
        Main endpoint for receiving file metadata

        Headers:
            Authorization: Bearer <JWT>

        Body:
            {
                "filename": "report.pdf",
                "created_at": "2025-09-30T14:33:22Z",
                "file_size": 204800,
                "hash": "sha256..."
            }

        Returns:
            JSON response with status
        """
        metadata = request.get_json()

        # Additional type validation
        if not isinstance(metadata['filename'], str) or not metadata['filename']:
            return jsonify({'error': 'filename must be a non-empty string'}), 400

        if not isinstance(metadata['file_size'], int) or metadata['file_size'] < 0:
            return jsonify({'error': 'file_size must be a non-negative integer'}), 400

        app_logger.info(
            f"📝 Received metadata for file: {metadata['filename']} "
            f"({format_file_size(metadata['file_size'])}) "
            f"from {request.jwt_payload.get('iss')}"
        )

        # ============ Create a log file ============
        success, result = create_log_file(metadata, config, app_logger)

        if not success:
            app_logger.error(f"❌ Failed to create log file: {result}")

            # Sending error notifications
            send_email_notification(
                config,
                "Log File Creation Failed",
                f"Error: {result}\nMetadata: {metadata}",
                app_logger
            )
            send_syslog_notification(
                config,
                SyslogLevel.ERROR,
                f"Log creation failed: {result}",
                app_logger
            )

            return jsonify({'error': result}), 500

        # ============ Success ============
        app_logger.info(f"✅ Successfully processed file: {metadata['filename']}")

        return jsonify({
            'status': 'success',
            'message': 'Metadata logged successfully',
            'log_file': Path(result).name
        }), 200

    return log_bp