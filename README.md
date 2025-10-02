#    👁️   File Watcher & Logger System

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


**Services will be available at:**
- 🌐 **Logger Service:** http://localhost:5000
    
  - Health Check:  http://localhost:5000/health
  - API Endpoint:  http://localhost:5000/log (POST)
  - Configuration: http://localhost:5000/api/config (GET)
  - Recent Logs:   http://localhost:5000/api/logs/recent (GET)
  - Stats:         http://localhost:5000/api/stats (GET)
  
- 🌐 **Watcher Service:** http://localhost:8080
    
  - Health Check:  http://localhost:8080/health
  - Configuration: http://localhost:8080/api/config (GET)
  - Files Count:   http://localhost:8080/api/files/count (GET)
  - Processed Files: http://localhost:8080/api/files/processed (GET)
  - Pending Files:   http://localhost:8080/api/files/pending (GET)
  - Recent Logs:     http://localhost:8080/api/logs/recent (GET)
  - Statistics:      http://localhost:8080/api/stats (GET)
  - Test Connection: http://localhost:8080/api/test-connection (GET)
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
docker-compose logs -f watcher-service
docker-compose logs -f logger-service

# Stop services
docker-compose down
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

## 🔐 JWT Authentication

### Token Details

- **Algorithm:** HS256
- **Shared Secret:** `key-in-env`
- **Expiration:** 5 minutes from creation

### Claims Structure

```json
{
  "iss": "watcher-service",
  "exp": 1727534602,
  "iat": 1727534302
}
```
### Decode

![Decode](https://drive.google.com/drive/u/0/folders/19vzf3m2Lj-YCrHAZPFsQYM39hnV8JWxK)

### Encode

![Encode](https://drive.google.com/file/d/1avpbBm6dd6-4UbD_mjyP_9z6F0NT2xpU/view?usp=drive_link)


---
## Log File Naming Convention

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
## Example Log Files


**File:** `logs/test_txt-20250928T143322Z.txt`

```
Filename: test.txt
Size: 13B
Hash: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
Created At: 2025-09-28T14:33:22Z
```
---
### Email Notifications