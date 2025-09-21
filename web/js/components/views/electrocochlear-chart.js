// js/components/views/electrocochlear-waveform.js
// Canvas puro para trazo ECochG (OD/OI) con SP/AP y ratio
// API: new ElectrocochlearWaveformView(canvasId).render(data)
// data = { waveform: { oido_derecho: [{t(ms),v(µV)},...], oido_izquierdo: [...] },
//          sp: { oido_derecho: num|null, oido_izquierdo: num|null },
//          ap: { oido_derecho: num|null, oido_izquierdo: num|null },
//          params: { fs, windowMs, invert, smooth } }

class ElectrocochlearWaveformView {
  constructor(canvasId) {
    this.canvasId = canvasId;
    this.canvas = null;
    this.ctx = null;
    this.cfg = {
      margin: { top: 28, right: 22, bottom: 46, left: 60 },
      colors: {
        od: '#dc3545',
        oi: '#007bff',
        grid: '#e5e7eb',
        axes: '#9ca3af',
        text: '#111827',
        zero: '#9ca3af',
        spLbl: '#10b981',
        apLbl: '#f59e0b'
      },
      tickXms: [0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10],
      padYuv: 0.3, // acolchado (µV) sobre max abs
      minSpanY: 3.0 // al menos ±3 µV si la señal es muy pequeña
    };
  }

  init() {
    this.canvas = document.getElementById(this.canvasId);
    if (!this.canvas) return false;
    this.ctx = this.canvas.getContext('2d');
    return true;
  }

  render(data) {
    if (!this.init()) return;

    const cv = this.canvas, ctx = this.ctx, m = this.cfg.margin;
    ctx.clearRect(0, 0, cv.width, cv.height);

    const plotW = cv.width  - m.left - m.right;
    const plotH = cv.height - m.top  - m.bottom;

    // --- preparar datos ---
    const wfOD = (data?.waveform?.oido_derecho ?? []).filter(p => isFinite(p.t) && isFinite(p.v));
    const wfOI = (data?.waveform?.oido_izquierdo ?? []).filter(p => isFinite(p.t) && isFinite(p.v));
    const winMs = data?.params?.windowMs ?? 8;

    // X scale (ms)
    const xScale = (tMs) => m.left + (Math.max(0, Math.min(winMs, tMs)) / winMs) * plotW;

    // Y domain (µV) basado en datos de ambos oídos
    const allVals = [...wfOD.map(p=>p.v), ...wfOI.map(p=>p.v)];
    const maxAbs = allVals.length ? Math.max(...allVals.map(v=>Math.abs(v))) : 0;
    const span = Math.max(this.cfg.minSpanY, maxAbs + this.cfg.padYuv);
    const yMin = -span, yMax = span;
    const yScale = (uV) => m.top + (1 - (uV - yMin) / (yMax - yMin)) * plotH;

    // --- grilla y ejes ---
    this.drawGrid(xScale, yScale, winMs, yMin, yMax, plotW, plotH);

    // --- trazos ---
    this.drawWave(wfOD, xScale, yScale, this.cfg.colors.od);
    this.drawWave(wfOI, xScale, yScale, this.cfg.colors.oi);

    // línea base 0 µV
    ctx.strokeStyle = this.cfg.colors.zero; ctx.setLineDash([4,4]);
    ctx.beginPath(); ctx.moveTo(m.left, yScale(0)); ctx.lineTo(m.left + plotW, yScale(0)); ctx.stroke(); ctx.setLineDash([]);

    // --- marcadores SP/AP si existen (o autoestimados) ---
    const markOpts = { xScale, yScale };

    const spOD = this._num(data?.sp?.oido_derecho);
    const apOD = this._num(data?.ap?.oido_derecho);
    const spOI = this._num(data?.sp?.oido_izquierdo);
    const apOI = this._num(data?.ap?.oido_izquierdo);

    const detOD = this._detectIfNeeded(wfOD, spOD, apOD);
    const detOI = this._detectIfNeeded(wfOI, spOI, apOI);

    this.drawMarkers('OD', detOD, this.cfg.colors.od, markOpts);
    this.drawMarkers('OI', detOI, this.cfg.colors.oi, markOpts);

    // leyenda
    this.drawLegend();
  }

