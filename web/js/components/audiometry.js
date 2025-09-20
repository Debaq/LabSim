/**
 * AudiometryModule
 * - Formularios de umbrales aéreos/óseos + LDL (OD/OI)
 * - Canvas de audiograma separado y cargado como view: AudiogramChartView (audiogram-charts.js)
 * - Soporta frecuencias extendidas (checkbox)
 * - Exporta/lee datos con getData()/render(existingData)
 *
 * Requiere:
 *   this.app.loadScript(path)   // para cargar el view
 *   this.app.updateModuleData(moduleId, data) // para persistir cambios mientras editas
 */
class AudiometryModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'audiometry';

        // Estado UI
        this.showHighFreq = false;

        // View (canvas)
        this.chartView = null;

        // Frecuencias base y extendidas
        this.baseFreqs = ['125','250','500','1000','2000','4000','8000'];
        this.extFreqs  = ['9000','10000','11200','12500','14000','16000','18000','20000'];
    }

    // =========================
    // RENDER
    // =========================
    async render(existingData = {}) {
        // estado inicial desde datos existentes
        this.showHighFreq = !!existingData.frecuencias_ext;

        const freqsUI = this._currentFreqs();

        return `
        <div class="form-section">
        <h3 class="section-title">🎧 Audiometría Tonal</h3>
        <p class="section-description">Registro de umbrales aéreos/óseos y niveles de disconfort (LDL)</p>

        <div style="display:flex; gap:24px; align-items:flex-start; flex-wrap:wrap;">
        <!-- Panel formularios -->
        <div style="flex: 2; min-width: 520px;">
        <!-- Controles -->
        <div class="audiometry-controls" style="display:flex; gap:16px; align-items:center; margin-bottom:10px;">
        <label style="display:inline-flex; gap:8px; align-items:center;">
        <input type="checkbox" id="aud_show_hf" ${this.showHighFreq ? 'checked' : ''}/>
        <span>Mostrar frecuencias extendidas (9–20 kHz)</span>
        </label>
        </div>

        <!-- Aéreo -->
        <div class="audiometry-card">
        <h4 class="section-subtitle">Aéreos (dB HL)</h4>
        <div class="audiometry-grid">
        ${this._renderThresholdTable('umbrales_aereos', 'Aéreos', freqsUI, existingData?.umbrales_aereos)}
        </div>
        </div>

        <!-- Óseo -->
        <div class="audiometry-card">
        <h4 class="section-subtitle">Óseos (dB HL)</h4>
        <div class="audiometry-grid">
        ${this._renderThresholdTable('umbrales_oseos', 'Óseos', freqsUI, existingData?.umbrales_oseos)}
        </div>
        <p class="hint">* Usa 130 para “no responde” (se dibuja con flecha).</p>
        </div>

        <!-- LDL -->
        <div class="audiometry-card">
        <h4 class="section-subtitle">LDL (Nivel de Disconfort) (dB)</h4>
        <div class="audiometry-grid">
        ${this._renderThresholdTable('ldl_disconfort', 'LDL', freqsUI, existingData?.ldl_disconfort)}
        </div>
        </div>

        <!-- Observaciones -->
        <div class="form-group" style="margin-top: 12px;">
        <label class="label-optional">Observaciones</label>
        <textarea id="aud_observaciones" rows="3" placeholder="Comentarios clínicos...">${existingData?.observaciones || ''}</textarea>
        </div>
        </div>

        <!-- Panel gráfico -->
        <div style="flex: 1.6; min-width: 420px;">
        <h4 class="section-subtitle">📈 Audiograma</h4>
        <canvas id="audiogramCanvas" width="720" height="520" style="width:100%; height:auto; border:1px solid #dee2e6; border-radius:6px; background:#fff;"></canvas>
        <div class="legend" style="font-size:12px; color:#6c757d; margin-top:6px;">
        <span style="color:#dc3545; font-weight:600;">OD</span> / <span style="color:#007bff; font-weight:600;">OI</span> · Líneas continuas = aéreo · Líneas punteadas = óseo · ▲ = LDL · ⭳ = no responde
        </div>
        </div>
        </div>
        </div>

        <style>
        .audiometry-card {
            background:#fff; border:1px solid #e9ecef; border-radius:8px; padding:12px; margin-bottom:12px;
        }
        .audiometry-grid { overflow:auto; }
        table.aud-table { border-collapse: collapse; width: 100%; min-width: 520px; font-size:13px; }
        table.aud-table th, table.aud-table td { border:1px solid #dee2e6; padding:6px 8px; text-align:center; white-space:nowrap; }
        table.aud-table th { background:#f8f9fa; font-weight:600; }
        .ear-tag { display:inline-block; padding:2px 6px; border-radius:4px; font-size:12px; }
        .ear-od { background:#fdecea; color:#d63340; }
        .ear-oi { background:#e7f1ff; color:#0d6efd; }
        input.aud-input { width:64px; padding:4px; text-align:center; border:1px solid #ced4da; border-radius:4px; }
        input.aud-input:focus { border-color:#6f42c1; outline:none; box-shadow:0 0 0 2px rgba(111,66,193,0.1); }
        </style>
        `;
    }

    _renderThresholdTable(key, title, freqs, existing) {
        const od = existing?.oido_derecho || {};
        const oi = existing?.oido_izquierdo || {};
        const row = (earKey, earLabel, earData) => `
        <tr>
        <td style="text-align:left;">
        <span class="ear-tag ${earKey==='oido_derecho' ? 'ear-od' : 'ear-oi'}">${earLabel}</span>
        </td>
        ${freqs.map(f => `
            <td>
            <input class="aud-input" type="number" min="-10" max="130" step="5"
            id="${key}_${earKey}_${f}"
            value="${this._v(earData?.[f])}" />
            </td>
            `).join('')}
            </tr>
            `;
            return `
            <table class="aud-table">
            <thead>
            <tr>
            <th>Oído</th>
            ${freqs.map(f => `<th>${f}</th>`).join('')}
            </tr>
            </thead>
            <tbody>
            ${row('oido_derecho', 'OD', od)}
            ${row('oido_izquierdo','OI', oi)}
            </tbody>
            </table>
            `;
    }

    _currentFreqs() {
        return this.showHighFreq ? [...this.baseFreqs, ...this.extFreqs] : [...this.baseFreqs];
    }

    _v(x) { return (x === null || x === undefined) ? '' : x; }

    // =========================
    // INIT + EVENTOS
    // =========================
    async initEvents() {
        // Toggle de high freq
        const chk = document.getElementById('aud_show_hf');
        if (chk) {
            chk.addEventListener('change', () => {
                this.showHighFreq = chk.checked;
                // Re-render módulo para regenerar las tablas con columnas correctas
                const data = this.getData();
                data.frecuencias_ext = this.showHighFreq;
                this.app.updateModuleData(this.moduleId, data);
                this.app.refreshModule(this.moduleId); // asume que tu app soporta refrescar el módulo actual
            });
        }

        // Delegación de eventos: inputs + textarea
        const container = document.querySelector('.form-section');
        if (container) {
            container.addEventListener('input', (e) => {
                if (e.target && (e.target.classList.contains('aud-input') || e.target.id === 'aud_observaciones')) {
                    const data = this.getData();
                    this.app.updateModuleData(this.moduleId, data);
                    this.updateAudiogramPreview();
                }
            });
            container.addEventListener('change', (e) => {
                if (e.target && (e.target.classList.contains('aud-input') || e.target.id === 'aud_observaciones')) {
                    const data = this.getData();
                    this.app.updateModuleData(this.moduleId, data);
                    this.updateAudiogramPreview();
                }
            });
        }

        // Cargar el view y primera pinta
        await this.loadChartView();
        this.updateAudiogramPreview();
    }

    async loadChartView() {
        try {
            await this.app.loadScript('js/components/views/audiogram-charts.js');
            if (window.AudiogramChartView) {
                this.chartView = new window.AudiogramChartView('audiogramCanvas');
            } else {
                this.chartView = null;
            }
        } catch (e) {
            console.warn('audiogram-charts.js no disponible', e);
            this.chartView = null;
        }
    }

    updateAudiogramPreview() {
        const canvas = document.getElementById('audiogramCanvas');
        if (!canvas) return;

        const data = this.getData();

        if (this.chartView && typeof this.chartView.render === 'function') {
            this.chartView.render(data, { showHighFreq: this.showHighFreq, freqs: this._currentFreqs() });
        } else {
            const ctx = canvas.getContext('2d');
            const { width:w, height:h } = canvas;
            ctx.clearRect(0,0,w,h);
            ctx.fillStyle = '#666';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('Vista de audiograma no disponible', w/2, h/2);
            ctx.fillText('(carga audiogram-charts.js)', w/2, h/2 + 22);
        }
    }

    // =========================
    // DATA API
    // =========================
    getData() {
        const readSet = (key) => {
            const out = { oido_derecho: {}, oido_izquierdo: {} };
            const freqs = this._currentFreqs();
            freqs.forEach(f => {
                const odEl = document.getElementById(`${key}_oido_derecho_${f}`);
                const oiEl = document.getElementById(`${key}_oido_izquierdo_${f}`);
                const parse = (el) => {
                    if (!el) return null;
                    const v = el.value.trim();
                    if (v === '') return null;
                    const num = Number(v);
                    return Number.isFinite(num) ? num : null;
                };
                out.oido_derecho[f] = parse(odEl);
                out.oido_izquierdo[f] = parse(oiEl);
            });
            return out;
        };

        const data = {
            frecuencias_ext: this.showHighFreq,
            umbrales_aereos:   readSet('umbrales_aereos'),
            umbrales_oseos:    readSet('umbrales_oseos'),
            ldl_disconfort:    readSet('ldl_disconfort'),
            observaciones:     (document.getElementById('aud_observaciones')?.value || '').trim()
        };

        return data;
    }

    validate(data) {
        const errors = [];
        const checkSet = (set, label) => {
            const freqs = this._currentFreqs();
            ['oido_derecho','oido_izquierdo'].forEach(ear => {
                freqs.forEach(f => {
                    const v = set?.[ear]?.[f];
                    if (v === null || v === undefined || v === '') return;
                    if (typeof v !== 'number' || !Number.isFinite(v)) {
                        errors.push(`${label} ${ear === 'oido_derecho' ? 'OD' : 'OI'} ${f}Hz: valor inválido`);
                        return;
                    }
                    if (v < -10 || v > 130) {
                        errors.push(`${label} ${ear === 'oido_derecho' ? 'OD' : 'OI'} ${f}Hz: fuera de rango (-10 a 130 dB)`);
                    }
                });
            });
        };

        checkSet(data?.umbrales_aereos, 'Aéreos');
        checkSet(data?.umbrales_oseos,  'Óseos');
        checkSet(data?.ldl_disconfort,  'LDL');

        return { isValid: errors.length === 0, errors };
    }

    isComplete(data) {
        const hasAny = (set) => {
            if (!set) return false;
            const freqs = [...this.baseFreqs, ...this.extFreqs];
            return ['oido_derecho','oido_izquierdo'].some(ear =>
            freqs.some(f => typeof set?.[ear]?.[f] === 'number')
            );
        };
        return hasAny(data?.umbrales_aereos) || hasAny(data?.umbrales_oseos) || hasAny(data?.ldl_disconfort);
    }
}

// Exponer globalmente
window.AudiometryModule = AudiometryModule;
