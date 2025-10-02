"""
Move or copy files to the processed directory
"""

import shutil
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def move_file_to_processed(filepath, config):
    """
    Moves a file to the processed folder

    Args:
        filepath (str|Path): Path to the source file
        config (dict): Application configuration

    Returns:
        tuple: (success: bool, new_path: str)
    """
    try:
        source = Path(filepath)
        processed_dir = Path(config['watcher']['processed_directory'])

        # Create the folder if it doesn't exist
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Target path
        destination = processed_dir / source.name

        # If file already exists, add a timestamp
        if destination.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            destination = processed_dir / f"{source.stem}_{timestamp}{source.suffix}"

        # Move the file
        shutil.move(str(source), str(destination))

        logger.info(f"✅ Moved file to: {destination}")
        return True, str(destination)

    except Exception as e:
        logger.error(f"Failed to move file {filepath}: {e}")
        return False, None


def copy_file_to_processed(filepath, config):
    """
    Copies a file to the processed folder (alternative to moving)

    Args:
        filepath (str|Path): Path to the source file
        config (dict): Application configuration

    Returns:
        tuple: (success: bool, new_path: str)
    """
    try:
        source = Path(filepath)
        processed_dir = Path(config['watcher']['processed_directory'])

        # Create the folder if it doesn't exist
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Target path
        destination = processed_dir / source.name

        # If file already exists, add a timestamp
        if destination.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            destination = processed_dir / f"{source.stem}_{timestamp}{source.suffix}"

        # Copy the file
        shutil.copy2(str(source), str(destination))

        logger.info(f"✅ Copied file to: {destination}")
        return True, str(destination)

    except Exception as e:
        logger.error(f"Failed to copy file {filepath}: {e}")
        return False, None
