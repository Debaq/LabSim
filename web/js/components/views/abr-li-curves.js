/**
 * ABRLatencyIntensityView
 * Latencia (ms) vs Intensidad (dB nHL) para I, III, V.
 * Cambios solicitados:
 *  - Sin línea media: solo banda normativa (área transparente).
 *  - Eje X invertido: mostrar 0 → 80 (izquierda → derecha).
 *  - Los puntos reales se dibujan como números romanos ('I','III','V').
 *  - Colores: OD rojo, OI azul.
 *  - Intensidades fijas: [80, 60, 40, 20, 0] (datos); display: [0,20,40,60,80].
 */
class ABRLatencyIntensityView {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas?.getContext ? this.canvas.getContext('2d') : null;
    this.font = '12px system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif';

    this.colors = {
      grid: '#e9ecef',
      axes: '#6c757d',
      text: '#495057',
      bandI:  '#7c4dff',
      bandIII:'#20c997',
      bandV:  '#ff6b6b',
      od: '#d92534',
      oi: '#0d6efd'
    };
    this.alphaFill = 0.12;
    this.pad = { left: 54, right: 16, top: 36, bottom: 44 };

    this.dataIntensities = [80, 60, 40, 20, 0];
    this.displayIntensities = [0, 20, 40, 60, 80];

    this.normative = {
      adultos: {
        I:   { mean: [1.55, 1.65, 1.85, null, null], sd: [0.15, 0.17, 0.22, 0.25, 0.25] },
        III: { mean: [3.80, 4.10, 4.60, 5.30, null], sd: [0.22, 0.25, 0.32, 0.38, 0.40] },
        V:   { mean: [5.60, 5.95, 6.60, 7.40, 8.30], sd: [0.30, 0.35, 0.45, 0.55, 0.65] }
      },
      ninos: {
        I:   { mean: [1.80, 1.95, 2.25, null, null], sd: [0.20, 0.25, 0.30, 0.35, 0.35] },
        III: { mean: [4.20, 4.55, 5.05, 5.85, null], sd: [0.28, 0.32, 0.40, 0.50, 0.55] },
        V:   { mean: [6.20, 6.60, 7.20, 8.00, 8.90], sd: [0.35, 0.42, 0.52, 0.65, 0.80] }
      }
    };

