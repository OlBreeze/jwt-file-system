"""
Flask приложение для Logger Service
"""

from pathlib import Path
from flask import Flask
from .routes.config_routes import create_config_bp
from .routes.stats_routes import create_stats_bp
from .routes.logs_routes import create_logs_bp
from .routes.log_endpoint import create_log_bp
from .routes.error_handlers import  register_error_handlers


def create_app(config, logger):
    """
    Создает и настраивает Flask приложение

    Args:
        config (dict): Конфигурация приложения
        logger: Logger объект

    Returns:
        Flask: Настроенное приложение
    """
    base_dir = Path(__file__).parent.parent

    template_dir = base_dir / 'templates'
    static_dir = base_dir / 'static'

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir)
    )

    app.config['JSON_AS_ASCII'] = False

    # Сохраняем конфигурацию в контексте приложения
    app.config['LOGGER_CONFIG'] = config
    app.config['LOGGER_INSTANCE'] = logger

    # Регистрируем blueprints
    app.register_blueprint(create_config_bp(config, logger))
    app.register_blueprint(create_stats_bp(config, logger))
    app.register_blueprint(create_logs_bp(config, logger))
    app.register_blueprint(create_log_bp(config, logger))

    # Регистрируем обработчики ошибок
    register_error_handlers(app, config, logger)

    logger.info("Flask app created successfully")

    return app