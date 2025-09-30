"""
Logger Service - JWT File System
Принимает метаданные файлов через HTTP POST с JWT аутентификацией
"""

import os
import yaml
import jwt
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from pathlib import Path
import re
import smtplib
from email.mime.text import MIMEText
import socket


# ============================================
# 1. ЗАГРУЗКА КОНФИГУРАЦИИ
# ============================================

def load_config():
    """Загружает конфигурацию из config.yaml и переменных окружения"""
    config_path = Path(__file__).parent / 'config.yaml'

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Переопределение из переменных окружения
        if os.getenv('JWT_SECRET'):
            config['jwt']['secret'] = os.getenv('JWT_SECRET')

        if os.getenv('LOGGER_HOST'):
            config['service']['host'] = os.getenv('LOGGER_HOST')

        if os.getenv('LOGGER_PORT'):
            config['service']['port'] = int(os.getenv('LOGGER_PORT'))

        if os.getenv('LOG_LEVEL'):
            config['logging']['level'] = os.getenv('LOG_LEVEL')

        return config

    except FileNotFoundError:
        print(f"❌ Файл конфигурации не найден: {config_path}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Ошибка парсинга YAML: {e}")
        exit(1)


# ============================================
# 2. НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================

def setup_logging(config):
    """Настраивает логирование с ротацией файлов"""

    # Создаем папку для логов если её нет
    log_dir = Path(config['logging']['file']).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Определяем уровень логирования
    log_level = getattr(logging, config['logging']['level'].upper(), logging.INFO)

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler с ротацией
    file_handler = RotatingFileHandler(
        config['logging']['file'],
        maxBytes=config['logging']['max_size_mb'] * 1024 * 1024,
        backupCount=config['logging']['backup_count'],
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Настройка root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Отключаем логи werkzeug (Flask) если не DEBUG
    if log_level > logging.DEBUG:
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

    return root_logger


# ============================================
# 3. JWT ВАЛИДАЦИЯ
# ============================================

def validate_jwt_token(token, config):
    """
    Валидирует JWT токен

    Возвращает: (success: bool, result: dict/str)
    - Если успех: (True, payload)
    - Если ошибка: (False, error_message)
    """
    try:
        # Декодируем и проверяем токен
        payload = jwt.decode(
            token,
            config['jwt']['secret'],
            algorithms=[config['jwt']['algorithm']]
        )

        # Проверяем issuer
        if payload.get('iss') != config['jwt']['expected_issuer']:
            return False, f"Invalid issuer: expected '{config['jwt']['expected_issuer']}', got '{payload.get('iss')}'"

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
    """Извлекает токен из заголовка Authorization"""
    if not auth_header:
        return None, "Missing Authorization header"

    parts = auth_header.split()

    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None, "Invalid Authorization header format. Expected: 'Bearer <token>'"

    return parts[1], None


# ============================================
# 4. СОЗДАНИЕ ЛОГ-ФАЙЛОВ
# ============================================

def sanitize_filename(filename):
    """
    Очищает имя файла от небезопасных символов
    Заменяет их на underscore (_)
    """
    # Убираем расширение
    name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename

    # Заменяем все кроме букв, цифр, дефиса и подчеркивания на _
    sanitized = re.sub(r'[^\w\-]', '_', name_without_ext)

    # Убираем множественные подчеркивания
    sanitized = re.sub(r'_+', '_', sanitized)

    # Убираем подчеркивания в начале и конце
    sanitized = sanitized.strip('_')

    return sanitized if sanitized else 'unnamed'


def format_file_size(size_bytes):
    """Форматирует размер файла в человекочитаемый вид"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f}MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f}GB"


def format_timestamp_for_filename(iso_timestamp):
    """
    Преобразует ISO 8601 timestamp в формат для имени файла
    2025-09-30T14:33:22Z -> 20250930T143322Z
    """
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y%m%dT%H%M%SZ')
    except:
        # Если не удалось распарсить, используем текущее время
        return datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')


def create_log_file(metadata, config, logger):
    """
    Создает лог-файл с метаданными

    Возвращает: (success: bool, result: str)
    - Если успех: (True, filepath)
    - Если ошибка: (False, error_message)
    """
    try:
        # Создаем директорию для логов
        logs_dir = Path(config['storage']['logs_directory'])
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Проверяем лимит файлов
        existing_files = list(logs_dir.glob('*.txt'))
        max_files = config['storage'].get('max_files', 1000)

        if len(existing_files) >= max_files:
            if config['storage'].get('cleanup_enabled', True):
                # Удаляем самый старый файл
                oldest_file = min(existing_files, key=lambda p: p.stat().st_mtime)
                oldest_file.unlink()
                logger.warning(f"Removed oldest log file: {oldest_file.name} (max files limit reached)")
            else:
                return False, f"Maximum number of log files ({max_files}) reached"

        # Формируем имя файла
        sanitized_name = sanitize_filename(metadata['filename'])
        timestamp = format_timestamp_for_filename(metadata['created_at'])
        log_filename = f"{sanitized_name}-{timestamp}.txt"
        log_filepath = logs_dir / log_filename

        # Формируем содержимое
        file_size_formatted = format_file_size(metadata['file_size'])

        content = f"""Filename: {metadata['filename']}
Size: {file_size_formatted}
Created At: {metadata['created_at']}
Hash: {metadata.get('hash', 'N/A')}
Processed At: {datetime.utcnow().isoformat()}Z
"""

        # Записываем файл
        with open(log_filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ Created log file: {log_filename}")

        return True, str(log_filepath)

    except Exception as e:
        error_msg = f"Failed to create log file: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


# ============================================
# 5. УВЕДОМЛЕНИЯ
# ============================================

def send_email_notification(config, subject, message, logger):
    """Отправляет email уведомление"""
    if not config['notifications']['email']['enabled']:
        return

    try:
        email_config = config['notifications']['email']

        msg = MIMEText(message)
        msg['Subject'] = f"[Logger Service] {subject}"
        msg['From'] = email_config['from']
        msg['To'] = email_config['to']

        with smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port']) as server:
            if email_config.get('use_tls', True):
                server.starttls()

            password = email_config.get('password') or os.getenv('EMAIL_PASSWORD')
            if password:
                server.login(email_config['from'], password)

            server.send_message(msg)

        logger.debug(f"Email notification sent: {subject}")

    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")


def send_syslog_notification(config, level, message, logger):
    """Отправляет syslog уведомление"""
    if not config['notifications']['syslog']['enabled']:
        return

    try:
        syslog_config = config['notifications']['syslog']

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Формат syslog: <priority>timestamp hostname tag: message
        priority = 8 * 16 + level  # facility * 8 + severity
        syslog_msg = f"<{priority}>logger-service: {message}"

        sock.sendto(
            syslog_msg.encode('utf-8'),
            (syslog_config['host'], syslog_config['port'])
        )

        sock.close()
        logger.debug(f"Syslog notification sent: {message[:50]}...")

    except Exception as e:
        logger.error(f"Failed to send syslog notification: {e}")


# ============================================
# 6. FLASK APPLICATION
# ============================================

# Загружаем конфигурацию
config = load_config()

# Настраиваем логирование
logger = setup_logging(config)

# Создаем Flask приложение
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Поддержка Unicode в JSON


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': config['service']['name'],
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@app.route('/log', methods=['POST'])
def log_metadata():
    """
    Основной endpoint для приема метаданных файлов

    Headers:
        Authorization: Bearer <JWT>

    Body:
        {
            "filename": "report.pdf",
            "created_at": "2025-09-30T14:33:22Z",
            "file_size": 204800,
            "hash": "sha256..."
        }
    """

    # ============ JWT ВАЛИДАЦИЯ ============
    auth_header = request.headers.get('Authorization')

    token, error = extract_token_from_header(auth_header)
    if error:
        logger.warning(f"❌ Authorization failed: {error}")
        return jsonify({'error': error}), 401

    is_valid, result = validate_jwt_token(token, config)
    if not is_valid:
        logger.warning(f"❌ JWT validation failed: {result}")
        send_email_notification(config, "JWT Validation Failed", f"Error: {result}\nFrom IP: {request.remote_addr}",
                                logger)
        return jsonify({'error': result}), 401

    logger.debug(f"✅ JWT validated for issuer: {result.get('iss')}")

    # ============ ВАЛИДАЦИЯ PAYLOAD ============
    if not request.is_json:
        logger.warning("❌ Invalid content type: expected application/json")
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    metadata = request.get_json()

    # Проверяем обязательные поля
    required_fields = ['filename', 'created_at', 'file_size']
    missing_fields = [field for field in required_fields if field not in metadata]

    if missing_fields:
        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
        logger.warning(f"❌ {error_msg}")
        return jsonify({'error': error_msg}), 400

    # Валидация типов
    if not isinstance(metadata['filename'], str) or not metadata['filename']:
        return jsonify({'error': 'filename must be a non-empty string'}), 400

    if not isinstance(metadata['file_size'], int) or metadata['file_size'] < 0:
        return jsonify({'error': 'file_size must be a non-negative integer'}), 400

    logger.info(f"📝 Received metadata for file: {metadata['filename']} ({format_file_size(metadata['file_size'])})")

    # ============ СОЗДАНИЕ ЛОГ-ФАЙЛА ============
    success, result = create_log_file(metadata, config, logger)

    if not success:
        logger.error(f"❌ Failed to create log file: {result}")
        send_email_notification(
            config,
            "Log File Creation Failed",
            f"Error: {result}\nMetadata: {metadata}",
            logger
        )
        send_syslog_notification(config, 3, f"Log creation failed: {result}", logger)  # 3 = ERROR
        return jsonify({'error': result}), 500

    # ============ УСПЕХ ============
    logger.info(f"✅ Successfully processed file: {metadata['filename']}")

    return jsonify({
        'status': 'success',
        'message': 'Metadata logged successfully',
        'log_file': Path(result).name
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Обработка 404 ошибок"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Обработка 500 ошибок"""
    logger.error(f"Internal server error: {error}")
    send_email_notification(
        config,
        "Internal Server Error",
        f"Error: {str(error)}",
        logger
    )
    return jsonify({'error': 'Internal server error'}), 500


# ============================================
# 7. MAIN
# ============================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info(f"🚀 Starting {config['service']['name']}")
    logger.info(f"📍 Host: {config['service']['host']}")
    logger.info(f"📍 Port: {config['service']['port']}")
    logger.info(f"📁 Logs directory: {config['storage']['logs_directory']}")
    logger.info(f"🔐 JWT issuer expected: {config['jwt']['expected_issuer']}")
    logger.info(f"📧 Email notifications: {'enabled' if config['notifications']['email']['enabled'] else 'disabled'}")
    logger.info(f"📡 Syslog notifications: {'enabled' if config['notifications']['syslog']['enabled'] else 'disabled'}")
    logger.info("=" * 60)

    # Создаем директорию для логов метаданных
    Path(config['storage']['logs_directory']).mkdir(parents=True, exist_ok=True)

    # Запускаем Flask сервер
    app.run(
        host=config['service']['host'],
        port=config['service']['port'],
        debug=config['service'].get('debug', False)
    )