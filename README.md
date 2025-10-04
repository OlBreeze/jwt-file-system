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
python logger-service.py

# In another terminal, start Watcher Service
cd watcher-service
python watcher_service.py
```

### Configuration settings are stored in the `.env` file. Copy `.env.example` to `.env` and update the values:
```bash
cp .env.example .env
```  
#### Update the settings in .env file with your values
``` 
JWT_SECRET=key_test_ssss
EMAIL_PASSWORD='***hidden***'
EMAIL_FROM=test@gmail.com
EMAIL_TO=test@gmail.com
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
![Decode](https://github.com/user-attachments/assets/d5349b52-6510-4448-b6d3-d6589791e367)

### Encode
![Encode](https://github.com/user-attachments/assets/abb58071-e770-443b-8efe-98990e0e940e)

---
## Log File Naming Convention

**Pattern:** `<sanitized-filename>-<timestamp>.txt`

**Example:**  Arnona-20251002T205912Z.txt  
```
Filename: Arnona.pdf  
Size: 476.83KB  
Created At: 2025-10-02T20:59:12.171550+00:00  
Hash: 5e8545a2224f4bd34d7d64f6c8742943c9fbd639416750c5b2faf933db211790  
Processed At: 2025-10-02T20:59:12.271298+00:00
```

---
### Email Notifications

![Encode](https://github.com/user-attachments/assets/c8887952-0b1f-4b70-828f-fe1df77c1c71)


---

## 🎨 Web User Interface

Both services feature a fully functional web-based user interface for monitoring and configuration management.

### Features

- 📊 **Real-time Statistics** - Live monitoring of file processing metrics
- 🔧 **Configuration Management** - Update settings without restarting services
- 📝 **Log Viewer** - Browse recent logs with search and filtering
- 🔗 **Service Health** - Check connection status between services


### Accessing the UI

- **Logger Service UI:** http://localhost:5000/
- **Watcher Service UI:** http://localhost:8080/

### Status

⚠️ **Note:** The web interface is currently in beta and requires additional testing. Some features may not work as expected. We welcome feedback and bug reports!

### Surprise 🥚

Good things come to those who click persistently!  
Try clicking on the author's name multiple times in the footer... You might discover something fun! 🎉


![](https://github.com/user-attachments/assets/7d54e791-8e8b-47da-9f20-9a5b706cc7e4)

![](https://github.com/user-attachments/assets/c0b24d10-5837-40c2-94fe-008d319b4b86)

---