// js/components/views/audiogram/chart-core.js
// Funciones centrales: init, render, enableInteractiveMode

// Extender la clase AudiogramChartView con funciones centrales
Object.assign(AudiogramChartView.prototype, {
  
  init() {
    this.canvas = document.getElementById(this.canvasId);
    if (!this.canvas) return false;
    this.ctx = this.canvas.getContext('2d');

    // Agregar event listeners una sola vez
    if (!this.listenersAdded) {
      this.canvas.addEventListener('click', this.handleCanvasClick.bind(this));
      document.addEventListener('fullscreenchange', this.handleFullscreenChange.bind(this));
      this.listenersAdded = true;
    }

    return true;
  },

  render(data, opts = {}) {
    if (!this.init()) return;
    
    const ctx = this.ctx, cv = this.canvas;

    // Limpiar canvas
    ctx.clearRect(0, 0, cv.width, cv.height);

    // Layout
    const m = this.config.margin;
    const plotW = cv.width - m.left - m.right;
    const plotH = cv.height - m.top - m.bottom;

    // Frecuencias a mostrar
    const freqs = opts.freqs ?? (opts.showHighFreq
      ? ['125','250','500','1000','2000','4000','8000','9000','10000','11200','12500','14000','16000','18000','20000']
      : ['125','250','500','1000','2000','4000','8000']);

    // Escalas
    const xScale = (i) => m.left + (i / (freqs.length - 1)) * plotW;
    const yScale = (db) => m.top + ((db + 10) / 130) * plotH;

    // Dibujar componentes
    this.drawGrid(freqs, xScale, yScale, plotW, plotH);
    this.drawLDLLabel(data, xScale, yScale);
    this.drawData(data, freqs, xScale, yScale);
    
    // Guardar datos para interacción
    this.lastData = data;
    this.lastOpts = opts;
    
    // Panel de herramientas
    this.drawToolPanel();
  },

  enableInteractiveMode(callback) {
    this.isInteractive = true;
    this.onDataChange = callback;
  },

  getThreshold(data, type, freq) {
    switch (type) {
      case 'aereo_od': return data.umbrales_aereos?.oido_derecho?.[freq];
      case 'aereo_oi': return data.umbrales_aereos?.oido_izquierdo?.[freq];
      case 'oseo_od':  return data.umbrales_oseos?.oido_derecho?.[freq];
      case 'oseo_oi':  return data.umbrales_oseos?.oido_izquierdo?.[freq];
      case 'ldl_od':   return data.ldl_disconfort?.oido_derecho?.[freq];
      case 'ldl_oi':   return data.ldl_disconfort?.oido_izquierdo?.[freq];
      default: return null;
    }
  },

  getSymbolDbFromState(stateKey) {
    return this.symbolStatesDb?.[stateKey] || null;
  },

  updateAudiogramData(freq, toolType, db, state) {
    if (this.onDataChange) {
      this.onDataChange(freq, toolType, db, state);
    }
  }

});