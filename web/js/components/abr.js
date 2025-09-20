
/**
 * AbrModule - Módulo de Potenciales Evocados Auditivos (ABR)
 * Vista preparada para 3 archivos de gráficos (views) independientes.
 *
 * Cambios clave:
 *  - Sin "Configuración General".
 *  - Sin checkbox de "Buena morfología".
 *  - "Tone Burst" con subselector de frecuencias (500, 1k, 2k, 4k).
 *  - Placeholders convertidos en valores por defecto reales.
 *  - Auto-cálculo de II y IV siempre activo.
 *  - Loader de vistas (3 archivos): ABRWaveform80View, ABRWaveformFinalView, ABRLatencyIntensityView.
 */

class AbrModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'abr';

        // Ondas
        this.waves = ['I', 'II', 'III', 'IV', 'V'];
        this.editableWaves = ['I', 'III', 'V'];
        this.autoWaves = ['II', 'IV'];

        // Tabs de estímulo
        this.displayStimuli = [
            { id: 'click', name: 'Click', icon: '🔊' },
            { id: 'tone_burst', name: 'Tone Burst', icon: '📊' },
            { id: 'chirp', name: 'Chirp', icon: '🌊' }
        ];

        // Subtabs de frecuencia para Tone Burst
        this.toneBurstFrequencies = [
            { id: '500', label: '500 Hz' },
            { id: '1k', label: '1 kHz' },
            { id: '2k', label: '2 kHz' },
            { id: '4k', label: '4 kHz' }
        ];

        // Vistas de gráficos
        this.chartViews = { wf80: null, wfFinal: null, latency: null };
        this.chartViewsStatus = { wf80: 'pending', wfFinal: 'pending', latency: 'pending' };
        this.chartConfig = [
            { key: 'core',   file: 'js/components/views/abr-waveform-core.js',   className: null, canvasId: null },
            { key: 'wf80',   file: 'js/components/views/abr-waveform-80.js',     className: 'ABRWaveform80View',       canvasId: 'abrWaveform80Canvas' },
            { key: 'wfFinal',file: 'js/components/views/abr-waveform-final.js',  className: 'ABRWaveformFinalView',    canvasId: 'abrWaveformFinalCanvas' },
            { key: 'latency',file: 'js/components/views/abr-li-curves.js',       className: 'ABRLatencyIntensityView', canvasId: 'abrLatencyCanvas' },
        ];
    }

    /**
     * Render principal
     */
    async render(existingData = {}) {
        const activeStimulus = existingData.stimulus_activo || 'click';
        const activeTbFreq = existingData.tone_burst_activo || '1k';

        return `
        <div class="form-section">
        <h3 class="section-title">⚡ Potenciales Evocados Auditivos (ABR)</h3>
        <p class="section-description">Evaluación de la función auditiva mediante potenciales evocados del tronco cerebral</p>

        <div style="display: flex; gap: 30px;">
        <!-- Panel de Formularios -->
        <div style="flex: 2; min-width: 450px;">
        <!-- Tabs estímulo -->
        <div class="abr-stimulus-selector">
        ${this.renderStimulusSelector(activeStimulus)}
        </div>

        <!-- Formularios -->
        <div class="abr-stimulus-forms">
        ${this.renderStimulusForm({ id: 'click', name: 'Click', icon: '🔊' }, existingData['click'])}
        ${this.renderToneBurstForm(existingData['tone_burst'], activeTbFreq)}
        ${this.renderStimulusForm({ id: 'chirp', name: 'Chirp', icon: '🌊' }, existingData['chirp'])}
        </div>

        <!-- Observaciones -->
        <div class="form-group" style="margin-top: 20px;">
        <label class="label-optional">Observaciones</label>
        <textarea id="abr_observations" rows="3" placeholder="Comentarios clínicos...">${existingData.observaciones || ''}</textarea>
        </div>
        </div>

        <!-- Panel de Gráficos -->
        <div style="flex: 3; min-width: 500px;">
        <h4 class="section-subtitle">📊 Visualización de Resultados</h4>

        <div class="chart-container">
        <h5>Formas de Onda - 80 dB nHL</h5>
        <canvas id="abrWaveform80Canvas" class="chart-placeholder"></canvas>
        </div>

        <div class="chart-container">
        <h5>Formas de Onda - Final</h5>
        <canvas id="abrWaveformFinalCanvas" class="chart-placeholder"></canvas>
        </div>

        <div class="chart-container">
        <h5>Curvas Latencia-Intensidad</h5>
        <canvas id="abrLatencyCanvas" class="chart-placeholder"></canvas>
        </div>
        </div>
        </div>
        </div>

        <style>
        .abr-stimulus-selector { margin-bottom: 20px; background: #f8f9fa; border-radius: 8px; padding: 15px; }
        .stimulus-tabs { display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; }
        .stimulus-tab { padding: 8px 16px; border: 2px solid #dee2e6; border-radius: 6px; background: white; cursor: pointer; font-size: 13px; transition: all 0.2s ease; }
        .stimulus-tab.active { border-color: #6f42c1; background: #6f42c1; color: white; }
        .stimulus-tab:hover:not(.active) { border-color: #6f42c1; color: #6f42c1; }

        .abr-stimulus-forms { margin-bottom: 20px; }
        .stimulus-form { display: none; padding: 20px; background: white; border: 1px solid #dee2e6; border-radius: 8px; }
        .stimulus-form.active { display: block; }

        .tb-freq-tabs { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
        .tb-freq-tab { padding: 6px 10px; border: 1px solid #ced4da; border-radius: 6px; cursor: pointer; }
        .tb-freq-tab.active { background: #0d6efd; color: white; border-color: #0d6efd; }
        .tb-freq-form { display: none; }
        .tb-freq-form.active { display: block; }

        .abr-ear-section { margin-bottom: 25px; padding: 15px; background: #fafafa; border-radius: 6px; border-left: 3px solid; }
        .abr-ear-section.od { border-left-color: #dc3545; }
        .abr-ear-section.oi { border-left-color: #007bff; }
        .ear-title { font-weight: 600; margin-bottom: 15px; color: #333; }
        .ear-title.od { color: #dc3545; }
        .ear-title.oi { color: #007bff; }

        .abr-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 15px; }
        .abr-table th { background: #e9ecef; border: 1px solid #dee2e6; padding: 6px 8px; text-align: center; font-weight: 600; font-size: 12px; }
        .abr-table td { border: 1px solid #dee2e6; padding: 4px 6px; text-align: center; }

        .wave-label { background: #f8f9fa; font-weight: 500; width: 40px; }
        .wave-label.auto { background: #fff3cd; color: #856404; font-style: italic; }

        .abr-input { width: 60px; padding: 3px 5px; border: 1px solid #ced4da; border-radius: 3px; text-align: center; font-size: 12px; }
        .abr-input:focus { border-color: #6f42c1; outline: none; box-shadow: 0 0 0 2px rgba(111,66,193,0.1); }
        .abr-input:disabled { background: #f8f9fa; color: #6c757d; }

        .abr-checkbox { transform: scale(0.9); }

        .chart-container { margin-bottom: 15px; border: 1px solid #dee2e6; border-radius: 6px; padding: 15px; background: white; }
        .chart-container h5 { margin: 0 0 10px 0; font-size: 14px; color: #495057; text-align: center; }
        .chart-placeholder { width: 100%; height: 180px; background: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 4px; }
        </style>
        `;
    }

    /**
     * Selector de estímulo
     */
    renderStimulusSelector(activeStimulus) {
        return `
        <div class="stimulus-tabs">
        ${this.displayStimuli.map(stimulus => `
            <div class="stimulus-tab ${stimulus.id === activeStimulus ? 'active' : ''}" data-stimulus="${stimulus.id}">
            ${stimulus.icon} ${stimulus.name}
            </div>
            `).join('')}
            </div>
            `;
    }

    /**
     * Formulario simple (click, chirp)
     */
    renderStimulusForm(stimulus, existingData = {}) {
        const isActive = false;
        return `
        <div class="stimulus-form ${isActive ? 'active' : ''}" id="form_${stimulus.id}" data-stimulus="${stimulus.id}">
        <h4 class="section-subtitle">${stimulus.icon} ${stimulus.name}</h4>
        ${this.renderEarSection('od', 'Oído Derecho', existingData?.oido_derecho, stimulus.id)}
        ${this.renderEarSection('oi', 'Oído Izquierdo', existingData?.oido_izquierdo, stimulus.id)}
        </div>
        `;
    }

    /**
     * Formulario con subselector de frecuencias para Tone Burst
     */
    renderToneBurstForm(existingData = {}, activeFreq = '1k') {
        const isActive = false;
        return `
        <div class="stimulus-form ${isActive ? 'active' : ''}" id="form_tone_burst" data-stimulus="tone_burst">
        <h4 class="section-subtitle">📊 Tone Burst</h4>
        <div class="tb-freq-tabs">
        ${this.toneBurstFrequencies.map(f => `
            <div class="tb-freq-tab ${f.id === activeFreq ? 'active' : ''}" data-tb-freq="${f.id}">${f.label}</div>
            `).join('')}
            </div>

            ${this.toneBurstFrequencies.map(f => `
                <div class="tb-freq-form ${f.id === activeFreq ? 'active' : ''}" id="tb_form_${f.id}" data-tb-freq="${f.id}">
                ${this.renderEarSection('od', 'Oído Derecho', existingData?.[f.id]?.oido_derecho, `tone_burst_${f.id}`)}
                ${this.renderEarSection('oi', 'Oído Izquierdo', existingData?.[f.id]?.oido_izquierdo, `tone_burst_${f.id}`)}
                </div>
                `).join('')}
                </div>
                `;
    }

    /**
     * Sección por oído
     */
    renderEarSection(earId, earTitle, existingData = {}, stimulusId) {
        return `
        <div class="abr-ear-section ${earId}">
        <h5 class="ear-title ${earId}">${earTitle}</h5>

        <div class="intensity-section">
        <label style="font-weight: 600; margin-bottom: 8px; display: block;">Intensidad 80 dB nHL</label>
        <table class="abr-table">
        <thead>
        <tr>
        <th>Onda</th><th>Presente</th><th>Latencia (ms)</th><th>Amplitud (µV)</th><th>Replicabilidad (ms)</th>
        </tr>
        </thead>
        <tbody>
        ${this.renderWaveRows(earId, stimulusId, '80db', existingData?.['80db'] || {})}
        </tbody>
        </table>
        </div>

        <div class="intensity-section">
        <label style="font-weight: 600; margin-bottom: 8px; display: block;">Intensidad Final</label>
        <table class="abr-table">
        <thead>
        <tr>
        <th>Onda</th><th>Presente</th><th>Latencia (ms)</th><th>Amplitud (µV)</th><th>Replicabilidad (ms)</th>
        </tr>
        </thead>
        <tbody>
        ${this.renderWaveRows(earId, stimulusId, 'final', existingData?.['final'] || {})}
        </tbody>
        </table>
        </div>
        </div>
        `;
    }

    /**
     * Filas de ondas
     */
    renderWaveRows(earId, stimulusId, intensity, existingData = {}) {
        return this.waves.map(wave => {
            const isAuto = this.autoWaves.includes(wave);
            const wd = existingData[`onda_${wave}`] || {};
            const disabled = isAuto ? 'disabled' : '';
            const autoClass = isAuto ? 'auto' : '';
            const isPresent = wd.presente !== false; // por defecto true

            const defaultLatency = this.getDefaultLatency(wave, intensity);
            const defaultAmplitude = '0.25';
            const defaultRep = '0.05';

            return `
            <tr>
            <td class="wave-label ${autoClass}">${wave}${isAuto ? '*' : ''}</td>
            <td>
            <input type="checkbox" class="abr-checkbox wave-presence"
            id="${stimulusId}_${intensity}_presente_${wave}_${earId}"
            ${isPresent ? 'checked' : ''} ${disabled}>
            </td>
            <td>
            <input type="number" class="abr-input wave-latency"
            id="${stimulusId}_${intensity}_latencia_${wave}_${earId}"
            min="0" max="10" step="0.01"
            value="${wd.latencia ?? defaultLatency}"
            ${disabled || !isPresent ? 'disabled' : ''}>
            </td>
            <td>
            <input type="number" class="abr-input wave-amplitude"
            id="${stimulusId}_${intensity}_amplitud_${wave}_${earId}"
            min="0" max="5" step="0.01"
            value="${wd.amplitud ?? defaultAmplitude}"
            ${disabled || !isPresent ? 'disabled' : ''}>
            </td>
            <td>
            <input type="number" class="abr-input wave-replicability"
            id="${stimulusId}_${intensity}_replicabilidad_${wave}_${earId}"
            min="0" max="1" step="0.01"
            value="${wd.replicabilidad ?? defaultRep}"
            ${!isPresent ? 'disabled' : ''}>
            </td>
            </tr>
            `;
        }).join('');
    }

    /**
     * Defaults de latencia (puedes ajustar si tu protocolo difiere)
     */
    getDefaultLatency(wave, intensity) {
        const defaults = {
            '80db': { 'I': '1.5', 'II': '2.5', 'III': '3.5', 'IV': '4.5', 'V': '5.5' },
            'final': { 'I': '1.8', 'II': '2.8', 'III': '3.8', 'IV': '4.8', 'V': '5.8' }
        };
        return defaults[intensity]?.[wave] || '';
    }

    /**
     * Eventos y loader de vistas
     */
    async initEvents() {
        this.setupStimulusTabs();
        this.setupToneBurstTabs();
        this.setupPresenceControls();

        // Auto-save + repaint de charts
        const inputs = document.querySelectorAll('#tabsContent input, #tabsContent textarea');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                this.updateAutoWaves();
                this.app.updateModuleData(this.moduleId, this.getData());
                this.updateABRPreviews();
            });
            input.addEventListener('change', () => {
                this.updateAutoWaves();
                this.app.updateModuleData(this.moduleId, this.getData());
                this.updateABRPreviews();
            });
        });

        // Carga de vistas
        await this.loadChartViews();

        // Estado inicial
        this.updatePresenceStates();
        this.updateAutoWaves();
        this.updateABRPreviews();
    }

    async loadChartViews() {
        for (const cfg of this.chartConfig) {
            try {
                await this.app.loadScript(cfg.file);
                if (window[cfg.className]) {
                    this.chartViews[cfg.key] = new window[cfg.className](cfg.canvasId);
                    this.chartViewsStatus[cfg.key] = 'loaded';
                } else {
                    this.chartViews[cfg.key] = null;
                    this.chartViewsStatus[cfg.key] = 'error';
                }
            } catch (e) {
                this.chartViews[cfg.key] = null;
                this.chartViewsStatus[cfg.key] = 'missing';
            }
        }
    }

    /**
     * Tabs estímulo
     */
    setupStimulusTabs() {
        const tabs = document.querySelectorAll('.stimulus-tab');
        const forms = document.querySelectorAll('.stimulus-form');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const id = tab.dataset.stimulus;
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                forms.forEach(f => f.classList.remove('active'));
                const target = document.getElementById(`form_${id}`);
                if (target) target.classList.add('active');

                const data = this.getData();
                data.stimulus_activo = id;
                this.app.updateModuleData(this.moduleId, data);

                this.updateABRPreviews();
            });
        });

        if (tabs.length > 0) {
            const anyActive = Array.from(forms).some(f => f.classList.contains('active'));
            if (!anyActive) tabs[0].click();
        }
    }

    /**
     * Subtabs de Tone Burst
     */
    setupToneBurstTabs() {
        const freqTabs = document.querySelectorAll('.tb-freq-tab');
        const freqForms = document.querySelectorAll('.tb-freq-form');

        freqTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const fid = tab.dataset.tbFreq;
                freqTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                freqForms.forEach(f => f.classList.remove('active'));
                const target = document.getElementById(`tb_form_${fid}`);
                if (target) target.classList.add('active');

                const data = this.getData();
                data.tone_burst_activo = fid;
                this.app.updateModuleData(this.moduleId, data);

                this.updateABRPreviews();
            });
        });

        if (freqTabs.length > 0) {
            const anyActive = Array.from(freqForms).some(f => f.classList.contains('active'));
            if (!anyActive) freqTabs[0].click();
        }
    }

    /**
     * Presencia on/off
     */
    setupPresenceControls() {
        const presenceCheckboxes = document.querySelectorAll('.wave-presence');
        presenceCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updatePresenceStates();
                this.updateAutoWaves();
                this.updateABRPreviews();
            });
        });
    }

    updatePresenceStates() {
        const presenceCheckboxes = document.querySelectorAll('.wave-presence');
        presenceCheckboxes.forEach(cb => {
            const isPresent = cb.checked;
            const waveId = cb.id; // e.g., tone_burst_1k_80db_presente_I_od
            const latencyId = waveId.replace('_presente_', '_latencia_');
            const amplitudeId = waveId.replace('_presente_', '_amplitud_');
            const replicabilityId = waveId.replace('_presente_', '_replicabilidad_');

            const waveMatch = waveId.match(/_presente_([IVX]+)_/); // I, II, III, IV, V
            const waveLabel = waveMatch ? waveMatch[1] : '';
            const isAutoWave = (waveLabel === 'II' || waveLabel === 'IV');

            const latF = document.getElementById(latencyId);
            const ampF = document.getElementById(amplitudeId);
            const repF = document.getElementById(replicabilityId);

            if (latF) latF.disabled = !isPresent || isAutoWave;
            if (ampF) ampF.disabled = !isPresent || isAutoWave;
            if (repF) repF.disabled = !isPresent;

            if (!isPresent) {
                if (latF) latF.value = '';
                if (ampF) ampF.value = '';
                if (repF) repF.value = '';
            }
        });
    }

    /**
     * Auto-cálculo II y IV (siempre activo)
     */
    updateAutoWaves() {
        const latI = document.querySelectorAll('[id*="_latencia_I_"]');
        latI.forEach(fieldI => {
            const fieldIII = document.getElementById(fieldI.id.replace('_latencia_I_', '_latencia_III_'));
            const fieldV   = document.getElementById(fieldI.id.replace('_latencia_I_', '_latencia_V_'));
            const ampI     = document.getElementById(fieldI.id.replace('_latencia_I_', '_amplitud_I_'));
            const ampIII   = document.getElementById(fieldI.id.replace('_latencia_I_', '_amplitud_III_'));
            const ampV     = document.getElementById(fieldI.id.replace('_latencia_I_', '_amplitud_V_'));

            // Calcular II
            if (fieldIII && fieldI.value && fieldIII.value) {
                const outII = document.getElementById(fieldI.id.replace('_latencia_I_', '_latencia_II_'));
                if (outII && !outII.disabled) {
                    outII.value = ((parseFloat(fieldI.value) + parseFloat(fieldIII.value)) / 2).toFixed(2);
                }
            }
            if (ampI && ampIII && ampI.value && ampIII.value) {
                const outAII = document.getElementById(fieldI.id.replace('_latencia_I_', '_amplitud_II_'));
                if (outAII && !outAII.disabled) {
                    outAII.value = ((parseFloat(ampI.value) + parseFloat(ampIII.value)) / 2).toFixed(2);
                }
            }

            // Calcular IV
            if (fieldIII && fieldV && fieldIII.value && fieldV.value) {
                const outIV = document.getElementById(fieldI.id.replace('_latencia_I_', '_latencia_IV_'));
                if (outIV && !outIV.disabled) {
                    outIV.value = ((parseFloat(fieldIII.value) + parseFloat(fieldV.value)) / 2).toFixed(2);
                }
            }
            if (ampIII && ampV && ampIII.value && ampV.value) {
                const outAIV = document.getElementById(fieldI.id.replace('_latencia_I_', '_amplitud_IV_'));
                if (outAIV && !outAIV.disabled) {
                    outAIV.value = ((parseFloat(ampIII.value) + parseFloat(ampV.value)) / 2).toFixed(2);
                }
            }
        });
    }

    /**
     * Redibuja los tres gráficos si la vista está cargada
     */
    updateABRPreviews() {
        const data = this.getData();
        const mapping = { wf80: 'abrWaveform80Canvas', wfFinal: 'abrWaveformFinalCanvas', latency: 'abrLatencyCanvas' };

        Object.keys(this.chartViews).forEach(key => {
            const view = this.chartViews[key];
            const status = this.chartViewsStatus[key];
            const canvasId = mapping[key];

            if (status === 'loaded' && view && typeof view.render === 'function') {
                try {
                    view.render(data);
                } catch (e) {
                    this.renderStatusMessage(canvasId, 'error', key);
                }
            } else {
                this.renderStatusMessage(canvasId, status, key);
            }
        });
    }

    /**
     * Helper: mensaje en canvas cuando falta/carga/error
     * (Esqueleto similar al usado en tus módulos OAE)
     */
    renderStatusMessage(canvasId, status, key) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Clear
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Size fallback
        const w = canvas.width || canvas.clientWidth || 600;
        const h = canvas.height || canvas.clientHeight || 180;
        canvas.width = w;
        canvas.height = h;

        // Style
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        let msg = '';
        if (status === 'pending') msg = 'Cargando vista...';
        else if (status === 'missing') msg = 'Vista no disponible';
        else if (status === 'error') msg = 'Error al renderizar';
        else if (status === 'loaded') msg = 'Listo';

        ctx.fillStyle = '#999';
        ctx.fillText(`[${key}] ${msg}`, w / 2, h / 2);
    }

    /**
     * Data API
     */
    getData() {
        const getValue = (id) => {
            const element = document.getElementById(id);
            return element ? element.value : '';
        };

        const data = {
            stimulus_activo: document.querySelector('.stimulus-tab.active')?.dataset.stimulus || 'click',
            tone_burst_activo: document.querySelector('.tb-freq-tab.active')?.dataset.tbFreq || '1k',
            observaciones: getValue('abr_observations')
        };

        // Click / Chirp
        const collectStimulus = (stimulusId) => ({
            oido_derecho: this.getEarData(stimulusId, 'od'),
                                                 oido_izquierdo: this.getEarData(stimulusId, 'oi')
        });
        data['click'] = collectStimulus('click');
        data['chirp'] = collectStimulus('chirp');

        // Tone Burst por frecuencia
        data['tone_burst'] = {};
        this.toneBurstFrequencies.forEach(f => {
            data['tone_burst'][f.id] = {
                oido_derecho: this.getEarData(`tone_burst_${f.id}`, 'od'),
                                          oido_izquierdo: this.getEarData(`tone_burst_${f.id}`, 'oi')
            };
        });

        return data;
    }

    getEarData(stimulusId, earId) {
        const getWaveData = (intensity) => {
            const waveData = {};
            this.waves.forEach(wave => {
                const presente = document.getElementById(`${stimulusId}_${intensity}_presente_${wave}_${earId}`)?.checked ?? true;
                const lat = document.getElementById(`${stimulusId}_${intensity}_latencia_${wave}_${earId}`)?.value ?? '';
                const amp = document.getElementById(`${stimulusId}_${intensity}_amplitud_${wave}_${earId}`)?.value ?? '';
                const rep = document.getElementById(`${stimulusId}_${intensity}_replicabilidad_${wave}_${earId}`)?.value ?? '';

                if (presente || lat || amp || rep) {
                    waveData[`onda_${wave}`] = {
                        presente: !!presente,
                        latencia: lat ? parseFloat(lat) : null,
                               amplitud: amp ? parseFloat(amp) : null,
                               replicabilidad: rep ? parseFloat(rep) : null
                    };
                }
            });
            return waveData;
        };

        return {
            '80db': getWaveData('80db'),
            'final': getWaveData('final')
        };
    }

    /**
     * Validaciones
     */
    validate(data) {
        const errors = [];
        const checkSet = (set) => {
            ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
                ['80db', 'final'].forEach(intensity => {
                    const intensityData = set?.[ear]?.[intensity];
                    if (intensityData) {
                        this.waves.forEach(wave => {
                            const wd = intensityData[`onda_${wave}`];
                            if (wd && wd.presente) {
                                if (wd.latencia !== null && (wd.latencia < 0.5 || wd.latencia > 10)) {
                                    errors.push(`Latencia onda ${wave} en ${ear} ${intensity} fuera de rango (0.5-10 ms)`);
                                }
                                if (wd.amplitud !== null && (wd.amplitud < 0 || wd.amplitud > 5)) {
                                    errors.push(`Amplitud onda ${wave} en ${ear} ${intensity} fuera de rango (0-5 µV)`);
                                }
                            }
                        });
                    }
                });
            });
        };
        checkSet(data?.click);
        checkSet(data?.chirp);
        Object.keys(data?.tone_burst || {}).forEach(freq => checkSet(data.tone_burst[freq]));

        return { isValid: errors.length === 0, errors };
    }

    /**
     * Completitud mínima
     */
    isComplete(data) {
        if (!data) return false;

        const anySetHasData = (set) => {
            if (!set) return false;
            return ['oido_derecho', 'oido_izquierdo'].some(ear => {
                const earData = set[ear];
                if (!earData) return false;
                return ['80db', 'final'].some(intensity => {
                    const intData = earData[intensity];
                    if (!intData) return false;
                    return this.waves.some(wave => {
                        const wd = intData[`onda_${wave}`];
                        return wd?.presente && wd?.latencia !== null && wd?.latencia !== undefined;
                    });
                });
            });
        };

        const hasClick = anySetHasData(data?.click);
        const hasChirp = anySetHasData(data?.chirp);
        const hasTB = Object.keys(data?.tone_burst || {}).some(freq => anySetHasData(data.tone_burst[freq]));

        return hasClick || hasChirp || hasTB;
    }
}

// Exponer globalmente
window.AbrModule = AbrModule;
