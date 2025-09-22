// js/components/views/audiogram-charts.js
// Archivo principal que coordina todos los módulos

class AudiogramChartView {
  constructor(canvasId) {
    this.canvasId = canvasId;
    this.canvas = null;
    this.ctx = null;

    // Configuración básica
    this.symbolSize = 6;
    this.boneOffset = 14;
    this.ldlOffsetX = 8;
    this.ldlOffsetY = 8;

    this.interauralAttenuation = {
      125: 35, 250: 40, 500: 40, 1000: 40,
      2000: 45, 3000: 45, 4000: 50, 8000: 50
    };

    this.config = {
      margin: { top: 30, right: 40, bottom: 50, left: 60 },
      colors: {
        od: '#dc3545',
        oi: '#007bff',
        grid: '#ddd',
        gridStrong: '#333',
        text: '#333'
      }
    };

    // Estado interactivo
    this.activeTool = 'aereo_od';
    this.isFullscreen = false;
    this.symbolStates = {};
    this.symbolStatesDb = {};
    this.isInteractive = false;
    this.listenersAdded = false;
    this.lastData = null;
    this.lastOpts = null;
    this.onDataChange = null;

    // Cargar módulos
    this.loadModules();
  }

  async loadModules() {
    const modules = [
      'js/components/views/audiogram/chart-core.js',
      'js/components/views/audiogram/chart-drawing.js',
      'js/components/views/audiogram/chart-symbols.js',
      'js/components/views/audiogram/chart-interaction.js',
      'js/components/views/audiogram/chart-masking.js'
    ];

    for (const module of modules) {
      try {
        await this.loadScript(module);
      } catch (error) {
        console.warn(`No se pudo cargar ${module}:`, error.message);
      }
    }
  }

  loadScript(src) {
    return new Promise((resolve, reject) => {
      if (document.querySelector(`script[src="${src}"]`)) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  // Método básico para inicializar (será extendido por chart-core.js)
  init() {
    this.canvas = document.getElementById(this.canvasId);
    if (!this.canvas) return false;
    this.ctx = this.canvas.getContext('2d');
    return true;
  }

  // Método básico de render (será extendido por chart-core.js)
  render(data, opts = {}) {
    console.log('Método render será extendido por los módulos');
  }
}

// Exportar
window.AudiogramChartView = AudiogramChartView;
