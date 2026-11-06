"""El diapasón golpeado suena y se apaga igual que la barra (2026-11-06).

La barra de vibración baja lineal en dB (diapasones.vibracion): el sonido se
apaga con la misma caída por segundo y termina cuando la barra llega a 0.
"""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("LABSIM_DATA_DIR", tempfile.mkdtemp(prefix="labsim-test-"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np  # noqa: E402

from core.base import context  # noqa: E402,F401  (crea la QApplication)
import audiometria.Acumetria as A  # noqa: E402
from audiometria import audio_synth  # noqa: E402
from audiometria import diapasones as dp  # noqa: E402

CASO = {"id": 79, "edad": 24,
        "Aerea": [[20, 15]] * 9, "Osea": [[20, 15]] * 9,
        "Rinne": {"500": {"od": "positivo", "oi": "positivo"},
                  "1000": {"od": "positivo", "oi": "positivo"}},
        "Weber": {"500": "centrado", "1000": "centrado"}}


class _Cola:
    def push(self, accion, payload):
        pass


def _db(senal, desde_s, ventana_s=0.2):
    i = int(desde_s * audio_synth.SAMPLE_RATE)
    trozo = senal[i:i + int(ventana_s * audio_synth.SAMPLE_RATE)]
    return 20 * np.log10(np.sqrt(np.mean(trozo ** 2)))


def test_se_apaga_con_la_caida_de_la_barra():
    s = audio_synth.diapason(1024, dp.duracion_vibracion(), dp.CAIDA_DB_S)
    assert np.max(np.abs(s)) <= audio_synth.PEAK_REF + 1e-9
    # pasado el golpe, cada 10 s baja 10 * CAIDA_DB_S dB
    for t in (1.0, 11.0, 21.0, 31.0):
        assert abs((_db(s, t) - _db(s, t + 10.0)) - 10 * dp.CAIDA_DB_S) < 0.3, t
    # el golpe suena más fuerte que la fundamental sola
    assert _db(s, 0.0, 0.05) > _db(s, 1.0, 0.05)


def test_dura_lo_que_vibra():
    s = audio_synth.diapason(512, dp.duracion_vibracion(), dp.CAIDA_DB_S)
    segundos = len(s) / audio_synth.SAMPLE_RATE
    assert abs(segundos - dp.duracion_vibracion()) < 0.01
    assert dp.vibracion(dp.duracion_vibracion()) == 0.0
    assert dp.vibracion(dp.duracion_vibracion() - 1.0) > 0.0


def test_el_archivo_se_genera_una_vez(tmp_path=None):
    carpeta = tmp_path or tempfile.mkdtemp(prefix="labsim-diapason-")
    ruta = audio_synth.diapason_file(512, 3.0, dp.CAIDA_DB_S, str(carpeta))
    assert ruta and os.path.exists(ruta)
    antes = os.path.getmtime(ruta)
    assert audio_synth.diapason_file(512, 3.0, dp.CAIDA_DB_S, str(carpeta)) == ruta
    assert os.path.getmtime(ruta) == antes


def test_golpear_suena_el_diapason_elegido():
    w = A.Acumetria(None)
    w.log_queue = _Cola()
    w.la_super(dict(CASO), 102)
    assert w._sonido.source().isEmpty()
    w.botones_hz["1000"].click()
    w._golpear()
    assert "Diapason_1024_" in w._sonido.source().toLocalFile()
    w.botones_hz["500"].click()          # tomar el otro: el que sonaba se calla
    assert w._sonido.playbackState() == w._sonido.PlaybackState.StoppedState
    w._golpear()
    assert "Diapason_512_" in w._sonido.source().toLocalFile()
    w.la_super(None)                     # cambio de paciente: silencio
    assert w._sonido.playbackState() == w._sonido.PlaybackState.StoppedState


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
