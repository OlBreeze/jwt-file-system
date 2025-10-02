# Logger Service Dockerfile
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY main.py .
COPY config.yaml .

## Copy templates for Web UI
#COPY templates/ templates/
COPY . .
# Create a directory for service logs
RUN mkdir -p logs

# Opening the port
EXPOSE 5000

# Launch the application
CMD ["python", "-u", "main.py"]