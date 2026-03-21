/**
 * HearingAidsModule - Módulo Principal de Audífonos
 * Orquestador de las 3 secciones: Historial, Campo Libre y Prueba
 */

class HearingAidsModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'hearing-aids';
        
        // Componentes de las secciones
        this.sections = {
            history: null,
            fieldAudio: null,
            trial: null
        };

        // Estado de las secciones
        this.sectionStates = {
            history: 'pending',    // pending, loading, loaded, error
            fieldAudio: 'pending',
            trial: 'pending'
        };
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        return `
            <div class="form-section">
                <h3 class="section-title">🎧 Historia de Audífonos</h3>
                <p class="section-description">
                    Antecedentes de adaptación protésica, audiometría de campo libre y pruebas realizadas
                </p>

                <!-- Navegación por Secciones -->
                <div class="aids-nav">
                    <button class="aids-nav-btn active" data-section="history" id="historyNavBtn">
                        <span class="nav-icon">📋</span>
                        <span class="nav-text">Historial</span>
                    </button>
                    <button class="aids-nav-btn" data-section="fieldAudio" id="fieldAudioNavBtn">
                        <span class="nav-icon">🔊</span>
                        <span class="nav-text">Campo Libre</span>
                    </button>
                    <button class="aids-nav-btn" data-section="trial" id="trialNavBtn">
                        <span class="nav-icon">🧪</span>
                        <span class="nav-text">Prueba</span>
                    </button>
                </div>

                <!-- Contenedor de Secciones -->
                <div class="aids-sections-container">
                    <!-- Sección 1: Historial -->
                    <div class="aids-section active" id="historySection">
                        <div class="loading-placeholder">
                            <div class="loading-spinner"></div>
                            <p>Cargando historial de audífonos...</p>
                        </div>
                    </div>

                    <!-- Sección 2: Campo Libre -->
                    <div class="aids-section" id="fieldAudioSection">
                        <div class="loading-placeholder">
                            <div class="loading-spinner"></div>
                            <p>Cargando audiometría de campo libre...</p>
                        </div>
                    </div>

                    <!-- Sección 3: Prueba -->
                    <div class="aids-section" id="trialSection">
                        <div class="loading-placeholder">
                            <div class="loading-spinner"></div>
                            <p>Cargando datos de prueba...</p>
                        </div>
                    </div>
                </div>

                <!-- Resumen de Estado -->
                <div class="aids-status">
                    <div class="status-item" id="historyStatus">
                        <span class="status-icon">⏳</span>
                        <span class="status-text">Historial: Pendiente</span>
                    </div>
                    <div class="status-item" id="fieldAudioStatus">
                        <span class="status-icon">⏳</span>
                        <span class="status-text">Campo Libre: Pendiente</span>
                    </div>
                    <div class="status-item" id="trialStatus">
                        <span class="status-icon">⏳</span>
                        <span class="status-text">Prueba: Pendiente</span>
                    </div>
                </div>
            </div>

            <style>
            .aids-nav {
                display: flex;
                gap: 10px;
                margin-bottom: 25px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }

            .aids-nav-btn {
                flex: 1;
                padding: 12px 15px;
                border: 2px solid #dee2e6;
                background: white;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 5px;
                font-size: 13px;
            }

            .aids-nav-btn:hover {
                border-color: #2a5298;
                background: rgba(42, 82, 152, 0.05);
            }

            .aids-nav-btn.active {
                border-color: #2a5298;
                background: #2a5298;
                color: white;
            }

            .nav-icon {
                font-size: 18px;
            }

            .nav-text {
                font-weight: 500;
            }

            .aids-sections-container {
                min-height: 400px;
                position: relative;
            }

            .aids-section {
                display: none;
                animation: fadeIn 0.3s ease-in;
            }

            .aids-section.active {
                display: block;
            }

            .loading-placeholder {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 60px 20px;
                color: #666;
            }

            .loading-placeholder .loading-spinner {
                width: 30px;
                height: 30px;
                border: 3px solid #e9ecef;
                border-left: 3px solid #2a5298;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-bottom: 15px;
            }

            .aids-status {
                display: flex;
                gap: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 6px;
                margin-top: 20px;
                font-size: 13px;
            }

            .status-item {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .status-icon {
                font-size: 14px;
            }

            @media (max-width: 768px) {
                .aids-nav {
                    flex-direction: column;
                    gap: 8px;
                }

                .aids-nav-btn {
                    flex-direction: row;
                    justify-content: center;
                    padding: 10px 15px;
                }

                .aids-status {
                    flex-direction: column;
                    gap: 10px;
                }
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            </style>
        `;
    }

    /**
     * Inicializar eventos después de renderizar
     */
    async initEvents() {
        // Configurar navegación entre secciones
        this.setupSectionNavigation();

        // Cargar sección inicial (historial)
        await this.loadSection('history');
    }

    /**
     * Configurar navegación entre secciones
     */
    setupSectionNavigation() {
        const navButtons = document.querySelectorAll('.aids-nav-btn');
        
        navButtons.forEach(button => {
            button.addEventListener('click', async (e) => {
                const sectionName = e.currentTarget.dataset.section;
                await this.switchToSection(sectionName);
            });
        });
    }

    /**
     * Cambiar a una sección específica
     */
    async switchToSection(sectionName) {
        // Actualizar navegación visual
        this.updateNavigation(sectionName);

        // Cargar sección si no está cargada
        if (this.sectionStates[sectionName] === 'pending') {
            await this.loadSection(sectionName);
        }

        // Mostrar sección
        this.showSection(sectionName);
    }

    /**
     * Actualizar navegación visual
     */
    updateNavigation(activeSectionName) {
        const navButtons = document.querySelectorAll('.aids-nav-btn');
        const sections = document.querySelectorAll('.aids-section');

        // Actualizar botones
        navButtons.forEach(btn => {
            if (btn.dataset.section === activeSectionName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Actualizar secciones
        sections.forEach(section => {
            section.classList.remove('active');
        });
    }

    /**
     * Mostrar sección
     */
    showSection(sectionName) {
        const sectionElement = document.getElementById(`${sectionName}Section`);
        if (sectionElement) {
            sectionElement.classList.add('active');
        }
    }

    /**
     * Cargar una sección específica
     */
    async loadSection(sectionName) {
        try {
            this.sectionStates[sectionName] = 'loading';
            this.updateSectionStatus(sectionName, 'loading', 'Cargando...');

            // Mapeo de archivos
            const sectionFiles = {
                history: 'aids/hearing-aids-history.js',
                fieldAudio: 'aids/hearing-aids-field-audio.js',
                trial: 'aids/hearing-aids-trial.js'
            };

            const fileName = sectionFiles[sectionName];
            if (!fileName) {
                throw new Error(`Sección ${sectionName} no reconocida`);
            }

            // Cargar script de la sección
            await this.app.loadScript(`js/components/${fileName}`);

            // Crear instancia de la sección
            const sectionInstance = this.createSectionInstance(sectionName);
            this.sections[sectionName] = sectionInstance;

            // Obtener datos existentes para esta sección
            const existingData = this.getSectionData(sectionName);

            // Renderizar sección
            const sectionContent = await sectionInstance.render(existingData);
            const sectionElement = document.getElementById(`${sectionName}Section`);
            
            if (sectionElement) {
                sectionElement.innerHTML = sectionContent;
                
                // Inicializar eventos de la sección
                if (typeof sectionInstance.initEvents === 'function') {
                    await sectionInstance.initEvents();
                }
            }

            this.sectionStates[sectionName] = 'loaded';
            this.updateSectionStatus(sectionName, 'loaded', 'Completado');

        } catch (error) {
            this.sectionStates[sectionName] = 'error';
            this.updateSectionStatus(sectionName, 'error', 'Error');
            this.handleSectionError(sectionName, error);
        }
    }

    /**
     * Crear instancia de sección
     */
    createSectionInstance(sectionName) {
        const classNames = {
            history: 'HearingAidsHistorySection',
            fieldAudio: 'HearingAidsFieldAudioSection',
            trial: 'HearingAidsTrialSection'
        };

        const className = classNames[sectionName];
        if (!className || typeof window[className] !== 'function') {
            throw new Error(`Clase ${className} no encontrada para sección ${sectionName}`);
        }

        return new window[className](this.app, this);
    }

    /**
     * Obtener datos existentes de una sección
     */
    getSectionData(sectionName) {
        const allData = this.app.getModuleData(this.moduleId);
        return allData[sectionName] || {};
    }

    /**
     * Actualizar estado visual de sección
     */
    updateSectionStatus(sectionName, status, message) {
        const statusElement = document.getElementById(`${sectionName}Status`);
        if (!statusElement) return;

        const iconElement = statusElement.querySelector('.status-icon');
        const textElement = statusElement.querySelector('.status-text');

        const statusConfig = {
            pending: { icon: '⏳', color: '#6c757d' },
            loading: { icon: '🔄', color: '#17a2b8' },
            loaded: { icon: '✅', color: '#28a745' },
            error: { icon: '❌', color: '#dc3545' }
        };

        const config = statusConfig[status] || statusConfig.pending;
        
        if (iconElement) iconElement.textContent = config.icon;
        if (textElement) {
            textElement.textContent = `${this.getSectionDisplayName(sectionName)}: ${message}`;
            textElement.style.color = config.color;
        }
    }

    /**
     * Obtener nombre de visualización de sección
     */
    getSectionDisplayName(sectionName) {
        const names = {
            history: 'Historial',
            fieldAudio: 'Campo Libre',
            trial: 'Prueba'
        };
        return names[sectionName] || sectionName;
    }

    /**
     * Manejar error de sección
     */
    handleSectionError(sectionName, error) {
        const sectionElement = document.getElementById(`${sectionName}Section`);
        if (sectionElement) {
            sectionElement.innerHTML = `
                <div class="form-section">
                    <div class="alert alert-error">
                        <div class="alert-icon">❌</div>
                        <div class="alert-content">
                            <div class="title">Error cargando sección</div>
                            <div class="message">
                                No se pudo cargar la sección "${this.getSectionDisplayName(sectionName)}". 
                                ${error.message}
                            </div>
                        </div>
                    </div>
                    <div class="text-center mt-4">
                        <button class="btn btn-primary" onclick="labSimApp.modules.get('${this.moduleId}').loadSection('${sectionName}')">
                            🔄 Reintentar
                        </button>
                    </div>
                </div>
            `;
        }

        this.app.handleError(`Error en sección ${sectionName}`, error);
    }

    /**
     * Obtener datos del formulario
     */
    getData() {
        const data = {};

        // Recopilar datos de todas las secciones cargadas
        Object.keys(this.sections).forEach(sectionName => {
            const section = this.sections[sectionName];
            if (section && typeof section.getData === 'function') {
                data[sectionName] = section.getData();
            }
        });

        return data;
    }

    /**
     * Actualizar datos de una sección específica
     */
    updateSectionData(sectionName, sectionData) {
        const currentData = this.app.getModuleData(this.moduleId);
        const updatedData = {
            ...currentData,
            [sectionName]: sectionData
        };
        
        this.app.updateModuleData(this.moduleId, updatedData);
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        const errors = [];

        // Validar cada sección que tenga método de validación
        Object.keys(this.sections).forEach(sectionName => {
            const section = this.sections[sectionName];
            const sectionData = data[sectionName];
            
            if (section && typeof section.validate === 'function' && sectionData) {
                const sectionValidation = section.validate(sectionData);
                if (!sectionValidation.isValid) {
                    errors.push(...sectionValidation.errors.map(err => `${sectionName}: ${err}`));
                }
            }
        });

        return {
            isValid: errors.length === 0,
            errors
        };
    }

    /**
     * Verificar si está completo
     */
    isComplete(data) {
        if (!data) return false;

        // Al menos la sección de historial debe tener datos
        const hasHistory = data.history && Object.keys(data.history).length > 0;
        
        // O al menos datos de campo libre
        const hasFieldAudio = data.fieldAudio && Object.keys(data.fieldAudio).length > 0;

        return hasHistory || hasFieldAudio;
    }

    /**
     * Exportar datos para usar en otras secciones
     */
    exportSectionData(sectionName) {
        const section = this.sections[sectionName];
        if (section && typeof section.getData === 'function') {
            return section.getData();
        }
        return {};
    }
}

// Exponer globalmente
window.HearingAidsModule = HearingAidsModule;