// Load current config
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        console.log('Loaded config:', config); // Debug

        // Logging settings
        document.getElementById('log_level').value = config.logging.level;
        document.getElementById('max_size_mb').value = config.logging.max_size_mb;
        document.getElementById('backup_count').value = config.logging.backup_count;

        // Notifications - ИСПРАВЛЕНО
        document.getElementById('email_enabled').checked = config.notifications?.email?.enabled || false;
        document.getElementById('email_to').value = config.notifications?.email?.to || '';
        document.getElementById('syslog_enabled').checked = config.notifications?.syslog?.enabled || false;

        console.log('Email enabled:', config.notifications?.email?.enabled); // Debug
        console.log('Email to:', config.notifications?.email?.to); // Debug
    } catch (error) {
        showAlert('Failed to load configuration: ' + error.message, 'error');
        console.error('Load config error:', error); // Debug
    }
}

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
    console.log('Saving notifications:', data); // Debug
    await saveConfig('notifications', data);
});

// Save config API - ИСПРАВЛЕНО
async function saveConfig(section, data) {
    try {
        console.log(`Saving ${section}:`, data); // Debug

        const response = await fetch(`/api/config/${section}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showAlert(`${section} settings saved! Restart may be required.`, 'success');
            // ВАЖНО: Перезагружаем конфиг через 500мс чтобы увидеть изменения
            setTimeout(() => {
                console.log('Reloading config after save...'); // Debug
                loadConfig();
            }, 500);
        } else {
            const error = await response.json();
            showAlert('Failed to save: ' + error.error, 'error');
            console.error('Save error:', error); // Debug
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
        console.error('Save exception:', error); // Debug
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
        console.error('Test connection error:', error); // Debug
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
        console.error('Refresh stats error:', error); // Debug
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
        console.error('Refresh logs error:', error); // Debug
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
refreshLogs();
testConnection();

// Auto-refresh
setInterval(refreshStats, 30000);
setInterval(refreshLogs, 30000);
setInterval(testConnection, 60000);