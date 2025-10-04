"""
JWT Authentication
"""

import jwt
import logging
import time
from datetime import datetime, timedelta, timezone

_cached_token = None
_token_expiry = 0

logger = logging.getLogger(__name__)


def get_jwt_token(config):
    """
    Returns cached JWT token if valid, otherwise generates a new one.
    """
    global _cached_token, _token_expiry

    # Checking if the token has expired
    if _cached_token and time.time() < _token_expiry:
        return _cached_token

    # Generating a new token
    token = generate_jwt_token(config)
    if not token:
        return None

    # Extracting the expiration time from the token
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        _token_expiry = decoded.get("exp", 0)
    except Exception as e:
        logger.warning(f"Cannot decode token expiration: {e}")
        # fallback — If exp is not found, set it manually
        _token_expiry = time.time() + 300  # 5 min

    _cached_token = token
    logger.debug(f"Generated new JWT token (expires at {_token_expiry})")
    return token


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
