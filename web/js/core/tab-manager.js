/**
 * TabManager - Gestor del sistema de tabs y navegación
 */

class TabManager {
    constructor(app) {
        this.app = app;
        this.currentTabIndex = 0;
        this.tabs = [];
        this.direction = 'forward'; // forward | backward
        
        this.elements = {
            tabsHeader: null,
            tabsContent: null,
            prevBtn: null,
            nextBtn: null,
            progressFill: null,
            progressText: null,
            currentTabName: null
        };
    }

    /**
     * Inicializar el tab manager
     */
    init() {
        this.cacheElements();
        this.setupEventListeners();
        this.renderTabs();
        this.updateProgress();
        this.updateNavigation();
    }

    /**
     * Cachear elementos del DOM
     */
    cacheElements() {
        this.elements.tabsHeader = document.getElementById('tabsHeader');
        this.elements.tabsContent = document.getElementById('tabsContent');
        this.elements.prevBtn = document.getElementById('prevBtn');
        this.elements.nextBtn = document.getElementById('nextBtn');
        this.elements.progressFill = document.getElementById('progressFill');
        this.elements.progressText = document.getElementById('progressText');
        this.elements.currentTabName = document.getElementById('currentTabName');
    }

    /**
     * Configurar event listeners
     */
    setupEventListeners() {
        // Botones de navegación
        this.elements.prevBtn?.addEventListener('click', () => this.previousTab());
        this.elements.nextBtn?.addEventListener('click', () => this.nextTab());
    }

    /**
     * Renderizar tabs en el header
     */
    renderTabs() {
        if (!this.elements.tabsHeader) return;

        this.elements.tabsHeader.innerHTML = '';
        
        this.app.moduleConfig.forEach((moduleConfig, index) => {
            const tabButton = this.createTabButton(moduleConfig, index);
            this.elements.tabsHeader.appendChild(tabButton);
        });
    }

    /**
     * Crear botón de tab
     */
    createTabButton(moduleConfig, index) {
        const button = document.createElement('button');
        button.className = 'tab-button';
        button.dataset.moduleId = moduleConfig.id;
        button.dataset.index = index;
        
        // Contenido del botón
        button.innerHTML = `
            <span class="tab-icon">${moduleConfig.icon}</span>
            <span class="tab-text">${moduleConfig.name}</span>
        `;
        
        // Event listener
        button.addEventListener('click', () => this.goToTab(index));
        
        // Tooltip
        button.title = moduleConfig.description;
        
        return button;
    }

    /**
     * Ir a un tab específico
     */
    async goToTab(index) {
        if (index === this.currentTabIndex) return;
        
        // Validar índice
        if (index < 0 || index >= this.app.moduleConfig.length) {
            return;
        }

        // Determinar dirección
        this.direction = index > this.currentTabIndex ? 'forward' : 'backward';
        
        try {
            // Guardar datos del tab actual antes de cambiar
            await this.saveCurrentTabData();
            
            // Cambiar tab
            const previousIndex = this.currentTabIndex;
            this.currentTabIndex = index;
            
            // Cargar nuevo módulo
            const moduleConfig = this.app.moduleConfig[index];
            await this.loadModule(moduleConfig.id);
            
            // Actualizar UI
            this.updateTabStates(previousIndex, index);
            this.updateProgress();
            this.updateNavigation();
            
        } catch (error) {
            // Revertir en caso de error
            this.currentTabIndex = index > this.currentTabIndex ? 
                this.currentTabIndex : this.currentTabIndex;
            this.app.handleError('Error cambiando de tab', error);
        }
    }

    /**
     * Tab siguiente
     */
    async nextTab() {
        if (this.currentTabIndex < this.app.moduleConfig.length - 1) {
            await this.goToTab(this.currentTabIndex + 1);
        }
    }

    /**
     * Tab anterior
     */
    async previousTab() {
        if (this.currentTabIndex > 0) {
            await this.goToTab(this.currentTabIndex - 1);
        }
    }

    /**
     * Cargar módulo
     */
    async loadModule(moduleId) {
        try {
            // Cargar el módulo
            const module = await this.app.loadModule(moduleId);
            
            // Renderizar contenido
            await this.renderModuleContent(module, moduleId);
            
            // Aplicar animación
            this.applyTransitionAnimation();
            
        } catch (error) {
            this.app.handleError(`Error cargando módulo ${moduleId}`, error);
            this.renderErrorContent(moduleId);
        }
    }

    /**
     * Renderizar contenido del módulo
     */
    async renderModuleContent(module, moduleId) {
        if (!this.elements.tabsContent) return;

        // Obtener datos existentes
        const existingData = this.app.getModuleData(moduleId);
        
        // Renderizar contenido
        const content = await module.render(existingData);
        
        // Actualizar DOM
        this.elements.tabsContent.innerHTML = content;
        
        // Inicializar eventos del módulo
        if (typeof module.initEvents === 'function') {
            module.initEvents();
        }
        
        // Inicializar validaciones
        if (typeof module.initValidation === 'function') {
            module.initValidation();
        }
    }

