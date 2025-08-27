// KnowledgeHub Web App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Form submission handling
    const urlForm = document.getElementById('urlForm');
    if (urlForm) {
        urlForm.addEventListener('submit', function(e) {
            handleFormSubmission(e);
        });
    }

    // Auto-dismiss alerts
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        setTimeout(function() {
            card.classList.add('fade-in');
        }, index * 100);
    });
});

function handleFormSubmission(e) {
    const form = e.target;
    const submitBtn = form.querySelector('#submitBtn');
    const processingStatus = document.getElementById('processingStatus');
    const urlInput = form.querySelector('#url');
    
    if (!urlInput.value.trim()) {
        e.preventDefault();
        showAlert('Please enter a valid URL', 'error');
        return;
    }

    // Show processing state
    if (submitBtn && processingStatus) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing...';
        processingStatus.classList.remove('d-none');
        
        // Update status text based on URL type
        const url = urlInput.value.trim();
        const statusText = document.getElementById('statusText');
        if (statusText) {
            if (url.includes('youtube.com') || url.includes('youtu.be')) {
                statusText.textContent = 'Downloading and transcribing video...';
            } else {
                statusText.textContent = 'Extracting article content...';
            }
        }
    }
}

function showAlert(message, type = 'info') {
    const alertHTML = `
        <div class="alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Find or create alert container
    let alertContainer = document.querySelector('.alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.className = 'alert-container container mt-3';
        document.querySelector('main').insertBefore(alertContainer, document.querySelector('main').firstChild);
    }
    
    alertContainer.insertAdjacentHTML('beforeend', alertHTML);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        const alert = alertContainer.querySelector('.alert:last-child');
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

// URL validation
function isValidURL(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Format date relative to now
function formatRelativeDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + / to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to clear search
    if (e.key === 'Escape') {
        const searchInput = document.getElementById('searchInput');
        if (searchInput && searchInput === document.activeElement) {
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input'));
            searchInput.blur();
        }
    }
});

// Service Worker registration for PWA features (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/js/sw.js').then(function(registration) {
            console.log('ServiceWorker registration successful');
        }, function(err) {
            console.log('ServiceWorker registration failed: ', err);
        });
    });
}

// Progressive Web App functionality
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Show install button if desired
    const installBtn = document.getElementById('installBtn');
    if (installBtn) {
        installBtn.style.display = 'block';
        installBtn.addEventListener('click', () => {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                }
                deferredPrompt = null;
            });
        });
    }
});

// Handle offline/online status
window.addEventListener('online', function() {
    showAlert('Connection restored', 'success');
});

window.addEventListener('offline', function() {
    showAlert('You are currently offline. Some features may not work.', 'warning');
});

// Debounce function for search
function debounce(func, wait, immediate) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        var later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        var callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Enhanced clipboard functionality
async function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    try {
        await navigator.clipboard.writeText(text);
        showAlert(successMessage, 'success');
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showAlert(successMessage, 'success');
        } catch (err) {
            showAlert('Failed to copy to clipboard', 'error');
        }
        
        document.body.removeChild(textArea);
    }
}

// Theme toggle functionality (if implemented)
function toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.innerHTML = newTheme === 'light' ? 
            '<i class="bi bi-moon"></i>' : 
            '<i class="bi bi-sun"></i>';
    }
}

// Initialize theme on page load
(function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
})();

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Form validation enhancements
function validateURL(url) {
    const urlPattern = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;
    return urlPattern.test(url);
}

// Auto-resize textareas
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Initialize auto-resize for textareas
document.querySelectorAll('textarea[data-auto-resize]').forEach(textarea => {
    textarea.addEventListener('input', () => autoResize(textarea));
    autoResize(textarea); // Initial resize
});