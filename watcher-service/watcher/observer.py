"""
Observer setup for monitoring the file system
"""

import logging
from pathlib import Path
from watchdog.observers.polling import PollingObserver
from .file_watcher import FileWatcherHandler

logger = logging.getLogger(__name__)


def setup_observer(config, app_logger):
    """
    Creates and configures a PollingObserver to monitor a directory

    Args:
        config (dict): Application configuration
        app_logger: Application logger object

    Returns:
        PollingObserver: Configured observer
    """
    watch_dir = Path(config['watcher']['watch_directory'])

    # Create the event handler
    event_handler = FileWatcherHandler(config)

    # Create the observer (PollingObserver is used for Windows/Docker compatibility)
    observer = PollingObserver()

    # Set up directory monitoring
    observer.schedule(event_handler, str(watch_dir), recursive=False)

    logger.info(f"Observer configured for: {watch_dir}")

    return observer


def start_observer(observer):
    """
    Starts the observer

    Args:
        observer: Observer object
    """
    observer.start()
    logger.info("Observer started")


def stop_observer(observer):
    """
    Stops the observer

    Args:
        observer: Observer object
    """
    observer.stop()
    observer.join()
    logger.info("Observer stopped")
