# Watcher Service Dockerfile
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY watcher_service.py .
COPY config.yaml .

#COPY templates/ templates/
COPY . .
# Create a directory for service logs
RUN mkdir -p logs

# Launch the application
CMD ["python", "-u", "watcher_service.py"]