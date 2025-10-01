"""
Watcher Service - JWT File System
Мониторит папку на новые файлы и отправляет метаданные в Logger Service
Включает Web UI для управления конфигурацией
"""

import os
import yaml
import jwt
import time
import shutil
import hashlib
import logging
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from logging.handlers import RotatingFileHandler
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from flask import Flask, request, jsonify, render_template
from threading import Thread
import smtplib
from email.mime.text import MIMEText
import socket

# Глобальные переменные
config = None
logger = None

# Статистика
stats = {
    'total_processed': 0,
    'today_processed': 0,
    'failed': 0
}


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

        if os.getenv('LOGGER_URL'):
            config['logger_service']['url'] = os.getenv('LOGGER_URL')

        if os.getenv('LOG_LEVEL'):
            config['logging']['level'] = os.getenv('LOG_LEVEL')

        if os.getenv('WATCH_DIR'):
            config['watcher']['watch_directory'] = os.getenv('WATCH_DIR')

        if os.getenv('PROCESSED_DIR'):
            config['watcher']['processed_directory'] = os.getenv('PROCESSED_DIR')

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

    return root_logger


# ============================================
# 3. JWT ГЕНЕРАЦИЯ
# ============================================

def generate_jwt_token(config):
    """
    Генерирует JWT токен для аутентификации

    Возвращает: token (str)
    """
    try:
        payload = {
            'iss': config['jwt']['issuer'],
            'exp': datetime.now(timezone.utc) + timedelta(minutes=config['jwt']['expiration_minutes']),
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


# ============================================
# 4. РАБОТА С ФАЙЛАМИ
# ============================================

def calculate_file_hash(filepath):
    """
    Вычисляет SHA-256 хеш файла

    Возвращает: hash (str)
    """
    try:
        sha256_hash = hashlib.sha256()

        with open(filepath, "rb") as f:
            # Читаем файл блоками для экономии памяти
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    except Exception as e:
        logger.error(f"Failed to calculate hash for {filepath}: {e}")
        return None


def extract_metadata(filepath):
    """
    Извлекает метаданные файла

    Возвращает: dict с метаданными
    """
    try:
        file_path = Path(filepath)
        file_stat = file_path.stat()

        metadata = {
            'filename': file_path.name,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'file_size': file_stat.st_size,
            'hash': calculate_file_hash(filepath)
        }

        logger.debug(f"Extracted metadata: {metadata}")
        return metadata

    except Exception as e:
        logger.error(f"Failed to extract metadata from {filepath}: {e}")
        return None


def move_file_to_processed(filepath, config, logger):
    """
    Перемещает файл в папку processed

    Возвращает: (success: bool, new_path: str)
    """
    try:
        source = Path(filepath)
        processed_dir = Path(config['watcher']['processed_directory'])

        # Создаем папку если её нет
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Целевой путь
        destination = processed_dir / source.name

        # Если файл уже существует, добавляем timestamp
        if destination.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name_parts = source.stem, timestamp, source.suffix
            destination = processed_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"

        # Перемещаем файл
        shutil.move(str(source), str(destination))

        logger.info(f"✅ Moved file to: {destination}")
        return True, str(destination)

    except Exception as e:
        logger.error(f"Failed to move file {filepath}: {e}")
        return False, None


# ============================================
# 5. ОТПРАВКА В LOGGER SERVICE
# ============================================

def send_metadata_to_logger(metadata, config, logger):
    """
    Отправляет метаданные в Logger Service

    Возвращает: (success: bool, response: dict/str)
    """
    try:
        # Генерируем JWT токен
        token = generate_jwt_token(config)
        if not token:
            return False, "Failed to generate JWT token"

        # Подготавливаем запрос
        url = config['logger_service']['url']
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        timeout = config['logger_service'].get('timeout', 10)

        logger.debug(f"Sending metadata to {url}")

        # Отправляем POST запрос
        response = requests.post(
            url,
            json=metadata,
            headers=headers,
            timeout=timeout
        )

        # Проверяем статус
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


# ============================================
# 6. УВЕДОМЛЕНИЯ
# ============================================

def send_email_notification(config, subject, message, logger):
    """Отправляет email уведомление"""
    if not config['notifications']['email']['enabled']:
        return

    try:
        email_config = config['notifications']['email']

        msg = MIMEText(message)
        msg['Subject'] = f"[Watcher Service] {subject}"
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
        syslog_msg = f"<{priority}>watcher-service: {message}"

        sock.sendto(
            syslog_msg.encode('utf-8'),
            (syslog_config['host'], syslog_config['port'])
        )

        sock.close()
        logger.debug(f"Syslog notification sent")

    except Exception as e:
        logger.error(f"Failed to send syslog notification: {e}")


# ============================================
# 7. FILE WATCHER (WATCHDOG)
# ============================================

class FileWatcherHandler(FileSystemEventHandler):
    """Обработчик событий файловой системы"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.processing_files = set()  # Для предотвращения дублирования

    def on_created(self, event):
        """Вызывается при создании нового файла"""

        # Игнорируем директории
        if event.is_directory:
            return

        filepath = event.src_path

        # Проверяем что файл не обрабатывается
        if filepath in self.processing_files:
            return

        self.logger.info(f"📁 New file detected: {filepath}")

        # Добавляем в обработку
        self.processing_files.add(filepath)

        # Небольшая задержка для завершения записи файла
        time.sleep(0.5)

        # Проверяем что файл еще существует
        if not Path(filepath).exists():
            self.logger.warning(f"File disappeared: {filepath}")
            self.processing_files.discard(filepath)
            return

        # Обрабатываем файл
        self.process_file(filepath)

        # Убираем из обработки
        self.processing_files.discard(filepath)

    def process_file(self, filepath):
        """Обрабатывает один файл"""

        try:
            # 1. Извлекаем метаданные
            self.logger.debug(f"Extracting metadata from: {filepath}")
            metadata = extract_metadata(filepath)

            if not metadata:
                self.logger.error(f"Failed to extract metadata from: {filepath}")
                stats['failed'] += 1
                send_email_notification(
                    self.config,
                    "Metadata Extraction Failed",
                    f"File: {filepath}",
                    self.logger
                )
                return

            # 2. Отправляем в Logger Service
            self.logger.debug(f"Sending metadata to Logger Service")
            success, response = send_metadata_to_logger(metadata, self.config, self.logger)

            if not success:
                self.logger.error(f"Failed to send metadata: {response}")
                stats['failed'] += 1
                send_email_notification(
                    self.config,
                    "Failed to Send Metadata",
                    f"File: {filepath}\nError: {response}",
                    self.logger
                )
                send_syslog_notification(self.config, 3, f"Metadata send failed: {filepath}", self.logger)
                # НЕ перемещаем файл, чтобы повторить позже
                return

            # 3. Перемещаем файл в processed
            self.logger.debug(f"Moving file to processed directory")
            moved, new_path = move_file_to_processed(filepath, self.config, self.logger)

            if not moved:
                self.logger.error(f"Failed to move file: {filepath}")
                stats['failed'] += 1
                send_email_notification(
                    self.config,
                    "Failed to Move File",
                    f"File: {filepath}\nMetadata was sent successfully but file wasn't moved.",
                    self.logger
                )
                return

            # ✅ Успех!
            stats['total_processed'] += 1
            stats['today_processed'] += 1
            self.logger.info(f"✅ Successfully processed: {metadata['filename']}")
            self.logger.info(f"   Size: {metadata['file_size']} bytes")
            self.logger.info(f"   Hash: {metadata['hash'][:16]}...")
            self.logger.info(f"   Moved to: {new_path}")

        except Exception as e:
            stats['failed'] += 1
            self.logger.error(f"Error processing file {filepath}: {e}")
            send_email_notification(
                self.config,
                "File Processing Error",
                f"File: {filepath}\nError: {str(e)}",
                self.logger
            )


# ============================================
# 8. FLASK API FOR WEB UI
# ============================================

# Создаем Flask приложение для Web UI
web_app = Flask(__name__)
web_app.config['JSON_AS_ASCII'] = False


@web_app.route('/')
def index():
    """Web UI homepage"""
    try:
        return render_template('config.html')
    except:
        return jsonify({
            'service': 'watcher-service',
            'message': 'Web UI not available. Create templates/config.html to enable.',
            'endpoints': {
                'config': '/api/config (GET)',
                'update_config': '/api/config/<section> (PUT)',
                'stats': '/api/stats (GET)',
                'pending_files': '/api/files/pending (GET)',
                'recent_logs': '/api/logs/recent (GET)',
                'test_connection': '/api/test-connection (GET)'
            }
        }), 200


@web_app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify(config), 200


@web_app.route('/api/config/<section>', methods=['PUT'])
def update_config_endpoint(section):
    """Update configuration section"""
    try:
        data = request.get_json()

        if section in config:
            if isinstance(config[section], dict) and isinstance(data, dict):
                config[section].update(data)
            else:
                config[section] = data

            # Save to file
            config_path = Path(__file__).parent / 'config.yaml'
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False)

            logger.info(f"Configuration section '{section}' updated")
            return jsonify({'status': 'success', 'message': f'{section} updated'}), 200
        else:
            return jsonify({'error': f'Unknown section: {section}'}), 400

    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        return jsonify({'error': str(e)}), 500


@web_app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get service statistics"""
    try:
        watched_dir = Path(config['watcher']['watch_directory'])
        processed_dir = Path(config['watcher']['processed_directory'])

        pending_files = len(list(watched_dir.glob('*'))) if watched_dir.exists() else 0

        # Calculate success rate
        total = stats['total_processed'] + stats['failed']
        success_rate = round((stats['total_processed'] / total * 100) if total > 0 else 100, 1)

        return jsonify({
            'total_processed': stats['total_processed'],
            'today_processed': stats['today_processed'],
            'pending_files': pending_files,
            'success_rate': success_rate
        }), 200

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return jsonify({'error': str(e)}), 500


@web_app.route('/api/files/pending', methods=['GET'])
def get_pending_files():
    """Get list of pending files in watched directory"""
    try:
        watched_dir = Path(config['watcher']['watch_directory'])

        if not watched_dir.exists():
            return jsonify([]), 200

        files = []
        for file_path in watched_dir.glob('*'):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    'name': file_path.name,
                    'size': format_file_size(stat.st_size),
                    'created': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                })

        return jsonify(files), 200

    except Exception as e:
        logger.error(f"Failed to get pending files: {e}")
        return jsonify({'error': str(e)}), 500


