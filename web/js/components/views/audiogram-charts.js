// js/components/views/audiogram-charts.js
class AudiogramChartView {
  constructor(canvasId) {
    this.canvasId = canvasId;
    this.canvas = null;
    this.ctx = null;
    this.config = {
      margin: { top: 30, right: 40, bottom: 50, left: 60 },
      colors: {
        od: '#dc3545', // aéreo/óseo OD
        oi: '#007bff', // aéreo/óseo OI
        grid: '#ddd',
        gridStrong: '#333',
        text: '#333'
      }
    };
  }

  init() {
    this.canvas = document.getElementById(this.canvasId);
    if (!this.canvas) return false;
    this.ctx = this.canvas.getContext('2d');
    return true;
  }

  render(data, opts = {}) {
    if (!this.init()) return;
    const ctx = this.ctx, cv = this.canvas;

    // limpiar
    ctx.clearRect(0, 0, cv.width, cv.height);

    // layout
    const m = this.config.margin;
    const plotW = cv.width  - m.left - m.right;
    const plotH = cv.height - m.top  - m.bottom;

    // frecuencias a mostrar (incluye altas si te las pasan)
    const freqs = opts.freqs ??
      (opts.showHighFreq
        ? ['125','250','500','1000','2000','4000','8000','9000','10000','11200','12500','14000','16000','18000','20000']
        : ['125','250','500','1000','2000','4000','8000']);

    // escalas
    const xScale = (i) => m.left + (i / (freqs.length - 1)) * plotW;
    const yScale = (db) => m.top + ((db + 10) / 130) * plotH;

    // grilla y ejes (mismo diseño que tenías)
    this.drawGrid(freqs, xScale, yScale, plotW, plotH);

    // datos
    this.drawData(data, freqs, xScale, yScale);
  }

  drawGrid(freqs, xScale, yScale, plotW, plotH) {
    const ctx = this.ctx, m = this.config.margin;

    // verticales (frecuencias)
    ctx.strokeStyle = this.config.colors.grid;
    ctx.lineWidth = 1;
    ctx.fillStyle = '#666';
    ctx.font = '11px Arial';

    freqs.forEach((f, i) => {
      const x = xScale(i);
      ctx.beginPath();
      ctx.moveTo(x, m.top);
      ctx.lineTo(x, m.top + plotH);
      ctx.stroke();

      ctx.save();
      ctx.translate(x, m.top + plotH + 15);
      ctx.rotate(-Math.PI/4);
      ctx.fillText(f, -10, 0);
      ctx.restore();
    });

    // horizontales (dB)
    for (let db = -10; db <= 120; db += 10) {
      if (db === 0 || db === 20) {
        ctx.strokeStyle = this.config.colors.gridStrong;
        ctx.lineWidth = 2;
      } else {
        ctx.strokeStyle = this.config.colors.grid;
        ctx.lineWidth = 1;
      }
      const y = yScale(db);
      ctx.beginPath();
      ctx.moveTo(m.left, y);
      ctx.lineTo(m.left + plotW, y);
      ctx.stroke();

      if (db % 20 === 0) {
        ctx.fillStyle = '#333';
        ctx.fillText(String(db), m.left - 25, y + 3);
      }
    }

    // etiquetas superiores (frecuencias)
    ctx.fillStyle = '#333';
    ctx.font = '11px Arial';
    freqs.forEach((f, i) => {
      const x = xScale(i);
      ctx.save();
      ctx.translate(x, m.top - 10);
      ctx.rotate(-Math.PI/4);
      ctx.fillText(f, -10, 0);
      ctx.restore();
    });

    // títulos
    ctx.fillStyle = '#333';
    ctx.font = 'bold 12px Arial';
    ctx.fillText('Frecuencia (Hz)', m.left + plotW/2 - 40, m.top + plotH + 40);

    ctx.save();
    ctx.translate(15, m.top + plotH/2);
    ctx.rotate(-Math.PI/2);
    ctx.fillText('Umbral (dB HL)', -40, 0);
    ctx.restore();
  }

