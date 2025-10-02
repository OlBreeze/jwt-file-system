# File Watcher & Logger System
📥 A file appears in the watch_directory  "/watched"  
🔍 The system detects the file  
📊 It extracts metadata (name, creation time, size, hash)  
🔐 Metadata is securely sent to a remote service via API (with JWT-based authentication)  
📁 The file is moved or copied to the processed directory  "/processed"
🧾 A log entry is created  "/logs"
📧 A notification (email/syslog) is sent — if configured 


## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker & Docker Compose (optional)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd file-watcher-system

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

#### Option 2: Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start Logger Service
cd logger-service
python logger_service.py

# In another terminal, start Watcher Service
cd watcher-service
python watcher_service.py
```

---

## ⚙️ Configuration

Both services use `config.yaml` files with web-based configuration UI.

### Watcher Service Configuration

**File:** `watcher-service/config.yaml`

```yaml
watcher:
  watch_folder: "./watched"
  processed_folder: "./processed"
  check_interval: 5
  max_files_to_keep: 100

logger_service:
  url: "http://logger-service:5001/log"

jwt:
  secret: "sasa-Software2015"
  issuer: "watcher-service"
  expiration_minutes: 5

notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    from_address: "watcher@example.com"
    to_addresses:
      - "admin@example.com"
  syslog:
    enabled: false
    server: "localhost"
    port: 514

logging:
  level: "INFO"
  file: "./watcher.log"
  max_bytes: 10485760
  backup_count: 5
```

### Logger Service Configuration

**File:** `logger-service/config.yaml`

```yaml
logger:
  logs_folder: "./logs"
  max_files_to_keep: 500
  host: "0.0.0.0"
  port: 5001

jwt:
  secret: "sasa-Software2015"
  issuer: "watcher-service"

notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    from_address: "logger@example.com"
    to_addresses:
      - "admin@example.com"
  syslog:
    enabled: false
    server: "localhost"
    port: 514

logging:
  level: "INFO"
  file: "./logger.log"
  max_bytes: 10485760
  backup_count: 5
```

### Configuration UI

Access the configuration interfaces:

- **Watcher Service UI:** http://localhost:5000/config
- **Logger Service UI:** http://localhost:5001/config

---

## 📡 API Reference

### POST /log

Logs file metadata to the Logger Service.

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Request Body:**
```json
{
  "filename": "report.pdf",
  "created_at": "2025-09-28T14:33:22Z",
  "file_size": 204800,
  "hash": "abc123def456..."
}
```

**Response Codes:**
- `200 OK` - Log created successfully
- `400 Bad Request` - Invalid payload
- `401 Unauthorized` - Invalid or expired JWT
- `500 Internal Server Error` - Logging failure

---

## 🔐 JWT Authentication

### Token Details

- **Algorithm:** HS256
- **Shared Secret:** `sasa-Software2015`
- **Expiration:** 5 minutes from creation

### Claims Structure

```json
{
  "iss": "watcher-service",
  "exp": 1727534602,
  "iat": 1727534302
}
```

### Implementation

**Token Generation (Watcher Service):**
```python
import jwt
from datetime import datetime, timedelta

def generate_jwt_token():
    payload = {
        'iss': 'watcher-service',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=5)
    }
    token = jwt.encode(payload, 'sasa-Software2015', algorithm='HS256')
    return token
```

**Token Validation (Logger Service):**
```python
import jwt

def validate_jwt_token(token):
    try:
        payload = jwt.decode(
            token, 
            'sasa-Software2015', 
            algorithms=['HS256'],
            issuer='watcher-service'
        )
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, "Token has expired"
    except jwt.InvalidIssuerError:
        return False, "Invalid issuer"
    except jwt.InvalidTokenError:
        return False, "Invalid token"
```

---

## 🛠️ Technology Stack

### Core Technologies

| Technology | Purpose | Implementation Details |
|------------|---------|------------------------|
| **Python 3.9+** | Programming Language | Core language for both services |
| **Flask** | Web Framework | REST API for Logger Service, Config UI for both |
| **PyJWT** | JWT Authentication | HS256 signing and verification |
| **Watchdog** | File Monitoring | Real-time file system event detection |
| **PyYAML** | Configuration | YAML parsing for config files |
| **Requests** | HTTP Client | Communication between services |

### Security Implementation

#### JWT (JSON Web Tokens)
- **Library:** PyJWT 2.8+
- **Algorithm:** HS256 (HMAC with SHA-256)
- **Token Lifecycle:** 5-minute expiration
- **Claims Validation:** Issuer (iss) and Expiration (exp) checks
- **Transport:** HTTP Authorization header (Bearer scheme)

**Security Features:**
- Shared secret stored in environment variables (optional)
- Automatic token expiration and renewal
- Signature verification on every request
- Protection against token tampering

#### File Hashing
- **Algorithm:** SHA-256
- **Purpose:** File integrity verification
- **Implementation:**
```python
import hashlib

