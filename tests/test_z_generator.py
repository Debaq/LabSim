"""
Tests del generador del impedanciómetro (src/impedanciometria/z_generator.py).

Lo que se cuida acá es lo que el alumno LEE en la pantalla del equipo:

- la compliance y la presión del pico tienen que separar las letras de
  Jerger (una Cs sorteada con compliance normal es una C con otro nombre);
- la gradiente tiene que distinguir una curva en punta de una redondeada.
  Con el ancho fijo de 200 daPa que había antes daba 0,85 en cualquier
  curva con pico: un número que no informaba nada.

La ficha del caso anticipa estos mismos números desde PHP
(CaseCharts::valoresTimpanograma); que las dos copias no se separen lo
comprueba labsim_backend/tests/test_charts_vs_js.php.
"""

import os
import sys

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from impedanciometria.z_generator import (ANCHOS_JERGER, FORMAS_JERGER,
                                          Z_225)

SEED = ('paciente-1', 'OD', '226')


def _curva(letra, seed=SEED):
    return Z_225(letter=letra, seed_key=seed).getDataSet()


def test_compliance_y_presion_caen_en_el_rango_de_la_letra():
    """El sorteo no se sale del rango que la ficha informa."""
    for letra, (c_min, c_max, p_min, p_max) in FORMAS_JERGER.items():
        d = _curva(letra)
        c, p = float(d[2]), float(d[3])
        # El jitter por barrido mueve la compliance un 3% y el pico 2 daPa.
        assert c_min * 0.97 - 0.01 <= c <= c_max * 1.03 + 0.01, f"{letra}: compliance {c}"
        assert p_min - 2 <= p <= p_max + 2, f"{letra}: presión {p}"


def test_las_rigidas_no_se_confunden_con_las_normales():
    """As y Cs son de compliance baja: no pueden solaparse con A y C."""
    for rigida, normal in (('As', 'A'), ('Cs', 'C')):
        assert FORMAS_JERGER[rigida][1] <= 0.3
        assert FORMAS_JERGER[rigida][1] <= FORMAS_JERGER[normal][0]


def test_el_pico_de_las_c_queda_dentro_de_la_ventana():
    """En -400 daPa el pico cae sobre el borde del barrido y no se lee."""
    for letra in ('C', 'Cs'):
        c_min, c_max, p_min, p_max = FORMAS_JERGER[letra]
        assert p_max < -100
        assert p_min > -400


def test_la_gradiente_distingue_las_curvas():
    """Ad en punta, Cs redondeada. Acá 1 es ancha y 0 es en punta."""
    g = {letra: float(_curva(letra)[4]) for letra in ('A', 'Ad', 'C', 'Cs')}
    assert g['Ad'] < g['A'] < g['C'] < g['Cs']
    assert len(set(g.values())) == len(g), f"la gradiente no separa las letras: {g}"


def test_el_ancho_es_el_de_un_adulto():
    """TW normal 50-110 daPa; el ancho fijo de 200 no entraba en ese rango."""
    for letra in ('A', 'As', 'Ad'):
        assert 50 <= ANCHOS_JERGER[letra] <= 110


def test_el_ancho_viaja_en_el_dataset():
    """Al recargar la curva guardada ya no hay letra de donde sacarlo."""
    for letra, ancho in ANCHOS_JERGER.items():
        d = _curva(letra)
        assert float(d[6]) == float(ancho), f"{letra}: {d[6]}"
        # Y reconstruirla a mano con ese ancho da la misma gradiente.
        rehecha = Z_225(manual=True, c=float(d[2]), p=int(float(d[3])),
                        vol=float(d[5]), pmax=float(d[6])).getDataSet()
        assert abs(float(rehecha[4]) - float(d[4])) <= 0.05, f"{letra}: {rehecha[4]} vs {d[4]}"


def test_el_mismo_paciente_lee_siempre_lo_mismo():
    """La semilla es (paciente, oído, sonda): el caso no cambia por click."""
    for letra in FORMAS_JERGER:
        primera, segunda = _curva(letra), _curva(letra)
        # El jitter por barrido mueve el valor, pero no lo resortea entero.
        assert abs(float(primera[2]) - float(segunda[2])) <= 0.05 * max(float(primera[2]), 0.01)
        assert abs(float(primera[3]) - float(segunda[3])) <= 4


def test_la_curva_sin_sello_no_inventa_numeros():
    """N = sonda sin sellar: no hay compliance ni presión que informar."""
    d = Z_225(letter='N').getDataSet()
    assert d[2] == d[3] == d[4] == 'N/D'


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
