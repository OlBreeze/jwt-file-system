"""Data formatting utilities"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def format_file_size(size_bytes):
    """Formats the file size into a human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f}MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f}GB"


def format_timestamp_for_filename(iso_timestamp):
    """
    Converts ISO 8601 timestamp to filename format

    Examples:
        2025-09-30T14:33:22Z -> 20250930T143322Z
        2025-09-30T14:33:22+00:00 -> 20250930T143322Z
    """
    # logger.debug("This is DEBUG")
    # logger.info("This is INFO")


    try:
        # Parsing different formats
        if iso_timestamp.endswith('Z'):
            dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        elif '+' in iso_timestamp or iso_timestamp.count('-') > 2:
            dt = datetime.fromisoformat(iso_timestamp)
        else:
            # If the format is unclear, use the current time
            dt = datetime.now(timezone.utc)

        return dt.strftime('%Y%m%dT%H%M%SZ')

    except Exception as e:
        # If parsing fails, use the current time.
        logger.warning(f"Failed to parse timestamp '{iso_timestamp}': {e}. Using current time.")
        return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')