def calculate_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
```

### Communication Protocol

#### HTTP/REST Architecture
- **Protocol:** HTTP/1.1
- **Format:** JSON for data exchange
- **Method:** POST for metadata transmission
- **Content-Type:** application/json
- **Authentication:** JWT Bearer token in headers

**Request Flow:**
```
1. Watcher detects file
2. Extract metadata (name, size, hash, timestamp)
3. Generate JWT token
4. POST to Logger: /log
5. Logger validates JWT
6. Logger creates log file
7. Logger returns 200 OK
8. Watcher moves file to processed/
```

### Logging Infrastructure

#### Multi-Level Logging System
- **Library:** Python logging module
- **Levels:** DEBUG, INFO, WARN, ERROR, FATAL
- **Format:** Timestamp, Level, Module, Message
- **Rotation:** Size-based (10MB) with 5 backup files

**Log Format Example:**
```
2025-09-28 14:33:22,123 - INFO - watcher_service - File detected: report.pdf
2025-09-28 14:33:22,456 - DEBUG - watcher_service - Generated JWT token
2025-09-28 14:33:22,789 - INFO - watcher_service - Metadata sent successfully
```

#### Separate Log Files
- **Watcher Service:** `watcher-service/watcher.log`
- **Logger Service:** `logger-service/logger.log`
- **Rotation Strategy:** Automatic when file reaches max size
- **Persistence:** Logs retained according to backup_count setting

### Notification System

#### Email Notifications
- **Protocol:** SMTP
- **Library:** Python smtplib
- **Authentication:** Username/Password
- **TLS Support:** Yes (Port 587)
- **Triggers:** 
  - File processing errors
  - JWT validation failures
  - Service startup/shutdown
  - Critical errors

**Implementation:**
```python
import smtplib
from email.mime.text import MIMEText

