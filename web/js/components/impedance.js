/**
 * ImpedanceModule - Módulo de Impedanciometría
 * Timpanometría, reflejos acústicos, función tubaria y deterioro
 */

class ImpedanceModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'impedance';
        this.chartView = null;

        // Opciones para reflejos acústicos
        this.reflexOptions = [
            '', 'N/D', 'Invertido',
            '70', '75', '80', '85', '90', '95', '100',
            '105', '110', '115', '120', '125'
        ];

        // Frecuencias para reflejos
        this.reflexFrequencies = ['500', '1000', '2000', '4000', 'WN'];
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        return `
        <div class="form-section">
        <h3 class="section-title">📈 Impedanciometría</h3>
        <p class="section-description">
        Evaluación de la función del oído medio mediante timpanometría y reflejos acústicos
        </p>

        <!-- Layout Principal: Formularios (40%) + Preview (60%) -->
        <div style="display: flex; gap: 30px;">
        <!-- Panel de Formularios -->
        <div style="flex: 2; min-width: 450px;">

        <!-- Timpanometría -->
        <div class="form-group">
        <h4 class="section-subtitle">Timpanometría</h4>

        <div class="ear-selector">
        <div class="ear-column">
        <div class="ear-title">Oído Derecho</div>

        <div class="form-row">
        <div class="form-col">
        <label for="compliance_od">Compliance Máxima (ml)</label>
        <input type="number"
        id="compliance_od"
        min="0" max="10" step="0.1"
        value="${existingData.timpanometria?.oido_derecho?.compliance_maxima || ''}"
        placeholder="0.0"
        tabindex="1">
        </div>
        <div class="form-col">
        <label for="presion_od">Presión (daPa)</label>
        <input type="number"
        id="presion_od"
        min="-400" max="200" step="5"
        value="${existingData.timpanometria?.oido_derecho?.presion || ''}"
        placeholder="0"
        tabindex="2">
        </div>
        </div>

        <div class="form-row">
        <div class="form-col">
        <label for="volumen_od">Volumen EAC (ml)</label>
        <input type="number"
        id="volumen_od"
        min="0" max="5" step="0.1"
        value="${existingData.timpanometria?.oido_derecho?.volumen_eac || ''}"
        placeholder="0.0"
        tabindex="3">
        </div>
        <div class="form-col">
        <label for="gradiente_od">Gradiente (daPa)</label>
        <input type="number"
        id="gradiente_od"
        min="0" max="300" step="5"
        value="${existingData.timpanometria?.oido_derecho?.gradiente || ''}"
        placeholder="0"
        tabindex="4">
        </div>
        </div>
        </div>

        <div class="ear-column">
        <div class="ear-title">Oído Izquierdo</div>

        <div class="form-row">
        <div class="form-col">
        <label for="compliance_oi">Compliance Máxima (ml)</label>
        <input type="number"
        id="compliance_oi"
        min="0" max="10" step="0.1"
        value="${existingData.timpanometria?.oido_izquierdo?.compliance_maxima || ''}"
        placeholder="0.0"
        tabindex="5">
        </div>
        <div class="form-col">
        <label for="presion_oi">Presión (daPa)</label>
        <input type="number"
        id="presion_oi"
        min="-400" max="200" step="5"
        value="${existingData.timpanometria?.oido_izquierdo?.presion || ''}"
        placeholder="0"
        tabindex="6">
        </div>
        </div>

        <div class="form-row">
        <div class="form-col">
        <label for="volumen_oi">Volumen EAC (ml)</label>
        <input type="number"
        id="volumen_oi"
        min="0" max="5" step="0.1"
        value="${existingData.timpanometria?.oido_izquierdo?.volumen_eac || ''}"
        placeholder="0.0"
        tabindex="7">
        </div>
        <div class="form-col">
        <label for="gradiente_oi">Gradiente (daPa)</label>
        <input type="number"
        id="gradiente_oi"
        min="0" max="300" step="5"
        value="${existingData.timpanometria?.oido_izquierdo?.gradiente || ''}"
        placeholder="0"
        tabindex="8">
        </div>
        </div>
        </div>
        </div>
        </div>

        <!-- Reflejos Acústicos -->
        <div class="form-group">
        <h4 class="section-subtitle">Reflejos Acústicos</h4>
        <p style="font-size: 12px; color: #666; margin-bottom: 15px;">
        Umbrales en dB SPL. WN no aplica para IPSI.
        </p>

        <table class="reflex-table">
        <thead>
        <tr>
        <th rowspan="2">Frecuencia</th>
        <th colspan="2" style="color: #dc3545;">OD</th>
        <th colspan="2" style="color: #007bff;">OI</th>
        </tr>
        <tr>
        <th style="color: #dc3545;">IPSI</th>
        <th style="color: #dc3545;">CONTRA</th>
        <th style="color: #007bff;">IPSI</th>
        <th style="color: #007bff;">CONTRA</th>
        </tr>
        </thead>
        <tbody>
        ${this.renderReflexRows(existingData.reflejos_acusticos)}
        </tbody>
        </table>
        </div>

        <!-- Función Tubaria (Placeholder) -->
        <div class="form-group">
        <h4 class="section-subtitle">Función Tubaria</h4>
        <div class="alert alert-info">
        <div class="alert-icon">🚧</div>
        <div class="alert-content">
        <div class="title">Por Desarrollar</div>
        <div class="message">
        Este apartado se implementará en una versión posterior
        </div>
        </div>
        </div>
        </div>

        <!-- Deterioro del Reflejo (Placeholder) -->
        <div class="form-group">
        <h4 class="section-subtitle">Deterioro del Reflejo</h4>
        <div class="alert alert-info">
        <div class="alert-icon">🚧</div>
        <div class="alert-content">
        <div class="title">Por Desarrollar</div>
        <div class="message">
        Este apartado se implementará en una versión posterior
        </div>
        </div>
        </div>
        </div>

        <!-- Observaciones -->
        <div class="form-group">
        <label for="impedance_observations" class="label-optional">Observaciones</label>
        <textarea id="impedance_observations"
        rows="3"
        placeholder="Comentarios adicionales sobre la impedanciometría...">${existingData.observaciones || ''}</textarea>
        </div>
        </div>

        <!-- Panel de Preview -->
        <div style="flex: 3; min-width: 500px;">
        <h4 class="section-subtitle">📊 Curvas Timpanométricas</h4>
        <div id="timpanogramPreview" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: white;">
        <canvas id="timpanogramCanvas" width="600" height="400" style="width: 100%; height: auto;"></canvas>
        </div>
        <div style="margin-top: 10px; font-size: 12px; color: #666;">
        <span style="color: #dc3545;">● OD (Rojo)</span> &nbsp;&nbsp;
        <span style="color: #007bff;">● OI (Azul)</span>
        </div>

        <!-- Interpretación automática -->
        <div id="timpanogramInterpretation" style="margin-top: 15px;">
        <!-- La interpretación se generará dinámicamente -->
        </div>
        </div>
        </div>
        </div>

        <style>
        .reflex-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            font-size: 13px;
        }

        .reflex-table th {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 6px 8px;
            text-align: center;
            font-weight: 600;
            font-size: 12px;
        }

        .reflex-table td {
            border: 1px solid #dee2e6;
            padding: 4px;
            text-align: center;
        }

        .reflex-table .freq-label {
            background: #f8f9fa;
            font-weight: 500;
            text-align: center;
        }

        .reflex-select {
            width: 70px;
            padding: 2px 4px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            font-size: 11px;
            text-align: center;
        }

        .reflex-select:focus {
            border-color: #2a5298;
            outline: none;
            box-shadow: 0 0 0 2px rgba(42, 82, 152, 0.1);
        }

        .wn-row .ipsi-cell {
            background: #f8f9fa;
            color: #999;
        }

        .wn-row .ipsi-cell select {
            background: #f8f9fa;
            color: #999;
            cursor: not-allowed;
        }

        .interpretation-card {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 12px;
            margin-top: 10px;
        }

        .interpretation-title {
            font-weight: 600;
            color: #2a5298;
            margin-bottom: 8px;
        }

        .interpretation-item {
            margin-bottom: 4px;
            font-size: 13px;
        }
        </style>
        `;
    }

    /**
     * Renderizar filas de reflejos acústicos
     */
    renderReflexRows(reflexData) {
        let html = '';
        let tabIndex = 9;

        this.reflexFrequencies.forEach(freq => {
            const isWN = freq === 'WN';
            const rowClass = isWN ? 'wn-row' : '';

            // Obtener valores existentes
            const odIpsi = reflexData?.oido_derecho?.ipsi?.[freq] || '';
            const odContra = reflexData?.oido_derecho?.contra?.[freq] || '';
            const oiIpsi = reflexData?.oido_izquierdo?.ipsi?.[freq] || '';
            const oiContra = reflexData?.oido_izquierdo?.contra?.[freq] || '';

            html += `
            <tr class="${rowClass}">
            <td class="freq-label">${freq} Hz</td>
            <td class="${isWN ? 'ipsi-cell' : ''}">
            <select class="reflex-select"
            id="reflex_od_ipsi_${freq}"
            ${isWN ? 'disabled' : ''}
            tabindex="${isWN ? '' : tabIndex++}">
            ${this.renderReflexOptions(odIpsi, isWN)}
            </select>
            </td>
            <td>
            <select class="reflex-select"
            id="reflex_od_contra_${freq}"
            tabindex="${tabIndex++}">
            ${this.renderReflexOptions(odContra, false)}
            </select>
            </td>
            <td class="${isWN ? 'ipsi-cell' : ''}">
            <select class="reflex-select"
            id="reflex_oi_ipsi_${freq}"
            ${isWN ? 'disabled' : ''}
            tabindex="${isWN ? '' : tabIndex++}">
            ${this.renderReflexOptions(oiIpsi, isWN)}
            </select>
            </td>
            <td>
            <select class="reflex-select"
            id="reflex_oi_contra_${freq}"
            tabindex="${tabIndex++}">
            ${this.renderReflexOptions(oiContra, false)}
            </select>
            </td>
            </tr>
            `;
        });

        return html;
    }

    /**
     * Renderizar opciones para select de reflejos
     */
    renderReflexOptions(selectedValue, isIpsiWN) {
        let options = '';

        this.reflexOptions.forEach(option => {
            // Para IPSI WN, no mostrar opciones numéricas
            if (isIpsiWN && !isNaN(option) && option !== '') {
                return;
            }

            const selected = option === selectedValue ? 'selected' : '';
            const displayText = option === '' ? '---' : option;
            options += `<option value="${option}" ${selected}>${displayText}</option>`;
        });

        return options;
    }

    /**
     * Inicializar eventos después de renderizar
     */
    async initEvents() {
        // Cargar vista del gráfico
        await this.loadChartView();

        // Auto-save y update preview al cambiar valores
        const inputs = document.querySelectorAll('#tabsContent input, #tabsContent select, #tabsContent textarea');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                this.updateTimpanogramPreview();
                this.updateInterpretation();
                this.app.updateModuleData(this.moduleId, this.getData());
            });

            input.addEventListener('change', () => {
                this.updateTimpanogramPreview();
                this.updateInterpretation();
                this.app.updateModuleData(this.moduleId, this.getData());
            });
        });

        // Validación en tiempo real para inputs numéricos
        const numberInputs = document.querySelectorAll('#tabsContent input[type="number"]');
        numberInputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
        });

        // Renderizar preview inicial
        setTimeout(() => {
            this.updateTimpanogramPreview();
            this.updateInterpretation();
        }, 100);
    }

    /**
     * Cargar componente de vista del gráfico
     */
    async loadChartView() {
        try {
            await this.app.loadScript('js/components/views/timpanogram-charts.js');
            this.chartView = new TimpanogramChartView('timpanogramCanvas');
        } catch (error) {
            console.warn('No se pudo cargar timpanogram-charts.js, usando fallback');
            this.chartView = null;
        }
    }

    /**
     * Validar campo individual
     */
    validateField(input) {
        const value = parseFloat(input.value);
        const min = parseFloat(input.min);
        const max = parseFloat(input.max);

        input.classList.remove('field-error', 'field-success');

        if (input.value === '') {
            return true; // Vacío es válido
        }

        if (isNaN(value) || value < min || value > max) {
            input.classList.add('field-error');
            this.app.notify(`Valor fuera del rango permitido (${min}-${max})`, 'warning');
            return false;
        }

        input.classList.add('field-success');
        return true;
    }

    /**
     * Actualizar preview del timpanograma
     */
    updateTimpanogramPreview() {
        if (this.chartView) {
            // Usar componente de vista especializado
            const data = this.getData();
            this.chartView.render(data);
        } else {
            // Fallback simple si no se cargó el componente
            this.renderSimpleFallback();
        }
    }

    /**
     * Fallback simple si no hay componente de vista
     */
    renderSimpleFallback() {
        const canvas = document.getElementById('timpanogramCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = '#666';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Vista previa no disponible', canvas.width/2, canvas.height/2);
        ctx.fillText('(timpanogram-charts.js no cargado)', canvas.width/2, canvas.height/2 + 20);
    }

    /**
     * Actualizar interpretación automática
     */
    updateInterpretation() {
        const interpretationDiv = document.getElementById('timpanogramInterpretation');
        if (!interpretationDiv) return;

        const data = this.getData();
        const interpretations = [];

        ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
            const earData = data.timpanometria?.[ear];
            if (!earData) return;

            const earLabel = ear === 'oido_derecho' ? 'OD' : 'OI';
            const type = this.interpretTimpanogramType(earData);

            if (type) {
                interpretations.push(`${earLabel}: ${type}`);
            }
        });

        if (interpretations.length > 0) {
            interpretationDiv.innerHTML = `
            <div class="interpretation-card">
            <div class="interpretation-title">Interpretación Automática</div>
            ${interpretations.map(interp =>
                `<div class="interpretation-item">• ${interp}</div>`
            ).join('')}
            </div>
            `;
        } else {
            interpretationDiv.innerHTML = '';
        }
    }

    /**
     * Interpretar tipo de timpanograma
     */
    interpretTimpanogramType(earData) {
        const compliance = parseFloat(earData.compliance_maxima);
        const presion = parseFloat(earData.presion);

        if (isNaN(compliance) || isNaN(presion)) return null;

        // Tipo A: Normal
        if (compliance >= 0.3 && compliance <= 1.7 && presion >= -100 && presion <= 50) {
            return 'Tipo A (Normal)';
        }

        // Tipo B: Plano
        if (compliance < 0.3) {
            return 'Tipo B (Plano)';
        }

        // Tipo C: Presión negativa
        if (presion < -150) {
            return 'Tipo C (Presión negativa)';
        }

        // Tipo As: Rígido
        if (compliance < 0.3 && presion >= -100) {
            return 'Tipo As (Rígido)';
        }

        // Tipo Ad: Hipermóvil
        if (compliance > 1.7) {
            return 'Tipo Ad (Hipermóvil)';
        }

        return 'Atípico';
    }

    /**
     * Obtener datos del formulario
     */
    getData() {
        const getValue = (id) => {
            const element = document.getElementById(id);
            return element ? element.value : '';
        };

        const getNumberValue = (id) => {
            const value = getValue(id);
            return value ? parseFloat(value) : null;
        };

        const data = {
            timpanometria: {
                oido_derecho: {
                    compliance_maxima: getNumberValue('compliance_od'),
                    presion: getNumberValue('presion_od'),
                    volumen_eac: getNumberValue('volumen_od'),
                    gradiente: getNumberValue('gradiente_od')
                },
                oido_izquierdo: {
                    compliance_maxima: getNumberValue('compliance_oi'),
                    presion: getNumberValue('presion_oi'),
                    volumen_eac: getNumberValue('volumen_oi'),
                    gradiente: getNumberValue('gradiente_oi')
                }
            },
            reflejos_acusticos: {
                oido_derecho: {
                    ipsi: {},
                    contra: {}
                },
                oido_izquierdo: {
                    ipsi: {},
                    contra: {}
                }
            },
            observaciones: getValue('impedance_observations')
        };

        // Recopilar reflejos acústicos
        this.reflexFrequencies.forEach(freq => {
            ['od', 'oi'].forEach(ear => {
                ['ipsi', 'contra'].forEach(type => {
                    const value = getValue(`reflex_${ear}_${type}_${freq}`);
                    if (value && value !== '') {
                        const earKey = ear === 'od' ? 'oido_derecho' : 'oido_izquierdo';
                        data.reflejos_acusticos[earKey][type][freq] = value;
                    }
                });
            });
        });

        return data;
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        const errors = [];

        if (!data || typeof data !== 'object') {
            errors.push('Datos de impedanciometría inválidos');
            return { isValid: false, errors };
        }

        // Validar rangos timpanometría
        ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
            const earData = data.timpanometria?.[ear];
            if (earData) {
                if (earData.compliance_maxima !== null &&
                    (earData.compliance_maxima < 0 || earData.compliance_maxima > 10)) {
                    errors.push(`Compliance ${ear} debe estar entre 0-10 ml`);
                    }
                    if (earData.presion !== null &&
                        (earData.presion < -400 || earData.presion > 200)) {
                        errors.push(`Presión ${ear} debe estar entre -400 y 200 daPa`);
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

        // Al menos un oído debe tener timpanometría completa
        const hasCompleteOD = data.timpanometria?.oido_derecho?.compliance_maxima !== null &&
        data.timpanometria?.oido_derecho?.presion !== null;

        const hasCompleteOI = data.timpanometria?.oido_izquierdo?.compliance_maxima !== null &&
        data.timpanometria?.oido_izquierdo?.presion !== null;

        return hasCompleteOD || hasCompleteOI;
    }
}

// Exponer globalmente
window.ImpedanceModule = ImpedanceModule;
