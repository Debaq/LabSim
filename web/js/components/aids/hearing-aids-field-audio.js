/**
 * HearingAidsFieldAudioSection - Sección de Audiometría de Campo Libre
 * Umbrales sin audífonos, con audífonos actuales y ganancia funcional
 */

class HearingAidsFieldAudioSection {
    constructor(app, parentModule) {
        this.app = app;
        this.parent = parentModule;
        this.sectionId = 'fieldAudio';
        
        // Frecuencias para audiometría de campo libre
        this.frequencies = ['250', '500', '1000', '2000', '4000', '8000'];
        
        // Vista del gráfico
        this.chartView = null;
    }

    /**
     * Renderizar contenido de la sección
     */
    async render(existingData = {}) {
        return `
            <div class="aids-field-audio-content">
                <!-- Layout Principal: Formularios (40%) + Preview (60%) -->
                <div style="display: flex; gap: 30px;">
                    
                    <!-- Panel de Formularios -->
                    <div style="flex: 2; min-width: 400px;">
                        
                        <!-- Información de Campo Libre -->
                        <div class="form-group">
                            <h4 class="section-subtitle">🔊 Audiometría de Campo Libre</h4>
                            <p class="field-note">
                                Umbrales obtenidos en campo libre con y sin audífonos actuales del paciente
                            </p>
                        </div>

                        <!-- Toggle para Audífonos Actuales -->
                        <div class="form-group">
                            <div class="form-row">
                                <div class="form-col-auto">
                                    <label style="display: flex; align-items: center; gap: 10px;">
                                        <input type="checkbox" 
                                               id="tiene_audifonos_actuales" 
                                               ${existingData.tiene_audifonos_actuales ? 'checked' : ''}
                                               tabindex="1">
                                        <strong>Paciente tiene audífonos actuales</strong>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <!-- Umbrales Sin Audífonos -->
                        <div class="audiometry-section">
                            <h5 class="audiometry-title">Umbrales Sin Audífonos</h5>
                            <div class="ear-selector">
                                <div class="ear-column">
                                    <div class="ear-title" style="color: #dc3545;">🔴 Oído Derecho (OD)</div>
                                    <div class="frequency-grid">
                                        ${this.renderFrequencyGrid('sin_audifonos', 'od', existingData.sin_audifonos?.oido_derecho, 2)}
                                    </div>
                                </div>
                                <div class="ear-column">
                                    <div class="ear-title" style="color: #007bff;">🔵 Oído Izquierdo (OI)</div>
                                    <div class="frequency-grid">
                                        ${this.renderFrequencyGrid('sin_audifonos', 'oi', existingData.sin_audifonos?.oido_izquierdo, 10)}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Umbrales Con Audífonos Actuales -->
                        <div class="audiometry-section" id="con_audifonos_section" style="display: none;">
                            <h5 class="audiometry-title">Umbrales Con Audífonos Actuales</h5>
                            <div class="ear-selector">
                                <div class="ear-column">
                                    <div class="ear-title" style="color: #dc3545;">🔴 Oído Derecho (OD)</div>
                                    <div class="frequency-grid">
                                        ${this.renderFrequencyGrid('con_audifonos', 'od', existingData.con_audifonos?.oido_derecho, 20)}
                                    </div>
                                </div>
                                <div class="ear-column">
                                    <div class="ear-title" style="color: #007bff;">🔵 Oído Izquierdo (OI)</div>
                                    <div class="frequency-grid">
                                        ${this.renderFrequencyGrid('con_audifonos', 'oi', existingData.con_audifonos?.oido_izquierdo, 28)}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- SRT y Discriminación -->
                        <div class="logoaudio-section">
                            <h5 class="audiometry-title">SRT y Discriminación en Campo Libre</h5>
                            <table class="field-audio-table">
                                <thead>
                                    <tr>
                                        <th>Condición</th>
                                        <th style="color: #dc3545;">SRT OD</th>
                                        <th style="color: #007bff;">SRT OI</th>
                                        <th style="color: #dc3545;">Disc. OD (%)</th>
                                        <th style="color: #007bff;">Disc. OI (%)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td class="condition-label">Sin audífonos</td>
                                        <td>
                                            <input type="number" 
                                                   id="srt_sin_od" 
                                                   class="field-audio-input"
                                                   min="0" max="100" step="5"
                                                   value="${existingData.srt_discriminacion?.sin_audifonos?.srt_od || ''}"
                                                   placeholder="dB"
                                                   tabindex="36">
                                        </td>
                                        <td>
                                            <input type="number" 
                                                   id="srt_sin_oi" 
                                                   class="field-audio-input"
                                                   min="0" max="100" step="5"
                                                   value="${existingData.srt_discriminacion?.sin_audifonos?.srt_oi || ''}"
                                                   placeholder="dB"
                                                   tabindex="37">
                                        </td>
                                        <td>
                                            <input type="number" 
                                                   id="disc_sin_od" 
                                                   class="field-audio-input"
                                                   min="0" max="100" step="1"
                                                   value="${existingData.srt_discriminacion?.sin_audifonos?.disc_od || ''}"
                                                   placeholder="%"
                                                   tabindex="38">
                                        </td>
                                        <td>
                                            <input type="number" 
                                                   id="disc_sin_oi" 
                                                   class="field-audio-input"
                                                   min="0" max="100" step="1"
                                                   value="${existingData.srt_discriminacion?.sin_audifonos?.disc_oi || ''}"
                                                   placeholder="%"
                                                   tabindex="39">
                                        </td>
                                    </tr>
                                    <tr id="con_audifonos_row" style="display: none;">
                                        <td class="condition-label">Con audífonos</td>
                                        <td>
                                            <input type="number" 
                                                   id="srt_con_od" 
                                                   class="field-audio-input"
                                                   min="0" max="100" step="5"
                                                   value="${existingData.srt_discriminacion?.con_audifonos?.srt_od || ''}"
                                                   placeholder="dB"
                                                   tabindex="40">
                                        </td>
                                        <td>
                                            <input type="number" 
                                                   id="srt_con_oi" 
                                                   class="field-audio-input"
                                                   min="0" max="100" step="5"
                                                   value="${existingData.srt_discriminacion?.con_audifonos?.srt_oi || ''}"
                                                   placeholder="dB"
                                                   tabindex="41">
                                        </td>
                                        <td>
                                            <input type="number" 
                                                   id="disc_con_od" 
                                                   class="field-audio-input"
                                                   min="0" max="100" step="1"
                                                   value="${existingData.srt_discriminacion?.con_audifonos?.disc_od || ''}"
                                                   placeholder="%"
                                                   tabindex="42">
                                        </td>
                                        <td>
                                            <input type="number" 
                                                   id="disc_con_oi" 
                                                   class="field-audio-input"
                                                   min="0" max="100" step="1"
                                                   value="${existingData.srt_discriminacion?.con_audifonos?.disc_oi || ''}"
                                                   placeholder="%"
                                                   tabindex="43">
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <!-- Mediciones Adicionales -->
                        <div class="additional-section" id="additional_section" style="display: none;">
                            <h5 class="audiometry-title">Mediciones Adicionales</h5>
                            
                            <div class="form-row">
                                <div class="form-col-2">
                                    <label>LDL Con Audífonos OD (dB)</label>
                                    <input type="number" 
                                           id="ldl_con_od"
                                           min="60" max="130" step="5"
                                           value="${existingData.mediciones_adicionales?.ldl_con_od || ''}"
                                           placeholder="100"
                                           tabindex="44">
                                </div>
                                <div class="form-col-2">
                                    <label>LDL Con Audífonos OI (dB)</label>
                                    <input type="number" 
                                           id="ldl_con_oi"
                                           min="60" max="130" step="5"
                                           value="${existingData.mediciones_adicionales?.ldl_con_oi || ''}"
                                           placeholder="100"
                                           tabindex="45">
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-col-2">
                                    <label>SNR en Ruido Sin Audífonos (dB)</label>
                                    <input type="number" 
                                           id="snr_sin"
                                           min="-10" max="20" step="1"
                                           value="${existingData.mediciones_adicionales?.snr_sin || ''}"
                                           placeholder="8"
                                           tabindex="46">
                                </div>
                                <div class="form-col-2">
                                    <label>SNR en Ruido Con Audífonos (dB)</label>
                                    <input type="number" 
                                           id="snr_con"
                                           min="-10" max="20" step="1"
                                           value="${existingData.mediciones_adicionales?.snr_con || ''}"
                                           placeholder="3"
                                           tabindex="47">
                                </div>
                            </div>
                        </div>

                        <!-- Observaciones -->
                        <div class="form-group">
                            <label class="label-optional">Observaciones de Campo Libre</label>
                            <textarea id="observaciones_campo_libre" 
                                      rows="3" 
                                      tabindex="48"
                                      placeholder="Comentarios sobre las condiciones de prueba, calibración, comportamiento del paciente...">${existingData.observaciones || ''}</textarea>
                        </div>
                    </div>

                    <!-- Panel de Preview -->
                    <div style="flex: 3; min-width: 500px;">
                        <h4 class="section-subtitle">📊 Audiograma de Campo Libre</h4>
                        <div id="fieldAudioPreview" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: white;">
                            <canvas id="fieldAudioCanvas" width="600" height="450" style="width: 100%; height: auto;"></canvas>
                        </div>
                        
                        <!-- Leyenda del Gráfico -->
                        <div style="margin-top: 10px; font-size: 12px; color: #666; display: flex; gap: 20px; justify-content: center;">
                            <span style="color: #dc3545;">🔴 Sin audífonos OD</span>
                            <span style="color: #007bff;">🔵 Sin audífonos OI</span>
                            <span id="legend_con_audifonos" style="display: none;">
                                <span style="color: #dc3545;">🔺 Con audífonos OD</span>
                                <span style="color: #007bff;">🔷 Con audífonos OI</span>
                            </span>
                        </div>

                        <!-- Resumen de Ganancia Funcional -->
                        <div id="ganancia_summary" style="display: none; margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 6px;">
                            <h5 style="margin-bottom: 10px; color: #2a5298;">Ganancia Funcional Promedio</h5>
                            <div id="ganancia_content"></div>
                        </div>
                    </div>
                </div>
            </div>

            <style>
            .aids-field-audio-content {
                animation: slideIn 0.3s ease-out;
            }

            .audiometry-section {
                margin-bottom: 25px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #17a2b8;
            }

            .logoaudio-section {
                margin-bottom: 25px;
                padding: 20px;
                background: #f1f8ff;
                border-radius: 8px;
                border-left: 4px solid #007bff;
            }

            .additional-section {
                margin-bottom: 25px;
                padding: 20px;
                background: #f0f8f0;
                border-radius: 8px;
                border-left: 4px solid #28a745;
            }

            .audiometry-title {
                color: #2a5298;
                font-size: 1em;
                margin-bottom: 15px;
                font-weight: 600;
            }

            .field-note {
                font-size: 13px;
                color: #666;
                margin-bottom: 15px;
                line-height: 1.4;
                font-style: italic;
            }

            .frequency-grid {
                display: grid;
                grid-template-columns: auto 1fr;
                gap: 8px;
                align-items: center;
            }

            .freq-label {
                font-weight: 600;
                padding: 8px;
                background: linear-gradient(135deg, #e9ecef, #f8f9fa);
                border-radius: 4px;
                text-align: center;
                color: #495057;
                font-size: 12px;
                min-width: 45px;
            }

            .freq-input {
                padding: 6px 8px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                font-weight: 500;
                font-size: 13px;
                width: 100%;
            }

            .freq-input:focus {
                border-color: #17a2b8;
                outline: none;
                box-shadow: 0 0 0 2px rgba(23, 162, 184, 0.1);
                transform: none;
            }

            .field-audio-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
                margin-bottom: 15px;
            }

            .field-audio-table th {
                background: #e9ecef;
                border: 1px solid #dee2e6;
                padding: 8px 10px;
                text-align: center;
                font-weight: 600;
                font-size: 12px;
            }

            .field-audio-table td {
                border: 1px solid #dee2e6;
                padding: 6px 8px;
                text-align: center;
            }

            .condition-label {
                background: #f8f9fa;
                font-weight: 500;
                text-align: left !important;
                padding-left: 12px !important;
            }

            .field-audio-input {
                width: 55px;
                padding: 4px 6px;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                text-align: center;
                font-size: 12px;
            }

            .field-audio-input:focus {
                border-color: #007bff;
                outline: none;
                box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
            }

            @keyframes slideIn {
                from { opacity: 0; transform: translateX(-10px); }
                to { opacity: 1; transform: translateX(0); }
            }
            </style>
        `;
    }