  // === dibujo base ===
  drawGrid(xScale, yScale, winMs, yMin, yMax, plotW, plotH) {
    const ctx = this.ctx, m = this.cfg.margin;

    // marco
    ctx.strokeStyle = this.cfg.colors.grid;
    ctx.lineWidth = 1;
    ctx.strokeRect(m.left, m.top, plotW, plotH);

    // ticks Y cada 1 µV (si el rango lo permite)
    const stepY = this._niceStep((yMax - yMin) / 6) || 1;
    for (let v = Math.ceil(yMin/stepY)*stepY; v <= yMax; v += stepY) {
      const y = yScale(v);
      ctx.strokeStyle = v === 0 ? this.cfg.colors.axes : this.cfg.colors.grid;
      ctx.lineWidth = v === 0 ? 1.5 : 1;
      ctx.beginPath(); ctx.moveTo(m.left, y); ctx.lineTo(m.left + plotW, y); ctx.stroke();
      this._label(`${this._fmt(v,2)}`, m.left - 34, y + 3, '11px Arial', this.cfg.colors.text, 'right');
    }

    // ticks X según lista predefinida (sólo dentro de ventana)
    const ticks = this.cfg.tickXms.filter(t => t <= winMs);
    ticks.forEach(t => {
      const x = xScale(t);
      ctx.strokeStyle = this.cfg.colors.grid; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, m.top); ctx.lineTo(x, m.top + plotH); ctx.stroke();
      this._label(`${this._fmt(t, t<1?2:1)} ms`, x, m.top + plotH + 16, '11px Arial', this.cfg.colors.text, 'center');
    });

