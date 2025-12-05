// Enhanced UX Helper Functions
class SaathiUXHelper {
    constructor() {
        this.isOnline = navigator.onLine;
        this.setupConnectionMonitor();
        this.setupGlobalErrorHandler();
        this.addPageTransitions();
    }

    // Connection monitoring
    setupConnectionMonitor() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showNotification('✅ Connection restored', 'success');
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showNotification('⚠️ Connection lost - some features may not work', 'warning');
        });

        // No inline indicator needed; rely on notifications only
    }

    // Global error handler
    setupGlobalErrorHandler() {
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            this.showNotification('⚠️ Something went wrong. Please refresh if issues persist.', 'error');
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            // Don't show notification for every promise rejection to avoid spam
        });
    }

    // Smooth page transitions
    addPageTransitions() {
        document.addEventListener('DOMContentLoaded', () => {
            document.body.classList.add('page-transition');
        });
    }

    // Enhanced notification system
    showNotification(message, type = 'info', duration = 4000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 9999;
            padding: 15px 20px; border-radius: 8px; font-weight: bold;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transform: translateX(100%); transition: transform 0.3s ease;
            max-width: 350px; word-wrap: break-word;
        `;
        
        // Set colors based on type
        const styles = {
            error: { bg: '#f8d7da', color: '#721c24', border: '#f1aeb5' },
            success: { bg: '#d1e7dd', color: '#0f5132', border: '#a3cfbb' },
            warning: { bg: '#fff3cd', color: '#664d03', border: '#ffecb5' },
            info: { bg: '#cce7ff', color: '#004085', border: '#99d6ff' }
        };
        
        const style = styles[type] || styles.info;
        notification.style.background = style.bg;
        notification.style.color = style.color;
        notification.style.border = `1px solid ${style.border}`;
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => notification.style.transform = 'translateX(0)', 100);
        
        // Auto remove
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, duration);
        
        return notification;
    }

    // Input validation helpers
    validateInput(input, rules) {
        const errors = [];
        const value = input.value.trim();
        
        if (rules.required && !value) {
            errors.push(`${rules.label || 'This field'} is required`);
        }
        
        if (rules.minLength && value.length < rules.minLength) {
            errors.push(`${rules.label || 'This field'} must be at least ${rules.minLength} characters`);
        }
        
        if (rules.maxLength && value.length > rules.maxLength) {
            errors.push(`${rules.label || 'This field'} must not exceed ${rules.maxLength} characters`);
        }
        
        if (rules.pattern && !rules.pattern.test(value)) {
            errors.push(rules.patternMessage || `${rules.label || 'This field'} format is invalid`);
        }
        
        if (rules.custom && typeof rules.custom === 'function') {
            const customError = rules.custom(value);
            if (customError) errors.push(customError);
        }
        
        return errors;
    }

    // Form validation
    validateForm(formElement, validationRules) {
        const allErrors = [];
        
        Object.keys(validationRules).forEach(fieldName => {
            const field = formElement.querySelector(`[name="${fieldName}"], #${fieldName}`);
            if (field) {
                const errors = this.validateInput(field, validationRules[fieldName]);
                if (errors.length > 0) {
                    allErrors.push({ field, errors });
                    this.highlightError(field, errors[0]);
                } else {
                    this.clearError(field);
                }
            }
        });
        
        return allErrors;
    }

    highlightError(field, message) {
        field.classList.add('error-highlight');
        
        // Remove existing error message
        const existingError = field.parentNode.querySelector('.form-error');
        if (existingError) existingError.remove();
        
        // Add new error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.textContent = message;
        field.parentNode.insertBefore(errorDiv, field.nextSibling);
    }

    clearError(field) {
        field.classList.remove('error-highlight');
        const errorDiv = field.parentNode.querySelector('.form-error');
        if (errorDiv) errorDiv.remove();
    }

    // Loading state management
    setLoading(element, loading = true) {
        if (loading) {
            element.disabled = true;
            element.classList.add('loading-btn');
            element.dataset.originalText = element.textContent;
            element.textContent = 'Loading...';
        } else {
            element.disabled = false;
            element.classList.remove('loading-btn');
            if (element.dataset.originalText) {
                element.textContent = element.dataset.originalText;
                delete element.dataset.originalText;
            }
        }
    }

    // Debounce function for search/input
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Auto-save functionality
    setupAutoSave(formSelector, saveKey, interval = 30000) {
        const form = document.querySelector(formSelector);
        if (!form) return;

        // Load saved data
        const savedData = localStorage.getItem(saveKey);
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                Object.keys(data).forEach(key => {
                    const field = form.querySelector(`[name="${key}"]`);
                    if (field) field.value = data[key];
                });
            } catch (e) {
                console.warn('Failed to load saved form data:', e);
            }
        }

        // Auto-save on change
        const saveData = this.debounce(() => {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            localStorage.setItem(saveKey, JSON.stringify(data));
        }, 1000);

        form.addEventListener('input', saveData);
        form.addEventListener('change', saveData);

        // Periodic save
        const periodicSave = setInterval(saveData, interval);
        
        // Clear on successful submit
        form.addEventListener('submit', () => {
            localStorage.removeItem(saveKey);
            clearInterval(periodicSave);
        });
    }
}

// Initialize UX helper when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.saathiUX = new SaathiUXHelper();
    
    // Add enhanced UX styles
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'enhanced-ux.css';
    document.head.appendChild(link);
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SaathiUXHelper;
}
