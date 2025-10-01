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

COPY templates/ templates/

# Создаем директорию для логов сервиса
RUN mkdir -p logs

# Запускаем приложение
CMD ["python", "-u", "app.py"]