    /**
     * Renderizar grid de frecuencias
     */
    renderFrequencyGrid(type, ear, data = {}, startTabIndex = 1) {
        return this.frequencies.map((freq, index) => {
            const value = data ? data[freq] || '' : '';
            const tabIndex = startTabIndex + index;
            
            return `
                <div class="freq-label">${freq} Hz</div>
                <input type="number" 
                       id="${type}_${ear}_${freq}" 
                       class="freq-input"
                       min="0" max="120" step="5"
                       value="${value}"
                       placeholder="dB"
                       tabindex="${tabIndex}">
            `;
        }).join('');
    }

    /**
     * Inicializar eventos después de renderizar
     */
    async initEvents() {
        // Cargar vista del gráfico
        await this.loadChartView();

        // Configurar visibilidad condicional
        this.setupConditionalSections();

        // Auto-save y update preview
        this.setupAutoSave();

        // Validación en tiempo real
        this.setupValidation();

        // Renderizar preview inicial
        setTimeout(() => {
            this.updateFieldAudioPreview();
        }, 100);
    }

    /**
     * Cargar componente de vista del gráfico
     */
    async loadChartView() {
        try {
            await this.app.loadScript('js/components/views/field-audiometry-chart.js');
            this.chartView = new window.FieldAudiometryChartView('fieldAudioCanvas');
        } catch (error) {
            console.warn('field-audiometry-chart.js no disponible, usando fallback');
            this.chartView = null;
        }
    }

