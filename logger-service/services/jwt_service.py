"""JWT authentication"""
import jwt

def validate_jwt_token(token, config):
    """Validates JWT token"""
    try:
        payload = jwt.decode(
            token,
            config['jwt']['secret'],
            algorithms=[config['jwt']['algorithm']]
        )

        if payload.get('iss') != config['jwt']['expected_issuer']:
            return False, f"Invalid issuer"

        return True, payload

    except jwt.ExpiredSignatureError:
        return False, "Token has expired"
    except jwt.InvalidSignatureError:
        return False, "Invalid token signature"
    except jwt.DecodeError:
        return False, "Token decode error"
    except Exception as e:
        return False, f"Token validation error: {str(e)}"


def extract_token_from_header(auth_header):
    """Extracts the token from the Authorization header."""
    if not auth_header:
        return None, "Missing Authorization header"

    parts = auth_header.split()

    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None, "Invalid Authorization header format"

    return parts[1], None