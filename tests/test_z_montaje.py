"""
El paciente en el impedanciómetro (impedanciometria/montaje.py): la oliva,
la sonda y el fono contralateral, puestos por el alumno en la cabeza.

- Sin la sonda en el oído, o con una oliva que no sella, el equipo no mide
  (SONDA ABIERTA / FUGA) y queda en el registro (z_sin_sello).
- La sonda define el oído medido: al meterla el equipo pasa a ese oído, y
  el botón del otro oído no cambia mientras la sonda no se dé vuelta.
- En CONTRA el estímulo llega solo con el fono en el oído opuesto.
- Meter la sonda o el fono en un oído NR es la falta grave al ponerlos.
- Dar vuelta todo: cada conducto lleva una sola cosa.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
os.chdir(RAIZ)  # context.get_resource() usa rutas relativas a la raíz

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from core.cabeza_electrodos import datos  # noqa: E402
from impedanciometria.montaje import (CONTRA, SONDA, MontajeZ, oliva_que_sella,  # noqa: E402
                                      OLIVAS_MM)
from impedanciometria.ventana import ImpedanciometriaWindow  # noqa: E402

BUENA = oliva_que_sella()


def _caso(z_od='A', z_oi='A', contra=90):
    return {
        'id': 7, 'Z_OD': z_od, 'Z_OI': z_oi,
        'volume': ['1.2', '1.1'], 'ETF': ['Normal', 'Normal'],
        'Reflex': {'ipsi': [[85, 85]] * 4, 'contra': [[contra, contra]] * 5,
                   'tipo': {'od': 'normal', 'oi': 'normal'}},
    }


def _ventana(caso=None):
    v = ImpedanciometriaWindow()
    v.logs = []
    v.z._log = lambda action, **payload: v.logs.append((action, payload))
    v.paciente.log = v.z._log
    v.la_super(caso or _caso())
    return v


def _acciones(v):
    return [a for a, _ in v.logs]


def _parar(z):
    for timer in (z.time_ch0, z.time_reflex, z.time_decay, z.time_etf):
        timer.stop()
    z.probe_tone.stop()
    z.reflex_tone.stop()


def _armar(v, sonda='OD'):
    v.paciente._elegir_oliva(BUENA)
    v.paciente.poner(SONDA, sonda)
    v.paciente.poner(CONTRA, 'OI' if sonda == 'OD' else 'OD')


def test_la_mediana_es_la_que_sella():
    assert BUENA == OLIVAS_MM[len(OLIVAS_MM) // 2] == 13


def test_cada_conducto_lleva_una_sola_cosa():
    m = MontajeZ()
    m.elegir_oliva(BUENA)
    m.poner(SONDA, 'OD')
    m.poner(CONTRA, 'OI')
    assert m.sella() and m.contra_en_el_otro()
    # Dar vuelta: la sonda al OI devuelve el fono a la mesa.
    assert m.poner(SONDA, 'OI') == CONTRA
    assert m.contra is None and not m.contra_en_el_otro()
    m.poner(CONTRA, 'OD')
    assert m.contra_en_el_otro()
    # Con la sonda metida no se cambia la oliva.
    assert not m.elegir_oliva(9)


def test_sin_sonda_el_equipo_no_mide():
    v = _ventana()
    v.z.stimulus_click()
    assert not v.z.time_ch0.isActive()
    assert v.z.avisos[v.z.Z].item.isVisible()
    assert ('z_sin_sello', 'sin_sonda') in [(a, p.get('que')) for a, p in v.logs]


def test_sonda_sin_oliva_no_entra():
    v = _ventana()
    v.paciente.poner(SONDA, 'OD')
    assert v.paciente.montaje.sonda is None
    assert 'z_sonda_sin_oliva' in _acciones(v)


def test_oliva_que_no_sella_da_fuga():
    v = _ventana()
    v.paciente._elegir_oliva(OLIVAS_MM[0])
    v.paciente.poner(SONDA, 'OD')
    v.z.stimulus_click()
    assert not v.z.time_ch0.isActive()
    assert ('z_sin_sello', 'oliva') in [(a, p.get('que')) for a, p in v.logs]
    # Se saca, se cambia la oliva y se vuelve a meter: ahora mide.
    v.paciente.sacar(SONDA)
    v.paciente._elegir_oliva(BUENA)
    v.paciente.poner(SONDA, 'OD')
    v.z.stimulus_click()
    assert v.z.time_ch0.isActive()
    _parar(v.z)


def test_la_sonda_define_el_oido_medido():
    v = _ventana()
    assert v.z.Z.get_side() == 'OD'
    _armar(v, sonda='OI')
    assert v.z.Z.get_side() == 'OI'
    # El botón del otro oído no cambia: la sonda está en OI.
    v.z._elegir_lado('OD')
    assert v.z.Z.get_side() == 'OI'
    assert 'z_lado_sin_sonda' in _acciones(v)
    # Dar vuelta todo: sonda a OD, fono a OI.
    v.paciente.poner(SONDA, 'OD')
    assert v.z.Z.get_side() == 'OD'
    assert v.paciente.montaje.contra is None
    v.paciente.poner(CONTRA, 'OI')
    assert v.paciente.montaje.contra_en_el_otro()


def _reflejo(v, modo):
    z = v.z
    z.show_screen(z.Z_reflex)
    z.set_reflex_mode(modo)
    z.dB = 110
    z.stimulus_click()
    assert z.time_reflex.isActive()
    while z.time_reflex.isActive():
        z.reflex_animate()
    probe_idx = 0 if z.Z.get_side() == 'OD' else 1
    return z.reflex_results[probe_idx][modo][z.reflex_freq_idx]


def test_contra_sin_fono_no_llega():
    v = _ventana()
    v.paciente._elegir_oliva(BUENA)
    v.paciente.poner(SONDA, 'OD')
    assert _reflejo(v, 'CONTRA') is None, "sin fono contralateral no hay estímulo"
    v.paciente.poner(CONTRA, 'OI')
    assert _reflejo(v, 'CONTRA') == 110
    assert _reflejo(v, 'IPSI') == 110
    _parar(v.z)


def test_sonda_en_oido_nr_es_falta_grave_al_ponerla():
    v = _ventana(_caso(z_od='NR'))
    v.paciente._elegir_oliva(BUENA)
    v.paciente.poner(SONDA, 'OI')            # sano: nada
    assert 'z_no_realizable' not in _acciones(v)
    v.paciente.poner(CONTRA, 'OD')           # el fono en el NR: falta
    faltas = [p for a, p in v.logs if a == 'z_no_realizable']
    assert len(faltas) == 1 and faltas[0]['que'] == 'auricular' and faltas[0]['screen'] == 'montaje'
    assert v.z.fuera_de_uso
    v.z.stimulus_click()
    assert not v.z.time_ch0.isActive()
    # Paciente nuevo: todo a la mesa y el equipo limpio.
    v.la_super(_caso())
    assert v.paciente.montaje.sonda is None and v.paciente.montaje.oliva is None
    assert not v.z.fuera_de_uso


def test_la_cabeza_pone_la_sonda_en_el_conducto():
    v = _ventana()
    v.paciente._elegir_oliva(BUENA)
    v.paciente.elegir_herramienta(SONDA)
    d = datos()
    v.paciente._en_la_piel(d["pos"][d["por_id"]["cae_izq"]], None)
    assert v.paciente.montaje.sonda == 'OI'
    v.paciente.elegir_herramienta(CONTRA)
    v.paciente._en_la_piel(d["pos"][d["por_id"]["Cz"]], None)   # el vértex no es un conducto
    assert v.paciente.montaje.contra is None
    # El fono de concha va sobre la oreja: basta el pabellón, no el conducto.
    v.paciente._en_la_piel(d["pos"][d["por_id"]["A2"]], None)
    assert v.paciente.montaje.contra == 'OD'
    v.paciente.cabeza.grab()   # se dibuja sin caerse, con la sonda puesta


def test_etf_arranca_en_membrana_integra_y_da_la_diferencia():
    from impedanciometria.ZETFscreen import PRUEBA_INTEGRA
    v = _ventana()
    _armar(v)
    z = v.z
    z.show_screen(z.Z_etf)
    assert z.Z_etf.prueba == PRUEBA_INTEGRA
    for maniobra in ('reposo', 'positiva', 'negativa'):
        z.etf_maniobra(maniobra)
    assert z.Z_etf.lbl_info[3].text().startswith("Dif. máx"), z.Z_etf.lbl_info[3].text()
    dif = int(z.Z_etf.lbl_info[3].text().split()[-2])
    assert 8 <= dif <= 18, dif   # ETF Normal (Lu y Wang 2026)


def test_etf_perforada_sin_presion_no_arranca():
    v = _ventana()
    _armar(v)
    z = v.z
    z.show_screen(z.Z_etf)
    z.btn1_click()                       # a membrana perforada
    z.etf_pressure = 0
    z.etf_perforada()
    assert not z.time_etf.isActive()
    assert z.avisos[z.Z_etf].item.isVisible()
    assert 'z_etf_sin_presion' in _acciones(v)
    z.etf_pressure = -200
    z.etf_perforada()
    assert z.time_etf.isActive()
    assert not z.avisos[z.Z_etf].item.isVisible()
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
    sys.stdout.flush()
    os._exit(1 if fallas else 0)
