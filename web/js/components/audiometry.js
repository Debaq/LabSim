/**
 * AudiometryModule - Módulo de Audiometría
 * Umbrales auditivos, vías aérea y ósea, LDL
 */

class AudiometryModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'audiometry';
        this.showHighFreq = false;

        // Frecuencias estándar
        this.frequencies = {
            standard: ['125', '250', '500', '1000', '2000', '4000', '8000'],
            high: ['9000', '10000', '11200', '12500', '14000', '16000', '18000', '20000'],
            bone: ['250', '500', '1000', '2000', '4000'], // Solo estas para vía ósea
            ldl: ['250', '500', '1000', '2000', '4000'] // Solo estas para LDL
        };
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        return `
        <div class="form-section">
        <h3 class="section-title">🎧 Audiometría Tonal</h3>
        <p class="section-description">
        Registro de umbrales auditivos por vía aérea y ósea.
        Ingresa valores en dB HL. Deja vacío para umbral no obtenido. Use 130 dB para umbral ausente.
        </p>

        <!-- Layout Principal: Formularios (40%) + Preview (60%) -->
        <div style="display: flex; gap: 30px;">
        <!-- Panel de Formularios -->
        <div style="flex: 2; min-width: 400px;">

        <!-- Control de Altas Frecuencias -->
        <div class="form-group">
        <div class="checkbox-group">
        <div class="checkbox-item">
        <input type="checkbox" id="showHighFreq" ${this.showHighFreq ? 'checked' : ''}>
        <label for="showHighFreq">Mostrar altas frecuencias (9K - 20K Hz)</label>
        </div>
        </div>
        </div>

        <!-- Tabla Vía Aérea -->
        <div class="form-group">
        <h4 class="section-subtitle">Vía Aérea (dB HL)</h4>
        <table class="audiometry-table">
        <thead>
        <tr>
        <th>Frecuencia</th>
        <th style="color: #dc3545;">OD</th>
        <th style="color: #007bff;">OI</th>
        </tr>
        </thead>
        <tbody>
        ${this.renderAudiometryRows('aereo', existingData.umbrales_aereos)}
        </tbody>
        </table>
        </div>

        <!-- Tabla Vía Ósea -->
        <div class="form-group">
        <h4 class="section-subtitle">Vía Ósea (dB HL)</h4>
        <p style="font-size: 12px; color: #666; margin-bottom: 10px;">
        Solo frecuencias 250-4000 Hz.
        </p>
        <table class="audiometry-table">
        <thead>
        <tr>
        <th>Frecuencia</th>
        <th style="color: #dc3545;">OD</th>
        <th style="color: #007bff;">OI</th>
        </tr>
        </thead>
        <tbody>
        ${this.renderBoneRows(existingData.umbrales_oseos)}
        </tbody>
        </table>
        </div>

        <!-- Tabla LDL -->
        <div class="form-group">
        <h4 class="section-subtitle">LDL - Nivel de Disconfort (dB HL)</h4>
        <p style="font-size: 12px; color: #666; margin-bottom: 10px;">
        Solo frecuencias 250-4000 Hz. Ausente por defecto en 120 dB.
        </p>
        <table class="audiometry-table">
        <thead>
        <tr>
        <th>Frecuencia</th>
        <th style="color: #dc3545;">OD</th>
        <th style="color: #007bff;">OI</th>
        </tr>
        </thead>
        <tbody>
        ${this.renderLDLRows(existingData.ldl_disconfort)}
        </tbody>
        </table>
        </div>

        <!-- Observaciones -->
        <div class="form-group">
        <label for="observaciones">Observaciones</label>
        <textarea id="observaciones"
        placeholder="Particularidades del examen, dificultades técnicas, etc."
        style="min-height: 80px;">${existingData.observaciones || ''}</textarea>
        </div>
        </div>

        <!-- Panel de Preview -->
        <div style="flex: 3; min-width: 500px;">
        <h4 class="section-subtitle">📊 Preview del Audiograma</h4>
        <div id="audiogramPreview" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: white;">
        <canvas id="audiogramCanvas" width="600" height="400" style="width: 100%; height: auto;"></canvas>
        </div>
        </div>
        </div>
        </div>

        <style>
        .audiometry-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            font-size: 14px;
        }

        .audiometry-table th {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 8px 12px;
            text-align: center;
            font-weight: 600;
        }

        .audiometry-table td {
            border: 1px solid #dee2e6;
            padding: 4px 8px;
            text-align: center;
        }

        .audiometry-table .freq-label {
            background: #f8f9fa;
            font-weight: 500;
            text-align: right;
            padding-right: 15px;
        }

        .audiometry-input {
            width: 60px;
            padding: 4px 6px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            text-align: center;
            font-size: 13px;
        }

        .audiometry-input:focus {
            border-color: #2a5298;
            outline: none;
            box-shadow: 0 0 0 2px rgba(42, 82, 152, 0.1);
        }

        .high-freq-row {
            display: ${this.showHighFreq ? 'table-row' : 'none'};
        }
        </style>
        `;
    }

    /**
     * Renderizar filas de audiometría (aérea/ósea)
     */
    renderAudiometryRows(type, existingData) {
        const allFreqs = [...this.frequencies.standard, ...this.frequencies.high];
        let html = '';

        allFreqs.forEach((freq, freqIndex) => {
            const isHighFreq = this.frequencies.high.includes(freq);
            const rowClass = isHighFreq ? 'high-freq-row' : '';

            const valueOD = existingData?.oido_derecho?.[freq] || '';
            const valueOI = existingData?.oido_izquierdo?.[freq] || '';

            // Calcular tabindex: aéreo OD (1-15), aéreo OI (16-30), óseo OD (31-45), óseo OI (46-60)
            let tabIndexOD, tabIndexOI;
            if (type === 'aereo') {
                tabIndexOD = freqIndex + 1;
                tabIndexOI = freqIndex + 16;
            } else { // oseo
                tabIndexOD = freqIndex + 31;
                tabIndexOI = freqIndex + 46;
            }

            html += `
            <tr class="${rowClass}">
            <td class="freq-label">${freq} Hz</td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="${type}_od_${freq}"
            data-freq="${freq}"
            data-type="${type}_od"
            min="0" max="120" step="5"
            value="${valueOD}"
            placeholder="-"
            tabindex="${tabIndexOD}">
            </td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="${type}_oi_${freq}"
            data-freq="${freq}"
            data-type="${type}_oi"
            min="0" max="120" step="5"
            value="${valueOI}"
            placeholder="-"
            tabindex="${tabIndexOI}">
            </td>
            </tr>
            `;
        });

        return html;
    }

    /**
     * Renderizar filas de vía ósea (solo 250-4000 Hz)
     */
    renderBoneRows(existingData) {
        let html = '';

        this.frequencies.bone.forEach((freq, freqIndex) => {
            const valueOD = existingData?.oido_derecho?.[freq] || '';
            const valueOI = existingData?.oido_izquierdo?.[freq] || '';

            // Tabindex para óseo: OD (31-35), OI (36-40)
            const tabIndexOD = freqIndex + 31;
            const tabIndexOI = freqIndex + 36;

            html += `
            <tr>
            <td class="freq-label">${freq} Hz</td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="oseo_od_${freq}"
            data-freq="${freq}"
            data-type="oseo_od"
            min="0" max="130" step="5"
            value="${valueOD}"
            placeholder="-"
            tabindex="${tabIndexOD}">
            </td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="oseo_oi_${freq}"
            data-freq="${freq}"
            data-type="oseo_oi"
            min="0" max="130" step="5"
            value="${valueOI}"
            placeholder="-"
            tabindex="${tabIndexOI}">
            </td>
            </tr>
            `;
        });

        return html;
    }

    /**
     * Renderizar filas de LDL (solo 250-4000 Hz)
     */
    renderLDLRows(existingData) {
        let html = '';

        this.frequencies.ldl.forEach((freq, freqIndex) => {
            const valueOD = existingData?.oido_derecho?.[freq] || '';
            const valueOI = existingData?.oido_izquierdo?.[freq] || '';

            // Tabindex para LDL: OD (41-45), OI (46-50)
            const tabIndexOD = freqIndex + 41;
            const tabIndexOI = freqIndex + 46;

            html += `
            <tr>
            <td class="freq-label">${freq} Hz</td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="ldl_od_${freq}"
            data-freq="${freq}"
            data-type="ldl_od"
            min="60" max="130" step="5"
            value="${valueOD}"
            placeholder="120"
            tabindex="${tabIndexOD}">
            </td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="ldl_oi_${freq}"
            data-freq="${freq}"
            data-type="ldl_oi"
            min="60" max="130" step="5"
            value="${valueOI}"
            placeholder="120"
            tabindex="${tabIndexOI}">
            </td>
            </tr>
            `;
        });

        return html;
    }

    /**
     * Inicializar eventos después de renderizar
     */
    initEvents() {
        // Toggle de altas frecuencias
        const showHighFreqCheck = document.getElementById('showHighFreq');
        if (showHighFreqCheck) {
            showHighFreqCheck.addEventListener('change', (e) => {
                this.showHighFreq = e.target.checked;
                this.toggleHighFrequencies();
            });
        }

        // Eventos de cambio en inputs
        const inputs = document.querySelectorAll('.audiometry-input');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                this.validateInput(input);
                this.updateAudiogramPreview();
                this.app.updateModuleData(this.moduleId, this.getData());
            });
        });

        // Evento para observaciones
        const observaciones = document.getElementById('observaciones');
        if (observaciones) {
            observaciones.addEventListener('input', () => {
                this.app.updateModuleData(this.moduleId, this.getData());
            });
        }

        // Renderizar preview inicial
        setTimeout(() => {
            this.updateAudiogramPreview();
        }, 100);
    }

    /**
     * Mostrar/ocultar altas frecuencias
     */
    toggleHighFrequencies() {
        const highFreqRows = document.querySelectorAll('.high-freq-row');
        highFreqRows.forEach(row => {
            row.style.display = this.showHighFreq ? 'table-row' : 'none';
        });

        this.updateAudiogramPreview();
    }

    /**
     * Validar input individual
     */
    validateInput(input) {
        const value = parseInt(input.value);

        input.classList.remove('field-error', 'field-success');

        if (input.value === '') {
            return true; // Vacío es válido
        }

        if (isNaN(value) || value < 0 || value > 120 || value % 5 !== 0) {
            input.classList.add('field-error');
            return false;
        }

        input.classList.add('field-success');
        return true;
    }

    /**
     * Actualizar preview del audiograma
     */
    updateAudiogramPreview() {
        const canvas = document.getElementById('audiogramCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const data = this.getData();

        // Limpiar canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Configuración del audiograma
        const margin = { top: 30, right: 40, bottom: 50, left: 60 };
        const plotWidth = canvas.width - margin.left - margin.right;
        const plotHeight = canvas.height - margin.top - margin.bottom;

        // Frecuencias a mostrar
        const freqsToShow = this.showHighFreq ?
        [...this.frequencies.standard, ...this.frequencies.high] :
        this.frequencies.standard;

        // Escalas
        const freqScale = (index) => margin.left + (index / (freqsToShow.length - 1)) * plotWidth;
        const dbScale = (db) => margin.top + ((db + 10) / 130) * plotHeight;

        this.drawAudiogramGrid(ctx, margin, plotWidth, plotHeight, freqsToShow);
        this.drawAudiogramData(ctx, data, freqsToShow, freqScale, dbScale);
    }

    /**
     * Dibujar grilla del audiograma
     */
    drawAudiogramGrid(ctx, margin, width, height, frequencies) {
        ctx.strokeStyle = '#ddd';
        ctx.lineWidth = 1;
        ctx.font = '11px Arial';
        ctx.fillStyle = '#666';

        // Líneas verticales (frecuencias)
        frequencies.forEach((freq, index) => {
            const x = margin.left + (index / (frequencies.length - 1)) * width;

            ctx.beginPath();
            ctx.moveTo(x, margin.top);
            ctx.lineTo(x, margin.top + height);
            ctx.stroke();

            // Etiquetas de frecuencia
            ctx.save();
            ctx.translate(x, margin.top + height + 15);
            ctx.rotate(-Math.PI/4);
            ctx.fillText(freq, -10, 0);
            ctx.restore();
        });

        // Líneas horizontales (dB)
        for (let db = -10; db <= 120; db += 10) {
            const y = margin.top + ((db + 10) / 130) * height;

            // Líneas más gruesas en 0 y 20 dB
            if (db === 0 || db === 20) {
                ctx.strokeStyle = '#333';
                ctx.lineWidth = 2;
            } else {
                ctx.strokeStyle = '#ddd';
                ctx.lineWidth = 1;
            }

            ctx.beginPath();
            ctx.moveTo(margin.left, y);
            ctx.lineTo(margin.left + width, y);
            ctx.stroke();

            // Etiquetas de dB
            if (db % 20 === 0) {
                ctx.fillStyle = '#333';
                ctx.fillText(db.toString(), margin.left - 25, y + 3);
            }
        }

        // Etiquetas de frecuencia en la parte superior
        ctx.fillStyle = '#333';
        ctx.font = '11px Arial';
        frequencies.forEach((freq, index) => {
            const x = margin.left + (index / (frequencies.length - 1)) * width;
            ctx.save();
            ctx.translate(x, margin.top - 10);
            ctx.rotate(-Math.PI/4);
            ctx.fillText(freq, -10, 0);
            ctx.restore();
        });

        // Títulos
        ctx.fillStyle = '#333';
        ctx.font = 'bold 12px Arial';
        ctx.fillText('Frecuencia (Hz)', margin.left + width/2 - 40, margin.top + height + 40);

        ctx.save();
        ctx.translate(15, margin.top + height/2);
        ctx.rotate(-Math.PI/2);
        ctx.fillText('Umbral (dB HL)', -40, 0);
        ctx.restore();
    }

    /**
     * Dibujar datos del audiograma
     */
    drawAudiogramData(ctx, data, frequencies, freqScale, dbScale) {
        const styles = {
            aereo_od: { color: '#dc3545', symbol: 'circle', line: 'solid' },
            aereo_oi: { color: '#007bff', symbol: 'x', line: 'solid' },
            oseo_od: { color: '#dc3545', symbol: 'bracket_right', line: 'dashed' },
            oseo_oi: { color: '#007bff', symbol: 'bracket_left', line: 'dashed' },
            ldl_od: { color: '#dc3545', symbol: 'triangle', line: 'none' },
            ldl_oi: { color: '#007bff', symbol: 'triangle', line: 'none' }
        };

        Object.keys(styles).forEach(type => {
            const style = styles[type];
            const points = [];
            const absentPoints = []; // Para umbrales ausentes (130 dB)

        frequencies.forEach((freq, index) => {
            let value = this.getValueForType(data, type, freq);

            if (value !== null && value !== undefined && value !== '') {
                const x = freqScale(index);
                const intValue = parseInt(value);

                if (intValue === 130) {
                    // Umbral ausente - dibujar flecha hacia abajo
                    const y = dbScale(120); // Posicionar en 120 dB
                    absentPoints.push({ x, y, freq, value });
                    this.drawSymbol(ctx, x, y, 'arrow_down', style.color);
                } else {
                    // Umbral normal
                    const y = dbScale(intValue);
                    points.push({ x, y, freq, value });
                    this.drawSymbol(ctx, x, y, style.symbol, style.color);
                }
            }
        });

        // Dibujar líneas conectoras solo para umbrales normales (no ausentes)
        if (points.length > 1 && style.line !== 'none') {
            ctx.strokeStyle = style.color;
            ctx.lineWidth = 2;
            ctx.setLineDash(style.line === 'dashed' ? [4, 4] : []);

            ctx.beginPath();
            ctx.moveTo(points[0].x, points[0].y);
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(points[i].x, points[i].y);
            }
            ctx.stroke();
            ctx.setLineDash([]);
        }
        });
    }

    /**
     * Obtener valor según tipo de medición
     */
    getValueForType(data, type, freq) {
        switch (type) {
            case 'aereo_od':
                return data.umbrales_aereos?.oido_derecho?.[freq];
            case 'aereo_oi':
                return data.umbrales_aereos?.oido_izquierdo?.[freq];
            case 'oseo_od':
                return data.umbrales_oseos?.oido_derecho?.[freq];
            case 'oseo_oi':
                return data.umbrales_oseos?.oido_izquierdo?.[freq];
            case 'ldl_od':
                return data.ldl_disconfort?.oido_derecho?.[freq];
            case 'ldl_oi':
                return data.ldl_disconfort?.oido_izquierdo?.[freq];
            default:
                return null;
        }
    }

    /**
     * Dibujar símbolos del audiograma
     */
    drawSymbol(ctx, x, y, symbol, color) {
        ctx.fillStyle = color;
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;

        switch (symbol) {
            case 'circle':
                ctx.beginPath();
                ctx.arc(x, y, 3, 0, 2 * Math.PI);
                ctx.stroke();
                break;
            case 'x':
                ctx.beginPath();
                ctx.moveTo(x - 3, y - 3);
                ctx.lineTo(x + 3, y + 3);
                ctx.moveTo(x + 3, y - 3);
                ctx.lineTo(x - 3, y + 3);
                ctx.stroke();
                break;
            case 'bracket_right':
                ctx.beginPath();
                ctx.moveTo(x - 2, y - 3);
                ctx.lineTo(x + 2, y - 3);
                ctx.lineTo(x + 2, y + 3);
                ctx.lineTo(x - 2, y + 3);
                ctx.stroke();
                break;
            case 'bracket_left':
                ctx.beginPath();
                ctx.moveTo(x + 2, y - 3);
                ctx.lineTo(x - 2, y - 3);
                ctx.lineTo(x - 2, y + 3);
                ctx.lineTo(x + 2, y + 3);
                ctx.stroke();
                break;
            case 'triangle': // Pirámide para LDL
                ctx.beginPath();
                ctx.moveTo(x, y - 4);
                ctx.lineTo(x - 3, y + 2);
                ctx.lineTo(x + 3, y + 2);
                ctx.closePath();
                ctx.fill();
                break;
        }
    }

    /**
     * Obtener datos del formulario
     */
    getData() {
        const data = {
            umbrales_aereos: {
                oido_derecho: {},
                oido_izquierdo: {}
            },
            umbrales_oseos: {
                oido_derecho: {},
                oido_izquierdo: {}
            },
            ldl_disconfort: {
                oido_derecho: {},
                oido_izquierdo: {}
            },
            observaciones: ''
        };

        // Recopilar umbrales aéreos y óseos
        const allFreqs = [...this.frequencies.standard, ...this.frequencies.high];
        allFreqs.forEach(freq => {
            ['aereo', 'oseo'].forEach(type => {
                ['od', 'oi'].forEach(ear => {
                    const input = document.getElementById(`${type}_${ear}_${freq}`);
                    if (input && input.value !== '') {
                        const earKey = ear === 'od' ? 'oido_derecho' : 'oido_izquierdo';
                        const typeKey = type === 'aereo' ? 'umbrales_aereos' : 'umbrales_oseos';
                        data[typeKey][earKey][freq] = parseInt(input.value);
                    }
                });
            });
        });

        // Recopilar LDL (solo frecuencias específicas)
        this.frequencies.ldl.forEach(freq => {
            ['od', 'oi'].forEach(ear => {
                const input = document.getElementById(`ldl_${ear}_${freq}`);
                if (input && input.value !== '') {
                    const earKey = ear === 'od' ? 'oido_derecho' : 'oido_izquierdo';
                    data.ldl_disconfort[earKey][freq] = parseInt(input.value);
                }
            });
        });

        // Observaciones
        const observaciones = document.getElementById('observaciones');
        if (observaciones) {
            data.observaciones = observaciones.value;
        }

        return data;
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        const errors = [];

        if (!data || typeof data !== 'object') {
            errors.push('Datos de audiometría inválidos');
            return { isValid: false, errors };
        }

        const hasAereoOD = data.umbrales_aereos?.oido_derecho &&
        Object.keys(data.umbrales_aereos.oido_derecho).length > 0;
        const hasAereoOI = data.umbrales_aereos?.oido_izquierdo &&
        Object.keys(data.umbrales_aereos.oido_izquierdo).length > 0;

        if (!hasAereoOD && !hasAereoOI) {
            errors.push('Debe ingresar al menos algunos umbrales de vía aérea');
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

        const hasAereoOD = data.umbrales_aereos?.oido_derecho &&
        Object.keys(data.umbrales_aereos.oido_derecho).length >= 3;
        const hasAereoOI = data.umbrales_aereos?.oido_izquierdo &&
        Object.keys(data.umbrales_aereos.oido_izquierdo).length >= 3;

        return hasAereoOD || hasAereoOI;
    }
}

// Exponer globalmente
window.AudiometryModule = AudiometryModule;
