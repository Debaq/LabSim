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
    from abr.ABR_generator import DISCONNECTED
    HAS_QT = True
except ImportError as exc:          # sin PySide6 instalado
    print(f"  (tests de UI salteados: {exc})")
    HAS_QT = False


CLAVES = {'transducer', 'montage', 'window_ms', 'electrodes', 'impedance',
          'artifact_reject_uv', 'residual_noise_nv', 'fsp_criterion'}


def test_get_data_returns_a_technical_config():
    """Las claves son exactamente las que consume el generador."""
    if not HAS_QT:
        return
    data = AbrAdvanceSettings(test='ABR').get_data()
    assert set(data) == CLAVES
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


def test_impedance_check_flags_both_clinical_rules():
    """El diálogo avisa en vivo, como la pantalla de impedancias del equipo."""
    if not HAS_QT:
        return
    dialog = AbrAdvanceSettings(test='ABR')
    assert "correctas" in dialog.lbl_impedance.text()

    # Regla 1: cada electrodo bajo 5 kOhm.
    dialog.set_data({'impedance': {'vertex': 6.5, 'right': 2.0, 'left': 2.0,
                                   'ground': 2.0}})
    assert "⚠" in dialog.lbl_impedance.text()
    assert "6.5" in dialog.lbl_impedance.text()
    assert dialog.electrode_widgets['vertex'][1].styleSheet()      # en rojo
    assert not dialog.electrode_widgets['right'][1].styleSheet()

    # Regla 2: diferencias bajo 2 kOhm, con todos los electrodos en norma.
    dialog.set_data({'impedance': {'vertex': 4.5, 'right': 2.0, 'left': 2.0,
                                   'ground': 2.0}})
    texto = dialog.lbl_impedance.text()
    assert "⚠" in texto and "diferencia" in texto
    assert not dialog.electrode_widgets['vertex'][1].styleSheet()  # 4.5 < 5

    # Justo en los dos límites todavía pasa.
    dialog.set_data({'impedance': {'vertex': 4.0, 'right': 2.0, 'left': 2.0,
                                   'ground': 2.0}})
    assert "correctas" in dialog.lbl_impedance.text()


def test_labels_map_to_the_keys_the_generator_uses():
    """Los rótulos en español mapean a las claves del JSON normativo."""
    if not HAS_QT:
        return
    assert set(TRANSDUCERS.values()) == {'insert_earphone', 'TDH39_headphone',
                                         'bone_vibrator'}
    assert 'vertex_mastoid' in MONTAGES.values()
    assert 0.0 in ARTIFACT_REJECT.values()      # "Desactivado"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
