"""
API endpoints for working with files
"""

import logging
from pathlib import Path
from datetime import datetime, timezone
from flask import Blueprint, jsonify, current_app
from api.utils import format_file_size

logger = logging.getLogger(__name__)

files_bp = Blueprint('files', __name__)


@files_bp.route('/files/pending', methods=['GET'])
def get_pending_files():
    """
    Get a list of files in the queue

    Returns:
        JSON: List of files pending processing
    """
    try:
        config = current_app.config['WATCHER_CONFIG']
        watched_dir = Path(config['watcher']['watch_directory'])

        if not watched_dir.exists():
            return jsonify([]), 200

        files = []
        for file_path in watched_dir.glob('*'):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    'name': file_path.name,
                    'size': format_file_size(stat.st_size),
                    'size_bytes': stat.st_size,
                    'created': datetime.fromtimestamp(
                        stat.st_mtime,
                        tz=timezone.utc
                    ).strftime('%Y-%m-%d %H:%M:%S')
                })

        # Sort by creation date
        files.sort(key=lambda x: x['created'], reverse=True)

        return jsonify(files), 200

    except Exception as e:
        logger.error(f"Failed to get pending files: {e}")
        return jsonify({'error': str(e)}), 500


@files_bp.route('/files/processed', methods=['GET'])
def get_processed_files():
    """
    Get a list of processed files

    Returns:
        JSON: list of processed files
    """
    try:
        config = current_app.config['WATCHER_CONFIG']
        processed_dir = Path(config['watcher']['processed_directory'])

        if not processed_dir.exists():
            return jsonify([]), 200

        files = []
        for file_path in processed_dir.glob('*'):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    'name': file_path.name,
                    'size': format_file_size(stat.st_size),
                    'size_bytes': stat.st_size,
                    'processed': datetime.fromtimestamp(
                        stat.st_mtime,
                        tz=timezone.utc
                    ).strftime('%Y-%m-%d %H:%M:%S')
                })

        # Sort by processing date
        files.sort(key=lambda x: x['processed'], reverse=True)

        return jsonify(files), 200

    except Exception as e:
        logger.error(f"Failed to get processed files: {e}")
        return jsonify({'error': str(e)}), 500


@files_bp.route('/files/count', methods=['GET'])
def get_files_count():
    """
    Get the number of files

    Returns:
        JSON: Number of files in different directories
    """
    try:
        config = current_app.config['WATCHER_CONFIG']
        watched_dir = Path(config['watcher']['watch_directory'])
        processed_dir = Path(config['watcher']['processed_directory'])

        pending_count = len(list(watched_dir.glob('*'))) if watched_dir.exists() else 0
        processed_count = len(list(processed_dir.glob('*'))) if processed_dir.exists() else 0

        return jsonify({
            'pending': pending_count,
            'processed': processed_count,
            'total': pending_count + processed_count
        }), 200

    except Exception as e:
        logger.error(f"Failed to get files count: {e}")
        return jsonify({'error': str(e)}), 500
