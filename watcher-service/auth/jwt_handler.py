"""
JWT Authentication
"""

import jwt
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def generate_jwt_token(config):
    """
    Generates a JWT token for authentication.

        Args:
            config (dict): Application configuration

        Returns:
            str: JWT token or None on error
    """
    try:
        payload = {
            'iss': config['jwt']['issuer'],
            'exp': datetime.now(timezone.utc) + timedelta(
                minutes=config['jwt']['expiration_minutes']
            ),
            'iat': datetime.now(timezone.utc)
        }

        token = jwt.encode(
            payload,
            config['jwt']['secret'],
            algorithm=config['jwt']['algorithm']
        )

        return token

    except Exception as e:
        logger.error(f"Failed to generate JWT token: {e}")
        return None


def verify_jwt_token(token, config):
    """
    Validates a JWT token

        Args:
            token (str): JWT token
            config (dict): Application configuration

        Returns:
            dict: The decoded payload or None on error
    """
    try:
        payload = jwt.decode(
            token,
            config['jwt']['secret'],
            algorithms=[config['jwt']['algorithm']]
        )
        return payload

    except jwt.ExpiredSignatureError:
        logger.error("JWT token has expired")
        return None

    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT token: {e}")
        return None