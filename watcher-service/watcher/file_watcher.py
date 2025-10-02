"""
File system event handler
"""

import time
import logging
from pathlib import Path
from watchdog.events import FileSystemEventHandler

from file_processing.metadata import extract_metadata, validate_metadata
from file_processing.file_mover import move_file_to_processed
from integration.logger_client import send_metadata_to_logger
from notifications.email_sender import send_error_notification
from notifications.syslog_sender import send_syslog_error
from core.stats import stats

logger = logging.getLogger(__name__)


class FileWatcherHandler(FileSystemEventHandler):
    """File system event handler"""

    def __init__(self, config):
        """
        Handler initialization

        Args:
            config (dict): Application configuration
        """
        self.config = config
        self.processing_files = set()  # To prevent duplication

    def on_created(self, event):
        """
        Called when a new file is created.

        Args:
            event: File system event
        """
        # Ignore directories
        if event.is_directory:
            return

        filepath = event.src_path
        filename = Path(filepath).name

        # Ignoring service files
        ignored_patterns = self.config['watcher'].get('ignored_files', [])
        if any(pattern in filename for pattern in ignored_patterns):
            logger.debug(f"Ignoring configured file: {filename}")
            return

        # We check that the file is not being processed.
        if filepath in self.processing_files:
            return

        logger.info(f"📁 New file detected: {filepath}")

        # Adding to processing
        self.processing_files.add(filepath)

        # There is a slight delay for the file to finish writing.
        time.sleep(0.5)

        # Проверяем что файл еще существует
        if not Path(filepath).exists():
            logger.warning(f"File disappeared: {filepath}")
            self.processing_files.discard(filepath)
            return

        # Processing a file
        self.process_file(filepath)

        # Removing from processing
        self.processing_files.discard(filepath)

    def process_file(self, filepath):
        """
        Processes a single file

        Args:
            filepath (str): File path
        """
        try:
            # 1. Extracting metadata
            logger.debug(f"Extracting metadata from: {filepath}")
            metadata = extract_metadata(filepath)

            if not metadata or not validate_metadata(metadata):
                logger.error(f"Failed to extract valid metadata from: {filepath}")
                stats.increment_failed()
                send_error_notification(
                    self.config,
                    "Metadata Extraction Failed",
                    filepath,
                    "Could not extract valid metadata"
                )
                return

            # 2. We send to Logger Service
            logger.debug(f"Sending metadata to Logger Service")
            success, response = send_metadata_to_logger(metadata, self.config)

            if not success:
                logger.error(f"Failed to send metadata: {response}")
                stats.increment_failed()
                send_error_notification(
                    self.config,
                    "Failed to Send Metadata",
                    filepath,
                    str(response)
                )
                send_syslog_error(self.config, f"Metadata send failed: {filepath}")
                # DO NOT move the file to try again later.
                return

            # 3. Move the file to processed
            logger.debug(f"Moving file to processed directory")
            moved, new_path = move_file_to_processed(filepath, self.config)

            if not moved:
                logger.error(f"Failed to move file: {filepath}")
                stats.increment_failed()
                send_error_notification(
                    self.config,
                    "Failed to Move File",
                    filepath,
                    "Metadata was sent successfully but file wasn't moved"
                )
                return

            # ✅ Success!
            stats.increment_processed()
            logger.info(f"✅ Successfully processed: {metadata['filename']}")
            logger.info(f"   Size: {metadata['file_size']} bytes")
            logger.info(f"   Hash: {metadata['hash'][:16]}...")
            logger.info(f"   Moved to: {new_path}")

        except Exception as e:
            stats.increment_failed()
            logger.error(f"Error processing file {filepath}: {e}")
            send_error_notification(
                self.config,
                "File Processing Error",
                filepath,
                str(e)
            )