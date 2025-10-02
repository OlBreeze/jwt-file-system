"""
Extracting file metadata
"""

import logging
from pathlib import Path
from datetime import datetime, timezone
from .hash_calculator import calculate_file_hash

logger = logging.getLogger(__name__)


def extract_metadata(filepath):
    """
    Retrieves file metadata.

    Args:
        filepath (str|Path): File path.

    Returns:
        dict: File metadata, or None on error.
    """
    try:
        file_path = Path(filepath)

        if not file_path.exists():
            logger.error(f"File does not exist: {filepath}")
            return None

        file_stat = file_path.stat()

        metadata = {
            'filename': file_path.name,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'file_size': file_stat.st_size,
            'hash': calculate_file_hash(filepath)
        }

        logger.debug(f"Extracted metadata: {metadata}")
        return metadata

    except Exception as e:
        logger.error(f"Failed to extract metadata from {filepath}: {e}")
        return None


def validate_metadata(metadata):
    """
    Checks the validity of metadata.

    Args:
        metadata (dict): Metadata to check.

    Returns:
        bool: True if the metadata is valid.
    """
    required_fields = ['filename', 'created_at', 'file_size', 'hash']

    if not metadata:
        return False

    for field in required_fields:
        if field not in metadata:
            logger.error(f"Missing required field: {field}")
            return False

        if metadata[field] is None:
            logger.error(f"Field {field} is None")
            return False

    return True