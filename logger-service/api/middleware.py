"""Middleware and decorators for APIs

This code contains two decorators for the Flask API:

1. @require_jwt - protect endpoints with JWT

What it does:
- Checks for the presence of a JWT token in the Authorization header
- Validates the token
- Adds the token payload to the request object for use in the route

2. @validate_json - validates the JSON payload

What it does:
- Checks that the request contains JSON
- Checks for required fields in the JSON
"""

from functools import wraps
from flask import request, jsonify
import logging

from  services.jwt_service import extract_token_from_header, validate_jwt_token

logger = logging.getLogger(__name__)


def require_jwt(config):
    """
    Decorator for protecting endpoints with JWT

    Usage:
        @app.route('/protected')
        @require_jwt(config)
        def protected_route():
            return jsonify({'message': 'Authorized!'})
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')

            token, error = extract_token_from_header(auth_header)
            if error:
                logger.warning(f"❌ Authorization failed: {error}")
                return jsonify({'error': error}), 401

            is_valid, result = validate_jwt_token(token, config)
            if not is_valid:
                logger.warning(f"❌ JWT validation failed: {result}")
                return jsonify({'error': result}), 401

            #Add a token payload to the request for use in the route
            request.jwt_payload = result

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_json(*required_fields):
    """
    Decorator for JSON payload validation

    Usage:
        @app.route('/log', methods=['POST'])
        @validate_json('filename', 'created_at', 'file_size')
        def log_metadata():
            data = request.get_json()
            # data is guaranteed to contain all required_fields
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400

            data = request.get_json()
            missing = [field for field in required_fields if field not in data]

            if missing:
                error_msg = f"Missing required fields: {', '.join(missing)}"
                logger.warning(f"❌ {error_msg}")
                return jsonify({'error': error_msg}), 400

            return f(*args, **kwargs)

        return decorated_function

    return decorator