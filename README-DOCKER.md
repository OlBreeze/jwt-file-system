# JWT File System - Docker Instructions

## 📋 Предварительные требования

- Docker (версия 20.10+)
- Docker Compose (версия 2.0+)

Проверьте установку:
```bash
docker --version
docker-compose --version
```

---

## 🚀 Быстрый старт

### 1. Клонируйте/создайте структуру проекта

```
jwt-file-system/
├── logger-service/
│   ├── app.py
│   ├── config.yaml
│   ├── requirements.txt
│   └── Dockerfile
├── watcher-service/
│   ├── app.py
│   ├── config.yaml
│   ├── requirements.txt
│   └── Dockerfile
├── watched/
├── processed/
├── logs/
├── docker-compose.yml
└── .env.example
```

### 2. Создайте необходимые папки

```bash
mkdir -p watched processed logs
mkdir -p logger-service/logs watcher-service/logs
```

### 3. Запустите систему

```bash
# Сборка и запуск всех сервисов
docker-compose up --build

# Или в фоновом режиме
docker-compose up --build -d
```

**Ожидаемый вывод:**
```
Creating network "jwt-file-system_jwt-file-system-network" with driver "bridge"
Creating logger-service ... done
Creating watcher-service ... done
Attaching to logger-service, watcher-service
logger-service    | ============================================================
logger-service    | 🚀 Starting logger-service
logger-service    | 📍 Host: 0.0.0.0
logger-service    | 📍 Port: 5000
logger-service    | ============================================================
watcher-service   | ============================================================
watcher-service   | 🚀 Starting watcher-service
watcher-service   | 📁 Watching directory: /app/watched
watcher-service   | ✅ Logger Service is available
watcher-service   | 👀 Watching for new files...
watcher-service   | ============================================================
```

---

## 🧪 Тестирование системы

### Создайте тестовый файл:

```bash
echo "Hello Docker World!" > watched/test-docker.txt
```

### Проверьте результат (через 1-2 секунды):

```bash
# Файл должен переместиться
ls processed/

# Должен создаться лог
ls logs/

# Просмотр содержимого лога
cat logs/test-docker-*.txt
```

**Ожидаемое содержимое:**
```
Filename: test-docker.txt
Size: 20B
Created At: 2025-09-30T14:33:22Z
Hash: abc123...
Processed At: 2025-09-30T14:33:23Z
```

---

## 📊 Управление контейнерами

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Только Logger Service
docker-compose logs -f logger-service

# Только Watcher Service
docker-compose logs -f watcher-service

# Последние 100 строк
docker-compose logs --tail=100
```

### Статус сервисов

```bash
docker-compose ps
```

**Вывод:**
```
NAME              STATUS          PORTS
logger-service    Up 2 minutes    0.0.0.0:5000->5000/tcp
watcher-service   Up 2 minutes
```

### Остановка системы

```bash
# Остановить, но сохранить контейнеры
docker-compose stop

# Остановить и удалить контейнеры
docker-compose down

# Удалить всё включая volumes
docker-compose down -v
```

### Перезапуск сервиса

```bash
# Перезапустить Logger Service
docker-compose restart logger-service

# Перезапустить Watcher Service
docker-compose restart watcher-service
```

---

## 🔧 Отладка

### Вход в контейнер

```bash
# Logger Service
docker exec -it logger-service /bin/bash

# Watcher Service
docker exec -it watcher-service /bin/bash
```

### Проверка health check

```bash
# Logger Service должен отвечать на /health
curl http://localhost:5000/health
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "service": "logger-service",
  "timestamp": "2025-09-30T14:33:22Z"
}
```

### Просмотр логов внутри контейнера

```bash
# Войти в контейнер
docker exec -it logger-service /bin/bash

# Просмотр логов сервиса
cat logs/logger-service.log

# Выход
exit
```

---

## 🔐 Переменные окружения

### Создайте .env файл (опционально)

```bash
cp .env.example .env
nano .env
```

### Использование в docker-compose.yml

```yaml
services:
  logger-service:
    env_file:
      - .env
```

---

## 📈 Мониторинг

### Использование ресурсов

```bash
docker stats logger-service watcher-service
```

### Проверка сети

```bash
docker network inspect jwt-file-system_jwt-file-system-network
```

---

## 🔄 Обновление сервисов

### После изменения кода:

```bash
# Пересобрать только изменённые сервисы
docker-compose up --build -d

# Или конкретный сервис
docker-compose up --build -d logger-service
```

---

## 🧹 Очистка

### Удалить всё связанное с проектом:

```bash
# Остановить и удалить контейнеры, сети
docker-compose down

# Удалить образы
docker rmi jwt-file-system-logger-service
docker rmi jwt-file-system-watcher-service

# Удалить неиспользуемые образы и volumes
docker system prune -a --volumes
```

---

## 🐛 Решение проблем

### Logger Service не запускается

```bash
# Проверьте логи
docker-compose logs logger-service

# Проверьте порт 5000 (может быть занят)
lsof -i :5000  # Mac/Linux
netstat -ano | findstr :5000  # Windows
```

### Watcher Service не видит Logger Service

```bash
# Проверьте что оба в одной сети
docker network inspect jwt-file-system_jwt-file-system-network

# Проверьте переменную LOGGER_URL
docker exec watcher-service env | grep LOGGER_URL
```

### Файлы не обрабатываются

```bash
# Проверьте права на папки
ls -la watched/ processed/ logs/

# Проверьте логи Watcher
docker-compose logs -f watcher-service

# Проверьте что папки правильно смонтированы
docker inspect watcher-service | grep Mounts -A 20
```

---

## 🎯 Production рекомендации

1. **Измените JWT_SECRET** на более сложный:
   ```bash
   openssl rand -base64 32
   ```

2. **Используйте .env файл** вместо хардкода в docker-compose.yml

3. **Настройте логирование** в external систему (ELK, Splunk)

4. **Добавьте reverse proxy** (nginx) перед Logger Service

5. **Настройте мониторинг** (Prometheus + Grafana)

6. **Используйте secrets** для чувствительных данных:
   ```yaml
   secrets:
     jwt_secret:
       external: true
   ```

---

## 📚 Дополнительные команды

```bash
# Просмотр всех контейнеров
docker ps -a

# Просмотр образов
docker images

# Очистка логов Docker
truncate -s 0 /var/lib/docker/containers/*/*-json.log

# Экспорт контейнера
docker export logger-service > logger-service.tar

# Сохранение образа
docker save jwt-file-system-logger-service > logger-image.tar
```

---

## ✅ Готово!

Теперь ваша система работает в Docker контейнерах! 🐳