    /**
     * Renderizar contenido de error
     */
    renderErrorContent(moduleId) {
        if (!this.elements.tabsContent) return;
        
        const moduleConfig = this.app.getModuleConfig(moduleId);
        
        this.elements.tabsContent.innerHTML = `
            <div class="form-section">
                <div class="alert alert-error">
                    <div class="alert-icon">❌</div>
                    <div class="alert-content">
                        <div class="title">Error cargando módulo</div>
                        <div class="message">
                            No se pudo cargar el módulo "${moduleConfig?.name || moduleId}". 
                            Por favor, inténtalo de nuevo.
                        </div>
                    </div>
                </div>
                <div class="text-center mt-4">
                    <button class="btn btn-primary" onclick="labSimApp.tabManager.loadModule('${moduleId}')">
                        🔄 Reintentar
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Aplicar animación de transición
     */
    applyTransitionAnimation() {
        if (!this.elements.tabsContent) return;
        
        const animationClass = this.direction === 'forward' ? 'slide-in-right' : 'slide-in-left';
        
        this.elements.tabsContent.classList.remove('slide-in-right', 'slide-in-left', 'fade-in');
        this.elements.tabsContent.classList.add(animationClass);
        
        // Remover clase después de la animación
        setTimeout(() => {
            this.elements.tabsContent.classList.remove(animationClass);
        }, 300);
    }

    /**
     * Guardar datos del tab actual
     */
    async saveCurrentTabData() {
        const currentModuleId = this.app.moduleConfig[this.currentTabIndex]?.id;
        if (!currentModuleId) return;

        const currentModule = this.app.modules.get(currentModuleId);
        if (currentModule && typeof currentModule.getData === 'function') {
            const data = currentModule.getData();
            this.app.updateModuleData(currentModuleId, data);
        }
    }

    /**
     * Actualizar estados de los tabs
     */
    updateTabStates(previousIndex, currentIndex) {
        const tabButtons = this.elements.tabsHeader?.querySelectorAll('.tab-button');
        if (!tabButtons) return;

        // Remover estado activo del tab anterior
        if (previousIndex >= 0 && tabButtons[previousIndex]) {
            tabButtons[previousIndex].classList.remove('active');
        }

        // Agregar estado activo al tab actual
        if (tabButtons[currentIndex]) {
            tabButtons[currentIndex].classList.add('active');
        }
    }

    /**
     * Actualizar estado de completado de un tab
     */
    updateTabState(moduleId, completed) {
        const tabButton = this.elements.tabsHeader?.querySelector(`[data-module-id="${moduleId}"]`);
        if (tabButton) {
            if (completed) {
                tabButton.classList.add('completed');
            } else {
                tabButton.classList.remove('completed');
            }
        }
    }

    /**
     * Actualizar barra de progreso
     */
    updateProgress() {
        const total = this.app.moduleConfig.length;
        const current = this.currentTabIndex + 1;
        const percentage = (current / total) * 100;

        // Actualizar barra visual
        if (this.elements.progressFill) {
            this.elements.progressFill.style.width = `${percentage}%`;
        }

        // Actualizar texto
        if (this.elements.progressText) {
            this.elements.progressText.textContent = `Paso ${current} de ${total}`;
        }
    }

    /**
     * Actualizar navegación
     */
    updateNavigation() {
        const currentModule = this.app.moduleConfig[this.currentTabIndex];
        
        // Actualizar nombre del tab actual
        if (this.elements.currentTabName && currentModule) {
            this.elements.currentTabName.textContent = currentModule.name;
        }

        // Habilitar/deshabilitar botones
        if (this.elements.prevBtn) {
            this.elements.prevBtn.disabled = this.currentTabIndex === 0;
        }

        if (this.elements.nextBtn) {
            const isLastTab = this.currentTabIndex === this.app.moduleConfig.length - 1;
            this.elements.nextBtn.disabled = false; // Siempre permitir navegar
            this.elements.nextBtn.textContent = isLastTab ? 'Finalizar →' : 'Siguiente →';
        }
    }

    /**
     * Verificar si se puede avanzar al siguiente tab
     */
    canAdvanceToNext() {
        const currentModuleId = this.app.moduleConfig[this.currentTabIndex]?.id;
        const currentModule = this.app.modules.get(currentModuleId);
        
        if (currentModule && typeof currentModule.canAdvance === 'function') {
            return currentModule.canAdvance();
        }
        
        return true; // Por defecto, permitir avance
    }

    /**
     * Ir al primer tab incompleto
     */
    goToFirstIncomplete() {
        const incompleteIndex = this.app.moduleConfig.findIndex(m => !m.completed && m.required);
        if (incompleteIndex !== -1) {
            this.goToTab(incompleteIndex);
        }
    }

    /**
     * Obtener índice del tab actual
     */
    getCurrentTabIndex() {
        return this.currentTabIndex;
    }

    /**
     * Obtener ID del módulo actual
     */
    getCurrentModuleId() {
        return this.app.moduleConfig[this.currentTabIndex]?.id;
    }

    /**
     * Verificar si es el último tab
     */
    isLastTab() {
        return this.currentTabIndex === this.app.moduleConfig.length - 1;
    }

    /**
     * Verificar si es el primer tab
     */
    isFirstTab() {
        return this.currentTabIndex === 0;
    }

    /**
     * Obtener estadísticas de completado
     */
    getCompletionStats() {
        const total = this.app.moduleConfig.length;
        const completed = this.app.moduleConfig.filter(m => m.completed).length;
        const required = this.app.moduleConfig.filter(m => m.required).length;
        const requiredCompleted = this.app.moduleConfig.filter(m => m.required && m.completed).length;

        return {
            total,
            completed,
            required,
            requiredCompleted,
            percentage: Math.round((completed / total) * 100),
            canExport: requiredCompleted === required
        };
    }
}