  drawData(data, freqs, xScale, yScale) {
    const styles = {
      aereo_od: { color: this.config.colors.od, symbol: 'circle', line: 'solid' },
      aereo_oi: { color: this.config.colors.oi, symbol: 'x',      line: 'solid' },
      oseo_od:  { color: this.config.colors.od, symbol: 'br_r',   line: 'dashed' },
      oseo_oi:  { color: this.config.colors.oi, symbol: 'br_l',   line: 'dashed' },
      ldl_od:   { color: this.config.colors.od, symbol: 'tri',    line: 'none'   },
      ldl_oi:   { color: this.config.colors.oi, symbol: 'tri',    line: 'none'   }
    };

    const getVal = (type, f) => {
      switch (type) {
        case 'aereo_od': return data.umbrales_aereos?.oido_derecho?.[f];
        case 'aereo_oi': return data.umbrales_aereos?.oido_izquierdo?.[f];
        case 'oseo_od':  return data.umbrales_oseos?.oido_derecho?.[f];
        case 'oseo_oi':  return data.umbrales_oseos?.oido_izquierdo?.[f];
        case 'ldl_od':   return data.ldl_disconfort?.oido_derecho?.[f];
        case 'ldl_oi':   return data.ldl_disconfort?.oido_izquierdo?.[f];
        default: return null;
      }
    };

    Object.keys(styles).forEach(type => {
      const st = styles[type];
      const pts = [];
      freqs.forEach((f, i) => {
        const v = getVal(type, f);
        if (v !== '' && v !== null && v !== undefined) {
          const iv = parseInt(v, 10);
          const x = xScale(i);
          if (iv === 130) {
            const y = yScale(120);
            this.drawSymbol(x, y, 'arrow', st.color);
          } else {
            const y = yScale(iv);
            pts.push({ x, y });
            this.drawSymbol(x, y, st.symbol, st.color);
          }
        }
      });

      if (pts.length > 1 && st.line !== 'none') {
        const ctx = this.ctx;
        ctx.strokeStyle = st.color;
        ctx.lineWidth = 2;
        ctx.setLineDash(st.line === 'dashed' ? [4,4] : []);
        ctx.beginPath();
        ctx.moveTo(pts[0].x, pts[0].y);
        for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    });
  }

  drawSymbol(x, y, symbol, color) {
    const ctx = this.ctx;
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 2;

    switch (symbol) {
      case 'circle':
        ctx.beginPath(); ctx.arc(x, y, 3, 0, 2*Math.PI); ctx.stroke(); break;
      case 'x':
        ctx.beginPath();
        ctx.moveTo(x-3, y-3); ctx.lineTo(x+3, y+3);
        ctx.moveTo(x+3, y-3); ctx.lineTo(x-3, y+3);
        ctx.stroke(); break;
      case 'br_r':
        ctx.beginPath();
        ctx.moveTo(x-2,y-3); ctx.lineTo(x+2,y-3);
        ctx.lineTo(x+2,y+3); ctx.lineTo(x-2,y+3);
        ctx.stroke(); break;
      case 'br_l':
        ctx.beginPath();
        ctx.moveTo(x+2,y-3); ctx.lineTo(x-2,y-3);
        ctx.lineTo(x-2,y+3); ctx.lineTo(x+2,y+3);
        ctx.stroke(); break;
      case 'tri':
        ctx.beginPath();
        ctx.moveTo(x, y-4); ctx.lineTo(x-3, y+2); ctx.lineTo(x+3, y+2);
        ctx.closePath(); ctx.fill(); break;
      case 'arrow':
        // flecha hacia abajo cómoda
        ctx.beginPath();
        ctx.moveTo(x, y-6); ctx.lineTo(x, y+6); ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x-3, y+3); ctx.lineTo(x, y+6); ctx.lineTo(x+3, y+3);
        ctx.stroke(); break;
    }
  }
}

window.AudiogramChartView = AudiogramChartView;
