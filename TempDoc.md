# File Watcher & Logger System

A distributed file monitoring and logging system consisting of two microservices: **Watcher Service** and **Logger Service**.  
The system monitors a local directory for new files, extracts metadata, securely sends it to another service, and processes each file end-to-end.
---

## 🌟 Features

- **Automated File Monitoring** - Real-time detection of new files
- **JWT Authentication** - Secure communication between services
- **Configurable Settings** - UI-based configuration management
- **Multi-Level Logging** - DEBUG, INFO, WARN, ERROR, FATAL levels
- **Error Notifications** - Email and Syslog support
- **File Archiving** - Automatic file processing and relocation
- **Docker Support** - Fully containerized deployment
- **SHA-256 Hashing** - File integrity verification

---

## 📋 System Architecture

```
┌─────────────────┐          HTTP/JWT           ┌─────────────────┐
│                 │ ───────────────────────────>│                 │
│ Watcher Service │                             │ Logger Service  │
│                 │ <───────────────────────────│                 │
└─────────────────┘        200 OK/Error         └─────────────────┘
         │                                                │
         │                                                │
         v                                                v
    ./watched/                                       ./logs/
    ./processed/
```

### Component Responsibilities

#### 1. Watcher Service
- Monitors `./watched/` directory for new files
- Extracts file metadata (name, size, timestamp, SHA-256 hash)
- Generates JWT tokens with HS256 algorithm
- Sends metadata to Logger Service via HTTP POST
- Moves processed files to `./processed/` on success
- Retries failed operations

#### 2. Logger Service
- Exposes REST API endpoint: `POST /log`
- Validates JWT tokens (signature, issuer, expiration)
- Creates timestamped log files in `./logs/`
- Returns appropriate HTTP status codes
- Handles errors gracefully

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker & Docker Compose (optional)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/OlBreeze/jwt-file-system.git
cd jwt-file-system

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