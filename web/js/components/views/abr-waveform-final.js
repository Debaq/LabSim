/**
 * ABRWaveformFinalView
 * Vista fina para la traza "Final" reutilizando ABRWaveformCore (OD arriba / OI abajo).
 * Requiere que abr-waveform-core.js esté cargado previamente.
 */
class ABRWaveformFinalView {
  constructor(canvasId) {
    if (!window.ABRWaveformCore) {
      console.error('ABRWaveformCore no está cargado. Carga abr-waveform-core.js antes de este archivo.');
      return;
    }
    this.core = new window.ABRWaveformCore({
      canvasId,
      intensityKey: 'final',
      title: 'Final'
    });
  }
  render(data) {
    if (!this.core) return;
    this.core.render(data);
  }
}

window.ABRWaveformFinalView = ABRWaveformFinalView;
