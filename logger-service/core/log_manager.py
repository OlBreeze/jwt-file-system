"""Log File Management"""
import re
from pathlib import Path
from datetime import datetime, timezone
from utils.formatters import format_file_size, format_timestamp_for_filename

def sanitize_filename(filename):
    """Sanitizes the file name of unsafe characters."""
    name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
    sanitized = re.sub(r'[^\w\-]', '_', name_without_ext)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    return sanitized if sanitized else 'unnamed'


def create_log_file(metadata, config, logger):
    """Creates a log file with metadata"""
    try:
        logs_dir = Path(config['storage']['logs_directory'])
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Checking file limits
        existing_files = list(logs_dir.glob('*.txt'))
        max_files = config['storage'].get('max_files', 1000)

        if len(existing_files) >= max_files:
            if config['storage'].get('cleanup_enabled', True):
                oldest = min(existing_files, key=lambda p: p.stat().st_mtime)
                oldest.unlink()
                logger.warning(f"Removed: {oldest.name}")
            else:
                return False, f"Max files ({max_files}) reached"

        # Formation of a name
        sanitized = sanitize_filename(metadata['filename'])
        timestamp = format_timestamp_for_filename(metadata['created_at'])
        log_filename = f"{sanitized}-{timestamp}.txt"
        log_filepath = logs_dir / log_filename

        # Content
        content = f"""Filename: {metadata['filename']}
Size: {format_file_size(metadata['file_size'])}
Created At: {metadata['created_at']}
Hash: {metadata.get('hash', 'N/A')}
Processed At: {datetime.now(timezone.utc).isoformat()}
"""

        with open(log_filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ Created: {log_filename}")
        return True, str(log_filepath)

    except Exception as e:
        return False, f"Failed: {str(e)}"