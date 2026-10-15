"""
Impedanciometría no realizable (Z = NR, CaseBuilder::Z_NO_REALIZABLE).

En un oído NR la sonda no va (atresia, otitis externa o herpes zóster ótico
con secreción, cuerpo extraño): el equipo no barre el timpanograma ni busca
reflejos con la sonda ahí, y en CONTRA tampoco estimula por ese oído. El
intento queda en el log (z_no_realizable) y la pantalla lo avisa. El otro
oído se mide normal.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# core.base arma la QApplication al importarse (ver ApplicationContext).
from impedanciometria.Z import ZControl  # noqa: E402
from impedanciometria.z_generator import oido_no_realizable  # noqa: E402


def _caso(z_od='NR', z_oi='A'):
    return {
        'id': 7, 'Z_OD': z_od, 'Z_OI': z_oi,
        'volume': ['1.2', '1.1'], 'ETF': ['Normal', 'Normal'],
        # filas por frecuencia, columnas por oído de la sonda
        'Reflex': {'ipsi': [[85, 85]] * 4, 'contra': [[90, 90]] * 5,
                   'tipo': {'od': 'normal', 'oi': 'normal'}},
    }


def _z(caso):
    z = ZControl()
    z.logs = []
    z._log = lambda action, **payload: z.logs.append(action)
    z.la_super(caso)
    return z


def _parar(z):
    for timer in (z.time_ch0, z.time_reflex, z.time_decay, z.time_etf):
        timer.stop()
    z.probe_tone.stop()
    z.reflex_tone.stop()


def test_oido_no_realizable():
    assert oido_no_realizable(_caso(), 0)
    assert not oido_no_realizable(_caso(), 1)
    assert not oido_no_realizable(None, 0)


def test_timpanograma_no_se_barre_en_el_oido_nr():
    z = _z(_caso())
    assert z.Z.get_side() == 'OD'
    assert z.store_data[0].is_null(0), "no se genera curva para un oído sin sonda"
    z.stimulus_click()
    assert not z.time_ch0.isActive()
    assert z.avisos[z.Z].item.isVisible()
    assert 'z_no_realizable' in z.logs
    # El otro oído se mide normal y el aviso se va.
    z.side_change()
    assert not z.avisos[z.Z].item.isVisible()
    z.stimulus_click()
    assert z.time_ch0.isActive()
    _parar(z)


def test_reflejo_contra_no_estimula_por_el_oido_nr():
    z = _z(_caso())
    z.side_change()                      # sonda en OI (sano)
    z.show_screen(z.Z_reflex)
    z.dB = 100
    z.set_reflex_mode('CONTRA')          # el tono entraría por OD (NR)
    z.stimulus_click()
    assert not z.time_reflex.isActive()
    assert z.avisos[z.Z_reflex].item.isVisible()
    z.set_reflex_mode('IPSI')            # sonda y tono en OI: se hace
    assert not z.avisos[z.Z_reflex].item.isVisible()
    z.stimulus_click()
    assert z.time_reflex.isActive()
    _parar(z)


def test_decay_y_etf_bloqueados_con_la_sonda_en_el_oido_nr():
    z = _z(_caso())
    z.show_screen(z.Z_decay)
    z.dB = 100
    z.stimulus_click()
    assert not z.time_decay.isActive()
    z.show_screen(z.Z_etf)
    z.stimulus_click()
    assert not z.time_etf.isActive()
    assert z.avisos[z.Z_etf].item.isVisible()
    _parar(z)



if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {nombre}")
            except AssertionError as exc:
                fallas += 1
                print(f"FAIL {nombre}: {exc!r}")
    sys.exit(1 if fallas else 0)
