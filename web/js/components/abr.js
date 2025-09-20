/**
 * AbrModule - Módulo de Potenciales Evocados Auditivos (ABR)
 * Ondas I, III, V con auto-cálculo de II y IV
 */

class AbrModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'abr';
        
        // Configuración de ondas
        this.waves = ['I', 'II', 'III', 'IV', 'V'];
        this.editableWaves = ['I', 'III', 'V'];
        this.autoWaves = ['II', 'IV'];
        
        // Tipos de estímulo
        this.stimulusTypes = [
            { id: 'click', name: 'Click', icon: '🔊' },
            { id: 'tone_burst', name: 'Tone Burst', icon: '📊' },
            { id: 'chirp', name: 'Chirp', icon: '🌊' }
        ];
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        return `
        <div class="form-section">
        <h3 class="section-title">⚡ Potenciales Evocados Auditivos (ABR)</h3>
        <p class="section-description">
        Evaluación de la función auditiva mediante potenciales evocados del tronco cerebral
        </p>

        <!-- Layout Principal: Formularios (40%) + Gráficos (60%) -->
        <div style="display: flex; gap: 30px;">
        
        <!-- Panel de Formularios -->
        <div style="flex: 2; min-width: 450px;">
        
        <!-- Selector de Estímulo -->
        <div class="abr-stimulus-selector">
        ${this.renderStimulusSelector(existingData.stimulus_activo || 'click')}
        </div>

        <!-- Configuración Global -->
        <div class="abr-global-config">
        <h4 class="section-subtitle">Configuración General</h4>
        
        <div class="form-row">
        <div class="form-col-3">
        <label>Intensidad 80 dB</label>
        <input type="checkbox" id="abr_80db_enabled" ${existingData.intensidad_80db?.habilitado !== false ? 'checked' : ''}>
        <span style="margin-left: 8px; font-size: 12px;">Activado</span>
        </div>
        <div class="form-col-3">
        <label>Intensidad Umbral</label>
        <input type="number" 
               id="abr_umbral_intensidad" 
               class="abr-input"
               min="0" max="80" step="5"
               value="${existingData.intensidad_umbral?.valor || 30}"
               placeholder="30"> dB nHL
        </div>
        <div class="form-col-3">
        <label>Umbral Habilitado</label>
        <input type="checkbox" id="abr_umbral_enabled" ${existingData.intensidad_umbral?.habilitado !== false ? 'checked' : ''}>
        <span style="margin-left: 8px; font-size: 12px;">Activado</span>
        </div>
        </div>

        <div class="form-row">
        <div class="form-col-2">
        <label>Generar Onda II</label>
        <input type="checkbox" id="abr_generar_onda_ii" ${existingData.generar_ondas?.II !== false ? 'checked' : ''}>
        <span style="margin-left: 8px; font-size: 12px;">Auto-calcular</span>
        </div>
        <div class="form-col-2">
        <label>Generar Onda IV</label>
        <input type="checkbox" id="abr_generar_onda_iv" ${existingData.generar_ondas?.IV !== false ? 'checked' : ''}>
        <span style="margin-left: 8px; font-size: 12px;">Auto-calcular</span>
        </div>
        </div>
        </div>

        <!-- Formularios por Estímulo -->
        <div class="abr-stimulus-forms">
        ${this.stimulusTypes.map(stimulus => this.renderStimulusForm(stimulus, existingData[stimulus.id])).join('')}
        </div>

        <!-- Observaciones -->
        <div class="form-group" style="margin-top: 20px;">
        <label class="label-optional">Observaciones</label>
        <textarea id="abr_observations"
                  rows="3"
                  placeholder="Comentarios sobre morfología, replicabilidad, calidad técnica...">${existingData.observaciones || ''}</textarea>
        </div>
        </div>

        <!-- Panel de Gráficos -->
        <div style="flex: 3; min-width: 500px;">
        <h4 class="section-subtitle">📊 Visualización de Resultados</h4>
        
        <!-- Formas de Onda 80 dB -->
        <div class="chart-container">
        <h5>Formas de Onda - 80 dB nHL</h5>
        <div id="abrWaveform80Canvas" class="chart-placeholder">
        <div class="placeholder-content">
        <span>📈 Gráfico de formas de onda</span>
        <small>Ondas I, II, III, IV, V por oído</small>
        </div>
        </div>
        </div>
        
        <!-- Formas de Onda Umbral -->
        <div class="chart-container">
        <h5>Formas de Onda - Umbral</h5>
        <div id="abrWaveformThresholdCanvas" class="chart-placeholder">
        <div class="placeholder-content">
        <span>📈 Gráfico de umbral</span>
        <small>Ondas detectables al umbral</small>
        </div>
        </div>
        </div>
        
        <!-- Curvas Latencia-Intensidad -->
        <div class="chart-container">
        <h5>Curvas Latencia-Intensidad</h5>
        <div id="abrLatencyCanvas" class="chart-placeholder">
        <div class="placeholder-content">
        <span>📊 Curvas L-I</span>
        <small>Latencia vs Intensidad por onda</small>
        </div>
        </div>
        </div>
        </div>
        </div>
        </div>

        <style>
        .abr-stimulus-selector {
            margin-bottom: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
        }

        .stimulus-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }

        .stimulus-tab {
            padding: 8px 16px;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            background: white;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s ease;
        }

        .stimulus-tab.active {
            border-color: #6f42c1;
            background: #6f42c1;
            color: white;
        }

        .stimulus-tab:hover:not(.active) {
            border-color: #6f42c1;
            color: #6f42c1;
        }

        .abr-global-config {
            margin-bottom: 25px;
            padding: 15px;
            background: #f1f3f4;
            border-radius: 8px;
            border-left: 4px solid #6f42c1;
        }

        .abr-stimulus-forms {
            margin-bottom: 20px;
        }

        .stimulus-form {
            display: none;
            padding: 20px;
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
        }

        .stimulus-form.active {
            display: block;
        }

        .abr-ear-section {
            margin-bottom: 25px;
            padding: 15px;
            background: #fafafa;
            border-radius: 6px;
            border-left: 3px solid;
        }

        .abr-ear-section.od {
            border-left-color: #dc3545;
        }

        .abr-ear-section.oi {
            border-left-color: #007bff;
        }

        .ear-title {
            font-weight: 600;
            margin-bottom: 15px;
            color: #333;
        }

        .ear-title.od {
            color: #dc3545;
        }

        .ear-title.oi {
            color: #007bff;
        }

        .abr-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-bottom: 15px;
        }

        .abr-table th {
            background: #e9ecef;
            border: 1px solid #dee2e6;
            padding: 6px 8px;
            text-align: center;
            font-weight: 600;
            font-size: 12px;
        }

        .abr-table td {
            border: 1px solid #dee2e6;
            padding: 4px 6px;
            text-align: center;
        }

        .wave-label {
            background: #f8f9fa;
            font-weight: 500;
            width: 40px;
        }

        .wave-label.auto {
            background: #fff3cd;
            color: #856404;
            font-style: italic;
        }

        .abr-input {
            width: 60px;
            padding: 3px 5px;
            border: 1px solid #ced4da;
            border-radius: 3px;
            text-align: center;
            font-size: 12px;
        }

        .abr-input:focus {
            border-color: #6f42c1;
            outline: none;
            box-shadow: 0 0 0 2px rgba(111, 66, 193, 0.1);
        }

        .abr-input:disabled {
            background: #f8f9fa;
            color: #6c757d;
        }

        .abr-checkbox {
            transform: scale(0.9);
        }

        .morphology-section {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-top: 10px;
            padding: 8px 12px;
            background: #e8f5e8;
            border-radius: 4px;
        }

        .chart-container {
            margin-bottom: 15px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            background: white;
        }

        .chart-container h5 {
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #495057;
            text-align: center;
        }

        .chart-placeholder {
            height: 150px;
            background: #f8f9fa;
            border: 2px dashed #dee2e6;
            border-radius: 4px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #6c757d;
        }

        .placeholder-content span {
            font-size: 16px;
            margin-bottom: 5px;
            display: block;
        }

        .placeholder-content small {
            font-size: 12px;
            opacity: 0.7;
        }
        </style>
        `;
    }

    /**
     * Renderizar selector de estímulo
     */
    renderStimulusSelector(activeStimulus) {
        return `
        <div class="stimulus-tabs">
        ${this.stimulusTypes.map(stimulus => `
        <div class="stimulus-tab ${stimulus.id === activeStimulus ? 'active' : ''}" 
             data-stimulus="${stimulus.id}">
        ${stimulus.icon} ${stimulus.name}
        </div>
        `).join('')}
        </div>
        `;
    }

    /**
     * Renderizar formulario por estímulo
     */
    renderStimulusForm(stimulus, existingData = {}) {
        const isActive = false; // Se manejará con JavaScript
        
        return `
        <div class="stimulus-form ${isActive ? 'active' : ''}" id="form_${stimulus.id}">
        <h4 class="section-subtitle">${stimulus.icon} ${stimulus.name}</h4>
        
        ${this.renderEarSection('od', 'Oído Derecho', existingData?.oido_derecho, stimulus.id)}
        ${this.renderEarSection('oi', 'Oído Izquierdo', existingData?.oido_izquierdo, stimulus.id)}
        </div>
        `;
    }

    /**
     * Renderizar sección por oído
     */
    renderEarSection(earId, earTitle, existingData = {}, stimulusId) {
        return `
        <div class="abr-ear-section ${earId}">
        <h5 class="ear-title ${earId}">${earTitle}</h5>
        
        <!-- Tabla de Ondas 80 dB -->
        <div class="intensity-section">
        <label style="font-weight: 600; margin-bottom: 8px; display: block;">Intensidad 80 dB nHL</label>
        <table class="abr-table">
        <thead>
        <tr>
        <th>Onda</th>
        <th>Latencia (ms)</th>
        <th>Amplitud (µV)</th>
        <th>Replicabilidad (ms)</th>
        </tr>
        </thead>
        <tbody>
        ${this.renderWaveRows(earId, stimulusId, '80db', existingData['80db'])}
        </tbody>
        </table>
        </div>

        <!-- Tabla de Ondas Umbral -->
        <div class="intensity-section">
        <label style="font-weight: 600; margin-bottom: 8px; display: block;">Intensidad Umbral</label>
        <table class="abr-table">
        <thead>
        <tr>
        <th>Onda</th>
        <th>Latencia (ms)</th>
        <th>Amplitud (µV)</th>
        <th>Replicabilidad (ms)</th>
        </tr>
        </thead>
        <tbody>
        ${this.renderWaveRows(earId, stimulusId, 'umbral', existingData['umbral'])}
        </tbody>
        </table>
        </div>

        <!-- Morfología -->
        <div class="morphology-section">
        <label style="font-weight: 500;">
        <input type="checkbox" 
               class="abr-checkbox" 
               id="${stimulusId}_morfologia_${earId}"
               ${existingData.buena_morfologia !== false ? 'checked' : ''}>
        Buena morfología
        </label>
        </div>
        </div>
        `;
    }

    /**
     * Renderizar filas de ondas
     */
    renderWaveRows(earId, stimulusId, intensity, existingData = {}) {
        return this.waves.map(wave => {
            const isAuto = this.autoWaves.includes(wave);
            const waveData = existingData[`onda_${wave}`] || {};
            const disabled = isAuto ? 'disabled' : '';
            const autoClass = isAuto ? 'auto' : '';
            
            return `
            <tr>
            <td class="wave-label ${autoClass}">
            ${wave}${isAuto ? '*' : ''}
            </td>
            <td>
            <input type="number" 
                   class="abr-input wave-latency" 
                   id="${stimulusId}_${intensity}_latencia_${wave}_${earId}"
                   min="0" max="10" step="0.01"
                   value="${waveData.latencia || ''}"
                   placeholder="${this.getDefaultLatency(wave, intensity)}"
                   ${disabled}>
            </td>
            <td>
            <input type="number" 
                   class="abr-input wave-amplitude" 
                   id="${stimulusId}_${intensity}_amplitud_${wave}_${earId}"
                   min="0" max="5" step="0.01"
                   value="${waveData.amplitud || ''}"
                   placeholder="0.25"
                   ${disabled}>
            </td>
            <td>
            <input type="number" 
                   class="abr-input wave-replicability" 
                   id="${stimulusId}_${intensity}_replicabilidad_${wave}_${earId}"
                   min="0" max="1" step="0.01"
                   value="${waveData.replicabilidad || '0.08'}"
                   placeholder="0.08">
            </td>
            </tr>
            `;
        }).join('');
    }

    /**
     * Obtener latencia por defecto para una onda
     */
    getDefaultLatency(wave, intensity) {
        const defaults = {
            '80db': { 'I': '1.5', 'II': '2.5', 'III': '3.5', 'IV': '4.5', 'V': '5.5' },
            'umbral': { 'I': '1.8', 'II': '2.8', 'III': '3.8', 'IV': '4.8', 'V': '5.8' }
        };
        return defaults[intensity]?.[wave] || '';
    }

    /**
     * Inicializar eventos después de renderizar
     */
    async initEvents() {
        // Configurar tabs de estímulo
        this.setupStimulusTabs();

        // Auto-cálculo de ondas II y IV
        this.setupAutoCalculation();

        // Auto-save al cambiar valores
        const inputs = document.querySelectorAll('#tabsContent input, #tabsContent textarea');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                this.updateAutoWaves();
                this.app.updateModuleData(this.moduleId, this.getData());
            });

            input.addEventListener('change', () => {
                this.updateAutoWaves();
                this.app.updateModuleData(this.moduleId, this.getData());
            });
        });

        // Configurar estado inicial
        this.updateIntensityStates();
        this.updateAutoWaves();
    }

    /**
     * Configurar tabs de estímulo
     */
    setupStimulusTabs() {
        const tabs = document.querySelectorAll('.stimulus-tab');
        const forms = document.querySelectorAll('.stimulus-form');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const stimulusId = tab.dataset.stimulus;

                // Actualizar tabs activos
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                // Actualizar formularios activos
                forms.forEach(f => f.classList.remove('active'));
                const targetForm = document.getElementById(`form_${stimulusId}`);
                if (targetForm) {
                    targetForm.classList.add('active');
                }

                // Guardar estímulo activo
                this.app.updateModuleData(this.moduleId, { 
                    ...this.getData(), 
                    stimulus_activo: stimulusId 
                });
            });
        });

        // Activar primer tab por defecto
        if (tabs.length > 0) {
            tabs[0].click();
        }
    }

    /**
     * Configurar auto-cálculo de ondas
     */
    setupAutoCalculation() {
        // Checkboxes de habilitación de intensidades
        const cb80db = document.getElementById('abr_80db_enabled');
        const cbUmbral = document.getElementById('abr_umbral_enabled');

        [cb80db, cbUmbral].forEach(cb => {
            if (cb) {
                cb.addEventListener('change', () => {
                    this.updateIntensityStates();
                });
            }
        });

        // Checkboxes de generación de ondas auto
        const cbOndaII = document.getElementById('abr_generar_onda_ii');
        const cbOndaIV = document.getElementById('abr_generar_onda_iv');

        [cbOndaII, cbOndaIV].forEach(cb => {
            if (cb) {
                cb.addEventListener('change', () => {
                    this.updateAutoWaves();
                });
            }
        });
    }

    /**
     * Actualizar estados de intensidades
     */
    updateIntensityStates() {
        const enabled80db = document.getElementById('abr_80db_enabled')?.checked ?? true;
        const enabledUmbral = document.getElementById('abr_umbral_enabled')?.checked ?? true;

        // Habilitar/deshabilitar campos según checkboxes
        const fields80db = document.querySelectorAll('[id*="_80db_"]');
        const fieldsUmbral = document.querySelectorAll('[id*="_umbral_"]');

        fields80db.forEach(field => {
            field.disabled = !enabled80db;
            if (!enabled80db) field.value = '';
        });

        fieldsUmbral.forEach(field => {
            field.disabled = !enabledUmbral;
            if (!enabledUmbral) field.value = '';
        });
    }

    /**
     * Actualizar ondas auto-calculadas
     */
    updateAutoWaves() {
        const generateII = document.getElementById('abr_generar_onda_ii')?.checked ?? true;
        const generateIV = document.getElementById('abr_generar_onda_iv')?.checked ?? true;

        this.stimulusTypes.forEach(stimulus => {
            ['od', 'oi'].forEach(ear => {
                ['80db', 'umbral'].forEach(intensity => {
                    if (generateII) {
                        this.calculateWaveII(stimulus.id, ear, intensity);
                    }
                    if (generateIV) {
                        this.calculateWaveIV(stimulus.id, ear, intensity);
                    }
                });
            });
        });
    }

    /**
     * Calcular onda II (promedio entre I y III)
     */
    calculateWaveII(stimulusId, ear, intensity) {
        const latencyI = this.getFieldValue(`${stimulusId}_${intensity}_latencia_I_${ear}`);
        const latencyIII = this.getFieldValue(`${stimulusId}_${intensity}_latencia_III_${ear}`);
        const amplitudeI = this.getFieldValue(`${stimulusId}_${intensity}_amplitud_I_${ear}`);
        const amplitudeIII = this.getFieldValue(`${stimulusId}_${intensity}_amplitud_III_${ear}`);

        if (latencyI && latencyIII) {
            const calculatedLatency = ((parseFloat(latencyI) + parseFloat(latencyIII)) / 2).toFixed(2);
            this.setFieldValue(`${stimulusId}_${intensity}_latencia_II_${ear}`, calculatedLatency);
        }

        if (amplitudeI && amplitudeIII) {
            const calculatedAmplitude = ((parseFloat(amplitudeI) + parseFloat(amplitudeIII)) / 2).toFixed(2);
            this.setFieldValue(`${stimulusId}_${intensity}_amplitud_II_${ear}`, calculatedAmplitude);
        }
    }

    /**
     * Calcular onda IV (promedio entre III y V)
     */
    calculateWaveIV(stimulusId, ear, intensity) {
        const latencyIII = this.getFieldValue(`${stimulusId}_${intensity}_latencia_III_${ear}`);
        const latencyV = this.getFieldValue(`${stimulusId}_${intensity}_latencia_V_${ear}`);
        const amplitudeIII = this.getFieldValue(`${stimulusId}_${intensity}_amplitud_III_${ear}`);
        const amplitudeV = this.getFieldValue(`${stimulusId}_${intensity}_amplitud_V_${ear}`);

        if (latencyIII && latencyV) {
            const calculatedLatency = ((parseFloat(latencyIII) + parseFloat(latencyV)) / 2).toFixed(2);
            this.setFieldValue(`${stimulusId}_${intensity}_latencia_IV_${ear}`, calculatedLatency);
        }

        if (amplitudeIII && amplitudeV) {
            const calculatedAmplitude = ((parseFloat(amplitudeIII) + parseFloat(amplitudeV)) / 2).toFixed(2);
            this.setFieldValue(`${stimulusId}_${intensity}_amplitud_IV_${ear}`, calculatedAmplitude);
        }
    }

    /**
     * Helper para obtener valor de campo
     */
    getFieldValue(id) {
        const field = document.getElementById(id);
        return field?.value || null;
    }

    /**
     * Helper para establecer valor de campo
     */
    setFieldValue(id, value) {
        const field = document.getElementById(id);
        if (field && !field.disabled) {
            field.value = value;
        }
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

        const getCheckboxValue = (id) => {
            const element = document.getElementById(id);
            return element ? element.checked : false;
        };

        const data = {
            stimulus_activo: document.querySelector('.stimulus-tab.active')?.dataset.stimulus || 'click',
            intensidad_80db: {
                habilitado: getCheckboxValue('abr_80db_enabled'),
                valor: 80
            },
            intensidad_umbral: {
                habilitado: getCheckboxValue('abr_umbral_enabled'),
                valor: getNumberValue('abr_umbral_intensidad')
            },
            generar_ondas: {
                II: getCheckboxValue('abr_generar_onda_ii'),
                IV: getCheckboxValue('abr_generar_onda_iv')
            },
            observaciones: getValue('abr_observations')
        };

        // Recopilar datos por estímulo
        this.stimulusTypes.forEach(stimulus => {
            data[stimulus.id] = {
                oido_derecho: this.getEarData(stimulus.id, 'od'),
                oido_izquierdo: this.getEarData(stimulus.id, 'oi')
            };
        });

        return data;
    }

    /**
     * Obtener datos de un oído específico
     */
    getEarData(stimulusId, earId) {
        const getWaveData = (intensity) => {
            const waveData = {};
            this.waves.forEach(wave => {
                const latencia = this.getFieldValue(`${stimulusId}_${intensity}_latencia_${wave}_${earId}`);
                const amplitud = this.getFieldValue(`${stimulusId}_${intensity}_amplitud_${wave}_${earId}`);
                const replicabilidad = this.getFieldValue(`${stimulusId}_${intensity}_replicabilidad_${wave}_${earId}`);

                if (latencia || amplitud || replicabilidad) {
                    waveData[`onda_${wave}`] = {
                        latencia: latencia ? parseFloat(latencia) : null,
                        amplitud: amplitud ? parseFloat(amplitud) : null,
                        replicabilidad: replicabilidad ? parseFloat(replicabilidad) : null
                    };
                }
            });
            return waveData;
        };

        return {
            '80db': getWaveData('80db'),
            'umbral': getWaveData('umbral'),
            buena_morfologia: document.getElementById(`${stimulusId}_morfologia_${earId}`)?.checked ?? true
        };
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        const errors = [];

        // Validar rangos de latencias
        this.stimulusTypes.forEach(stimulus => {
            ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
                ['80db', 'umbral'].forEach(intensity => {
                    const intensityData = data[stimulus.id]?.[ear]?.[intensity];
                    if (intensityData) {
                        this.waves.forEach(wave => {
                            const waveData = intensityData[`onda_${wave}`];
                            if (waveData) {
                                if (waveData.latencia !== null && (waveData.latencia < 0.5 || waveData.latencia > 10)) {
                                    errors.push(`Latencia onda ${wave} en ${stimulus.name} ${ear} ${intensity} fuera de rango (0.5-10 ms)`);
                                }
                                if (waveData.amplitud !== null && (waveData.amplitud < 0 || waveData.amplitud > 5)) {
                                    errors.push(`Amplitud onda ${wave} en ${stimulus.name} ${ear} ${intensity} fuera de rango (0-5 µV)`);
                                }
                            }
                        });
                    }
                });
            });
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

        // Al menos debe tener un estímulo con datos en al menos un oído
        const hasData = this.stimulusTypes.some(stimulus => {
            const stimulusData = data[stimulus.id];
            if (!stimulusData) return false;

            return ['oido_derecho', 'oido_izquierdo'].some(ear => {
                const earData = stimulusData[ear];
                if (!earData) return false;

                return ['80db', 'umbral'].some(intensity => {
                    const intensityData = earData[intensity];
                    if (!intensityData) return false;

                    // Al menos una onda debe tener latencia
                    return this.waves.some(wave => {
                        const waveData = intensityData[`onda_${wave}`];
                        return waveData?.latencia !== null && waveData?.latencia !== undefined;
                    });
                });
            });
        });

        return hasData;
    }
}

// Exponer globalmente
window.AbrModule = AbrModule;