@web_app.route('/api/logs/recent', methods=['GET'])
def get_recent_logs():
    """Get recent service logs"""
    try:
        log_file = Path(config['logging']['file'])

        if not log_file.exists():
            return jsonify([]), 200

        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-50:]

        logs = []
        for line in lines:
            parts = line.split(' - ')
            if len(parts) >= 3:
                logs.append({
                    'timestamp': parts[0],
                    'level': parts[2].strip(),
                    'message': ' - '.join(parts[3:]).strip()
                })

        return jsonify(logs), 200

    except Exception as e:
        logger.error(f"Failed to get recent logs: {e}")
        return jsonify({'error': str(e)}), 500


@web_app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Test connection to Logger Service"""
    try:
        logger_url = config['logger_service']['url'].replace('/log', '/health')
        response = requests.get(logger_url, timeout=5)

        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Logger Service is reachable',
                'response': response.json()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Logger returned status {response.status_code}'
            }), 200

    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Connection timeout'
        }), 200

    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'Cannot connect to Logger Service'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 200


def format_file_size(size_bytes):
    """Format file size for display"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f}MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f}GB"


# ============================================
# 9. MAIN
# ============================================

def main():
    """Главная функция"""

    global config, logger

    # Загружаем конфигурацию
    config = load_config()

    # Настраиваем логирование
    logger = setup_logging(config)

    logger.info("=" * 60)
    logger.info(f"🚀 Starting {config['service']['name']}")
    logger.info(f"📁 Watching directory: {config['watcher']['watch_directory']}")
    logger.info(f"📦 Processed directory: {config['watcher']['processed_directory']}")
    logger.info(f"🌐 Logger Service URL: {config['logger_service']['url']}")
    logger.info(f"🔐 JWT issuer: {config['jwt']['issuer']}")
    logger.info(f"⏱️  JWT expiration: {config['jwt']['expiration_minutes']} minutes")
    logger.info(f"📧 Email notifications: {'enabled' if config['notifications']['email']['enabled'] else 'disabled'}")
    logger.info(f"📡 Syslog notifications: {'enabled' if config['notifications']['syslog']['enabled'] else 'disabled'}")
    logger.info(f"🌐 Web UI: http://0.0.0.0:8080/")
    logger.info("=" * 60)

    # Создаем необходимые директории
    watch_dir = Path(config['watcher']['watch_directory'])
    processed_dir = Path(config['watcher']['processed_directory'])

    watch_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"✅ Directories ready")

    # Проверяем доступность Logger Service
    try:
        logger.info("🔍 Checking Logger Service availability...")
        response = requests.get(
            config['logger_service']['url'].replace('/log', '/health'),
            timeout=5
        )
        if response.status_code == 200:
            logger.info("✅ Logger Service is available")
        else:
            logger.warning(f"⚠️ Logger Service returned status {response.status_code}")
    except:
        logger.warning("⚠️ Cannot connect to Logger Service - will retry on file events")

    # Создаем обработчик событий
    event_handler = FileWatcherHandler(config, logger)

    # Создаем observer (используем PollingObserver для Windows/Docker)
    observer = PollingObserver()
    observer.schedule(event_handler, str(watch_dir), recursive=False)

    # Запускаем мониторинг в отдельном потоке
    observer.start()
    logger.info("👀 Watching for new files... (Press Ctrl+C to stop)")

    # Запускаем Flask API в отдельном потоке
    def run_web_app():
        web_app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

    web_thread = Thread(target=run_web_app, daemon=True)
    web_thread.start()
    logger.info("🌐 Web UI started on http://0.0.0.0:8080")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("🛑 Stopping watcher service...")
        observer.stop()

    observer.join()
    logger.info("👋 Watcher service stopped")


if __name__ == '__main__':
    main()