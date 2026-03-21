/**
 * NotificationManager - Gestor de notificaciones del sistema
 */

class NotificationManager {
    constructor() {
        this.container = null;
        this.notifications = new Map();
        this.defaultDuration = 5000; // 5 segundos
        this.maxNotifications = 5;
        this.init();
    }

    /**
     * Inicializar el notification manager
     */
    init() {
        this.container = document.getElementById('notificationContainer');
        if (!this.container) {
            console.warn('Notification container no encontrado');
        }
    }

    /**
     * Mostrar notificación
     */
    show(message, type = 'info', title = '', duration = null) {
        if (!this.container) return null;

        const id = this.generateId();
        const notification = this.createNotification(id, message, type, title);
        
        // Agregar al DOM
        this.container.appendChild(notification);
        
        // Animar entrada
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });

        // Configurar auto-remove
        const finalDuration = duration || this.defaultDuration;
        if (finalDuration > 0) {
            setTimeout(() => {
                this.remove(id);
            }, finalDuration);
        }

        // Almacenar referencia
        this.notifications.set(id, {
            element: notification,
            type,
            timestamp: Date.now()
        });

        // Limitar número de notificaciones
        this.enforceMaxNotifications();

        return id;
    }

    /**
     * Crear elemento de notificación
     */
    createNotification(id, message, type, title) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.dataset.id = id;

        const icon = this.getIconForType(type);
        
        notification.innerHTML = `
            ${title ? `<div class="title">${icon} ${title}</div>` : ''}
            <div class="message">${message}</div>
            <button class="notification-close" onclick="labSimApp.notificationManager.remove('${id}')" title="Cerrar">
                ×
            </button>
        `;

        // Event listener para cerrar
        const closeBtn = notification.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.remove(id);
            });
        }

        // Click en la notificación para cerrar
        notification.addEventListener('click', () => {
            this.remove(id);
        });

        return notification;
    }

    /**
     * Obtener icono según tipo
     */
    getIconForType(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    /**
     * Remover notificación
     */
    remove(id) {
        const notificationData = this.notifications.get(id);
        if (!notificationData) return;

        const element = notificationData.element;
        
        // Animar salida
        element.classList.remove('show');
        
        // Remover del DOM después de la animación
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
            this.notifications.delete(id);
        }, 300);
    }

    /**
     * Remover todas las notificaciones
     */
    removeAll() {
        this.notifications.forEach((_, id) => {
            this.remove(id);
        });
    }

    /**
     * Remover notificaciones por tipo
     */
    removeByType(type) {
        this.notifications.forEach((notification, id) => {
            if (notification.type === type) {
                this.remove(id);
            }
        });
    }

    /**
     * Limitar número máximo de notificaciones
     */
    enforceMaxNotifications() {
        if (this.notifications.size > this.maxNotifications) {
            // Remover las más antiguas
            const sortedNotifications = Array.from(this.notifications.entries())
                .sort((a, b) => a[1].timestamp - b[1].timestamp);
            
            const toRemove = sortedNotifications.slice(0, this.notifications.size - this.maxNotifications);
            toRemove.forEach(([id]) => this.remove(id));
        }
    }

    /**
     * Generar ID único
     */
    generateId() {
        return `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Métodos de conveniencia
     */
    success(message, title = 'Éxito') {
        return this.show(message, 'success', title);
    }

    error(message, title = 'Error') {
        return this.show(message, 'error', title, 8000); // Errores duran más
    }

    warning(message, title = 'Advertencia') {
        return this.show(message, 'warning', title, 6000);
    }

    info(message, title = '') {
        return this.show(message, 'info', title);
    }

    /**
     * Notificación de progreso (no se auto-remueve)
     */
    progress(message, title = 'Procesando...') {
        return this.show(message, 'info', title, 0);
    }

    /**
     * Actualizar notificación existente
     */
    update(id, message, type = null, title = null) {
        const notificationData = this.notifications.get(id);
        if (!notificationData) return false;

        const element = notificationData.element;
        
        // Actualizar tipo si se proporciona
        if (type && type !== notificationData.type) {
            element.className = `notification ${type} show`;
            notificationData.type = type;
        }

        // Actualizar contenido
        const titleElement = element.querySelector('.title');
        const messageElement = element.querySelector('.message');

        if (title !== null && titleElement) {
            const icon = this.getIconForType(type || notificationData.type);
            titleElement.innerHTML = `${icon} ${title}`;
        }

        if (messageElement) {
            messageElement.textContent = message;
        }

        return true;
    }

    /**
     * Obtener estadísticas
     */
    getStats() {
        const stats = {
            total: this.notifications.size,
            byType: {}
        };

        this.notifications.forEach((notification) => {
            const type = notification.type;
            stats.byType[type] = (stats.byType[type] || 0) + 1;
        });

        return stats;
    }

    /**
     * Configurar opciones globales
     */
    configure(options) {
        if (options.defaultDuration !== undefined) {
            this.defaultDuration = options.defaultDuration;
        }
        if (options.maxNotifications !== undefined) {
            this.maxNotifications = options.maxNotifications;
        }
    }
}