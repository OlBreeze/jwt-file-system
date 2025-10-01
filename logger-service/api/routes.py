"""Flask routes using middleware"""
from flask import Flask, request, jsonify, render_template
from datetime import datetime, timezone
from pathlib import Path
import yaml

from api.middleware import require_jwt, validate_json
from services.notification_service import send_email_notification, send_syslog_notification, SyslogLevel
from core.log_manager import create_log_file
from utils.formatters import format_file_size


def create_app(config, logger):
    """Creates and configures a Flask application"""
    base_dir = Path(__file__).parent.parent

    template_dir = base_dir / 'templates'
    static_dir = base_dir / 'static'

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir)
    )

    # ============================================
    # WEB UI ROUTES
    # ============================================

    @app.route('/', methods=['GET'])
    def index():
        """Web UI for configuration"""
        try:
            return render_template('config.html')
        except:
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

    # ============================================
    # API ROUTES
    # ============================================

    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': config['service']['name'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200

    @app.route('/api/config', methods=['GET'])
    def get_config():
        """Get current configuration"""
        return jsonify(config), 200

    @app.route('/api/config/<section>', methods=['PUT'])
    def update_config(section):
        """Update configuration section"""
        try:
            data = request.get_json()

            if section in config:
                # Update config in memory
                if isinstance(config[section], dict) and isinstance(data, dict):
                    config[section].update(data)
                else:
                    config[section] = data

                # Save to file
                config_path = Path(__file__).parent.parent / 'config.yaml'
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False)

                logger.info(f"Configuration section '{section}' updated")
                return jsonify({'status': 'success', 'message': f'{section} updated'}), 200
            else:
                return jsonify({'error': f'Unknown section: {section}'}), 400

        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """Get service statistics"""
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

            # Count today's logs
            today = datetime.now(timezone.utc).date()
            today_logs = sum(
                1 for f in log_files
                if datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).date() == today
            )

            # Calculate storage
            storage_bytes = sum(f.stat().st_size for f in log_files)
            storage_mb = storage_bytes / (1024 * 1024)

            return jsonify({
                'total_logs': total_logs,
                'today_logs': today_logs,
                'storage_mb': round(storage_mb, 2)
            }), 200

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/logs/recent', methods=['GET'])
    def get_recent_logs():
        """Get recent service logs"""
        try:
            log_file = Path(config['logging']['file'])

            if not log_file.exists():
                return jsonify([]), 200

            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-50:]  # Last 50 lines

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

    @app.route('/log', methods=['POST'])
    @require_jwt(config)
    @validate_json('filename', 'created_at', 'file_size')
    def log_metadata():
        """
        The main endpoint for receiving file metadata!!!

        Headers:
            Authorization: Bearer <JWT>

        Body:
            {
                "filename": "report.pdf",
                "created_at": "2025-09-30T14:33:22Z",
                "file_size": 204800,
                "hash": "sha256..."
            }

        Protected with JWT via decorator @require_jwt
        Validates JSON via decorator @validate_json
        """
        metadata = request.get_json()

        # Additional type validation
        if not isinstance(metadata['filename'], str) or not metadata['filename']:
            return jsonify({'error': 'filename must be a non-empty string'}), 400

        if not isinstance(metadata['file_size'], int) or metadata['file_size'] < 0:
            return jsonify({'error': 'file_size must be a non-negative integer'}), 400

        logger.info(
            f"📝 Received metadata for file: {metadata['filename']} "
            f"({format_file_size(metadata['file_size'])}) "
            f"from {request.jwt_payload.get('iss')}"
        )

        # ============ CREATING A LOG FILE ============
        success, result = create_log_file(metadata, config, logger)

        if not success:
            logger.error(f"❌ Failed to create log file: {result}")
            send_email_notification(
                config,
                "Log File Creation Failed",
                f"Error: {result}\nMetadata: {metadata}",
                logger
            )
            send_syslog_notification(config, SyslogLevel.ERROR, f"Log creation failed: {result}", logger)
            return jsonify({'error': result}), 500

        # ============ Success ============
        logger.info(f"✅ Successfully processed file: {metadata['filename']}")

        return jsonify({
            'status': 'success',
            'message': 'Metadata logged successfully',
            'log_file': Path(result).name
        }), 200

    # ============================================
    # ERROR HANDLERS
    # ============================================

    @app.errorhandler(404)
    def not_found(error):
        """Handling 404 errors"""
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handling 500 errors"""
        logger.error(f"Internal server error: {error}")
        send_email_notification(
            config,
            "Internal Server Error",
            f"Error: {str(error)}",
            logger
        )
        return jsonify({'error': 'Internal server error'}), 500

    return app