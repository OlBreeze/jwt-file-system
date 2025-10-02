"""
Helper functions for the API
"""


def format_file_size(size_bytes):
    """
    Formats file size for display

    Args:
        size_bytes (int): Size in bytes

    Returns:
        str: Formatted size
    """
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f}MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f}GB"


def parse_log_line(line):
    """
    Parses a log line

    Args:
        line (str): A line from the log file

    Returns:
        dict: Parsed log entry or None
    """
    parts = line.split(' - ')

    if len(parts) < 3:
        return None

    return {
        'timestamp': parts[0],
        'logger': parts[1],
        'level': parts[2].strip(),
        'message': ' - '.join(parts[3:]).strip()
    }


def validate_config_section(section, data):
    """
    Validates data for configuration update

    Args:
        section (str): Section name
        data (dict): Data to be updated

    Returns:
        tuple: (is_valid: bool, error_message: str)
    """

    # Section-specific validation
    if section == 'jwt':
        if 'expiration_minutes' in data:
            if not isinstance(data['expiration_minutes'], int) or data['expiration_minutes'] <= 0:
                return False, "expiration_minutes must be a positive integer"

    elif section == 'logger_service':
        if 'timeout' in data:
            if not isinstance(data['timeout'], int) or data['timeout'] <= 0:
                return False, "timeout must be a positive integer"

    elif section == 'logging':
        if 'level' in data:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if data['level'].upper() not in valid_levels:
                return False, f"level must be one of: {', '.join(valid_levels)}"

    return True, None


def sanitize_config_for_display(config):
    """
    Removes sensitive data from configuration for display

    Args:
        config (dict): Configuration

    Returns:
        dict: Safe copy of the configuration
    """
    import copy
    safe_config = copy.deepcopy(config)

    # Hide JWT secret
    if 'jwt' in safe_config and 'secret' in safe_config['jwt']:
        safe_config['jwt']['secret'] = '***hidden***'

    # Hide email password
    if 'notifications' in safe_config:
        if 'email' in safe_config['notifications']:
            if 'password' in safe_config['notifications']['email']:
                safe_config['notifications']['email']['password'] = '***hidden***'

    return safe_config
