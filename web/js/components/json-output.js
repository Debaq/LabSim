/**
 * JsonOutputModule - Módulo de Resultado JSON
 * Resumen, visualización, descarga y limpieza de datos
 */

class JsonOutputModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'json-output';
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        const completionStats = this.app.tabManager.getCompletionStats();
        const jsonData = this.app.exportJSON();

        return `
        <div class="form-section">
        <h3 class="section-title">📄 Resultado JSON</h3>
        <p class="section-description">
        Resumen del perfil generado, visualización del JSON y opciones de exportación
        </p>

        <!-- Tabla Resumen -->
        <div class="summary-section">
        <h4 class="section-subtitle">📊 Resumen de Completado</h4>
        ${this.renderSummaryTable()}
        </div>

        <!-- Visualización JSON -->
        <div class="json-section">
        <h4 class="section-subtitle">👁️ Visualización del JSON</h4>
        <div class="json-viewer">
        <pre id="jsonDisplay">${this.formatJSON(jsonData)}</pre>
        </div>
        </div>

        <!-- Acciones -->
        <div class="actions-section">
        <h4 class="section-subtitle">🛠️ Acciones</h4>
        <div class="action-buttons">
        <button class="btn btn-success" id="downloadJsonBtn" ${completionStats.canExport ? '' : 'disabled'}>
        📥 Descargar JSON
        </button>
        <button class="btn btn-warning" id="clearDataBtn">
        🗑️ Limpiar Todo
        </button>
        </div>
        ${!completionStats.canExport ? `
        <div class="alert alert-warning">
        <div class="alert-icon">⚠️</div>
        <div class="alert-content">
        <div class="title">Módulos requeridos incompletos</div>
        <div class="message">
        Completa todos los módulos requeridos para habilitar la descarga del JSON.
        </div>
        </div>
        </div>
        ` : ''}
        </div>
        </div>

        <style>
        .summary-section {
        margin-bottom: 30px;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 8px;
        }

        .summary-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        }

        .summary-table th {
        background: #e9ecef;
        border: 1px solid #dee2e6;
        padding: 10px 12px;
        text-align: left;
        font-weight: 600;
        }

        .summary-table td {
        border: 1px solid #dee2e6;
        padding: 8px 12px;
        }

        .status-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        }

        .status-completed {
        background: #d4edda;
        color: #155724;
        }

        .status-incomplete {
        background: #f8d7da;
        color: #721c24;
        }

        .status-required {
        background: #fff3cd;
        color: #856404;
        }

        .json-section {
        margin-bottom: 30px;
        }

        .json-viewer {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        max-height: 400px;
        overflow-y: auto;
        }

        .json-viewer pre {
        margin: 0;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.4;
        color: #333;
        white-space: pre-wrap;
        word-wrap: break-word;
        }

        .actions-section {
        padding: 20px;
        background: #f8f9fa;
        border-radius: 8px;
        }

        .action-buttons {
        display: flex;
        gap: 15px;
        margin-bottom: 15px;
        }

        .action-buttons .btn {
        flex: 0 0 auto;
        min-width: 150px;
        }
        </style>
        `;
    }

    /**
     * Renderizar tabla resumen
     */
    renderSummaryTable() {
        const modules = this.app.moduleConfig;
        
        let html = `
        <table class="summary-table">
        <thead>
        <tr>
        <th>Módulo</th>
        <th>Estado</th>
        <th>Requerido</th>
        <th>Descripción</th>
        </tr>
        </thead>
        <tbody>
        `;

        modules.forEach(module => {
            const statusClass = module.completed ? 'status-completed' : 'status-incomplete';
            const statusText = module.completed ? '✅ Completado' : '❌ Incompleto';
            const requiredClass = module.required ? 'status-required' : '';
            const requiredText = module.required ? '⚠️ Requerido' : 'Opcional';

            html += `
            <tr>
            <td><strong>${module.name}</strong></td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td><span class="status-badge ${requiredClass}">${requiredText}</span></td>
            <td>${module.description}</td>
            </tr>
            `;
        });

        html += '</tbody></table>';

        // Estadísticas
        const stats = this.app.tabManager.getCompletionStats();
        html += `
        <div style="margin-top: 15px; display: flex; gap: 20px; font-size: 14px;">
        <div><strong>Total:</strong> ${stats.completed}/${stats.total} módulos</div>
        <div><strong>Requeridos:</strong> ${stats.requiredCompleted}/${stats.required}</div>
        <div><strong>Progreso:</strong> ${stats.percentage}%</div>
        </div>
        `;

        return html;
    }

    /**
     * Formatear JSON para visualización
     */
    formatJSON(jsonString) {
        try {
            const parsed = JSON.parse(jsonString);
            return JSON.stringify(parsed, null, 2);
        } catch (error) {
            return jsonString;
        }
    }

    /**
     * Inicializar eventos después de renderizar
     */
    async initEvents() {
        // Botón de descarga
        const downloadBtn = document.getElementById('downloadJsonBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.downloadJSON();
            });
        }

        // Botón de limpiar
        const clearBtn = document.getElementById('clearDataBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.confirmClearData();
            });
        }

        // Actualizar vista cada vez que se carga el módulo
        this.updateDisplay();
    }

    /**
     * Actualizar display del JSON
     */
    updateDisplay() {
        const jsonDisplay = document.getElementById('jsonDisplay');
        if (jsonDisplay) {
            const jsonData = this.app.exportJSON();
            jsonDisplay.textContent = this.formatJSON(jsonData);
        }
    }

    /**
     * Descargar JSON
     */
    downloadJSON() {
        try {
            const jsonData = this.app.exportJSON();
            const blob = new Blob([jsonData], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `labsim_perfil_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.app.notify('JSON descargado exitosamente', 'success');
        } catch (error) {
            this.app.handleError('Error descargando JSON', error);
        }
    }

    /**
     * Confirmar limpieza de datos
     */
    confirmClearData() {
        const confirmed = confirm(
            '⚠️ ¿Estás seguro de que quieres limpiar todos los datos?\n\n' +
            'Esta acción eliminará toda la información ingresada en todos los módulos.\n' +
            'Esta acción no se puede deshacer.'
        );

        if (confirmed) {
            this.clearAllData();
        }
    }

    /**
     * Limpiar todos los datos
     */
    clearAllData() {
        try {
            // Limpiar datos de la aplicación
            this.app.clearData();

            // Ir al primer módulo
            this.app.tabManager.goToTab(0);

            this.app.notify('Todos los datos han sido eliminados', 'info');
        } catch (error) {
            this.app.handleError('Error limpiando datos', error);
        }
    }

    /**
     * Obtener datos del formulario
     */
    getData() {
        // Este módulo no tiene datos propios
        return {};
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        return {
            isValid: true,
            errors: []
        };
    }

    /**
     * Verificar si está completo
     */
    isComplete(data) {
        // Siempre está completo ya que solo muestra información
        return true;
    }
}

// Exponer globalmente
window.JsonOutputModule = JsonOutputModule;