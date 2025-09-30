"""
Watcher Service - JWT File System
Мониторит папку на новые файлы и отправляет метаданные в Logger Service
"""

import os
import yaml
import jwt
import time
import shutil
import hashlib
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from logging.handlers import RotatingFileHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
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
            'exp': datetime.utcnow() + timedelta(minutes=config['jwt']['expiration_minutes']),
            'iat': datetime.utcnow()
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
            'created_at': datetime.utcnow().isoformat() + 'Z',
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
                send_email_notification(
                    self.config,
                    "Failed to Move File",
                    f"File: {filepath}\nMetadata was sent successfully but file wasn't moved.",
                    self.logger
                )
                return

            # ✅ Успех!
            self.logger.info(f"✅ Successfully processed: {metadata['filename']}")
            self.logger.info(f"   Size: {metadata['file_size']} bytes")
            self.logger.info(f"   Hash: {metadata['hash'][:16]}...")
            self.logger.info(f"   Moved to: {new_path}")

        except Exception as e:
            self.logger.error(f"Error processing file {filepath}: {e}")
            send_email_notification(
                self.config,
                "File Processing Error",
                f"File: {filepath}\nError: {str(e)}",
                self.logger
            )


# ============================================
# 8. MAIN
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

    # Создаем observer
    # - observer = Observer() !!! because Windows
    from watchdog.observers.polling import PollingObserver
    observer = PollingObserver()
    # -
    observer.schedule(event_handler, str(watch_dir), recursive=False)

    # Запускаем мониторинг
    observer.start()
    logger.info("👀 Watching for new files... (Press Ctrl+C to stop)")

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