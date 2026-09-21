"""El informe de la TEOAE: lo que queda guardado al terminar de medir.

Reventaba con `KeyError: 0` justo al cerrar la captura --o sea después de
esperar la medición entera, con el paciente en atención-- porque
`snr_per_band` y `pass_per_band` vienen indexados POR FRECUENCIA
({1000: 8.2, 2000: ...}), como los arma el generador recorriendo
`normative['bands_hz']`, y el informe los leía por posición.

El dibujo de las barras sí los trataba como diccionario, así que la
pantalla se veía bien y el error aparecía solo al guardar: por eso no
saltó antes.
"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from oae.widgets.teoae_panel import TeoaePanel
    HAS_UI = True
except Exception as exc:  # pragma: no cover - sin PySide6/pyqtgraph
    print(f"  (salteado: {exc})")
    HAS_UI = False

CASO = {'type': 'normal', 'umbral': 10, 'desviaciones': {}, 'sello_pct': 90}


def _panel_con_medicion(caso=None, ear='OD'):
    panel = TeoaePanel()
    resultado = panel.generator.generate(80.0, 260, ear, caso or CASO, n_frames=4)
    panel._anim_ear = ear
    panel._last_result = resultado
    panel._last_level = 80.0
    panel._last_n = 260
    return panel, resultado['frames'][-1]


def test_the_report_survives_the_end_of_the_capture():
    if not HAS_UI:
        return
    panel, frame = _panel_con_medicion()
    # La forma que devuelve el generador: por frecuencia, no por posición.
    assert isinstance(frame['snr_per_band'], dict)
    panel._store_report(frame)
    informe = panel._report['OD']
    assert len(informe['bandas']) == len(frame['snr_per_band'])
    for banda in informe['bandas']:
        assert banda['snr_db'] is not None, banda
        assert banda['pass'] in (True, False), banda


def test_each_band_keeps_its_own_number():
    """Y no el de otra banda: indexar por posición podía correrlos."""
    if not HAS_UI:
        return
    panel, frame = _panel_con_medicion()
    panel._store_report(frame)
    for banda in panel._report['OD']['bandas']:
        esperado = frame['snr_per_band'][int(banda['hz'])]
        assert abs(banda['snr_db'] - round(float(esperado), 1)) < 0.05, banda
        assert banda['pass'] == bool(frame['pass_per_band'][int(banda['hz'])])


def test_a_referred_ear_is_reported_as_referred():
    """Un oído sin emisiones tiene que quedar guardado como tal."""
    if not HAS_UI:
        return
    sordo = dict(CASO, type='coclear', umbral=70,
                 desviaciones={str(hz): 40 for hz in (500, 1000, 2000, 4000)})
    panel, frame = _panel_con_medicion(sordo)
    panel._store_report(frame)
    informe = panel._report['OD']
    assert informe['n_pass'] < informe['n_bandas'], informe
    assert informe['overall_pass'] is False


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