    this.group = 'adultos';
    this._injectControls();
  }

  render(data) {
    if (!this.canvas || !this.ctx) return;
    this._ensureSize();
    this._clear();

    const real = this._extractRealDataByEar(data);

    const yMin = 0.8;
    const yMax = Math.max(
      this._maxOf(this.normative[this.group].I),
                          this._maxOf(this.normative[this.group].III),
                          this._maxOf(this.normative[this.group].V),
                          this._maxArr(real.OD.I), this._maxArr(real.OD.III), this._maxArr(real.OD.V),
                          this._maxArr(real.OI.I), this._maxArr(real.OI.III), this._maxArr(real.OI.V),
                          9.0
    ) + 0.4;

    this._setScales({ xDomain: [0, this.displayIntensities.length - 1], yDomain: [yMin, yMax] });

    this._drawGrid();
    this._drawAxes();
    this._title(`Curvas Latencia–Intensidad · ${this.group === 'adultos' ? 'Adultos' : 'Niños'}`);

    this._plotNormBand('I',   this.colors.bandI);
    this._plotNormBand('III', this.colors.bandIII);
    this._plotNormBand('V',   this.colors.bandV);

    this._plotRoman(real.OD, this.colors.od);
    this._plotRoman(real.OI, this.colors.oi);

    this._legend();
  }

  // === UI ===
  _injectControls() {
    if (!this.canvas?.parentElement) return;
    const wrapper = this.canvas.parentElement;

    const bar = document.createElement('div');
    bar.style.display = 'flex';
    bar.style.justifyContent = 'flex-end';
    bar.style.gap = '14px';
    bar.style.alignItems = 'center';
    bar.style.margin = '0 0 6px 0';
    bar.style.font = this.font;

    const lbl = document.createElement('label');
    lbl.textContent = 'Norma:';
    lbl.style.color = '#495057';

    const makeRadio = (txt, value) => {
      const lab = document.createElement('label');
      lab.style.display = 'inline-flex';
      lab.style.alignItems = 'center';
      lab.style.gap = '6px';
      lab.style.cursor = 'pointer';
      const rb = document.createElement('input');
      rb.type = 'radio';
      rb.name = 'abr-li-norm';
      rb.value = value;
      rb.checked = (this.group === value);
      rb.addEventListener('change', () => {
        this.group = value;
        if (this._lastData) this.render(this._lastData);
      });
        const span = document.createElement('span');
        span.textContent = txt;
        lab.appendChild(rb);
        lab.appendChild(span);
        return lab;
    };

    bar.appendChild(lbl);
    bar.appendChild(makeRadio('Adultos', 'adultos'));
    bar.appendChild(makeRadio('Niños', 'ninos'));

    wrapper.insertBefore(bar, this.canvas);
  }

  // === Datos reales ===
  _extractRealDataByEar(data) {
    this._lastData = data;

    const stim = data?.stimulus_activo || 'click';
    let block = null;
    if (stim === 'tone_burst') {
      const f = data?.tone_burst_activo || '1k';
      block = data?.tone_burst?.[f] || {};
    } else {
      block = data?.[stim] || {};
    }

    const right = block?.oido_derecho;
    const left  = block?.oido_izquierdo;

    const from80 = (ear) => {
      const o = ear?.['80db'] || {};
      return {
        I:   o?.onda_I?.latencia ?? null,
        III: o?.onda_III?.latencia ?? null,
        V:   o?.onda_V?.latencia ?? null
      };
    };

    const od80 = from80(right);
    const oi80 = from80(left);

    const extraR = (right?.lat_int) || {};
    const extraL = (left?.lat_int)  || {};

    const toArray = (ear80, extra) => {
      const map = { 80: ear80, 60: extra[60] || {}, 40: extra[40] || {}, 20: extra[20] || {}, 0: extra[0] || {} };
      const arrByWave = (w) => this.dataIntensities.map(L => {
        const src = map[L];
        const v = (L === 80) ? ear80[w] : (typeof src[w] === 'number' ? src[w] : null);
        return v ?? null;
      });
      return { I: arrByWave('I'), III: arrByWave('III'), V: arrByWave('V') };
    };

    return {
      OD: toArray(od80, extraR),
      OI: toArray(oi80, extraL)
    };
  }

  // === Dibujo ===
  _setScales({ xDomain, yDomain }) {
    this.xDomain = xDomain;
    this.yDomain = yDomain;
  }

  _drawGrid() {
    const ctx = this.ctx;
    ctx.save();
    ctx.strokeStyle = this.colors.grid;
    ctx.lineWidth = 1;

    for (let i = 0; i < this.displayIntensities.length; i++) {
      const x = this._x(i);
      this._line(x, this._y(this.yDomain[0]), x, this._y(this.yDomain[1]));
    }

    const step = 0.5;
    for (let y = Math.ceil(this.yDomain[0]/step)*step; y <= this.yDomain[1]+1e-6; y += step) {
      const yy = this._y(y);
      this._line(this._x(0), yy, this._x(this.displayIntensities.length-1), yy);
    }

    ctx.restore();
  }

  _drawAxes() {
    const ctx = this.ctx;
    ctx.save();
    ctx.strokeStyle = this.colors.axes;
    ctx.lineWidth = 1.5;

    this._line(this._x(0), this._y(this.yDomain[0]), this._x(this.displayIntensities.length-1), this._y(this.yDomain[0]));
    this._line(this._x(0), this._y(this.yDomain[0]), this._x(0), this._y(this.yDomain[1]));

    ctx.fillStyle = this.colors.text;
    ctx.font = this.font;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    for (let i = 0; i < this.displayIntensities.length; i++) {
      ctx.fillText(`${this.displayIntensities[i]}`, this._x(i), this._y(this.yDomain[0]) + 8);
    }
    ctx.fillText('Intensidad (dB nHL)', (this._x(0)+this._x(this.displayIntensities.length-1))/2, this._y(this.yDomain[0]) + 24);

    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let y = Math.ceil(this.yDomain[0]); y <= this.yDomain[1]+1e-6; y += 1.0) {
      ctx.fillText(`${y.toFixed(0)}`, this._x(0) - 6, this._y(y));
    }
    ctx.save();
    ctx.rotate(-Math.PI/2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText('Latencia (ms)', -(this._y(this.yDomain[0]) + (this._y(this.yDomain[1])-this._y(this.yDomain[0]))/2), this._x(0) - 38);
    ctx.restore();

    ctx.restore();
  }

  _title(text) {
    const ctx = this.ctx;
    ctx.save();
    ctx.fillStyle = this.colors.text;
    ctx.font = '600 13px ' + this.font;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
    ctx.fillText(text, this.pad.left, this.pad.top - 10);
    ctx.restore();
  }

  _plotNormBand(wave, color) {
    const set = this.normative[this.group][wave];
    if (!set) return;
    const { mean, sd } = set;

    const mapIdx = (L) => this.dataIntensities.indexOf(L);
    const order = this.displayIntensities;

    const upper = [], lower = [];
    for (let i = 0; i < order.length; i++) {
      const idx = mapIdx(order[i]);
      if (idx === -1) { upper.push(null); lower.push(null); continue; }
      const m = mean[idx];
      if (m == null) { upper.push(null); lower.push(null); continue; }
      const s = (sd?.[idx] ?? 0.3);
      upper.push(m + 2*s);
      lower.push(m - 2*s);
    }

    this._fillBand(lower, upper, color, this.alphaFill);
  }

  _plotRoman(earData, color) {
    this._scatterRoman(earData.I,   'I',   color);
    this._scatterRoman(earData.III, 'III', color);
    this._scatterRoman(earData.V,   'V',   color);
  }

  _legend() {
    const ctx = this.ctx;
    ctx.save();
    ctx.font = this.font;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';

    let x = this._x(this.displayIntensities.length-1) - 160;
    const y = this._y(this.yDomain[1]) + 18;

    const item = (c, label) => {
      ctx.fillStyle = c;
      ctx.fillRect(x, y-4, 18, 3);
      ctx.fillStyle = this.colors.text;
      ctx.fillText(label, x + 24, y);
      x += 80;
    };

    item(this.colors.od, 'OD');
    item(this.colors.oi, 'OI');

    ctx.restore();
  }

  // === Primitivas ===
  _ensureSize() {
    const w = this.canvas.clientWidth || 640;
    const h = this.canvas.clientHeight || 300;
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width  = Math.round(w * dpr);
    this.canvas.height = Math.round(h * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  _clear() {
    const ctx = this.ctx;
    const w = this.canvas.width / (window.devicePixelRatio || 1);
    const h = this.canvas.height / (window.devicePixelRatio || 1);
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, w, h);
  }

  _x(i) {
    const left = this.pad.left;
    const right = (this.canvas.width / (window.devicePixelRatio || 1)) - this.pad.right;
    const plotW = right - left;
    const t = (i - 0) / (this.displayIntensities.length - 1);
    return left + plotW * t;
  }

  _y(ms) {
    const top = this.pad.top;
    const bottom = (this.canvas.height / (window.devicePixelRatio || 1)) - this.pad.bottom;
    const plotH = bottom - top;
    const t = (ms - this.yDomain[0]) / (this.yDomain[1] - this.yDomain[0]);
    return bottom - plotH * t;
  }

  _line(x1, y1, x2, y2) {
    const ctx = this.ctx;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }

  _fillBand(lower, upper, color, alpha=0.12) {
    const ctx = this.ctx;
    ctx.save();
    ctx.fillStyle = this._alpha(color, alpha);

    const pts = [];
    for (let i = 0; i < upper.length; i++) {
      if (upper[i] == null) continue;
      pts.push([this._x(i), this._y(upper[i])]);
    }
    for (let i = lower.length - 1; i >= 0; i--) {
      if (lower[i] == null) continue;
      pts.push([this._x(i), this._y(lower[i])]);
    }

    if (pts.length >= 3) {
      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (let k = 1; k < pts.length; k++) ctx.lineTo(pts[k][0], pts[k][1]);
      ctx.closePath();
      ctx.fill();
    }
    ctx.restore();
  }

  _scatterRoman(arr, roman, color) {
    const ctx = this.ctx;
    ctx.save();
    ctx.fillStyle = color;
    ctx.font = 'bold 12px ' + this.font;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    const mapIdx = (L) => this.dataIntensities.indexOf(L);
    for (let i = 0; i < this.displayIntensities.length; i++) {
      const L = this.displayIntensities[i];
      const j = mapIdx(L);
      if (j === -1) continue;
      const v = arr[j];
      if (typeof v === 'number') {
        const x = this._x(i), y = this._y(v);
        ctx.fillText(roman, x, y);
      }
    }

    ctx.restore();
  }

  _alpha(hexOrCss, a) {
    if (hexOrCss.startsWith('#') && hexOrCss.length === 7) {
      const r = parseInt(hexOrCss.slice(1,3),16);
      const g = parseInt(hexOrCss.slice(3,5),16);
      const b = parseInt(hexOrCss.slice(5,7),16);
      return `rgba(${r}, ${g}, ${b}, ${a})`;
    }
    return hexOrCss;
  }

  _maxOf(set) {
    if (!set) return 0;
    const arr = set.mean || [];
    let m = 0;
    for (const v of arr) if (typeof v === 'number') m = Math.max(m, v);
    return m;
  }

  _maxArr(arr) {
    if (!arr) return 0;
    let m = 0;
    for (const v of arr) if (typeof v === 'number') m = Math.max(m, v);
    return m;
  }
}

window.ABRLatencyIntensityView = ABRLatencyIntensityView;
