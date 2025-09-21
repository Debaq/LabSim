/**
 * ElectrocochleoModule - Rehecho para soportar trazos temporales (ECochG)
 *
 * Objetivo:
 * - Mantener captura de SP/AP (µV) para OD/OI (resumen cuantitativo)
 * - Agregar soporte a forma de onda temporal (0–10 ms aprox.) por oído
 * - Previsualizar trazo realista con un view externo si está disponible
 * - Fallback de dibujo interno si el view no está cargado
 *
 * View externo esperado: js/components/views/electrocochlear-waveform.js
 * Debe exponer window.ElectrocochlearWaveformView(canvasId)
 */
class ElectrocochleoModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'electrocochleo';

        // Config UI
        this.defaultFs = 20000; // Hz (20 kHz)
        this.defaultWindowMs = 8; // ms visibles por defecto

        // Handler del view externo
        this.waveView = null;
    }

    /** Render principal */
    async render(existingData = {}) {
        const d = this._withDefaults(existingData);

        return `
        <div class="form-section">
        <h3 class="section-title">⚡ Electrocochleografía (ECochG)</h3>
        <p class="section-description">
        Registra SP (Summating Potential) y AP (Action Potential), y permite adjuntar/pegar
        la <strong>señal temporal</strong> (trazo en µV) para una visualización realista.
        </p>

        <div style="display:flex; gap:24px; align-items:flex-start;">
        <!-- Panel izquierdo: Config + Datos numéricos -->
        <div style="flex:2; min-width:380px;">

        <div class="form-group">
        <h4 class="section-subtitle">Parámetros de visualización</h4>
        <div class="inline-fields" style="display:flex; gap:12px; flex-wrap:wrap;">
        <label>Fs (Hz)
        <input id="ecochg_fs" type="number" class="audiometry-input" min="2000" max="96000" step="100"
        value="${d.params.fs}" />
        </label>
        <label>Ventana (ms)
        <input id="ecochg_window" type="number" class="audiometry-input" min="3" max="20" step="1"
        value="${d.params.windowMs}" />
        </label>
        <label>Invertir polaridad
        <input id="ecochg_invert" type="checkbox" ${d.params.invert ? 'checked' : ''} />
        </label>
        <label>Suavizado (puntos)
        <input id="ecochg_smooth" type="number" class="audiometry-input" min="0" max="25" step="1"
        value="${d.params.smooth}" />
        </label>
        </div>
        <p style="font-size:12px; color:#666; margin-top:6px;">Admite datos en CSV: "tiempo(ms), microvoltios" o solo "microvoltios" con Fs arriba.</p>
        </div>

        <div class="form-group">
        <h4 class="section-subtitle">Valores cuantitativos</h4>
        <table class="audiometry-table">
        <thead>
        <tr>
        <th></th>
        <th style="color:#dc3545;">OD</th>
        <th style="color:#007bff;">OI</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td class="freq-label">SP (µV)</td>
        <td><input id="sp_od" type="number" step="0.01" class="audiometry-input" value="${this._val(d.sp?.oido_derecho)}" /></td>
        <td><input id="sp_oi" type="number" step="0.01" class="audiometry-input" value="${this._val(d.sp?.oido_izquierdo)}" /></td>
        </tr>
        <tr>
        <td class="freq-label">AP (µV)</td>
        <td><input id="ap_od" type="number" step="0.01" class="audiometry-input" value="${this._val(d.ap?.oido_derecho)}" /></td>
        <td><input id="ap_oi" type="number" step="0.01" class="audiometry-input" value="${this._val(d.ap?.oido_izquierdo)}" /></td>
        </tr>
        </tbody>
        </table>
        <div style="font-size:12px; color:#555; margin-top:6px;">
        El <strong>ratio SP/AP</strong> se calcula automáticamente en el gráfico si hay valores.
        </div>
        </div>

        <div class="form-group">
        <h4 class="section-subtitle">Señal temporal (pegar CSV o texto)</h4>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
        <div>
        <label for="wf_od">OD</label>
        <textarea id="wf_od" placeholder="t(ms),uV\n0.00,0.02\n0.05,-0.01\n..." style="min-height:120px;">${this._textFromWave(d.waveform?.oido_derecho)}</textarea>
        </div>
        <div>
        <label for="wf_oi">OI</label>
        <textarea id="wf_oi" placeholder="uV (una columna)\n0.02\n-0.01\n..." style="min-height:120px;">${this._textFromWave(d.waveform?.oido_izquierdo)}</textarea>
        </div>
        </div>
        <div style="margin-top:8px; display:flex; gap:8px; flex-wrap:wrap;">
        <button id="wf_demo_od" class="btn btn-secondary">Demo OD</button>
        <button id="wf_demo_oi" class="btn btn-secondary">Demo OI</button>
        <button id="wf_clear" class="btn btn-light">Limpiar</button>
        </div>
        </div>

        <div class="form-group">
        <label for="ecochg_obs">Observaciones</label>
        <textarea id="ecochg_obs" placeholder="Calidad de registro, número de promedios, electrodos, etc." style="min-height:80px;">${d.observaciones || ''}</textarea>
        </div>
        </div>

        <!-- Panel derecho: Preview -->
        <div style="flex:3; min-width:520px;">
        <h4 class="section-subtitle">📈 Preview de trazo ECochG</h4>
        <div id="ecochgPreview" style="border:1px solid #ddd; border-radius:8px; padding:12px; background:white;">
        <canvas id="ecochgCanvas" width="700" height="420" style="width:100%; height:auto;"></canvas>
        <div id="ecochgNoView" style="display:none; padding:12px; color:#666; font-size:13px;">
        Vista previa no disponible. Carga <code>js/components/views/electrocochlear-waveform.js</code> para habilitar el trazo. Como fallback, verás un dibujo simple.
        </div>
        </div>
        </div>
        </div>
        </div>

        <style>
        .audiometry-table { width:100%; border-collapse:collapse; margin-bottom:10px; font-size:14px; }
        .audiometry-table th { background:#f8f9fa; border:1px solid #dee2e6; padding:8px 12px; text-align:center; font-weight:600; }
        .audiometry-table td { border:1px solid #dee2e6; padding:4px 8px; text-align:center; }
        .audiometry-table .freq-label { background:#f8f9fa; font-weight:500; text-align:right; padding-right:15px; }
        .audiometry-input { width:100px; padding:4px 6px; border:1px solid #dee2e6; border-radius:4px; text-align:center; font-size:13px; }
        .btn { border:1px solid #ccc; padding:6px 10px; border-radius:6px; cursor:pointer; }
        .btn-secondary { background:#f3f4f6; }
        .btn-light { background:#fff; }
        .btn:hover { filter:brightness(0.98); }
        </style>
        `;
    }

    /** Inicializar eventos y cargar view externo */
    async initEvents() {
        // Cambios de inputs
        ['ecochg_fs','ecochg_window','ecochg_smooth','sp_od','sp_oi','ap_od','ap_oi'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('input', () => this._onDataChange());
        });
            const invert = document.getElementById('ecochg_invert');
            if (invert) invert.addEventListener('change', () => this._onDataChange());

            // Textareas waveform
            const wfOD = document.getElementById('wf_od');
        const wfOI = document.getElementById('wf_oi');
        if (wfOD) wfOD.addEventListener('input', () => this._onDataChange());
        if (wfOI) wfOI.addEventListener('input', () => this._onDataChange());

        // Botones demo / limpiar
        const bDemoOD = document.getElementById('wf_demo_od');
        const bDemoOI = document.getElementById('wf_demo_oi');
        const bClear  = document.getElementById('wf_clear');
        if (bDemoOD) bDemoOD.addEventListener('click', () => { this._loadDemo('od'); });
        if (bDemoOI) bDemoOI.addEventListener('click', () => { this._loadDemo('oi'); });
        if (bClear)  bClear.addEventListener('click', () => { this._clearWaveforms(); });

        // Cargar view externo
        await this._loadWaveformView();

        // Primer render
        setTimeout(() => this.updatePreview(), 50);
    }

    async _loadWaveformView() {
        try {
            await this.app.loadScript('js/components/views/electrocochlear-waveform.js');
            if (window.ElectrocochlearWaveformView) {
                this.waveView = new window.ElectrocochlearWaveformView('ecochgCanvas');
                document.getElementById('ecochgNoView').style.display = 'none';
            } else {
                this.waveView = null;
                document.getElementById('ecochgNoView').style.display = 'block';
                console.warn('ElectrocochlearWaveformView no encontrada');
            }
        } catch (e) {
            this.waveView = null;
            const el = document.getElementById('ecochgNoView');
            if (el) el.style.display = 'block';
            console.warn('No se pudo cargar electrocochlear-waveform.js, usando fallback', e);
        }
    }

    _onDataChange() {
        this.app.updateModuleData(this.moduleId, this.getData());
        this.updatePreview();
    }

    /** Recolecta datos del formulario */
    getData() {
        const fs = parseInt(document.getElementById('ecochg_fs')?.value || this.defaultFs, 10);
        const windowMs = parseFloat(document.getElementById('ecochg_window')?.value || this.defaultWindowMs);
        const invert = !!document.getElementById('ecochg_invert')?.checked;
        const smooth = parseInt(document.getElementById('ecochg_smooth')?.value || 0, 10);

        const spOD = this._num(document.getElementById('sp_od')?.value);
        const spOI = this._num(document.getElementById('sp_oi')?.value);
        const apOD = this._num(document.getElementById('ap_od')?.value);
        const apOI = this._num(document.getElementById('ap_oi')?.value);

        // Parse waveform textareas (acepta CSV t,uV o columna uV)
        const wfOD = this._parseWaveText(document.getElementById('wf_od')?.value || '', fs);
        const wfOI = this._parseWaveText(document.getElementById('wf_oi')?.value || '', fs);

        return {
            sp: { oido_derecho: spOD, oido_izquierdo: spOI },
            ap: { oido_derecho: apOD, oido_izquierdo: apOI },
            waveform: { oido_derecho: wfOD, oido_izquierdo: wfOI },
            params: { fs, windowMs, invert, smooth },
            observaciones: document.getElementById('ecochg_obs')?.value || ''
        };
    }

    /** Valida consistencia mínima */
    validate(data) {
        const errors = [];
        if (!data || typeof data !== 'object') errors.push('Datos inválidos');

        // Si no hay waveform para ningún oído, al menos debe existir AP o SP
        const hasWf = (data.waveform?.oido_derecho?.length || 0) > 0 || (data.waveform?.oido_izquierdo?.length || 0) > 0;
        const hasNums = (data.sp?.oido_derecho != null) || (data.sp?.oido_izquierdo != null) ||
        (data.ap?.oido_derecho != null) || (data.ap?.oido_izquierdo != null);
        if (!hasWf && !hasNums) errors.push('Ingrese al menos SP/AP o una forma de onda');

        return { isValid: errors.length === 0, errors };
    }

    isComplete(data) {
        // Consideramos completo si hay waveform en al menos un oído
        const hasWfOD = (data.waveform?.oido_derecho?.length || 0) > 16;
        const hasWfOI = (data.waveform?.oido_izquierdo?.length || 0) > 16;
        return hasWfOD || hasWfOI;
    }

    /** Actualiza la previsualización */
    updatePreview() {
        const canvas = document.getElementById('ecochgCanvas');
        if (!canvas) return;

        const data = this.getData();

        if (this.waveView && typeof this.waveView.render === 'function') {
            // View externo: pasa datos crudos y params
            this.waveView.render(data);
            return;
        }

        // Fallback simple: dibuja señal OD/OI (si existen) + marcadores SP/AP
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const m = { top: 30, right: 20, bottom: 50, left: 60 };
        const plotW = canvas.width - m.left - m.right;
        const plotH = canvas.height - m.top - m.bottom;

        // Ejes
        ctx.strokeStyle = '#ddd';
        ctx.strokeRect(m.left, m.top, plotW, plotH);

        // Eje temporal 0–windowMs
        const ms = data.params.windowMs || this.defaultWindowMs;
        const xScale = (tMs) => m.left + (tMs / ms) * plotW;

        // Eje voltaje: auto con ±maxAbs o ±3 µV
        const allVals = [];
        ['oido_derecho','oido_izquierdo'].forEach(ear => {
            (data.waveform?.[ear] || []).forEach(p => allVals.push(p.v));
        });
        const maxAbs = Math.max(3, Math.max(...allVals.map(v => Math.abs(v) || 0), 0));
        const yScale = (uV) => m.top + (1 - ((uV + maxAbs) / (2*maxAbs))) * plotH;

        const drawWave = (arr, color) => {
            if (!arr || arr.length < 2) return;
            ctx.strokeStyle = color; ctx.lineWidth = 1.6; ctx.beginPath();
            ctx.moveTo(xScale(arr[0].t), yScale(arr[0].v));
            for (let i=1;i<arr.length;i++) ctx.lineTo(xScale(arr[i].t), yScale(arr[i].v));
            ctx.stroke();
        };

        // Dibuja OD/OI
        drawWave(data.waveform.oido_derecho, '#dc3545');
        drawWave(data.waveform.oido_izquierdo, '#007bff');

        // Baseline 0 µV
        ctx.strokeStyle = '#aaa'; ctx.setLineDash([4,4]);
        const y0 = yScale(0); ctx.beginPath(); ctx.moveTo(m.left, y0); ctx.lineTo(m.left + plotW, y0); ctx.stroke(); ctx.setLineDash([]);

        // SP/AP markers (si hay valores)
        const drawMarker = (label, uV, x, color) => {
            if (uV == null) return;
            const y = yScale(uV);
            ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 1.5;
            ctx.beginPath(); ctx.moveTo(x-6,y); ctx.lineTo(x+6,y); ctx.stroke();
            ctx.font = '11px Arial'; ctx.fillText(`${label}: ${uV}µV`, x+8, y-4);
        };

        const tAPms = 1.5; // referencia visual fija en fallback
        drawMarker('SP OD', data.sp.oido_derecho, xScale(0.8), '#dc3545');
        drawMarker('AP OD', data.ap.oido_derecho, xScale(tAPms), '#dc3545');
        drawMarker('SP OI', data.sp.oido_izquierdo, xScale(0.8), '#007bff');
        drawMarker('AP OI', data.ap.oido_izquierdo, xScale(tAPms), '#007bff');

        // Etiquetas ejes
        ctx.fillStyle = '#333'; ctx.font = 'bold 12px Arial';
        ctx.fillText('Tiempo (ms)', m.left + plotW/2 - 30, m.top + plotH + 35);
        ctx.save(); ctx.translate(18, m.top + plotH/2); ctx.rotate(-Math.PI/2); ctx.fillText('Amplitud (µV)', -36, 0); ctx.restore();
    }

    /** DEMOS rápidas para probar preview sin datos reales */
    _loadDemo(ear) {
        const fs = parseInt(document.getElementById('ecochg_fs')?.value || this.defaultFs, 10);
        const windowMs = parseFloat(document.getElementById('ecochg_window')?.value || this.defaultWindowMs);
        const n = Math.floor((windowMs/1000) * fs);

        const arr = [];
        for (let i=0;i<n;i++) {
            const t = (i/fs)*1000; // ms
            // Señal sintética: pequeña línea base + SP lento + AP pico rápido ~1.5 ms
            const sp = -0.05 * (1 - Math.exp(-t/2));
            const ap = (t>1.2 && t<2.2) ? Math.exp(-((t-1.6)**2)/(2*0.08**2)) * 0.8 : 0; // pico gaussiano
            const noise = (Math.random()-0.5)*0.02;
            arr.push({ t, v: sp + ap + noise });
        }

        const ta = document.getElementById(ear === 'od' ? 'wf_od' : 'wf_oi');
        if (ta) ta.value = arr.map(p => `${p.t.toFixed(3)},${p.v.toFixed(4)}`).join('\n');

        // Valores SP/AP sugeridos
        if (ear === 'od') {
            const sp = document.getElementById('sp_od'); if (sp && !sp.value) sp.value = -0.4;
            const ap = document.getElementById('ap_od'); if (ap && !ap.value) ap.value = 0.8;
        } else {
            const sp = document.getElementById('sp_oi'); if (sp && !sp.value) sp.value = -0.35;
            const ap = document.getElementById('ap_oi'); if (ap && !ap.value) ap.value = 0.7;
        }

        this._onDataChange();
    }

    _clearWaveforms() {
        const od = document.getElementById('wf_od');
        const oi = document.getElementById('wf_oi');
        if (od) od.value = '';
        if (oi) oi.value = '';
        this._onDataChange();
    }

    /** Utilidades */
    _withDefaults(d) {
        return {
            sp: d?.sp || { oido_derecho: null, oido_izquierdo: null },
            ap: d?.ap || { oido_derecho: null, oido_izquierdo: null },
            waveform: d?.waveform || { oido_derecho: [], oido_izquierdo: [] },
            params: {
                fs: d?.params?.fs ?? this.defaultFs,
                windowMs: d?.params?.windowMs ?? this.defaultWindowMs,
                invert: d?.params?.invert ?? false,
                smooth: d?.params?.smooth ?? 0
            },
            observaciones: d?.observaciones || ''
        };
    }

    _val(v) { return (v === null || v === undefined) ? '' : v; }
    _num(v) { return (v === '' || v === null || v === undefined) ? null : Number(v); }

    _textFromWave(arr) {
        if (!arr || !arr.length) return '';
        const limited = arr.slice(0, 2000); // limitar por si es muy grande
        return limited.map(p => (p.t !== undefined ? `${p.t},${p.v}` : `${p.v}`)).join('\n');
    }

    _parseWaveText(text, fs) {
        if (!text || !text.trim()) return [];
        const lines = text.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
        const out = [];

        // Detectar si la primera línea tiene coma/; (CSV con tiempo)
        const hasTime = /[,;\t]/.test(lines[0]) && lines[0].split(/[,;\t]/).length >= 2;

        if (hasTime) {
            for (const ln of lines) {
                const [a,b] = ln.split(/[,;\t]/);
                const t = parseFloat(a);
                const v = parseFloat(b);
                if (isFinite(t) && isFinite(v)) out.push({ t, v });
            }
        } else {
            // Solo amplitud por muestra en µV; reconstruir t según Fs
            let i = 0;
            for (const ln of lines) {
                const v = parseFloat(ln);
                if (isFinite(v)) {
                    const t = (i++ / fs) * 1000; // ms
                    out.push({ t, v });
                }
            }
        }

        // Invertir si así está marcado
        const invert = !!document.getElementById('ecochg_invert')?.checked;
        if (invert) out.forEach(p => p.v = -p.v);

        // Suavizado simple por media móvil si corresponde
        const smooth = parseInt(document.getElementById('ecochg_smooth')?.value || '0', 10);
        if (smooth && smooth > 1) {
            const k = Math.min(Math.max(2, smooth|0), 25);
            const buf = out.map(p => p.v);
            const sm = [];
            for (let i=0;i<buf.length;i++) {
                let s=0,c=0;
                for (let j=-k;j<=k;j++) {
                    const idx = i+j; if (idx>=0 && idx<buf.length) { s+=buf[idx]; c++; }
                }
                sm[i] = s/c;
            }
            for (let i=0;i<out.length;i++) out[i].v = sm[i];
        }

        // Recortar a ventana ms si procede
        const windowMs = parseFloat(document.getElementById('ecochg_window')?.value || this.defaultWindowMs);
        return out.filter(p => p.t >= 0 && p.t <= windowMs);
    }
}

// Exponer globalmente
window.ElectrocochleoModule = ElectrocochleoModule;
