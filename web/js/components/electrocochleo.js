/**
 * ElectrocochleoModule - Módulo de Electrocoleografía
 * Potenciales de Sumación (SP) y Acción (AP) con ratio SP/AP
 */

class ElectrocochleoModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'electrocochleo';
        this.chartView = null;
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        return `
        <div class="form-section">
            <h3 class="section-title">🔬 Electrocoleografía</h3>
            <p class="section-description">
                Evaluación de los potenciales cocleares: Potencial de Sumación (SP) y Potencial de Acción (AP)
            </p>

            <!-- Layout Principal: Formularios (40%) + Preview (60%) -->
            <div style="display: flex; gap: 30px;">
                
                <!-- Panel de Formularios -->
                <div style="flex: 2; min-width: 400px;">
                    
                    <!-- Configuración de Estímulo -->
                    <div class="electro-section">
                        <h4 class="section-subtitle">Configuración del Estímulo</h4>
                        
                        <div class="form-row">
                            <div class="form-col-2">
                                <label>Tipo de Estímulo</label>
                                <select id="stimulus_type" tabindex="1">
                                    <option value="click" ${this.getSelectedValue(existingData.configuracion?.tipo_estimulo, 'click')}>Click</option>
                                    <option value="tone_burst" ${this.getSelectedValue(existingData.configuracion?.tipo_estimulo, 'tone_burst')}>Tone Burst</option>
                                    <option value="chirp" ${this.getSelectedValue(existingData.configuracion?.tipo_estimulo, 'chirp')}>Chirp</option>
                                </select>
                            </div>
                            <div class="form-col-2">
                                <label>Intensidad (dB nHL)</label>
                                <input type="number" 
                                       id="stimulus_intensity"
                                       min="70" max="120" step="5"
                                       value="${existingData.configuracion?.intensidad || 90}"
                                       tabindex="2">
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-col-2">
                                <label>Frecuencia (Hz)</label>
                                <select id="stimulus_frequency" tabindex="3">
                                    <option value="1000" ${this.getSelectedValue(existingData.configuracion?.frecuencia, '1000')}>1000 Hz</option>
                                    <option value="2000" ${this.getSelectedValue(existingData.configuracion?.frecuencia, '2000')}>2000 Hz</option>
                                    <option value="4000" ${this.getSelectedValue(existingData.configuracion?.frecuencia, '4000')}>4000 Hz</option>
                                    <option value="8000" ${this.getSelectedValue(existingData.configuracion?.frecuencia, '8000')}>8000 Hz</option>
                                </select>
                            </div>
                            <div class="form-col-2">
                                <label>Polaridad</label>
                                <select id="stimulus_polarity" tabindex="4">
                                    <option value="condensacion" ${this.getSelectedValue(existingData.configuracion?.polaridad, 'condensacion')}>Condensación</option>
                                    <option value="rarefaccion" ${this.getSelectedValue(existingData.configuracion?.polaridad, 'rarefaccion')}>Rarefacción</option>
                                    <option value="alternante" ${this.getSelectedValue(existingData.configuracion?.polaridad, 'alternante')}>Alternante</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Mediciones por Oído -->
                    <div class="electro-section">
                        <h4 class="section-subtitle">Mediciones de Potenciales</h4>
                        
                        <div class="ear-measurements">
                            <!-- Oído Derecho -->
                            <div class="ear-column">
                                <div class="ear-title" style="color: #dc3545;">🔴 Oído Derecho</div>
                                
                                <div class="measurement-group">
                                    <label>Potencial de Sumación (SP)</label>
                                    <div class="input-with-unit">
                                        <input type="number" 
                                               id="sp_od"
                                               min="-2.0" max="2.0" step="0.01"
                                               value="${existingData.potencial_sumacion?.oido_derecho || ''}"
                                               placeholder="-0.25"
                                               tabindex="5">
                                        <span class="unit">µV</span>
                                    </div>
                                </div>

                                <div class="measurement-group">
                                    <label>Potencial de Acción (AP)</label>
                                    <div class="input-with-unit">
                                        <input type="number" 
                                               id="ap_od"
                                               min="0" max="20" step="0.01"
                                               value="${existingData.potencial_accion?.oido_derecho || ''}"
                                               placeholder="2.85"
                                               tabindex="6">
                                        <span class="unit">µV</span>
                                    </div>
                                </div>

                                <div class="calculated-ratio">
                                    <label>Ratio SP/AP</label>
                                    <div class="ratio-display" id="ratio_od">
                                        ${this.calculateRatio(existingData.potencial_sumacion?.oido_derecho, existingData.potencial_accion?.oido_derecho)}
                                    </div>
                                </div>
                            </div>

                            <!-- Oído Izquierdo -->
                            <div class="ear-column">
                                <div class="ear-title" style="color: #007bff;">🔵 Oído Izquierdo</div>
                                
                                <div class="measurement-group">
                                    <label>Potencial de Sumación (SP)</label>
                                    <div class="input-with-unit">
                                        <input type="number" 
                                               id="sp_oi"
                                               min="-2.0" max="2.0" step="0.01"
                                               value="${existingData.potencial_sumacion?.oido_izquierdo || ''}"
                                               placeholder="-0.18"
                                               tabindex="7">
                                        <span class="unit">µV</span>
                                    </div>
                                </div>

                                <div class="measurement-group">
                                    <label>Potencial de Acción (AP)</label>
                                    <div class="input-with-unit">
                                        <input type="number" 
                                               id="ap_oi"
                                               min="0" max="20" step="0.01"
                                               value="${existingData.potencial_accion?.oido_izquierdo || ''}"
                                               placeholder="3.20"
                                               tabindex="8">
                                        <span class="unit">µV</span>
                                    </div>
                                </div>

                                <div class="calculated-ratio">
                                    <label>Ratio SP/AP</label>
                                    <div class="ratio-display" id="ratio_oi">
                                        ${this.calculateRatio(existingData.potencial_sumacion?.oido_izquierdo, existingData.potencial_accion?.oido_izquierdo)}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Interpretación Clínica -->
                    <div class="electro-section">
                        <h4 class="section-subtitle">Interpretación Clínica</h4>
                        <p class="clinical-note">
                            <strong>Valores de referencia:</strong><br>
                            • Ratio SP/AP normal: ≤ 0.37<br>
                            • Ratio SP/AP patológico: > 0.37 (sugiere hidropesía endolinfática)<br>
                            • SP normal: Negativo (-0.1 a -0.5 µV)<br>
                            • AP normal: Positivo (1.0 a 8.0 µV)
                        </p>
                        
                        <div class="interpretation-display" id="clinical_interpretation">
                            ${this.generateInterpretation(existingData)}
                        </div>
                    </div>

                    <!-- Observaciones -->
                    <div class="form-group" style="margin-top: 20px;">
                        <label class="label-optional">Observaciones</label>
                        <textarea id="electrocochleo_observations"
                                  rows="3"
                                  tabindex="9"
                                  placeholder="Comentarios sobre la calidad del registro, artefactos, condiciones de medición...">${existingData.observaciones || ''}</textarea>
                    </div>
                </div>

                <!-- Panel de Preview -->
                <div style="flex: 3; min-width: 500px;">
                    <h4 class="section-subtitle">📊 Visualización de Potenciales</h4>
                    <div id="electrocochlearPreview" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: white;">
                        <canvas id="electrocochlearCanvas" width="600" height="400" style="width: 100%; height: auto;"></canvas>
                    </div>
                    <div style="margin-top: 10px; font-size: 12px; color: #666;">
                        <span style="color: #dc3545;">● OD</span> &nbsp;&nbsp;
                        <span style="color: #007bff;">● OI</span> &nbsp;&nbsp;
                        <span style="color: #28a745;">— SP</span> &nbsp;&nbsp;
                        <span style="color: #fd7e14;">— AP</span>
                    </div>
                </div>
            </div>
        </div>

        <style>
            .electro-section {
                margin-bottom: 25px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #6f42c1;
            }

            .ear-measurements {
                display: flex;
                gap: 25px;
            }

            .ear-column {
                flex: 1;
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 20px;
                transition: all 0.3s ease;
            }

            .ear-column:hover {
                border-color: #6f42c1;
                box-shadow: 0 4px 15px rgba(111, 66, 193, 0.1);
            }

            .measurement-group {
                margin-bottom: 15px;
            }

            .measurement-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #333;
                font-size: 13px;
            }

            .input-with-unit {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .input-with-unit input {
                flex: 1;
                padding: 8px 12px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-size: 13px;
                text-align: right;
            }

            .input-with-unit input:focus {
                border-color: #6f42c1;
                outline: none;
                box-shadow: 0 0 0 2px rgba(111, 66, 193, 0.1);
            }

            .input-with-unit .unit {
                font-size: 12px;
                color: #666;
                font-weight: 500;
                min-width: 20px;
            }

            .calculated-ratio {
                margin-top: 15px;
                padding: 10px;
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border-radius: 6px;
                border: 1px solid #dee2e6;
            }

            .calculated-ratio label {
                font-weight: 600;
                color: #495057;
                margin-bottom: 5px;
                font-size: 12px;
            }

            .ratio-display {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                text-align: center;
                font-family: 'Courier New', monospace;
            }

            .ratio-normal {
                color: #28a745;
            }

            .ratio-pathological {
                color: #dc3545;
            }

            .ratio-pending {
                color: #6c757d;
                font-style: italic;
            }

            .clinical-note {
                font-size: 12px;
                color: #666;
                background: #fff3cd;
                padding: 10px;
                border-radius: 6px;
                border-left: 4px solid #ffc107;
                line-height: 1.4;
                margin-bottom: 15px;
            }

            .interpretation-display {
                background: white;
                padding: 15px;
                border-radius: 6px;
                border: 2px solid #e9ecef;
                font-size: 14px;
                min-height: 60px;
            }

            .interpretation-normal {
                border-color: #28a745;
                background: #d4edda;
                color: #155724;
            }

            .interpretation-pathological {
                border-color: #dc3545;
                background: #f8d7da;
                color: #721c24;
            }

            .interpretation-pending {
                border-color: #6c757d;
                background: #f8f9fa;
                color: #6c757d;
            }

            @media (max-width: 768px) {
                .ear-measurements {
                    flex-direction: column;
                    gap: 15px;
                }
            }
        </style>
        `;
    }

    /**
     * Helper para valores seleccionados
     */
    getSelectedValue(currentValue, optionValue) {
        return currentValue === optionValue ? 'selected' : '';
    }

    /**
     * Calcular ratio SP/AP
     */
    calculateRatio(sp, ap) {
        if (!sp || !ap || sp === '' || ap === '') {
            return '<span class="ratio-pending">Pendiente</span>';
        }

        const spValue = parseFloat(sp);
        const apValue = parseFloat(ap);

        if (apValue === 0) {
            return '<span class="ratio-pending">AP = 0</span>';
        }

        const ratio = Math.abs(spValue) / apValue;
        const ratioFormatted = ratio.toFixed(3);

        if (ratio <= 0.37) {
            return `<span class="ratio-normal">${ratioFormatted}</span>`;
        } else {
            return `<span class="ratio-pathological">${ratioFormatted}</span>`;
        }
    }

    /**
     * Generar interpretación clínica
     */
    generateInterpretation(data) {
        if (!data.potencial_sumacion || !data.potencial_accion) {
            return '<div class="interpretation-pending">Complete las mediciones para obtener la interpretación clínica.</div>';
        }

        const interpretations = [];
        
        ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
            const sp = data.potencial_sumacion[ear];
            const ap = data.potencial_accion[ear];
            const earLabel = ear === 'oido_derecho' ? 'OD' : 'OI';

            if (sp && ap) {
                const spValue = parseFloat(sp);
                const apValue = parseFloat(ap);
                const ratio = Math.abs(spValue) / apValue;

                let interpretation = `<strong>${earLabel}:</strong> `;
                
                if (ratio <= 0.37) {
                    interpretation += `Ratio SP/AP normal (${ratio.toFixed(3)}). No evidencia de hidropesía endolinfática.`;
                } else {
                    interpretation += `Ratio SP/AP elevado (${ratio.toFixed(3)}). Sugiere hidropesía endolinfática compatible con enfermedad de Ménière.`;
                }

                interpretations.push(interpretation);
            }
        });

        if (interpretations.length === 0) {
            return '<div class="interpretation-pending">Complete las mediciones para obtener la interpretación clínica.</div>';
        }

        const hasPathological = interpretations.some(i => i.includes('elevado'));
        const cssClass = hasPathological ? 'interpretation-pathological' : 'interpretation-normal';

        return `<div class="${cssClass}">${interpretations.join('<br><br>')}</div>`;
    }

    /**
     * Inicializar eventos después de renderizar
     */
    async initEvents() {
        // Cargar vista del gráfico (cuando esté disponible)
        await this.loadChartView();

        // Auto-save y update display al cambiar valores
        const inputs = document.querySelectorAll('#tabsContent input, #tabsContent select, #tabsContent textarea');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                this.updateCalculations();
                this.updateElectrocochlearPreview();
                this.app.updateModuleData(this.moduleId, this.getData());
            });

            input.addEventListener('change', () => {
                this.updateCalculations();
                this.updateElectrocochlearPreview();
                this.app.updateModuleData(this.moduleId, this.getData());
            });
        });

        // Validación en tiempo real
        const numberInputs = document.querySelectorAll('#tabsContent input[type="number"]');
        numberInputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
        });

        // Renderizar preview inicial
        setTimeout(() => {
            this.updateCalculations();
            this.updateElectrocochlearPreview();
        }, 100);
    }

    /**
     * Cargar componente de vista del gráfico
     */
    async loadChartView() {
        try {
            await this.app.loadScript('js/components/views/electrocochlear-chart.js');
            this.chartView = new window.ElectrocochlearChartView('electrocochlearCanvas');
        } catch (error) {
            console.warn('electrocochlear-chart.js no disponible');
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

        if (input.value && (isNaN(value) || value < min || value > max)) {
            input.classList.add('field-error');
            this.app.notify(`Valor fuera del rango permitido (${min}-${max})`, 'warning');
        } else {
            input.classList.remove('field-error');
        }
    }

    /**
     * Actualizar cálculos y visualización
     */
    updateCalculations() {
        // Actualizar ratios
        ['od', 'oi'].forEach(ear => {
            const spInput = document.getElementById(`sp_${ear}`);
            const apInput = document.getElementById(`ap_${ear}`);
            const ratioDisplay = document.getElementById(`ratio_${ear}`);

            if (spInput && apInput && ratioDisplay) {
                const sp = spInput.value;
                const ap = apInput.value;
                ratioDisplay.innerHTML = this.calculateRatio(sp, ap);
            }
        });

        // Actualizar interpretación clínica
        const interpretationDisplay = document.getElementById('clinical_interpretation');
        if (interpretationDisplay) {
            const data = this.getData();
            interpretationDisplay.innerHTML = this.generateInterpretation(data);
        }
    }

    /**
     * Actualizar preview de potenciales
     */
    updateElectrocochlearPreview() {
        if (this.chartView) {
            const data = this.getData();
            this.chartView.render(data);
        } else {
            this.renderSimpleFallback();
        }
    }

    /**
     * Fallback simple si no hay componente de vista
     */
    renderSimpleFallback() {
        const canvas = document.getElementById('electrocochlearCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = '#666';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Vista previa no disponible', canvas.width/2, canvas.height/2);
        ctx.fillText('(electrocochlear-chart.js no cargado)', canvas.width/2, canvas.height/2 + 20);
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

        return {
            configuracion: {
                tipo_estimulo: getValue('stimulus_type') || 'click',
                intensidad: getNumberValue('stimulus_intensity') || 90,
                frecuencia: getValue('stimulus_frequency') || '1000',
                polaridad: getValue('stimulus_polarity') || 'condensacion'
            },
            potencial_sumacion: {
                oido_derecho: getNumberValue('sp_od'),
                oido_izquierdo: getNumberValue('sp_oi')
            },
            potencial_accion: {
                oido_derecho: getNumberValue('ap_od'),
                oido_izquierdo: getNumberValue('ap_oi')
            },
            observaciones: getValue('electrocochleo_observations')
        };
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        const errors = [];

        // Validar rangos de intensidad
        if (data.configuracion?.intensidad) {
            if (data.configuracion.intensidad < 70 || data.configuracion.intensidad > 120) {
                errors.push('Intensidad debe estar entre 70-120 dB nHL');
            }
        }

        // Validar rangos SP
        ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
            const sp = data.potencial_sumacion?.[ear];
            if (sp !== null && sp !== undefined && (sp < -2.0 || sp > 2.0)) {
                errors.push(`SP ${ear} debe estar entre -2.0 y 2.0 µV`);
            }
        });

        // Validar rangos AP
        ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
            const ap = data.potencial_accion?.[ear];
            if (ap !== null && ap !== undefined && (ap < 0 || ap > 20)) {
                errors.push(`AP ${ear} debe estar entre 0 y 20 µV`);
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

        // Al menos un oído debe tener tanto SP como AP
        const odComplete = data.potencial_sumacion?.oido_derecho !== null && 
                          data.potencial_accion?.oido_derecho !== null;
        const oiComplete = data.potencial_sumacion?.oido_izquierdo !== null && 
                          data.potencial_accion?.oido_izquierdo !== null;

        return odComplete || oiComplete;
    }
}

// Exponer globalmente
window.ElectrocochleoModule = ElectrocochleoModule;
