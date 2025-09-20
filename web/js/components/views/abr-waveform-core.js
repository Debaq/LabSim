/**
 * ABRWaveformCore
 * Lógica compartida para dibujar morfología ABR apilada (OD/OI) en un canvas.
 * Parametrizable por intensidad ('80db' | 'final') y título.
 *
 * Uso:
 *   const core = new ABRWaveformCore({ canvasId: 'abrWaveform80Canvas', intensityKey: '80db', title: '80 dB nHL' });
 *   core.render(data);
 */
class ABRWaveformCore {
  constructor({ canvasId, intensityKey = '80db', title = '' }) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas?.getContext ? this.canvas.getContext('2d') : null;
    this.intensityKey = intensityKey;
    this.title = title;

    // Layout
    this.pad = { left: 46, right: 16, top: 24, bottom: 30, vgap: 30 };
    this.xDomain = [0, 10];   // ms
    this.gridMs = 1;

    // Estilo
    this.colors = {
      od: '#d92534',   // rojo OD
      oi: '#0d6efd',   // azul OI
      grid: '#e9ecef',
      axes: '#6c757d',
      text: '#495057',
      baseline: '#adb5bd'
    };
    this.font = '12px system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif';
  }

  render(data) {
    if (!this.canvas || !this.ctx) return;
    this._ensureSize();
    this._clear();
    this._drawTimeGrid();
    this._drawTitle();

    const { od, oi } = this._extractData(data, this.intensityKey);
    const X = this._linspace(this.xDomain[0], this.xDomain[1], 500);

    const wfOD = this._synthesizeABR(X, od);
    const wfOI = this._synthesizeABR(X, oi);

    // OD arriba, OI abajo
    this._plotTrack(X, wfOD, 'od');
    this._plotTrack(X, wfOI, 'oi');

    // Etiquetas de picos I–III–V
    this._labelPeaks(od, 'od');
    this._labelPeaks(oi, 'oi');

    this._legend();
  }

  // ===== Selección de datos por intensidad =====
  _extractData(data, intensityKey) {
    const stim = data?.stimulus_activo || 'click';
    let block = null;
    if (stim === 'tone_burst') {
      const f = data?.tone_burst_activo || '1k';
      block = data?.tone_burst?.[f] || {};
    } else {
      block = data?.[stim] || {};
    }
    const od = block?.oido_derecho?.[intensityKey] || {};
    const oi = block?.oido_izquierdo?.[intensityKey] || {};

    const normalize = (ear) => {
      const out = {};
      ['I','II','III','IV','V'].forEach(w => {
        const k = `onda_${w}`;
        const it = ear?.[k] || {};
        out[w] = {
          presente: it.presente !== false,
          latencia: (typeof it.latencia === 'number') ? it.latencia : null,
          amplitud: (typeof it.amplitud === 'number') ? it.amplitud : null
        };
      });
      return out;
    };

    return { od: normalize(od), oi: normalize(oi) };
  }

  // ===== Síntesis morfológica compartida =====
  _synthesizeABR(X, series) {
    // Defaults típicos a 80 dB nHL (adultos). Para "Final" la síntesis también aplica;
    // si entregas latencias/amplitudes medidas, las usa para desplazar/escala picos.
    const defaults = {
      I:   { t: 1.6, a: 0.5,  w: 0.08 },
      II:  { t: 2.6, a: 0.25, w: 0.09 },
      III: { t: 3.7, a: 0.7,  w: 0.10 },
      IV:  { t: 4.7, a: 0.3,  w: 0.11 },
      V:   { t: 5.7, a: 1.0,  w: 0.12 }
    };

    const peaks = {};
    ['I','II','III','IV','V'].forEach(w => {
      const pres = series[w]?.presente ?? true;
      const t = (typeof series[w]?.latencia === 'number') ? series[w].latencia : defaults[w].t;
      // Mapear amplitud clínica (µV) a escala normalizada (0..~1.2)
      const aClin = (typeof series[w]?.amplitud === 'number') ? series[w].amplitud : null;
      const a = pres ? (aClin !== null ? Math.max(0.1, Math.min(1.2, aClin * 2.0)) : defaults[w].a) : 0.0;
      const wdt = defaults[w].w;
      peaks[w] = { t, a, w: wdt, present: pres };
    });

    // Suma de gaussianas (picos) + pequeño trough post-V
    const y = new Array(X.length).fill(0);
    for (let i = 0; i < X.length; i++) {
      const x = X[i];
      let s = 0;
      for (const w of ['I','II','III','IV','V']) {
        const p = peaks[w];
        if (!p.present || p.a <= 0) continue;
        s += p.a * Math.exp(-0.5 * ((x - p.t) / p.w) ** 2);
      }
      // "trough" pos-V
      const tV = peaks['V'].t;
      const wV = peaks['V'].w * 1.4;
      const aV = peaks['V'].a;
      const trough = -0.35 * aV * Math.exp(-0.5 * ((x - (tV + 0.2)) / wV) ** 2);
      y[i] = s + trough;
    }

    // Normalizar [-1..1] (no mostramos eje Y)
    const maxAbs = y.reduce((m,v) => Math.max(m, Math.abs(v)), 0.0001);
    const scale = 1.0 / maxAbs;
    return y.map(v => v * scale);
  }

  // ===== Dibujo (compartido) =====
  _plotTrack(X, Ynorm, ear) {
    const ctx = this.ctx;
    const { left, right, top, bottom, vgap } = this.pad;
    const w = this.canvas.width / (window.devicePixelRatio || 1);
    const h = this.canvas.height / (window.devicePixelRatio || 1);
    const plotH = (h - top - bottom - vgap) / 2;
    const yTop = (ear === 'od') ? top : top + plotH + vgap;
    const yMid = yTop + plotH / 2;

    // Baseline
    ctx.save();
    ctx.strokeStyle = this.colors.baseline;
    ctx.lineWidth = 1;
    this._line(this._x(this.xDomain[0], left, w - right), yMid, this._x(this.xDomain[1], left, w - right), yMid);
    ctx.restore();

    // Trazo
    ctx.save();
    ctx.strokeStyle = ear === 'od' ? this.colors.od : this.colors.oi;
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < X.length; i++) {
      const x = this._x(X[i], left, w - right);
      const yy = this._mapY(Ynorm[i], yTop + plotH - 8, yTop + 8); // padding vertical
      if (i === 0) ctx.moveTo(x, yy); else ctx.lineTo(x, yy);
    }
    ctx.stroke();
    ctx.restore();

    // Etiqueta de oído
    ctx.save();
    ctx.fillStyle = this.colors.text;
    ctx.font = this.font;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    const earLabel = ear === 'od' ? 'OD' : 'OI';
    ctx.fillText(`${earLabel} · ${this.title || (this.intensityKey === 'final' ? 'Final' : '80 dB nHL')}`, this._x(this.xDomain[0], left, w - right), yTop - 16);
    ctx.restore();
  }

  _labelPeaks(series, ear) {
    const ctx = this.ctx;
    const { left, right, top, bottom, vgap } = this.pad;
    const w = this.canvas.width / (window.devicePixelRatio || 1);
    const h = this.canvas.height / (window.devicePixelRatio || 1);
    const plotH = (h - top - bottom - vgap) / 2;
    const yTop = (ear === 'od') ? top : top + plotH + vgap;
    const color = ear === 'od' ? this.colors.od : this.colors.oi;

    ctx.save();
    ctx.fillStyle = color;
    ctx.strokeStyle = color;
    ctx.font = this.font;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';

    ['I','III','V'].forEach(wv => {
      const it = series[wv];
      if (!it || it.presente === false) return;
      const t = (typeof it.latencia === 'number') ? it.latencia : (wv === 'I' ? 1.6 : (wv === 'III' ? 3.7 : 5.7));
      const x = this._x(t);
      const y = yTop + 14;
      ctx.fillText(wv, x, y);
      // guía vertical suave
      ctx.globalAlpha = 0.2;
      this._line(x, yTop+6, x, yTop+plotH-6);
      ctx.globalAlpha = 1.0;
    });

    ctx.restore();
  }

  _legend() {
    const ctx = this.ctx;
    ctx.save();
    ctx.font = this.font;
    ctx.textBaseline = 'middle';

    const w = this.canvas.width / (window.devicePixelRatio || 1);
    const h = this.canvas.height / (window.devicePixelRatio || 1);

    const x0 = w - 180;
    const y0 = h - 16;

    // OD
    ctx.fillStyle = this.colors.od;
    ctx.fillRect(x0, y0 - 4, 22, 2);
    ctx.fillStyle = this.colors.text;
    ctx.textAlign = 'left';
    ctx.fillText('OD', x0 + 28, y0);

    // OI
    const x1 = x0 + 70;
    ctx.fillStyle = this.colors.oi;
    ctx.fillRect(x1, y0 - 4, 22, 2);
    ctx.fillStyle = this.colors.text;
    ctx.fillText('OI', x1 + 28, y0);

    ctx.restore();
  }

  // ===== Utilitarios de canvas =====
  _drawTitle() {
    if (!this.title) return;
    const ctx = this.ctx;
    ctx.save();
    ctx.fillStyle = this.colors.text;
    ctx.font = '600 13px ' + this.font;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
    ctx.fillText(this.title, this.pad.left, this.pad.top - 10);
    ctx.restore();
  }

  _ensureSize() {
    const w = this.canvas.clientWidth || 640;
    const h = this.canvas.clientHeight || 260;
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = Math.round(w * dpr);
    this.canvas.height = Math.round(h * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  _clear() {
    const ctx = this.ctx;
    const w = this.canvas.width / (window.devicePixelRatio || 1);
    const h = this.canvas.height / (window.devicePixelRatio || 1);
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, w, h);
  }

  _drawTimeGrid() {
    const ctx = this.ctx;
    const w = this.canvas.width / (window.devicePixelRatio || 1);
    const h = this.canvas.height / (window.devicePixelRatio || 1);
    ctx.save();
    ctx.strokeStyle = this.colors.grid;
    ctx.fillStyle = this.colors.text;
    ctx.font = this.font;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';

    for (let ms = this.xDomain[0]; ms <= this.xDomain[1] + 1e-6; ms += this.gridMs) {
      const x = this._x(ms);
      this._line(x, this.pad.top - 6, x, h - this.pad.bottom + 6);
      ctx.fillText(`${ms}`, x, h - this.pad.bottom + 8);
    }
    ctx.fillText('Tiempo (ms)', (this._x(this.xDomain[0]) + this._x(this.xDomain[1])) / 2, h - this.pad.bottom + 22);
    ctx.restore();
  }

  _x(ms, leftOverride=null, rightOverride=null) {
    const w = this.canvas.width / (window.devicePixelRatio || 1);
    const left = leftOverride ?? this.pad.left;
    const right = rightOverride ?? (w - this.pad.right);
    const plotW = right - left;
    const t = (ms - this.xDomain[0]) / (this.xDomain[1] - this.xDomain[0]);
    return left + plotW * t;
  }

  _mapY(yNorm, yBottom, yTop) {
    const t = (yNorm + 1) / 2; // [-1..1] -> [0..1]
    return yBottom - (yBottom - yTop) * t;
  }

  _line(x1, y1, x2, y2) {
    const ctx = this.ctx;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }

  _linspace(a, b, n) {
    const out = new Array(n);
    const step = (b - a) / (n - 1);
    for (let i = 0; i < n; i++) out[i] = a + i * step;
    return out;
  }
}

window.ABRWaveformCore = ABRWaveformCore;
