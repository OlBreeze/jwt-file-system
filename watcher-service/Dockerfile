# Watcher Service Dockerfile
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app.py .
COPY config.yaml .

# Создаем директорию для логов сервиса
RUN mkdir -p logs

# Переменные окружения (можно переопределить в docker-compose)
ENV JWT_SECRET=sasa-Software2015
ENV LOGGER_URL=http://logger-service:5000/log
ENV WATCH_DIR=./watched
ENV PROCESSED_DIR=./processed
ENV LOG_LEVEL=INFO

# Запускаем приложение
CMD ["python", "-u", "app.py"]