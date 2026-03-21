/**
 * LabSim 3.0 - Aplicación Principal
 * Punto de entrada y configuración global
 */

class LabSimApp {
    constructor() {
        this.version = '3.0.0';
        this.modules = new Map();
        this.currentData = {};
        this.config = {
            debug: true,
            autoSave: true,
            validateOnChange: true,
            autoSaveInterval: 30000 // 30 segundos
        };

        this.autoSaveTimer = null;
        this.init();
    }

    /**
     * Inicialización de la aplicación
     */
    async init() {
        try {
            this.log('🚀 Iniciando LabSim 3.0...');

            // Mostrar loading
            this.showLoading('Inicializando aplicación...');

            // Inicializar managers
            await this.initializeManagers();

            // Configurar módulos disponibles
            await this.setupModules();

            // Cargar datos guardados
            this.loadSavedData();

            // Inicializar sistema de tabs
            this.tabManager.init();

            // Configurar eventos globales
            this.setupGlobalEvents();

            // Cargar módulo inicial
            await this.loadInitialModule();

            // Iniciar auto-guardado
            this.startAutoSave();

            this.hideLoading();
            this.notify('Aplicación inicializada correctamente', 'success');
            this.log('✅ LabSim 3.0 iniciado correctamente');

        } catch (error) {
            this.hideLoading();
            this.handleError('Error al inicializar la aplicación', error);
        }
    }

    /**
     * Inicializar managers del sistema
     */
    async initializeManagers() {
        // Tab Manager
        this.tabManager = new TabManager(this);

        // Notification Manager
        this.notificationManager = new NotificationManager();

        // Validation Manager (se cargará cuando sea necesario)
        this.validationManager = null;
    }

    /**
     * Configurar módulos disponibles
     */
    async setupModules() {
        // Configuración completa de módulos
        const allModules = [
            {
                id: 'agenda',
                name: 'Agenda',
                icon: '📅',
                description: 'Gestión de pacientes y agendas de atención',
                component: 'agenda.js',
                required: false,
                completed: false
            },
            {
                id: 'patient-info',
                name: 'Información Básica',
                icon: '👤',
                description: 'Datos demográficos y perfil del paciente',
                component: 'patient-info.js',
                required: true,
                completed: false
            },
            {
                id: 'anamnesis',
                name: 'Anamnesis',
                icon: '📋',
                description: 'Historia clínica y antecedentes',
                component: 'anamnesis.js',
                required: true,
                completed: false
            },
            {
                id: 'audiometry',
                name: 'Audiometría',
                icon: '🎧',
                description: 'Umbrales auditivos y LDL',
                component: 'audiometry.js',
                required: true,
                completed: false
            },
            {
                id: 'logoaudiometry',
                name: 'Logoaudiometría',
                icon: '🗣️',
                description: 'SDT, SRT y discriminación',
                component: 'logoaudiometry.js',
                required: false,
                completed: false
            },
            {
                id: 'supraliminal',
                name: 'Pruebas Supraliminares',
                icon: '📊',
                description: 'Reclutamiento y deterioro',
                component: 'supraliminal.js',
                required: false,
                completed: false
            },
            {
                id: 'impedance',
                name: 'Impedanciometría',
                icon: '📈',
                description: 'Timpanograma y reflejos',
                component: 'impedance.js',
                required: false,
                completed: false
            },
            {
                id: 'hearing-aids',
                name: 'Audífonos',
                icon: '🎧',
                description: 'Historia de audífonos, campo libre y pruebas',
                component: 'hearing-aids.js',
                required: false,
                completed: false
            },
            {
                id: 'oae',
                name: 'Emisiones OAE',
                icon: '🌊',
                description: 'Transientes y productos de distorsión',
                component: 'oae.js',
                required: false,
                completed: false
            },
            {
                id: 'abr',
                name: 'Potenciales ABR',
                icon: '⚡',
                description: 'Ondas I, III, V y latencias',
                component: 'abr.js',
                required: false,
                completed: false
            },
            {
                id: 'electrocochleo',
                name: 'Electrocoleografía',
                icon: '🔬',
                description: 'Potenciales SP y AP',
                component: 'electrocochleo.js',
                required: false,
                completed: false
            },
            {
                id: 'json-output',
                name: 'Resultado JSON',
                icon: '📄',
                description: 'Perfil generado y exportación',
                component: 'json-output.js',
                required: true,
                completed: false
            }
        ];

        // Detectar qué módulos realmente existen
        this.moduleConfig = [];

        for (const moduleInfo of allModules) {
            if (await this.checkModuleExists(moduleInfo.component)) {
                this.moduleConfig.push(moduleInfo);
                this.log(`✅ Módulo disponible: ${moduleInfo.id}`);
            } else {
                this.log(`⚠️ Módulo no encontrado: ${moduleInfo.id} (${moduleInfo.component})`);
            }
        }

        // Si no hay módulos, mostrar mensaje de placeholder
        if (this.moduleConfig.length === 0) {
            this.moduleConfig = [{
                id: 'placeholder',
                name: 'Sistema en Desarrollo',
                icon: '🚧',
                description: 'Agrega módulos en js/components/ para comenzar',
                component: null,
                required: false,
                completed: false
            }];
        }

        this.log(`📦 Módulos configurados: ${this.moduleConfig.length}`);
    }

