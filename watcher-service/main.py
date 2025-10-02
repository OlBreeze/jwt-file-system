"""
Watcher Service - JWT File System
"""

import time
from pathlib import Path
from threading import Thread

from core.config import load_config
from core.logger import setup_logging
from core.stats import stats
from watcher.observer import setup_observer
from api.app import create_app
from integration.logger_client import test_logger_connection


def main():
    """Main function"""

    # Loading the configuration
    config = load_config()

    # Setting up logging
    logger = setup_logging(config)

    logger.info("=" * 60)
    logger.info(f"🚀 Starting {config['service']['name']}")
    logger.info(f"📁 Watching directory: {config['watcher']['watch_directory']}")
    logger.info(f"📦 Processed directory: {config['watcher']['processed_directory']}")
    logger.info(f"🌐 Logger Service URL: {config['logger_service']['url']}")
    logger.info(f"🔐 JWT issuer: {config['jwt']['issuer']}")
    logger.info(f"⏱️  JWT expiration: {config['jwt']['expiration_minutes']} minutes")
    logger.info(f"📧 Email notifications: {'enabled' if config['notifications']['email']['enabled'] else 'disabled'}")
    logger.info(f"📡 Syslog notifications: {'enabled' if config['notifications']['syslog']['enabled'] else 'disabled'}")
    logger.info(f"🌐 Web UI: http://0.0.0.0:8080/")
    logger.info("=" * 60)

    # Create the necessary directories
    watch_dir = Path(config['watcher']['watch_directory'])
    processed_dir = Path(config['watcher']['processed_directory'])

    watch_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"✅ Directories ready")

    # Checking availability Logger Service
    test_logger_connection(config, logger)

    # Create and launch observer
    observer = setup_observer(config, logger)
    observer.start()
    logger.info("👀 Watching for new files... (Press Ctrl+C to stop)")

    # Run the Flask API in a separate thread
    web_app = create_app(config, logger, stats)

    def run_web_app():
        web_app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

    web_thread = Thread(target=run_web_app, daemon=True) # separate thread!!!
    web_thread.start()
    logger.info("🌐 Web UI started on http://0.0.0.0:8080")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("🛑 Stopping watcher service...")
        observer.stop()

    observer.join()
    logger.info("👋 Watcher service stopped")


if __name__ == '__main__':
    main()