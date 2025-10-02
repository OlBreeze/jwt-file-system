// Load current config
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        // Directory settings
        document.getElementById('watch_directory').value = config.watcher.watch_directory;
        document.getElementById('processed_directory').value = config.watcher.processed_directory;
        document.getElementById('check_interval').value = config.watcher.check_interval;

        // Logger connection
        document.getElementById('logger_url').value = config.logger_service.url;
        document.getElementById('timeout').value = config.logger_service.timeout;
        document.getElementById('retry_attempts').value = config.logger_service.retry_attempts || 3;

        // JWT settings
        document.getElementById('jwt_issuer').value = config.jwt.issuer;
        document.getElementById('expiration_minutes').value = config.jwt.expiration_minutes;
        document.getElementById('jwt_algorithm').value = config.jwt.algorithm;

        // Logging settings
        document.getElementById('log_level').value = config.logging.level;
        document.getElementById('max_size_mb').value = config.logging.max_size_mb;
        document.getElementById('backup_count').value = config.logging.backup_count;

        // Notifications
        document.getElementById('email_enabled').checked = config.notifications.email.enabled;
        document.getElementById('email_to').value = config.notifications.email.to;
        document.getElementById('syslog_enabled').checked = config.notifications.syslog.enabled;
    } catch (error) {
        showAlert('Failed to load configuration: ' + error.message, 'error');
    }
}

// Save directory settings
document.getElementById('directory-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
        watch_directory: formData.get('watch_directory'),
        processed_directory: formData.get('processed_directory'),
        check_interval: parseInt(formData.get('check_interval'))
    };
    await saveConfig('watcher', data);
});

// Save logger connection
document.getElementById('logger-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
        url: formData.get('logger_url'),
        timeout: parseInt(formData.get('timeout')),
        retry_attempts: parseInt(formData.get('retry_attempts'))
    };
    await saveConfig('logger_service', data);
});

// Save JWT settings
document.getElementById('jwt-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
        issuer: formData.get('jwt_issuer'),
        expiration_minutes: parseInt(formData.get('expiration_minutes')),
        algorithm: formData.get('jwt_algorithm')
    };
    await saveConfig('jwt', data);
});

// Save logging settings
document.getElementById('logging-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
        level: formData.get('log_level'),
        max_size_mb: parseInt(formData.get('max_size_mb')),
        backup_count: parseInt(formData.get('backup_count'))
    };
    await saveConfig('logging', data);
});

// Save notifications
document.getElementById('notifications-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        email: {
            enabled: document.getElementById('email_enabled').checked,
            to: document.getElementById('email_to').value
        },
        syslog: {
            enabled: document.getElementById('syslog_enabled').checked
        }
    };
    await saveConfig('notifications', data);
});

// Save config API
async function saveConfig(section, data) {
    try {
        const response = await fetch(`/api/config/${section}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showAlert(`${section} settings saved! Restart may be required.`, 'success');
        } else {
            const error = await response.json();
            showAlert('Failed to save: ' + error.error, 'error');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
    }
}

// Test connection to Logger Service
async function testConnection() {
    try {
        const response = await fetch('/api/test-connection');
        const result = await response.json();

        if (result.success) {
            showAlert('✅ Connection successful!', 'success');
            document.getElementById('logger-indicator').classList.remove('disconnected');
            document.getElementById('logger-status').textContent = 'Connected to Logger Service';
        } else {
            showAlert('❌ Connection failed: ' + result.error, 'error');
            document.getElementById('logger-indicator').classList.add('disconnected');
            document.getElementById('logger-status').textContent = 'Disconnected from Logger Service';
        }
    } catch (error) {
        showAlert('Connection test failed: ' + error.message, 'error');
    }
}

// Refresh stats
async function refreshStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('total-processed').textContent = stats.total_processed;
        document.getElementById('today-processed').textContent = stats.today_processed;
        document.getElementById('pending-files').textContent = stats.pending_files;
        document.getElementById('success-rate').textContent = stats.success_rate + '%';
        document.getElementById('processed-count').textContent = stats.total_processed;
    } catch (error) {
        showAlert('Failed to refresh stats', 'error');
    }
}

// Refresh pending files
async function refreshFiles() {
    try {
        const response = await fetch('/api/files/pending');
        const files = await response.json();

        const filesList = document.getElementById('pending-files-list');
        document.getElementById('pending-badge').textContent = files.length;

        if (files.length === 0) {
            filesList.innerHTML = '<div style="text-align: center; color: #999;">No pending files</div>';
        } else {
            filesList.innerHTML = files.map(file => `
                        <div class="file-item">
                            <div>
                                <div class="name">📄 ${file.name}</div>
                                <div class="size">${file.size}</div>
                            </div>
                            <div class="time">${file.created}</div>
                        </div>
                    `).join('');
        }
    } catch (error) {
        showAlert('Failed to refresh files', 'error');
    }
}

// Refresh logs
async function refreshLogs() {
    try {
        const response = await fetch('/api/logs/recent');
        const logs = await response.json();

        const logsPreview = document.getElementById('logs-preview');
        logsPreview.innerHTML = logs.map(log =>
            `<div class="log-line ${log.level.toLowerCase()}">${log.timestamp} - ${log.level} - ${log.message}</div>`
        ).join('');
    } catch (error) {
        showAlert('Failed to refresh logs', 'error');
    }
}

// Show alert
function showAlert(message, type) {
    const alert = document.getElementById('alert');
    alert.className = `alert ${type}`;
    alert.textContent = message;
    alert.style.display = 'block';

    setTimeout(() => {
        alert.style.display = 'none';
    }, 5000);
}

// Initialize
loadConfig();
refreshStats();
refreshFiles();
refreshLogs();
testConnection();

// Auto-refresh
setInterval(refreshStats, 30000);
setInterval(refreshFiles, 10000);
setInterval(refreshLogs, 30000);
setInterval(testConnection, 60000);