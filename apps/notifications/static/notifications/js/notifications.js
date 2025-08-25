/**
 * Centralized Notification System
 * Provides a consistent way for all apps to show notifications
 */

class NotificationSystem {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Create notification container if it doesn't exist
        this.createContainer();

        // Set up auto-hide for existing messages
        this.setupAutoHide();
    }

    createContainer() {
        // Check if container already exists
        this.container = document.querySelector('.notifications-container');

        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'notifications-container';
            document.body.appendChild(this.container);
        }
    }

    /**
     * Show a notification
     * @param {string} message - The message to display
     * @param {string} type - 'success', 'error', 'warning', 'info'
     * @param {number} duration - Auto-hide duration in milliseconds (0 = no auto-hide)
     * @param {Object} options - Additional options
     */
    show(message, type = 'info', duration = 0, options = {}) {
        const notification = this.createNotification(message, type, options);

        // Add to container
        this.container.appendChild(notification);

        // Trigger entrance animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Auto-hide if duration is set
        if (duration > 0) {
            setTimeout(() => {
                this.hide(notification);
            }, duration);
        }

        return notification;
    }

    /**
     * Show a success notification
     */
    success(message, duration = 5000, options = {}) {
        return this.show(message, 'success', duration, options);
    }

    /**
     * Show an error notification
     */
    error(message, duration = 15000, options = {}) {
        return this.show(message, 'error', duration, options);
    }

    /**
     * Show a warning notification
     */
    warning(message, duration = 10000, options = {}) {
        return this.show(message, 'warning', duration, options);
    }

    /**
     * Show an info notification
     */
    info(message, duration = 8000, options = {}) {
        return this.show(message, 'info', duration, options);
    }

    /**
     * Hide a specific notification
     */
    hide(notification) {
        notification.classList.add('hiding');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    /**
     * Hide all notifications
     */
    hideAll() {
        const notifications = this.container.querySelectorAll('.notification');
        notifications.forEach(notification => this.hide(notification));
    }

    /**
     * Create notification element
     */
    createNotification(message, type, options = {}) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.setAttribute('role', 'alert');

        // Add custom classes if provided
        if (options.className) {
            notification.classList.add(options.className);
        }

        // Create notification content
        const content = document.createElement('div');
        content.className = 'notification-content';

        // Icon
        const icon = document.createElement('span');
        icon.className = 'notification-icon';
        icon.innerHTML = this.getIcon(type);

        // Message
        const messageSpan = document.createElement('span');
        messageSpan.className = 'notification-text';
        messageSpan.textContent = message;

        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.className = 'notification-close';
        closeBtn.innerHTML = '×';
        closeBtn.setAttribute('aria-label', 'Close notification');
        closeBtn.onclick = () => this.hide(notification);

        // Assemble notification
        content.appendChild(icon);
        content.appendChild(messageSpan);
        content.appendChild(closeBtn);
        notification.appendChild(content);

        return notification;
    }

    /**
     * Get icon for notification type
     */
    getIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || '💬';
    }

    /**
     * Set up auto-hide for existing Django messages
     */
    setupAutoHide() {
        const messages = document.querySelectorAll('.message');
        messages.forEach(message => {
            const type = this.getMessageType(message);
            const duration = this.getAutoHideDuration(type);

            if (duration > 0) {
                setTimeout(() => {
                    message.style.animation = 'slideOutRight 0.3s ease-in forwards';
                    setTimeout(() => message.remove(), 300);
                }, duration);
            }
        });
    }

    /**
     * Get message type from Django message classes
     */
    getMessageType(message) {
        if (message.classList.contains('message-success')) return 'success';
        if (message.classList.contains('message-error')) return 'error';
        if (message.classList.contains('message-warning')) return 'warning';
        if (message.classList.contains('message-info')) return 'info';
        return 'info';
    }

    /**
     * Get auto-hide duration for message type
     */
    getAutoHideDuration(type) {
        const durations = {
            success: 5000,
            info: 8000,
            warning: 10000,
            error: 15000
        };
        return durations[type] || 8000;
    }
}

// Create global notification system instance
window.notifications = new NotificationSystem();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSystem;
} 