
/**
 * ABRWaveform80View
 * Vista fina que reutiliza ABRWaveformCore para la traza de 80 dB.
 * Requiere que abr-waveform-core.js esté cargado previamente.
 */
class ABRWaveform80View {
  constructor(canvasId) {
    if (!window.ABRWaveformCore) {
      console.error('ABRWaveformCore no está cargado. Carga abr-waveform-core.js antes de este archivo.');
      return;
    }
    this.core = new window.ABRWaveformCore({
      canvasId,
      intensityKey: '80db',
      title: '80 dB nHL'
    });
  }

  render(data) {
    if (!this.core) return;
    this.core.render(data);
  }
}

window.ABRWaveform80View = ABRWaveform80View;