    /**
     * Verificar si un módulo existe
     */
    async checkModuleExists(componentFile) {
        if (!componentFile) return false;

        try {
            const response = await fetch(`js/components/${componentFile}`, { method: 'HEAD' });
            return response.ok;
        } catch {
            return false;
        }
    }

    /**
     * Configurar eventos globales
     */
    setupGlobalEvents() {
        // Navegación con teclado
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey) {
                if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    this.tabManager.nextTab();
                } else if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    this.tabManager.previousTab();
                }
            }
        });

        // Prevenir pérdida de datos
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges()) {
                e.preventDefault();
                e.returnValue = 'Tienes cambios sin guardar. ¿Estás seguro de que quieres salir?';
                return e.returnValue;
            }
        });

        // Auto-guardado al cambiar de ventana
        window.addEventListener('blur', () => {
            this.saveCurrentData();
        });
    }

    /**
     * Cargar módulo inicial
     */
    async loadInitialModule() {
        if (this.moduleConfig.length === 0) return;

        const firstModule = this.moduleConfig[0];

        // Si es el placeholder, mostrar mensaje especial
        if (firstModule.id === 'placeholder') {
            await this.loadPlaceholderContent();
        } else {
            await this.tabManager.loadModule(firstModule.id);
        }
    }

    /**
     * Cargar contenido placeholder
     */
    async loadPlaceholderContent() {
        const content = document.getElementById('tabsContent');
        if (content) {
            content.innerHTML = `
            <div class="form-section">
            <div class="text-center">
            <h3 class="section-title">🚧 Sistema en Desarrollo</h3>
            <p class="section-description">
            Para comenzar a usar LabSim 3.0, agrega módulos en la carpeta:<br>
            <code>js/components/</code>
            </p>
            <div class="alert alert-info">
            <div class="alert-icon">💡</div>
            <div class="alert-content">
            <div class="title">Empezar es fácil</div>
            <div class="message">
            Crea tu primer módulo copiando el template de la documentación.
            El sistema detectará automáticamente los módulos disponibles.
            </div>
            </div>
            </div>
            </div>
            </div>
            `;
        }
    }

    /**
     * Cargar módulo dinámicamente
     */
    async loadModule(moduleId) {
        // Si es placeholder, cargar contenido especial
        if (moduleId === 'placeholder') {
            await this.loadPlaceholderContent();
            return { render: () => '', initEvents: () => {}, getData: () => ({}) };
        }

        if (this.modules.has(moduleId)) {
            return this.modules.get(moduleId);
        }

        const moduleConfig = this.getModuleConfig(moduleId);
        if (!moduleConfig) {
            throw new Error(`Módulo ${moduleId} no encontrado en la configuración`);
        }

        try {
            this.log(`Cargando módulo: ${moduleId}`);

            // Cargar script del módulo
            await this.loadScript(`js/components/${moduleConfig.component}`);

            // Crear instancia del módulo
            const ModuleClass = this.getModuleClass(moduleId);
            const moduleInstance = new ModuleClass(this);

            // Almacenar módulo
            this.modules.set(moduleId, moduleInstance);

            this.log(`✅ Módulo ${moduleId} cargado correctamente`);
            return moduleInstance;

        } catch (error) {
            this.handleError(`Error cargando módulo ${moduleId}`, error);
            throw error;
        }
    }

    /**
     * Cargar script dinámicamente
     */
    loadScript(src) {
        return new Promise((resolve, reject) => {
            // Verificar si ya está cargado
            if (document.querySelector(`script[src="${src}"]`)) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = () => reject(new Error(`Error cargando script: ${src}`));
            document.head.appendChild(script);
        });
    }

    /**
     * Obtener clase del módulo basada en el ID
     */
    getModuleClass(moduleId) {
        const className = moduleId.split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join('') + 'Module';

        if (typeof window[className] !== 'function') {
            throw new Error(`Clase ${className} no encontrada para el módulo ${moduleId}`);
        }

        return window[className];
    }

    /**
     * Obtener configuración de módulo
     */
    getModuleConfig(moduleId) {
        return this.moduleConfig.find(m => m.id === moduleId);
    }

    /**
     * Obtener datos de un módulo
     */
    getModuleData(moduleId) {
        return this.currentData[moduleId] || {};
    }

    /**
     * Actualizar datos de un módulo
     */
    updateModuleData(moduleId, data) {
        this.currentData[moduleId] = { ...this.currentData[moduleId], ...data };

        // Marcar como completado si tiene datos válidos
        const moduleConfig = this.getModuleConfig(moduleId);
        if (moduleConfig) {
            const module = this.modules.get(moduleId);
            if (module && typeof module.isComplete === 'function') {
                moduleConfig.completed = module.isComplete(data);
            } else {
                moduleConfig.completed = data && Object.keys(data).length > 0;
            }

            // Actualizar estado visual del tab
            this.tabManager.updateTabState(moduleId, moduleConfig.completed);
        }

        this.log(`Datos actualizados para módulo: ${moduleId}`, data);
    }

    /**
     * Validar datos de un módulo
     */
    validateModuleData(moduleId, data) {
        const module = this.modules.get(moduleId);
        if (module && typeof module.validate === 'function') {
            return module.validate(data);
        }

        return { isValid: true, errors: [] };
    }

    /**
     * Exportar datos como JSON
     */
    exportJSON() {
        const exportData = {
            metadata: {
                schema_version: "1.0",
                created_date: new Date().toISOString().split('T')[0],
                generator_version: this.version,
                export_timestamp: new Date().toISOString()
            },
            ...this.currentData
        };

        return JSON.stringify(exportData, null, 2);
    }

    /**
     * Verificar si se puede exportar
     */
    canExport() {
        const requiredModules = this.moduleConfig.filter(m => m.required);
        return requiredModules.every(m => m.completed);
    }

    /**
     * Importar datos desde JSON
     */
    importJSON(jsonData) {
        try {
            const data = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData;

            // Validar estructura básica
            if (!data.metadata || !data.metadata.schema_version) {
                throw new Error('Formato de datos inválido');
            }

            // Cargar datos
            Object.keys(data).forEach(key => {
                if (key !== 'metadata') {
                    this.currentData[key] = data[key];
                }
            });

            // Actualizar estados de completado
            this.updateModuleCompletionStates();

            this.notify('Datos importados correctamente', 'success');
            this.log('✅ Datos importados:', data);

        } catch (error) {
            this.handleError('Error importando datos', error);
        }
    }

    /**
     * Actualizar estados de completado de módulos
     */
    updateModuleCompletionStates() {
        this.moduleConfig.forEach(moduleConfig => {
            const data = this.getModuleData(moduleConfig.id);
            const module = this.modules.get(moduleConfig.id);

            if (module && typeof module.isComplete === 'function') {
                moduleConfig.completed = module.isComplete(data);
            } else {
                moduleConfig.completed = data && Object.keys(data).length > 0;
            }

            this.tabManager.updateTabState(moduleConfig.id, moduleConfig.completed);
        });
    }

    /**
     * Auto-guardado
     */
    startAutoSave() {
        if (!this.config.autoSave) return;

        this.autoSaveTimer = setInterval(() => {
            this.saveCurrentData();
        }, this.config.autoSaveInterval);

        this.log('🔄 Auto-guardado iniciado');
    }

    /**
     * Detener auto-guardado
     */
    stopAutoSave() {
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
            this.autoSaveTimer = null;
            this.log('⏹️ Auto-guardado detenido');
        }
    }

    /**
     * Guardar datos actuales
     */
    saveCurrentData() {
        try {
            // Obtener datos del módulo actual
            const currentModuleId = this.tabManager.getCurrentModuleId();
            if (currentModuleId) {
                const currentModule = this.modules.get(currentModuleId);
                if (currentModule && typeof currentModule.getData === 'function') {
                    const data = currentModule.getData();
                    this.updateModuleData(currentModuleId, data);
                }
            }

            // Guardar en localStorage
            localStorage.setItem('labsim_data', JSON.stringify(this.currentData));
            localStorage.setItem('labsim_timestamp', Date.now().toString());

            this.log('💾 Datos guardados automáticamente');

        } catch (error) {
            this.handleError('Error guardando datos', error);
        }
    }

    /**
     * Cargar datos guardados
     */
    loadSavedData() {
        try {
            const savedData = localStorage.getItem('labsim_data');
            if (savedData) {
                this.currentData = JSON.parse(savedData);

                const timestamp = localStorage.getItem('labsim_timestamp');
                if (timestamp) {
                    const saveDate = new Date(parseInt(timestamp));
                    this.notify(`Datos cargados desde ${saveDate.toLocaleString()}`, 'info');
                }

                this.log('📂 Datos cargados desde localStorage:', this.currentData);
            }
        } catch (error) {
            this.handleError('Error cargando datos guardados', error);
        }
    }

    /**
     * Verificar si hay cambios sin guardar
     */
    hasUnsavedChanges() {
        try {
            const savedData = localStorage.getItem('labsim_data');
            const currentDataStr = JSON.stringify(this.currentData);
            return savedData !== currentDataStr;
        } catch {
            return false;
        }
    }

    /**
     * Limpiar datos
     */
    clearData() {
        this.currentData = {};
        localStorage.removeItem('labsim_data');
        localStorage.removeItem('labsim_timestamp');

        // Resetear estados de completado
        this.moduleConfig.forEach(m => {
            m.completed = false;
            this.tabManager.updateTabState(m.id, false);
        });

        this.notify('Datos eliminados', 'info');
        this.log('🗑️ Datos limpiados');
    }

    /**
     * Mostrar loading
     */
    showLoading(message = 'Cargando...') {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            const text = overlay.querySelector('p');
            if (text) text.textContent = message;
            overlay.classList.add('show');
        }
    }

    /**
     * Ocultar loading
     */
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('show');
        }
    }

    /**
     * Mostrar notificación
     */
    notify(message, type = 'info', title = '') {
        if (this.notificationManager) {
            return this.notificationManager.show(message, type, title);
        } else {
            console.log(`[${type.toUpperCase()}] ${title}: ${message}`);
        }
    }

    /**
     * Manejar errores
     */
    handleError(message, error) {
        const errorMsg = error ? `${message}: ${error.message}` : message;

        console.error(errorMsg, error);
        this.notify(errorMsg, 'error');

        if (this.config.debug) {
            console.error('Stack trace:', error?.stack);
        }
    }

    /**
     * Log de desarrollo
     */
    log(message, data = null) {
        if (this.config.debug) {
            if (data) {
                console.log(`[LabSim] ${message}`, data);
            } else {
                console.log(`[LabSim] ${message}`);
            }
        }
    }
}

// Inicializar aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.labSimApp = new LabSimApp();
});

// Exponer globalmente para depuración
if (typeof window !== 'undefined') {
    window.LabSimApp = LabSimApp;
}
