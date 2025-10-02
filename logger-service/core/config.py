"""Configuration management"""
import os
import yaml
from pathlib import Path

from dotenv import load_dotenv


def load_config(config_path=None):
    """Loads configuration from config.yaml and environment variables"""
    #--- for local development
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()
    #---
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'config.yaml'

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # JWT Secret (required)
        jwt_secret = os.getenv('JWT_SECRET')
        if jwt_secret:
            config['jwt']['secret'] = jwt_secret
        elif not config['jwt'].get('secret'):
            print("❌ ERROR: JWT_SECRET not set!")
            exit(1)

        # Other overrides from environment
        if os.getenv('LOGGER_HOST'):
            config['service']['host'] = os.getenv('LOGGER_HOST')

        if os.getenv('LOGGER_PORT'):
            config['service']['port'] = int(os.getenv('LOGGER_PORT'))

        if os.getenv('LOG_LEVEL'):
            config['logging']['level'] = os.getenv('LOG_LEVEL')

        if os.getenv('EMAIL_PASSWORD'):
            config['notifications']['email']['password'] = os.getenv('EMAIL_PASSWORD')

        return config

    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"❌ YAML parsing error: {e}")
        exit(1)
