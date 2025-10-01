# Logger Service Dockerfile
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app.py .
COPY config.yaml .

# Копируем templates для Web UI
COPY templates/ templates/

# Создаем директорию для логов сервиса
RUN mkdir -p logs

# Переменные окружения (можно переопределить в docker-compose)
ENV JWT_SECRET=sasa-Software2015
ENV LOGGER_HOST=0.0.0.0
ENV LOGGER_PORT=5000
ENV LOG_LEVEL=INFO

# Открываем порт
EXPOSE 5000

# Запускаем приложение
CMD ["python", "-u", "app.py"]