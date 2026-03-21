/**
 * OAEModule - Módulo de Emisiones Otoacústicas
 * EOA Espontáneas, TEOAE/DPOAE Clínicas y Screener
 */

class OaeModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'oae';

        // Frecuencias para cada tipo de prueba
        this.frequencies = {
            teoae: ['1000', '1500', '2000', '3000', '4000'],
            dpoae: ['1000', '1500', '2000', '3000', '4000', '6000']
        };

        // Vistas de gráficos (se cargarán dinámicamente)
        this.chartViews = {
            teoaeClinical: null,
            dpoaeClinical: null,
            teoaeScreener: null,
            dpoaeScreener: null
        };

        // Estado de carga de cada vista
        this.chartViewsStatus = {
            teoaeClinical: 'pending',
            dpoaeClinical: 'pending',
            teoaeScreener: 'pending',
            dpoaeScreener: 'pending'
        };
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        return `
        <div class="form-section">
        <h3 class="section-title">🌊 Emisiones Otoacústicas (EOA)</h3>
        <p class="section-description">
        Evaluación de la función coclear mediante emisiones otoacústicas espontáneas, transientes y productos de distorsión
        </p>

        <!-- Layout Principal: Formularios (40%) + Gráficos (60%) -->
        <div style="display: flex; gap: 30px;">

        <!-- Panel de Formularios -->
        <div style="flex: 2; min-width: 450px;">

        <!-- EOA Espontáneas -->
        <div class="oae-section">
        <h4 class="section-subtitle">EOA Espontáneas</h4>
        <p class="field-note">Emisiones sin estimulación acústica (presentes por defecto en oídos normales)</p>

        <div class="ear-selector-simple">
        <div class="ear-simple">
        <label>OD:</label>
        <select id="espontaneas_od" tabindex="1">
        <option value="presente" ${this.getSelectedValue(existingData.espontaneas?.oido_derecho, 'presente')}>Presente</option>
        <option value="ausente" ${this.getSelectedValue(existingData.espontaneas?.oido_derecho, 'ausente')}>Ausente</option>
        </select>
        </div>
        <div class="ear-simple">
        <label>OI:</label>
        <select id="espontaneas_oi" tabindex="2">
        <option value="presente" ${this.getSelectedValue(existingData.espontaneas?.oido_izquierdo, 'presente')}>Presente</option>
        <option value="ausente" ${this.getSelectedValue(existingData.espontaneas?.oido_izquierdo, 'ausente')}>Ausente</option>
        </select>
        </div>
        </div>
        </div>

        <!-- TEOAE Clínicas -->
        <div class="oae-section">
        <h4 class="section-subtitle">TEOAE Clínicas</h4>
        <p class="field-note">
        <strong>Valores normales:</strong> SNR ≥6 dB = Normal | SNR 3-5 dB = Límite | SNR <3 dB = Ausente
        </p>
        ${this.renderTEOAETable('clinicas', existingData.transientes_clinicas)}
        </div>

        <!-- DPOAE Clínicas -->
        <div class="oae-section">
        <h4 class="section-subtitle">DPOAE Clínicas</h4>
        <p class="field-note">
        <strong>Valores normales:</strong> Amplitud ≥-5 dB SPL = Normal | -10 a -5 dB = Límite | <-10 dB = Ausente
        </p>
        ${this.renderDPOAETable('clinicas', existingData.producto_distorsion_clinicas)}
        </div>

        <!-- TEOAE Screener -->
        <div class="oae-section">
        <h4 class="section-subtitle">TEOAE Screener</h4>
        <p class="field-note" style="color: #666;">
        <em>Se completa automáticamente basado en valores clínicos. Resultado: Pasa/No Pasa por frecuencia</em>
        </p>
        ${this.renderScreenerTable('teoae', existingData.transientes_screener)}
        </div>

        <!-- DPOAE Screener -->
        <div class="oae-section">
        <h4 class="section-subtitle">DPOAE Screener</h4>
        <p class="field-note" style="color: #666;">
        <em>Se completa automáticamente basado en valores clínicos. Resultado: Pasa/No Pasa por frecuencia</em>
        </p>
        ${this.renderScreenerTable('dpoae', existingData.producto_distorsion_screener)}
        </div>

        <!-- Observaciones -->
        <div class="form-group" style="margin-top: 20px;">
        <label class="label-optional">Observaciones</label>
        <textarea id="oae_observations"
        rows="3"
        placeholder="Comentarios sobre las emisiones otoacústicas, calidad de la prueba, etc.">${existingData.observaciones || ''}</textarea>
        </div>
        </div>

        <!-- Panel de Gráficos -->
        <div style="flex: 3; min-width: 500px;">
        <h4 class="section-subtitle">📊 Visualización de Resultados</h4>

        <!-- TEOAE Clínicas -->
        <div class="chart-container">
        <h5>TEOAE Clínicas</h5>
        <canvas id="teoaeClinicasCanvas" width="500" height="300"></canvas>
        </div>

        <!-- DPOAE Clínicas -->
        <div class="chart-container">
        <h5>DPOAE Clínicas</h5>
        <canvas id="dpoaeClinicasCanvas" width="500" height="300"></canvas>
        </div>

        <!-- TEOAE Screener -->
        <div class="chart-container">
        <h5>TEOAE Screener</h5>
        <canvas id="teoaeScreenerCanvas" width="500" height="200"></canvas>
        </div>

        <!-- DPOAE Screener -->
        <div class="chart-container">
        <h5>DPOAE Screener</h5>
        <canvas id="dpoaeScreenerCanvas" width="500" height="200"></canvas>
        </div>
        </div>
        </div>
        </div>

        <style>
        .oae-section {
            margin-bottom: 25px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #17a2b8;
        }

        .field-note {
            font-size: 12px;
            color: #666;
            margin-bottom: 10px;
            line-height: 1.4;
        }

        .ear-selector-simple {
            display: flex;
            gap: 30px;
            align-items: center;
        }

        .ear-simple {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .ear-simple label {
            font-weight: 600;
            color: #333;
            min-width: 25px;
        }

        .ear-simple select {
            padding: 6px 10px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            font-size: 13px;
        }

        .oae-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 10px;
        }

        .oae-table th {
            background: #e9ecef;
            border: 1px solid #dee2e6;
            padding: 6px 8px;
            text-align: center;
            font-weight: 600;
            font-size: 12px;
        }

        .oae-table td {
            border: 1px solid #dee2e6;
            padding: 4px 6px;
            text-align: center;
        }

        .freq-header {
            background: #f1f3f4;
            font-weight: 500;
            writing-mode: vertical-lr;
            text-orientation: mixed;
            width: 35px;
        }

        .oae-input {
            width: 50px;
            padding: 3px 5px;
            border: 1px solid #ced4da;
            border-radius: 3px;
            text-align: center;
            font-size: 12px;
        }

        .oae-input:focus {
            border-color: #17a2b8;
            outline: none;
            box-shadow: 0 0 0 2px rgba(23, 162, 184, 0.1);
        }

        .oae-select {
            width: 70px;
            padding: 2px 4px;
            border: 1px solid #ced4da;
            border-radius: 3px;
            font-size: 11px;
        }

        .screener-result {
            font-weight: 600;
            padding: 3px 6px;
            border-radius: 3px;
            font-size: 11px;
        }

        .screener-result.pasa {
            background: #d4edda;
            color: #155724;
        }

        .screener-result.no-pasa {
            background: #f8d7da;
            color: #721c24;
        }

        .screener-result.pendiente {
            background: #fff3cd;
            color: #856404;
        }

        .chart-container {
            margin-bottom: 15px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 10px;
            background: white;
        }

        .chart-container h5 {
            margin: 0 0 8px 0;
            font-size: 13px;
            color: #495057;
            text-align: center;
        }

        .chart-container canvas {
            width: 100%;
            height: auto;
            display: block;
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
     * Renderizar tabla TEOAE
     */
    renderTEOAETable(type, existingData) {
        const isClinica = type === 'clinicas';
        let html = `
        <table class="oae-table">
        <thead>
        <tr>
        <th rowspan="2">Hz</th>
        <th colspan="2" style="color: #dc3545;">OD</th>
        <th colspan="2" style="color: #007bff;">OI</th>
        </tr>
        <tr>
        <th style="color: #dc3545;">Resp</th>
        <th style="color: #dc3545;">SNR</th>
        <th style="color: #007bff;">Resp</th>
        <th style="color: #007bff;">SNR</th>
        </tr>
        </thead>
        <tbody>
        `;

        this.frequencies.teoae.forEach((freq, index) => {
            const tabIndex = isClinica ? (3 + index * 4) : null;
            const odResp = existingData?.oido_derecho?.[freq]?.respuesta || (isClinica ? '' : 'pendiente');
            const odSNR = existingData?.oido_derecho?.[freq]?.snr || '';
            const oiResp = existingData?.oido_izquierdo?.[freq]?.respuesta || (isClinica ? '' : 'pendiente');
            const oiSNR = existingData?.oido_izquierdo?.[freq]?.snr || '';

            html += `
            <tr>
            <td class="freq-header">${freq}</td>
            <td>
            ${isClinica ? `
                <select class="oae-select" id="teoae_${type}_resp_od_${freq}" ${tabIndex ? `tabindex="${tabIndex}"` : ''}>
                <option value="">-</option>
                <option value="presente" ${odResp === 'presente' ? 'selected' : ''}>Presente</option>
                <option value="ausente" ${odResp === 'ausente' ? 'selected' : ''}>Ausente</option>
                <option value="no_realizado" ${odResp === 'no_realizado' ? 'selected' : ''}>No realizado</option>
                </select>
                ` : `
                <div class="screener-result ${odResp}" id="teoae_screener_resp_od_${freq}">
                ${this.getScreenerLabel(odResp)}
                </div>
                `}
                </td>
                <td>
                ${isClinica ? `
                    <input type="number"
                    class="oae-input"
                    id="teoae_${type}_snr_od_${freq}"
                    min="0" max="30" step="0.1"
                    value="${odSNR}"
                    placeholder="8.5"
                    ${tabIndex ? `tabindex="${tabIndex + 1}"` : ''}>
                    ` : `
                    <span id="teoae_screener_snr_od_${freq}" style="font-size: 11px;">${odSNR}</span>
                    `}
                    </td>
                    <td>
                    ${isClinica ? `
                        <select class="oae-select" id="teoae_${type}_resp_oi_${freq}" ${tabIndex ? `tabindex="${tabIndex + 2}"` : ''}>
                        <option value="">-</option>
                        <option value="presente" ${oiResp === 'presente' ? 'selected' : ''}>Presente</option>
                        <option value="ausente" ${oiResp === 'ausente' ? 'selected' : ''}>Ausente</option>
                        <option value="no_realizado" ${oiResp === 'no_realizado' ? 'selected' : ''}>No realizado</option>
                        </select>
                        ` : `
                        <div class="screener-result ${oiResp}" id="teoae_screener_resp_oi_${freq}">
                        ${this.getScreenerLabel(oiResp)}
                        </div>
                        `}
                        </td>
                        <td>
                        ${isClinica ? `
                            <input type="number"
                            class="oae-input"
                            id="teoae_${type}_snr_oi_${freq}"
                            min="0" max="30" step="0.1"
                            value="${oiSNR}"
                            placeholder="8.5"
                            ${tabIndex ? `tabindex="${tabIndex + 3}"` : ''}>
                            ` : `
                            <span id="teoae_screener_snr_oi_${freq}" style="font-size: 11px;">${oiSNR}</span>
                            `}
                            </td>
                            </tr>
                            `;
        });

        html += '</tbody></table>';
        return html;
    }

    /**
     * Renderizar tabla DPOAE
     */
    renderDPOAETable(type, existingData) {
        const isClinica = type === 'clinicas';
        let html = `
        <table class="oae-table">
        <thead>
        <tr>
        <th rowspan="2">Hz</th>
        <th colspan="2" style="color: #dc3545;">OD</th>
        <th colspan="2" style="color: #007bff;">OI</th>
        </tr>
        <tr>
        <th style="color: #dc3545;">Resp</th>
        <th style="color: #dc3545;">Amp</th>
        <th style="color: #007bff;">Resp</th>
        <th style="color: #007bff;">Amp</th>
        </tr>
        </thead>
        <tbody>
        `;

        this.frequencies.dpoae.forEach((freq, index) => {
            const tabIndex = isClinica ? (50 + index * 4) : null; // Empezar desde 50 para DPOAE
            const odResp = existingData?.oido_derecho?.[freq]?.respuesta || (isClinica ? '' : 'pendiente');
            const odAmp = existingData?.oido_derecho?.[freq]?.amplitud || '';
            const oiResp = existingData?.oido_izquierdo?.[freq]?.respuesta || (isClinica ? '' : 'pendiente');
            const oiAmp = existingData?.oido_izquierdo?.[freq]?.amplitud || '';

            html += `
            <tr>
            <td class="freq-header">${freq}</td>
            <td>
            ${isClinica ? `
                <select class="oae-select" id="dpoae_${type}_resp_od_${freq}" ${tabIndex ? `tabindex="${tabIndex}"` : ''}>
                <option value="">-</option>
                <option value="presente" ${odResp === 'presente' ? 'selected' : ''}>Presente</option>
                <option value="ausente" ${odResp === 'ausente' ? 'selected' : ''}>Ausente</option>
                <option value="no_realizado" ${odResp === 'no_realizado' ? 'selected' : ''}>No realizado</option>
                </select>
                ` : `
                <div class="screener-result ${odResp}" id="dpoae_screener_resp_od_${freq}">
                ${this.getScreenerLabel(odResp)}
                </div>
                `}
                </td>
                <td>
                ${isClinica ? `
                    <input type="number"
                    class="oae-input"
                    id="dpoae_${type}_amp_od_${freq}"
                    min="-30" max="10" step="0.1"
                    value="${odAmp}"
                    placeholder="-3.2"
                    ${tabIndex ? `tabindex="${tabIndex + 1}"` : ''}>
                    ` : `
                    <span id="dpoae_screener_amp_od_${freq}" style="font-size: 11px;">${odAmp}</span>
                    `}
                    </td>
                    <td>
                    ${isClinica ? `
                        <select class="oae-select" id="dpoae_${type}_resp_oi_${freq}" ${tabIndex ? `tabindex="${tabIndex + 2}"` : ''}>
                        <option value="">-</option>
                        <option value="presente" ${oiResp === 'presente' ? 'selected' : ''}>Presente</option>
                        <option value="ausente" ${oiResp === 'ausente' ? 'selected' : ''}>Ausente</option>
                        <option value="no_realizado" ${oiResp === 'no_realizado' ? 'selected' : ''}>No realizado</option>
                        </select>
                        ` : `
                        <div class="screener-result ${oiResp}" id="dpoae_screener_resp_oi_${freq}">
                        ${this.getScreenerLabel(oiResp)}
                        </div>
                        `}
                        </td>
                        <td>
                        ${isClinica ? `
                            <input type="number"
                            class="oae-input"
                            id="dpoae_${type}_amp_oi_${freq}"
                            min="-30" max="10" step="0.1"
                            value="${oiAmp}"
                            placeholder="-3.2"
                            ${tabIndex ? `tabindex="${tabIndex + 3}"` : ''}>
                            ` : `
                            <span id="dpoae_screener_amp_oi_${freq}" style="font-size: 11px;">${oiAmp}</span>
                            `}
                            </td>
                            </tr>
                            `;
        });

        html += '</tbody></table>';
        return html;
    }

    /**
     * Renderizar tabla de screener
     */
    renderScreenerTable(type, existingData) {
        if (type === 'teoae') {
            return this.renderTEOAETable('screener', existingData);
        } else {
            return this.renderDPOAETable('screener', existingData);
        }
    }

    /**
     * Obtener label para screener
     */
    getScreenerLabel(status) {
        switch (status) {
            case 'pasa': return 'PASA';
            case 'no-pasa': return 'NO PASA';
            case 'pendiente': return 'Pendiente';
            default: return 'Pendiente';
        }
    }

    /**
     * Inicializar eventos después de renderizar
     */
    async initEvents() {
        // Cargar vistas de gráficos
        await this.loadChartViews();

        // Auto-save y update preview al cambiar valores
        const inputs = document.querySelectorAll('#tabsContent input, #tabsContent select, #tabsContent textarea');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                this.updateScreenerData();
                this.updateOAEPreviews();
                this.app.updateModuleData(this.moduleId, this.getData());
            });

            input.addEventListener('change', () => {
                this.updateScreenerData();
                this.updateOAEPreviews();
                this.app.updateModuleData(this.moduleId, this.getData());
            });
        });

        // Renderizar previews iniciales
        setTimeout(() => {
            this.updateScreenerData();
            this.updateOAEPreviews();
        }, 100);
    }

    /**
     * Cargar componentes de vista de gráficos
     */
    async loadChartViews() {
        const chartConfigs = [
            {
                key: 'dpoaeClinical',
                file: 'js/components/views/dpoae-clinical-chart.js',
                className: 'DPOAEClinicalChartView',
                canvasId: 'dpoaeClinicasCanvas'
            },
            {
                key: 'teoaeClinical',
                file: 'js/components/views/teoae-clinical-chart.js',
                className: 'TEOAEClinicalChartView',
                canvasId: 'teoaeClinicasCanvas'
            },
            {
                key: 'teoaeScreener',
                file: 'js/components/views/teoae-screener-chart.js',
                className: 'TEOAEScreenerChartView',
                canvasId: 'teoaeScreenerCanvas'
            },
            {
                key: 'dpoaeScreener',
                file: 'js/components/views/dpoae-screener-chart.js',
                className: 'DPOAEScreenerChartView',
                canvasId: 'dpoaeScreenerCanvas'
            }
        ];

        for (const config of chartConfigs) {
            try {
                await this.app.loadScript(config.file);

                if (window[config.className]) {
                    this.chartViews[config.key] = new window[config.className](config.canvasId);
                    this.chartViewsStatus[config.key] = 'loaded';
                    console.log(`✅ Vista ${config.key} cargada correctamente`);
                } else {
                    this.chartViewsStatus[config.key] = 'error';
                    console.warn(`⚠️ Clase ${config.className} no encontrada en ${config.file}`);
                }
            } catch (error) {
                this.chartViews[config.key] = null;
                this.chartViewsStatus[config.key] = 'missing';
                console.log(`📋 Vista ${config.key} pendiente de implementación`);
            }
        }
    }

    /**
     * Actualizar datos de screener automáticamente
     */
    updateScreenerData() {
        // TEOAE Screener basado en TEOAE Clínicas
        this.frequencies.teoae.forEach(freq => {
            ['od', 'oi'].forEach(ear => {
                const snrInput = document.getElementById(`teoae_clinicas_snr_${ear}_${freq}`);
                const respSelect = document.getElementById(`teoae_clinicas_resp_${ear}_${freq}`);

                if (snrInput && respSelect) {
                    const snr = parseFloat(snrInput.value);
                    const resp = respSelect.value;

                    const screenerRespElem = document.getElementById(`teoae_screener_resp_${ear}_${freq}`);
                    const screenerSNRElem = document.getElementById(`teoae_screener_snr_${ear}_${freq}`);

                    if (screenerRespElem && screenerSNRElem) {
                        let screenerStatus, screenerClass;

                        if (resp === 'no_realizado' || resp === '') {
                            screenerStatus = 'Pendiente';
                            screenerClass = 'pendiente';
                        } else if (resp === 'presente' && snr >= 6) {
                            screenerStatus = 'PASA';
                            screenerClass = 'pasa';
                        } else {
                            screenerStatus = 'NO PASA';
                            screenerClass = 'no-pasa';
                        }

                        screenerRespElem.textContent = screenerStatus;
                        screenerRespElem.className = `screener-result ${screenerClass}`;
                        screenerSNRElem.textContent = snrInput.value || '-';
                    }
                }
            });
        });

        // DPOAE Screener basado en DPOAE Clínicas
        this.frequencies.dpoae.forEach(freq => {
            ['od', 'oi'].forEach(ear => {
                const ampInput = document.getElementById(`dpoae_clinicas_amp_${ear}_${freq}`);
                const respSelect = document.getElementById(`dpoae_clinicas_resp_${ear}_${freq}`);

                if (ampInput && respSelect) {
                    const amp = parseFloat(ampInput.value);
                    const resp = respSelect.value;

                    const screenerRespElem = document.getElementById(`dpoae_screener_resp_${ear}_${freq}`);
                    const screenerAmpElem = document.getElementById(`dpoae_screener_amp_${ear}_${freq}`);

                    if (screenerRespElem && screenerAmpElem) {
                        let screenerStatus, screenerClass;

                        if (resp === 'no_realizado' || resp === '') {
                            screenerStatus = 'Pendiente';
                            screenerClass = 'pendiente';
                        } else if (resp === 'presente' && amp >= -5) {
                            screenerStatus = 'PASA';
                            screenerClass = 'pasa';
                        } else {
                            screenerStatus = 'NO PASA';
                            screenerClass = 'no-pasa';
                        }

                        screenerRespElem.textContent = screenerStatus;
                        screenerRespElem.className = `screener-result ${screenerClass}`;
                        screenerAmpElem.textContent = ampInput.value || '-';
                    }
                }
            });
        });
    }

    /**
     * Actualizar previews de gráficos
     */
    updateOAEPreviews() {
        const data = this.getData();

        // Mapeo de vistas a canvas
        const canvasMapping = {
            teoaeClinical: 'teoaeClinicasCanvas',
            dpoaeClinical: 'dpoaeClinicasCanvas',
            teoaeScreener: 'teoaeScreenerCanvas',
            dpoaeScreener: 'dpoaeScreenerCanvas'
        };

        // Actualizar cada gráfico según su estado
        Object.keys(this.chartViews).forEach(chartKey => {
            const chartView = this.chartViews[chartKey];
            const status = this.chartViewsStatus[chartKey];
            const canvasId = canvasMapping[chartKey];

            if (status === 'loaded' && chartView && typeof chartView.render === 'function') {
                // Vista cargada correctamente - renderizar
                console.log(`🎯 Renderizando ${chartKey} con datos:`, data);
                try {
                    chartView.render(data);
                    console.log(`✅ ${chartKey} renderizado exitosamente`);
                } catch (error) {
                    console.error(`❌ Error renderizando ${chartKey}:`, error);
                    this.renderStatusMessage(canvasId, 'error', chartKey);
                }
            } else {
                // Vista no disponible - mostrar mensaje apropiado
                this.renderStatusMessage(canvasId, status, chartKey);
            }
        });
    }

    /**
     * Renderizar mensaje de estado en canvas
     */
    /**
     * Renderizar mensaje de estado en canvas
     */
    renderStatusMessage(canvasId, status, chartKey) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Configurar estilo de texto
        ctx.fillStyle = '#666';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;

        switch (status) {
            case 'missing':
                ctx.fillStyle = '#856404';
                ctx.fillText('Gráfico pendiente de implementación', centerX, centerY - 8);
                ctx.fillStyle = '#999';
                ctx.font = '10px Arial';
                ctx.fillText(`(${chartKey})`, centerX, centerY + 8);
                break;

            case 'error':
                ctx.fillStyle = '#dc3545';
                ctx.fillText('Error cargando vista del gráfico', centerX, centerY - 8);
                ctx.fillStyle = '#999';
                ctx.font = '10px Arial';
                ctx.fillText('Verificar archivo de vista', centerX, centerY + 8);
                break;

            case 'pending':
            default:
                ctx.fillStyle = '#6c757d';
                ctx.fillText('Cargando vista...', centerX, centerY);
                break;
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

        const data = {
            espontaneas: {
                oido_derecho: getValue('espontaneas_od') || 'presente',
                oido_izquierdo: getValue('espontaneas_oi') || 'presente'
            },
            transientes_clinicas: {
                oido_derecho: {},
                oido_izquierdo: {}
            },
            producto_distorsion_clinicas: {
                oido_derecho: {},
                oido_izquierdo: {}
            },
            transientes_screener: {
                oido_derecho: {},
                oido_izquierdo: {}
            },
            producto_distorsion_screener: {
                oido_derecho: {},
                oido_izquierdo: {}
            },
            observaciones: getValue('oae_observations')
        };

        // Recopilar TEOAE clínicas
        this.frequencies.teoae.forEach(freq => {
            ['od', 'oi'].forEach(ear => {
                const earKey = ear === 'od' ? 'oido_derecho' : 'oido_izquierdo';
                const resp = getValue(`teoae_clinicas_resp_${ear}_${freq}`);
                const snr = getNumberValue(`teoae_clinicas_snr_${ear}_${freq}`);

                if (resp || snr !== null) {
                    data.transientes_clinicas[earKey][freq] = {
                        respuesta: resp || null,
                        snr: snr
                    };
                }
            });
        });

        // Recopilar DPOAE clínicas
        this.frequencies.dpoae.forEach(freq => {
            ['od', 'oi'].forEach(ear => {
                const earKey = ear === 'od' ? 'oido_derecho' : 'oido_izquierdo';
                const resp = getValue(`dpoae_clinicas_resp_${ear}_${freq}`);
                const amp = getNumberValue(`dpoae_clinicas_amp_${ear}_${freq}`);

                if (resp || amp !== null) {
                    data.producto_distorsion_clinicas[earKey][freq] = {
                        respuesta: resp || null,
                        amplitud: amp
                    };
                }
            });
        });

        // Recopilar screener data (auto-calculado)
        this.frequencies.teoae.forEach(freq => {
            ['od', 'oi'].forEach(ear => {
                const earKey = ear === 'od' ? 'oido_derecho' : 'oido_izquierdo';
                const screenerRespElem = document.getElementById(`teoae_screener_resp_${ear}_${freq}`);
                const screenerSNRElem = document.getElementById(`teoae_screener_snr_${ear}_${freq}`);

                if (screenerRespElem && screenerSNRElem) {
                    const status = screenerRespElem.textContent.toLowerCase();
                    let resultado;
                    if (status === 'pasa') resultado = 'pasa';
                    else if (status === 'no pasa') resultado = 'no-pasa';
                    else resultado = 'pendiente';

                    data.transientes_screener[earKey][freq] = {
                        resultado: resultado,
                        snr: screenerSNRElem.textContent !== '-' ? parseFloat(screenerSNRElem.textContent) : null
                    };
                }
            });
        });

        this.frequencies.dpoae.forEach(freq => {
            ['od', 'oi'].forEach(ear => {
                const earKey = ear === 'od' ? 'oido_derecho' : 'oido_izquierdo';
                const screenerRespElem = document.getElementById(`dpoae_screener_resp_${ear}_${freq}`);
                const screenerAmpElem = document.getElementById(`dpoae_screener_amp_${ear}_${freq}`);

                if (screenerRespElem && screenerAmpElem) {
                    const status = screenerRespElem.textContent.toLowerCase();
                    let resultado;
                    if (status === 'pasa') resultado = 'pasa';
                    else if (status === 'no pasa') resultado = 'no-pasa';
                    else resultado = 'pendiente';

                    data.producto_distorsion_screener[earKey][freq] = {
                        resultado: resultado,
                        amplitud: screenerAmpElem.textContent !== '-' ? parseFloat(screenerAmpElem.textContent) : null
                    };
                }
            });
        });

        return data;
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        const errors = [];

        // Validar rangos SNR
        ['transientes_clinicas'].forEach(test => {
            ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
                const earData = data[test]?.[ear];
                if (earData) {
                    Object.keys(earData).forEach(freq => {
                        const snr = earData[freq]?.snr;
                        if (snr !== null && (snr < 0 || snr > 30)) {
                            errors.push(`SNR en ${freq} Hz ${ear} debe estar entre 0-30 dB`);
                        }
                    });
                }
            });
        });

        // Validar rangos amplitud
        ['producto_distorsion_clinicas'].forEach(test => {
            ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
                const earData = data[test]?.[ear];
                if (earData) {
                    Object.keys(earData).forEach(freq => {
                        const amp = earData[freq]?.amplitud;
                        if (amp !== null && (amp < -30 || amp > 10)) {
                            errors.push(`Amplitud en ${freq} Hz ${ear} debe estar entre -30 a +10 dB SPL`);
                        }
                    });
                }
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

        // Al menos debe tener EOA espontáneas configuradas
        const hasEspontaneas = data.espontaneas?.oido_derecho || data.espontaneas?.oido_izquierdo;

        // O al menos algunas mediciones clínicas
        const hasTEOAE = data.transientes_clinicas?.oido_derecho &&
        Object.keys(data.transientes_clinicas.oido_derecho).length > 0 ||
        data.transientes_clinicas?.oido_izquierdo &&
        Object.keys(data.transientes_clinicas.oido_izquierdo).length > 0;

        const hasDPOAE = data.producto_distorsion_clinicas?.oido_derecho &&
        Object.keys(data.producto_distorsion_clinicas.oido_derecho).length > 0 ||
        data.producto_distorsion_clinicas?.oido_izquierdo &&
        Object.keys(data.producto_distorsion_clinicas.oido_izquierdo).length > 0;

        return hasEspontaneas || hasTEOAE || hasDPOAE;
    }
}

// Exponer globalmente
window.OaeModule = OaeModule;
