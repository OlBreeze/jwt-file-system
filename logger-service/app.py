"""
Logger Service - JWT File System
"""
from pathlib import Path
from core.config import load_config
from core.logger import setup_logging
from api.routes import create_app

if __name__ == '__main__':
    # Loading the configuration
    config = load_config()

    # Setting up logging
    logger = setup_logging(config)

    # Creating a Flask Application
    app = create_app(config, logger)

    # Create a directory for logs
    Path(config['storage']['logs_directory']).mkdir(parents=True, exist_ok=True)

    # Launch Information
    logger.info("=" * 60)
    logger.info(f"🚀 Starting {config['service']['name']}")
    logger.info(f"📍 Host: {config['service']['host']}")
    logger.info(f"📍 Port: {config['service']['port']}")
    logger.info(f"📁 Logs directory: {config['storage']['logs_directory']}")
    logger.info(f"🔐 JWT issuer: {config['jwt']['expected_issuer']}")
    logger.info(f"🌐 Web UI: http://{config['service']['host']}:{config['service']['port']}/")
    logger.info("=" * 60)

    # Let's start the server
    app.run(
        host=config['service']['host'],
        port=config['service']['port'],
        debug=config['service'].get('debug', False)
    )