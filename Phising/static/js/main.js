// Main JavaScript file for Phishing Simulator

// Copy to clipboard function
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function() {
            showNotification('✓ Lien copié dans le presse-papiers !', 'success');
        }, function(err) {
            showNotification('✗ Erreur lors de la copie : ' + err, 'error');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
            showNotification('✓ Lien copié dans le presse-papiers !', 'success');
        } catch (err) {
            showNotification('✗ Erreur lors de la copie', 'error');
        }
        document.body.removeChild(textArea);
    }
}

// Show notification function
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotif = document.querySelector('.notification');
    if (existingNotif) {
        existingNotif.remove();
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Confirm delete action with enhanced UI
function confirmDelete(message, callback) {
    const confirmed = confirm(message || 'Êtes-vous sûr de vouloir supprimer cet élément ?');
    if (confirmed && callback) {
        callback();
    }
    return confirmed;
}

// Track user click and send notification email
function trackClickAndNotify(campaignId, userId, eventType = 'click') {
    const data = {
        campaign_id: campaignId,
        user_id: userId,
        event_type: eventType,
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        language: navigator.language
    };
    
    // Send tracking data to backend
    fetch('/api/track-click', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            console.log('✓ Clic tracé et email envoyé:', result);
        }
    })
    .catch(error => {
        console.error('✗ Erreur tracking:', error);
    });
}

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    // Add loading state to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                submitBtn.textContent = submitBtn.textContent.replace(/^[^a-zA-Z]*/, '⏳ ');
                
                // Re-enable after 5 seconds in case of error
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.textContent = submitBtn.textContent.replace('⏳ ', '');
                }, 5000);
            }
        });
    });

    // Highlight active nav link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
});

// Table sorting functionality with visual feedback
function sortTable(tableId, column, asc = true) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const sortedRows = rows.sort((a, b) => {
        const aValue = a.children[column]?.textContent.trim() || '';
        const bValue = b.children[column]?.textContent.trim() || '';
        
        // Try numeric comparison first
        const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
        const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return asc ? aNum - bNum : bNum - aNum;
        }
        
        return asc
            ? aValue.localeCompare(bValue, undefined, { numeric: true })
            : bValue.localeCompare(aValue, undefined, { numeric: true });
    });
    
    tbody.innerHTML = '';
    sortedRows.forEach(row => tbody.appendChild(row));
    
    // Update header indicators
    const headers = table.querySelectorAll('th');
    headers.forEach((th, idx) => {
        th.classList.remove('sorted-asc', 'sorted-desc');
        if (idx === column) {
            th.classList.add(asc ? 'sorted-asc' : 'sorted-desc');
        }
    });
    
    showNotification(`Tableau trié par colonne ${column + 1}`, 'info');
}

// Filter table rows with real-time search
function filterTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    input.addEventListener('input', function() {
        const filter = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        let visibleCount = 0;
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const isVisible = text.includes(filter);
            row.style.display = isVisible ? '' : 'none';
            if (isVisible) visibleCount++;
        });
        
        // Show result count
        let countDisplay = document.getElementById(`${tableId}-count`);
        if (!countDisplay) {
            countDisplay = document.createElement('div');
            countDisplay.id = `${tableId}-count`;
            countDisplay.className = 'filter-count';
            input.parentElement.appendChild(countDisplay);
        }
        countDisplay.textContent = filter ? `${visibleCount} résultat(s) trouvé(s)` : '';
    });
}

// Export table to CSV with enhanced data capture
function exportTableToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) {
        showNotification('Table introuvable', 'error');
        return;
    }
    
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => {
            // Skip action columns
            if (col.querySelector('button, a.btn-small, .btn-delete-small')) {
                return '';
            }
            const text = col.textContent.trim().replace(/\s+/g, ' ');
            return '"' + text.replace(/"/g, '""') + '"';
        }).filter(cell => cell !== '');
        
        if (rowData.length > 0) {
            csv.push(rowData.join(','));
        }
    });
    
    const csvContent = '\uFEFF' + csv.join('\n'); // UTF-8 BOM for Excel
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification(`✓ Export réussi: ${filename}`, 'success');
    
    // Log export action
    logUserAction('export_csv', { table: tableId, filename: filename });
}

// Log user actions for analytics
function logUserAction(actionType, data = {}) {
    const logData = {
        action: actionType,
        timestamp: new Date().toISOString(),
        page: window.location.pathname,
        ...data
    };
    
    fetch('/api/log-action', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(logData)
    }).catch(err => console.log('Log action error:', err));
}

console.log('✓ Phishing Simulator JavaScript chargé');