    /**
     * Configurar secciones condicionales
     */
    setupConditionalSections() {
        const tieneAudifonosCheckbox = document.getElementById('tiene_audifonos_actuales');
        if (!tieneAudifonosCheckbox) return;

        const conditionalElements = [
            'con_audifonos_section',
            'con_audifonos_row', 
            'additional_section',
            'legend_con_audifonos',
            'ganancia_summary'
        ];

        const updateConditionalVisibility = () => {
            const shouldShow = tieneAudifonosCheckbox.checked;

            conditionalElements.forEach(elementId => {
                const element = document.getElementById(elementId);
                if (element) {
                    element.style.display = shouldShow ? 'block' : 'none';
                }
            });

            // Actualizar preview
            this.updateFieldAudioPreview();
        };

        // Configurar al cargar y al cambiar
        updateConditionalVisibility();
        tieneAudifonosCheckbox.addEventListener('change', updateConditionalVisibility);
    }

    /**
     * Configurar auto-guardado
     */
    setupAutoSave() {
        const inputs = document.querySelectorAll('#fieldAudioSection input, #fieldAudioSection textarea');
        
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                this.updateFieldAudioPreview();
                this.saveData();
            });

            input.addEventListener('change', () => {
                this.updateFieldAudioPreview();
                this.saveData();
            });
        });
    }

    /**
     * Configurar validación
     */
    setupValidation() {
        const numberInputs = document.querySelectorAll('#fieldAudioSection input[type="number"]');
        
        numberInputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
        });
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
     * Actualizar preview del audiograma
     */
    updateFieldAudioPreview() {
        if (this.chartView) {
            const data = this.getData();
            this.chartView.render(data);
            this.updateGananciaFuncional(data);
        } else {
            this.renderSimpleFallback();
        }
    }

    /**
     * Actualizar resumen de ganancia funcional
     */
    updateGananciaFuncional(data) {
        const gananciaContent = document.getElementById('ganancia_content');
        if (!gananciaContent || !data.tiene_audifonos_actuales) return;

        const gananciaOD = this.calculateGananciaFuncional(data, 'oido_derecho');
        const gananciaOI = this.calculateGananciaFuncional(data, 'oido_izquierdo');

        const promedioOD = this.calculatePromedio(gananciaOD);
        const promedioOI = this.calculatePromedio(gananciaOI);

        gananciaContent.innerHTML = `
            <div style="display: flex; gap: 30px;">
                <div>
                    <strong style="color: #dc3545;">OD:</strong> 
                    ${promedioOD !== null ? `${promedioOD.toFixed(1)} dB` : 'N/A'}
                </div>
                <div>
                    <strong style="color: #007bff;">OI:</strong> 
                    ${promedioOI !== null ? `${promedioOI.toFixed(1)} dB` : 'N/A'}
                </div>
            </div>
        `;
    }

    /**
     * Calcular ganancia funcional por oído
     */
    calculateGananciaFuncional(data, ear) {
        const ganancia = {};
        const sinAudifonos = data.sin_audifonos?.[ear] || {};
        const conAudifonos = data.con_audifonos?.[ear] || {};

        this.frequencies.forEach(freq => {
            const sinValue = parseFloat(sinAudifonos[freq]);
            const conValue = parseFloat(conAudifonos[freq]);
            
            if (!isNaN(sinValue) && !isNaN(conValue)) {
                ganancia[freq] = sinValue - conValue;
            }
        });

        return ganancia;
    }

    /**
     * Calcular promedio de ganancia
     */
    calculatePromedio(gananciaObj) {
        const valores = Object.values(gananciaObj).filter(v => !isNaN(v));
        if (valores.length === 0) return null;
        
        return valores.reduce((sum, val) => sum + val, 0) / valores.length;
    }

    /**
     * Fallback simple si no hay componente de vista
     */
    renderSimpleFallback() {
        const canvas = document.getElementById('fieldAudioCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = '#666';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Vista previa no disponible', canvas.width/2, canvas.height/2);
        ctx.fillText('(field-audiometry-chart.js no cargado)', canvas.width/2, canvas.height/2 + 20);
    }

    /**
     * Guardar datos automáticamente
     */
    saveData() {
        const data = this.getData();
        this.parent.updateSectionData(this.sectionId, data);
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

        const getFrequencyData = (prefix, ear) => {
            const data = {};
            this.frequencies.forEach(freq => {
                const value = getNumberValue(`${prefix}_${ear}_${freq}`);
                if (value !== null) {
                    data[freq] = value;
                }
            });
            return data;
        };

        return {
            tiene_audifonos_actuales: document.getElementById('tiene_audifonos_actuales')?.checked || false,
            sin_audifonos: {
                oido_derecho: getFrequencyData('sin_audifonos', 'od'),
                oido_izquierdo: getFrequencyData('sin_audifonos', 'oi')
            },
            con_audifonos: {
                oido_derecho: getFrequencyData('con_audifonos', 'od'),
                oido_izquierdo: getFrequencyData('con_audifonos', 'oi')
            },
            srt_discriminacion: {
                sin_audifonos: {
                    srt_od: getNumberValue('srt_sin_od'),
                    srt_oi: getNumberValue('srt_sin_oi'),
                    disc_od: getNumberValue('disc_sin_od'),
                    disc_oi: getNumberValue('disc_sin_oi')
                },
                con_audifonos: {
                    srt_od: getNumberValue('srt_con_od'),
                    srt_oi: getNumberValue('srt_con_oi'),
                    disc_od: getNumberValue('disc_con_od'),
                    disc_oi: getNumberValue('disc_con_oi')
                }
            },
            mediciones_adicionales: {
                ldl_con_od: getNumberValue('ldl_con_od'),
                ldl_con_oi: getNumberValue('ldl_con_oi'),
                snr_sin: getNumberValue('snr_sin'),
                snr_con: getNumberValue('snr_con')
            },
            observaciones: getValue('observaciones_campo_libre')
        };
    }

    /**
     * Validar datos de la sección
     */
    validate(data) {
        const errors = [];

        // Validar rangos de umbrales
        ['sin_audifonos', 'con_audifonos'].forEach(condition => {
            ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
                const earData = data[condition]?.[ear];
                if (earData) {
                    Object.keys(earData).forEach(freq => {
                        const value = earData[freq];
                        if (value !== null && (value < 0 || value > 120)) {
                            errors.push(`Umbral ${freq}Hz ${ear} ${condition} debe estar entre 0-120 dB`);
                        }
                    });
                }
            });
        });

        // Validar SRT
        const srtData = data.srt_discriminacion;
        if (srtData) {
            ['sin_audifonos', 'con_audifonos'].forEach(condition => {
                const condData = srtData[condition];
                if (condData) {
                    ['srt_od', 'srt_oi'].forEach(field => {
                        const value = condData[field];
                        if (value !== null && (value < 0 || value > 100)) {
                            errors.push(`SRT ${field} ${condition} debe estar entre 0-100 dB`);
                        }
                    });
                    
                    ['disc_od', 'disc_oi'].forEach(field => {
                        const value = condData[field];
                        if (value !== null && (value < 0 || value > 100)) {
                            errors.push(`Discriminación ${field} ${condition} debe estar entre 0-100%`);
                        }
                    });
                }
            });
        }

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

        // Al menos debe tener algunos umbrales sin audífonos
        const hasUmbralesSin = data.sin_audifonos?.oido_derecho && 
                              Object.keys(data.sin_audifonos.oido_derecho).length > 0 ||
                              data.sin_audifonos?.oido_izquierdo && 
                              Object.keys(data.sin_audifonos.oido_izquierdo).length > 0;

        return hasUmbralesSin;
    }
}

// Exponer globalmente
window.HearingAidsFieldAudioSection = HearingAidsFieldAudioSection;