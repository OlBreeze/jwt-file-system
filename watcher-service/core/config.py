"""Configuration management"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Loads environment variables
load_dotenv()


def load_config():
    """
    Loads configuration from config.yaml and environment variables.

    Returns:
        dict: Application configuration
    """
    config_path = Path(__file__).parent.parent / 'config.yaml'

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Overriding from environment variables (REQUIRED)
        jwt_secret = os.getenv('JWT_SECRET')
        if jwt_secret:
            config['jwt']['secret'] = jwt_secret
        elif not config['jwt'].get('secret'):
            print("❌ ERROR: JWT_SECRET not set! Set it via environment variable.")
            print("   Example: export JWT_SECRET=your-secret-key")
            exit(1)

        # Defining the environment
        is_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER_ENV') == 'true'

        # LOGGER_URL: environment variable priority, otherwise autodetect
        if os.getenv('LOGGER_URL'):
            config['logger_service']['url'] = os.getenv('LOGGER_URL')
        # else:
            # Auto-detection by environment
        url_key = 'url_docker' if is_docker else 'url_local'
        config['logger_service']['url'] = config['logger_service'].get(
                url_key,
                config['logger_service'].get('url')
            )

        # # Debug output
        # print(f"Using LOGGER_URL: {config['logger_service']['url']}")
        # print(f"Docker mode: {is_docker}")

        # Overriding other parameters from env
        if os.getenv('LOG_LEVEL'):
            config['logging']['level'] = os.getenv('LOG_LEVEL')

        if os.getenv('WATCH_DIR'):
            config['watcher']['watch_directory'] = os.getenv('WATCH_DIR')

        if os.getenv('PROCESSED_DIR'):
            config['watcher']['processed_directory'] = os.getenv('PROCESSED_DIR')

        # Email password from env
        if os.getenv('EMAIL_PASSWORD'):
            config['notifications']['email']['password'] = os.getenv('EMAIL_PASSWORD')

        return config

    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Parsing error YAML: {e}")
        exit(1)


def save_config(config):
    """
    Saves the configuration to a file.

    Args:
        config (dict): Configuration to save
    """
    config_path = Path(__file__).parent.parent / 'config.yaml'

    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)