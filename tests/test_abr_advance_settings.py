"""
Tests del diálogo de Parámetros Avanzados (src/abr/AbrAdvanceSettings.py).

El diálogo viejo (UI/AbrAdvanceSettings_ui.py) dibujaba estos campos y no
los leía nadie. Lo que se verifica acá es justamente el contrato que
faltaba: que get_data() devuelva un technical_config con las claves que
ABR_generator.generate_curve consume, y que el ida y vuelta con set_data()
no pierda nada.

Necesita PySide6 (está en requirements.txt). Sin entorno gráfico se corre
igual con QT_QPA_PLATFORM=offscreen, que es lo que se fija acá abajo.
"""

import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

try:
    # core.base crea el QApplication al importarse; por eso este import va
    # antes de tocar cualquier widget.
    from abr.AbrAdvanceSettings import (ARTIFACT_REJECT, AbrAdvanceSettings,
                                        MONTAGES, TRANSDUCERS,
                                        default_settings)
    from abr.ABR_generator import DISCONNECTED, UNCONNECTED_SETTINGS
    HAS_QT = True
except ImportError as exc:          # sin PySide6 instalado
    print(f"  (tests de UI salteados: {exc})")
    HAS_QT = False


# Las que el generador YA usa.
CLAVES = {'transducer', 'montage', 'window_ms', 'electrodes', 'impedance',
          'artifact_reject_uv', 'residual_noise_nv', 'fsp_criterion'}

# Y las que el diálogo muestra pero el modelo todavía no lee. Están porque
# el equipo real las tiene y el alumno las busca --el 2-1-2 del tone burst
# es el ejemplo que se repite--; viajan en el technical_config con la clave
# con la que se van a leer, así que conectar una es leerla en el generador
# y sacarla de esta lista.
PENDIENTES = set(UNCONNECTED_SETTINGS)


def test_get_data_returns_a_technical_config():
    """Las claves son exactamente las que consume el generador."""
    if not HAS_QT:
        return
    data = AbrAdvanceSettings(test='ABR').get_data()
    assert set(data) == CLAVES | PENDIENTES
    assert set(data['electrodes']) == {'vertex', 'right', 'left', 'ground'}
    assert set(data['impedance']) == set(data['electrodes'])
    # Y coincide con el default del protocolo, que es lo que usa ABR_Curve
    # mientras nadie abra el diálogo.
    assert data == default_settings('ABR')


def test_window_range_comes_from_the_protocol():
    """Cada potencial trae su ventana: no se edita un P300 en 12 ms."""
    if not HAS_QT:
        return
    abr = AbrAdvanceSettings(test='ABR')
    assert abr.sb_window.value() == 12
    p300 = AbrAdvanceSettings(test='P300')
    assert p300.sb_window.value() == 800
    assert p300.sb_window.minimum() < 800 < p300.sb_window.maximum()
    ecochg = AbrAdvanceSettings(test='ECochG')
    assert ecochg.sb_window.value() == 5
    assert ecochg.get_data()['montage'] == 'tympanic'


def test_round_trip_keeps_every_field():
    if not HAS_QT:
        return
    custom = dict(
        default_settings('ABR'),
        transducer='TDH39_headphone', montage='forehead_mastoid',
        window_ms=15.0, artifact_reject_uv=10.0, residual_noise_nv=100.0,
        fsp_criterion=4.0,
        electrodes={'vertex': 'Cz', 'right': 'A2', 'left': DISCONNECTED,
                    'ground': DISCONNECTED},
        impedance={'vertex': 7.5, 'right': 2.0, 'left': 3.5, 'ground': 2.0},
    )
    dialog = AbrAdvanceSettings(custom, test='ABR')
    assert dialog.get_data() == custom
    # set_data sobre un diálogo ya construido hace lo mismo.
    otro = AbrAdvanceSettings(test='ABR')
    otro.set_data(custom)
    assert otro.get_data() == custom


def test_disabled_rejection_and_fsp_come_back_as_falsy():
    """'Desactivado' tiene que llegar al generador como 0/None, no como texto."""
    if not HAS_QT:
        return
    dialog = AbrAdvanceSettings(test='ABR')
    dialog.set_data({'artifact_reject_uv': 0.0, 'fsp_criterion': 0.0})
    data = dialog.get_data()
    assert data['artifact_reject_uv'] == 0.0
    assert data['fsp_criterion'] is None


def test_restore_defaults_goes_back_to_the_protocol():
    if not HAS_QT:
        return
    dialog = AbrAdvanceSettings(test='ABR')
    dialog.set_data({'transducer': 'bone_vibrator', 'window_ms': 20.0,
                     'impedance': {'vertex': 9.0}})
    dialog.restore_defaults()
    assert dialog.get_data() == default_settings('ABR')


