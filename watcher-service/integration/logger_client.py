"""
Client for interaction with Logger Service
"""

import logging
import requests
from auth.jwt_handler import generate_jwt_token

logger = logging.getLogger(__name__)


def send_metadata_to_logger(metadata, config):
    """
    Sends metadata to the Logger Service

    Args:
        metadata (dict): File metadata
        config (dict): Application configuration

    Returns:
        tuple: (success: bool, response: dict|str)
    """
    try:
        # Generating a JWT token
        token = generate_jwt_token(config)
        if not token:
            return False, "Failed to generate JWT token"

        # Preparing a request
        url = config['logger_service']['url']

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        timeout = config['logger_service'].get('timeout', 10)

        logger.debug(f"Sending metadata to {url}")

        # Sending a POST request
        response = requests.post(
            url,
            json=metadata,
            headers=headers,
            timeout=timeout
        )

        # Checking the status
        if response.status_code == 200:
            logger.info(f"✅ Metadata sent successfully for: {metadata['filename']}")
            return True, response.json()
        else:
            error_msg = f"Logger returned {response.status_code}: {response.text}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

    except requests.exceptions.Timeout:
        error_msg = f"Timeout connecting to Logger Service ({timeout}s)"
        logger.error(f"❌ {error_msg}")
        return False, error_msg

    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to Logger Service"
        logger.error(f"❌ {error_msg}")
        return False, error_msg

    except Exception as e:
        error_msg = f"Failed to send metadata: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg

def get_logger_health_url(config):
    """Получить health URL из logger URL"""
    logger_url = config['logger_service']['url']
    # Заменяем /log на /health
    health_url = logger_url.rsplit('/log', 1)[0] + '/health'
    return health_url

def test_logger_connection(config, logger):
    """
    Checks the availability of the Logger Service.

    Args:
        config (dict): Application configuration
    logger: Logger object
    """
    try:
        logger.info("🔍 Checking Logger Service availability...")

        health_url = get_logger_health_url(config)
        response = requests.get(health_url, timeout=5)

        if response.status_code == 200:
            logger.info("✅ Logger Service is available")
        else:
            logger.warning(f"⚠️ Logger Service returned status {response.status_code}")

    except Exception as e:
        logger.warning(f"⚠️ Cannot connect to Logger Service: {e}")
        logger.warning("   Will retry on file events")