    // títulos
    this._label('Tiempo (ms)', m.left + plotW/2, m.top + plotH + 34, 'bold 12px Arial', this.cfg.colors.text, 'center');
    this._vlabel('Amplitud (µV)', 18, m.top + plotH/2, 'bold 12px Arial', this.cfg.colors.text);
  }

  drawWave(arr, xScale, yScale, color) {
    const ctx = this.ctx;
    if (!arr || arr.length < 2) return;

    // adelgazado simple por salto de x para evitar sobretrazo
    const minDx = (xScale(arr[arr.length-1].t) - xScale(arr[0].t)) / 1000; // ~1000 segmentos máx.
    ctx.strokeStyle = color; ctx.lineWidth = 1.8; ctx.beginPath();
    let lastX = -Infinity;
    for (let i=0;i<arr.length;i++) {
      const x = xScale(arr[i].t), y = yScale(arr[i].v);
      if (x - lastX < minDx && i !== 0 && i !== arr.length-1) continue;
      lastX = x;
      if (ctx.currentPathStarted) ctx.lineTo(x, y); else { ctx.moveTo(x, y); ctx.currentPathStarted = true; }
    }
    ctx.stroke(); ctx.currentPathStarted = false;
  }

  drawMarkers(label, det, color, { xScale, yScale }) {
    const ctx = this.ctx;
    if (!det) return;

    const { sp, ap, tSPms, tAPms } = det;

    // SP
    if (sp != null) {
      const x = xScale(tSPms ?? 0.8);
      const y = yScale(sp);
      this._hMarker(x, y, color);
      this._label(`SP ${label}: ${this._fmt(sp,3)} µV`, x + 8, y - 6, '11px Arial', this.cfg.colors.spLbl, 'left');
    }

    // AP
    if (ap != null) {
      const x = xScale(tAPms ?? 1.6);
      const y = yScale(ap);
      this._hMarker(x, y, color);
      this._label(`AP ${label}: ${this._fmt(ap,3)} µV`, x + 8, y - 6, '11px Arial', this.cfg.colors.apLbl, 'left');
    }

    // ratio si procede
    if (sp != null && ap != null && ap !== 0) {
      const ratio = Math.abs(sp) / Math.abs(ap);
      const x = xScale((tAPms ?? 1.6) + 0.25);
      const y = yScale((ap + (sp||0))/2);
      const ok = ratio <= 0.37;
      this._label(`SP/AP = ${ratio.toFixed(3)}`, x, y, '12px Courier New', ok? '#10b981' : '#ef4444', 'left');
    }
  }

  drawLegend() {
    const ctx = this.ctx;
    const y = this.canvas.height - 18;
    let x = 18;

    // OD
    this._legendSwatch(x, y-6, this.cfg.colors.od); x += 22;
    this._label('OD', x, y, '12px Arial', this.cfg.colors.text, 'left'); x += 36;

    // OI
    this._legendSwatch(x, y-6, this.cfg.colors.oi); x += 22;
    this._label('OI', x, y, '12px Arial', this.cfg.colors.text, 'left'); x += 36;

    // etiquetas SP/AP
    this._legendBox(x, y-10, this.cfg.colors.spLbl); x += 22;
    this._label('SP', x, y, '12px Arial', this.cfg.colors.text, 'left'); x += 28;
    this._legendBox(x, y-10, this.cfg.colors.apLbl); x += 22;
    this._label('AP', x, y, '12px Arial', this.cfg.colors.text, 'left');
  }

  // === helpers ===
  _detectIfNeeded(arr, spVal, apVal) {
    if ((!arr || arr.length < 8) && spVal == null && apVal == null) return null;

    // ventana heurística para clínica (clic): SP: 0.6–1.0 ms; AP: 1.1–2.5 ms
    const spWin = [0.6, 1.0];
    const apWin = [1.1, 2.5];

    const pickWin = (win) => arr.filter(p => p.t >= win[0] && p.t <= win[1]);
    const mean = (xs) => xs.length ? xs.reduce((a,b)=>a+b,0)/xs.length : null;

    let sp = spVal;
    if (sp == null) {
      const seg = pickWin(spWin).map(p=>p.v);
      sp = mean(seg); // SP suele ser deflexión sostenida
    }

    let ap = apVal;
    let tAPms = null;
    if (ap == null) {
      const seg = pickWin(apWin);
      if (seg.length) {
        // maximiza |v| (pico rápido)
        let best = seg[0];
        for (const p of seg) if (Math.abs(p.v) > Math.abs(best.v)) best = p;
        ap = best.v; tAPms = best.t;
      }
    } else {
      // si hay AP dado, estimar latencia como tiempo del |pico| en ventana
      const seg = pickWin(apWin);
      if (seg.length) {
        let best = seg[0];
        for (const p of seg) if (Math.abs(p.v) > Math.abs(best.v)) best = p;
        tAPms = best.t;
      }
    }

    // tSP aproximado: centro de la ventana SP si no hay dato
    const tSPms = (sp != null) ? (spWin[0] + spWin[1]) / 2 : null;

    if (sp == null && ap == null) return null;
    return { sp, ap, tSPms, tAPms };
  }

  _hMarker(x, y, color) {
    const ctx = this.ctx;
    ctx.strokeStyle = color; ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.moveTo(x-6, y); ctx.lineTo(x+6, y); ctx.stroke();
  }

  _legendSwatch(x, y, color) {
    const ctx = this.ctx; ctx.strokeStyle = color; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x+18, y); ctx.stroke();
  }

  _legendBox(x, y, color) {
    const ctx = this.ctx; ctx.fillStyle = color; ctx.fillRect(x, y, 16, 8);
  }

  _label(text, x, y, font, color, align='left') {
    const ctx = this.ctx; ctx.fillStyle = color; ctx.font = font; ctx.textAlign = align; ctx.fillText(text, x, y);
  }

  _vlabel(text, x, y, font, color) {
    const ctx = this.ctx; ctx.save(); ctx.translate(x, y); ctx.rotate(-Math.PI/2); this._label(text, 0, 0, font, color, 'center'); ctx.restore();
  }

  _fmt(v, dec=2) { return (Math.abs(v) >= 1 ? v.toFixed(dec) : v.toFixed(Math.max(dec, 3))); }
  _num(v) { return (v === '' || v === null || v === undefined) ? null : Number(v); }
  _niceStep(span) {
    if (!isFinite(span) || span <= 0) return 1;
    const pow10 = Math.pow(10, Math.floor(Math.log10(span)));
    const candidates = [1, 2, 2.5, 5, 10].map(c => c * pow10);
    for (const c of candidates) if (span / c <= 8) return c;
    return candidates[candidates.length-1];
  }
}

window.ElectrocochlearWaveformView = ElectrocochlearWaveformView;