def test_the_dialog_gives_no_hints():
    """El diálogo no le avisa nada al alumno: eso lo lee en el trazo.

    Ni mensajes de impedancia fuera de norma, ni valores en rojo, ni notas
    de qué estímulo conviene. Configurar mal los electrodos tiene que
    manifestarse como ruido o zumbido en la curva y que el alumno lo
    diagnostique, no como un cartel que le diga qué hizo mal.
    """
    if not HAS_QT:
        return
    from PySide6.QtWidgets import QLabel

    dialog = AbrAdvanceSettings(test='ABR')
    dialog.set_data({'impedance': {'vertex': 9.0, 'right': 2.0, 'left': 2.0,
                                   'ground': 2.0}})

    # Ningún spinbox se pinta según su valor.
    for _, spin in dialog.electrode_widgets.values():
        assert not spin.styleSheet(), spin.value()

    # Ningún texto del diálogo menciona límites, consecuencias ni consejos,
    # y ningún rótulo delata cuál es el valor "bueno" (nada de "estándar",
    # "habitual" ni "recomendado" al lado de una opción).
    prohibido = ('kΩ)', 'límite', 'ruidoso', 'red eléctrica', '⚠',
                 'conviene', 'umbrales por frecuencia',
                 'estándar', 'habitual', 'recomend', 'normal)')
    textos = [w.text() for w in dialog.findChildren(QLabel)]
    for combo in (dialog.cb_transducer, dialog.cb_montage, dialog.cb_reject,
                  dialog.cb_noise, dialog.cb_fsp):
        textos += [combo.itemText(i) for i in range(combo.count())]
    for combo, _ in dialog.electrode_widgets.values():
        textos += [combo.itemText(i) for i in range(combo.count())]

    for texto in textos:
        for palabra in prohibido:
            assert palabra.lower() not in texto.lower(), (texto, palabra)


def test_labels_map_to_the_keys_the_generator_uses():
    """Los rótulos en español mapean a las claves del JSON normativo."""
    if not HAS_QT:
        return
    assert set(TRANSDUCERS.values()) == {'insert_earphone', 'TDH39_headphone',
                                         'bone_vibrator'}
    assert 'vertex_mastoid' in MONTAGES.values()
    assert 0.0 in ARTIFACT_REJECT.values()      # "Desactivado"


def test_the_pending_parameters_are_there_and_marked():
    """Los parámetros que el equipo real tiene y el modelo todavía no usa.

    Faltaban y los alumnos los buscaban. Se dibujan, se guardan y viajan en
    el technical_config, pero el generador no los lee: el test fija las dos
    mitades del trato -- que estén, y que el diálogo no finja que hacen
    algo. Cuando uno se conecte, sale de UNCONNECTED_SETTINGS y este test
    deja de pedirlo.
    """
    if not HAS_QT:
        return
    d = AbrAdvanceSettings(test='ABR')
    data = d.get_data()
    for clave in UNCONNECTED_SETTINGS:
        assert clave in data, clave

    # El 2-1-2 es el que se pide por nombre: tiene que poder elegirse.
    assert d.cb_burst_env.findData('2-1-2') >= 0
    assert data['burst_envelope'] == '2-1-2'
    # Y el resto de las envolventes de rutina, que es de lo que se compara.
    for envolvente in ('2-0-2', '1-0-1', '5-0-5'):
        assert d.cb_burst_env.findData(envolvente) >= 0, envolvente

    # Y NO se distinguen en pantalla de los que sí funcionan: es un equipo
    # simulado, y un equipo no le avisa al operador cuáles de sus perillas
    # están implementadas. Marcarlos rompería la simulación.
    for widget in (d.cb_burst_env, d.cb_notch, d.cb_gain, d.cb_smoothing,
                   d.cb_transducer, d.cb_reject, d.cb_fsp):
        assert widget.toolTip() == '', widget.toolTip()
        assert widget.isEnabled()


def test_the_pending_parameters_survive_a_round_trip():
    """Se guardan aunque no hagan nada: si no, al reabrir el diálogo el
    alumno perdería lo que configuró y parecería un bug del equipo."""
    if not HAS_QT:
        return
    custom = dict(
        default_settings('ABR'),
        burst_envelope='5-0-5', burst_window='hanning', click_us=200.0,
        level_unit='peSPL', rate_jitter_pct=10.0, presentation='binaural',
        masking_noise='narrow', masking_offset_db=-10.0, channels=2,
        gain=50000.0, notch_hz=50.0, filter_slope=24.0,
        sample_rate_hz=48000.0, weighted_averaging=True, auto_stop='fsp',
        fsp_window_ms=8.0, smoothing=5.0,
    )
    assert AbrAdvanceSettings(custom, test='ABR').get_data() == custom


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")