def send_email_notification(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'watcher@example.com'
    msg['To'] = 'admin@example.com'
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('username', 'password')
        server.send_message(msg)
```

#### Syslog Integration
- **Protocol:** Syslog (RFC 5424)
- **Library:** Python logging.handlers.SysLogHandler
- **Transport:** UDP (default port 514)
- **Facility:** LOG_USER
- **Severity Mapping:** 
  - DEBUG → LOG_DEBUG
  - INFO → LOG_INFO
  - WARN → LOG_WARNING
  - ERROR → LOG_ERR
  - FATAL → LOG_CRIT

### File System Operations

#### Directory Monitoring
- **Library:** Watchdog (watchdog.observers)
- **Events:** File creation detection
- **Polling Interval:** Configurable (default 5 seconds)
- **Handler:** FileSystemEventHandler for on_created events

#### File Operations
```python
# Move file atomically
import shutil
shutil.move(source_path, destination_path)

# Ensure directory exists
import os
os.makedirs(directory, exist_ok=True)

# Safe filename sanitization
import re
safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', original_filename)
```

### Containerization

#### Docker Implementation
- **Base Image:** python:3.9-slim
- **Volume Mounts:** 
  - Config files (read-only)
  - Data directories (read-write)
- **Network:** Bridge network for inter-service communication
- **Health Checks:** HTTP endpoint monitoring
- **Environment Variables:** JWT_SECRET, LOGGER_URL

**Dockerfile Structure:**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "service.py"]
```

### Configuration Management

#### YAML-Based Configuration
- **Format:** YAML (human-readable)
- **Validation:** Schema validation on startup
- **Hot Reload:** Configuration changes without restart
- **UI Editor:** Web-based configuration interface
- **Persistence:** Changes saved back to config.yaml

#### Configuration UI
- **Framework:** Flask with HTML templates
- **Features:**
  - Live configuration editing
  - Input validation
  - Save/Reload functionality
  - Section organization
- **Endpoints:**
  - GET /config - Display configuration form
  - POST /config - Save configuration changes

### Data Storage

#### Log File Storage
- **Format:** Plain text (.txt)
- **Naming Convention:** `<filename>-<ISO8601-timestamp>.txt`
- **Content Structure:** Key-value pairs
- **Retention:** Configurable max_files_to_keep
- **Cleanup:** Automatic deletion of oldest files

**Log Entry Format:**
```
Filename: report.pdf
Size: 200KB
Hash: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
Created At: 2025-09-28T14:33:22Z
```

### Error Handling & Resilience

#### Retry Mechanism
- **Strategy:** Failed files remain in watched/ for retry
- **Backoff:** Configurable check_interval
- **Persistence:** No file loss on temporary failures

#### HTTP Error Responses
```python
# 400 Bad Request
{
  "error": "Missing required field: filename"
}

# 401 Unauthorized
{
  "error": "Invalid or expired JWT token"
}

# 500 Internal Server Error
{
  "error": "Failed to create log file"
}
```

#### Graceful Degradation
- Services continue operating with degraded functionality
- Notifications fail silently (logged but don't block)
- Configuration errors use default values
- File processing continues despite individual failures

---

## 📁 File Lifecycle

| Phase | Action | Location |
|-------|--------|----------|
| **Detected** | New file appears | `./watched/` |
| **Processing** | Metadata extracted | In memory |
| **Logged** | Log file created | `./logs/` |
| **Archived** | Original file moved | `./processed/` |

### Log File Naming Convention

**Pattern:** `<sanitized-filename>-<timestamp>.txt`

**Example:** `report_pdf-20250928T143322Z.txt`

**Content:**
```
Filename: report.pdf
Size: 200KB
Hash: abc123def456...
Created At: 2025-09-28T14:33:22Z
```

---

## 📊 Logging Levels

Both services support configurable logging:

| Level | Description | Use Case |
|-------|-------------|----------|
| **DEBUG** | Detailed diagnostic information | Development |
| **INFO** | General informational messages | Normal operation |
| **WARN** | Warning messages | Potential issues |
| **ERROR** | Error messages | Failures |
| **FATAL** | Critical failures | System crashes |

---

## 🔔 Notifications

### Email Notifications

Configure SMTP settings in `config.yaml`:

```yaml
notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
```

### Syslog Integration

Enable syslog for centralized logging:

```yaml
notifications:
  syslog:
    enabled: true
    server: "syslog-server.local"
    port: 514
```

---

## 🐳 Docker Deployment

### docker-compose.yml

```yaml
version: '3.8'

services:
  logger-service:
    build: ./logger-service
    ports:
      - "5001:5001"
    volumes:
      - ./logs:/app/logs
      - ./logger-service/config.yaml:/app/config.yaml
    environment:
      - JWT_SECRET=sasa-Software2015

  watcher-service:
    build: ./watcher-service
    depends_on:
      - logger-service
    volumes:
      - ./watched:/app/watched
      - ./processed:/app/processed
      - ./watcher-service/config.yaml:/app/config.yaml
    environment:
      - JWT_SECRET=sasa-Software2015
      - LOGGER_URL=http://logger-service:5001/log
```

### Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f watcher-service
docker-compose logs -f logger-service

# Rebuild after changes
docker-compose up -d --build
```

---

## 🧪 Testing

### Manual Testing

1. **Place a test file:**
   ```bash
   echo "Test content" > watched/test.txt
   ```

2. **Verify processing:**
   ```bash
   # Check if file moved
   ls processed/
   
   # Check log created
   ls logs/
   ```

3. **View service logs:**
   ```bash
   tail -f watcher-service/watcher.log
   tail -f logger-service/logger.log
   ```

### Example Log File

**File:** `logs/test_txt-20250928T143322Z.txt`

```
Filename: test.txt
Size: 13B
Hash: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
Created At: 2025-09-28T14:33:22Z
```

---

## 🛠️ Troubleshooting

### Common Issues

**File not being processed:**
- Check watcher service logs: `tail -f watcher-service/watcher.log`
- Verify folder permissions
- Ensure logger service is running

**JWT Authentication Failures:**
- Verify JWT secret matches in both services
- Check system time synchronization
- Token expires in 5 minutes

**Logger Service Not Responding:**
- Check if port 5001 is available
- Verify network connectivity between services
- Review logger service logs

### Debug Mode

Enable detailed logging:

```yaml
logging:
  level: "DEBUG"
```

---

## 📈 Performance Considerations

- **Check Interval:** Adjust `check_interval` based on file volume
- **Max Files:** Configure `max_files_to_keep` for automatic cleanup
- **Logging:** Use INFO level in production, DEBUG for troubleshooting

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👥 Authors

- Your Name - Initial work

---

## 🙏 Acknowledgments

- JWT implementation using PyJWT library
- Flask for REST API framework
- Watchdog for file system monitoring

---

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Email: support@example.com
- Documentation: [Wiki](wiki-url)

---

**Built with ❤️ using Python**