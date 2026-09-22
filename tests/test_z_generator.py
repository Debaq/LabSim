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

from impedanciometria.z_generator import (edad_meses_del_caso, is_infant_ear,
                                          map_letter_for_probe, z1000_del_caso)
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
        #
        # La tolerancia es 0.15 y no 0.05: la gradiente se mide sobre la
        # curva YA dibujada, que lleva ruido encima (`np.random.normal` en
        # curve_z), asi que dos curvas del mismo paciente no dan el mismo
        # numero exacto. En las rigidas (As, Cs) el pico es chico y el ruido
        # es el mismo, asi que ahi la gradiente es la menos reproducible:
        # sobre 300 reconstrucciones el percentil 95 da 0.08 y el peor caso
        # 0.13. Con 0.05 el test fallaba una de cada quince corridas.
        rehecha = Z_225(manual=True, c=float(d[2]), p=int(float(d[3])),
                        vol=float(d[5]), pmax=float(d[6])).getDataSet()
        assert abs(float(rehecha[4]) - float(d[4])) <= 0.15, f"{letra}: {rehecha[4]} vs {d[4]}"


def test_el_mismo_paciente_lee_siempre_lo_mismo():
    """La semilla es (paciente, oído, sonda): el caso no cambia por click."""
    for letra in FORMAS_JERGER:
        primera, segunda = _curva(letra), _curva(letra)
        # El jitter por barrido mueve el valor, pero no lo resortea entero.
        #
        # La tolerancia tiene dos partes, y las dos hacen falta:
        #
        # - El jitter DOBLE: cada lectura sale multiplicada por un uniforme
        #   en [0.97, 1.03] (ver z_generator, `c * random.uniform(...)`), asi
        #   que dos lecturas seguidas pueden diferir hasta un 6%.
        # - El redondeo: la compliance se informa con dos decimales
        #   (`round(self.input[1], 2)`), o sea en pasos de 0.01, y dos
        #   redondeos pueden separarse 0.02. En las curvas rigidas (As, Cs:
        #   compliance ~0.1) eso pesa MAS que el jitter, y una tolerancia
        #   puramente relativa no lo cubre nunca.
        #
        # Con el 5% relativo que habia, el test fallaba una de cada cuatro
        # corridas: lo suficiente para que la suite dejara de servir para
        # detectar regresiones y para mandar a cualquiera a buscar un bug
        # que no existe.
        assert abs(float(primera[2]) - float(segunda[2])) <= \
            0.07 * max(float(primera[2]), 0.01) + 0.02
        assert abs(float(primera[3]) - float(segunda[3])) <= 4


def test_la_curva_sin_sello_no_inventa_numeros():
    """N = sonda sin sellar: no hay compliance ni presión que informar."""
    d = Z_225(letter='N').getDataSet()
    assert d[2] == d[3] == d[4] == 'N/D'


# ------------------------------------------- sonda y edad (lactante)

def test_la_sonda_de_226_miente_en_un_lactante():
    """El hallazgo: a 226 Hz el lactante dibuja pico aunque este lleno.

    Bajo los 6 meses la pared del conducto todavia es cartilaginosa y su
    movimiento DOMINA la admitancia: el equipo muestra el pico de la pared,
    no el del oido medio. Por eso el estandar a esa edad es sonda de 1000
    Hz, y por eso el simulador tiene que DEJAR cometer el error -- si a 226
    Hz saliera plana, el alumno nunca se entera de que eligio mal la sonda.
    """
    bebe = {'edad': 0, 'edad_horas': 6}
    adulto = {'edad': 30}
    # Oido medio lleno (B): a 226 Hz el bebe lo muestra como normal.
    assert map_letter_for_probe('B', '226', seed_key=1,
                                edad_meses=edad_meses_del_caso(bebe)) == 'A'
    # El mismo oido, con la sonda que corresponde, se lee como lo que es.
    assert map_letter_for_probe('B', '1000', seed_key=1,
                                edad_meses=edad_meses_del_caso(bebe)) == 'B'
    # Y en un adulto la de 226 no miente.
    assert map_letter_for_probe('B', '226', seed_key=1,
                                edad_meses=edad_meses_del_caso(adulto)) == 'B'


def test_la_sonda_de_226_vuelve_a_servir_pasados_los_seis_meses():
    """El conducto se osifica: a los 8 meses la de 226 ya no tapa nada."""
    bebe_grande = {'edad': 0, 'edad_horas': 5760}       # 8 meses
    assert not is_infant_ear(edad_meses_del_caso(bebe_grande))
    assert map_letter_for_probe('B', '226', seed_key=1,
                                edad_meses=edad_meses_del_caso(bebe_grande)) == 'B'


def test_lo_que_la_pared_blanda_tapa_es_la_ausencia_de_pico():
    """Una rigida sigue leyendose rigida.

    La pared del conducto agrega movimiento, asi que puede inventar un pico
    donde no hay; no puede hacer que una compliance baja se vea alta sin
    pico. As y Cs se siguen informando como tales.
    """
    bebe = 0.2
    for letra in ('As', 'Cs', 'C', 'A', 'Ad'):
        assert map_letter_for_probe(letra, '226', seed_key=1, edad_meses=bebe) == letra


def test_sin_edad_no_se_inventa_un_lactante():
    """Un caso sin edad cargada se comporta como siempre."""
    assert not is_infant_ear(None)
    assert edad_meses_del_caso({}) is None
    assert map_letter_for_probe('B', '226', seed_key=1, edad_meses=None) == 'B'


def test_el_docente_puede_fijar_la_sonda_de_1000():
    """El caso que NECESITA un resultado concreto no puede quedar en el sorteo.

    Un lactante con el oído medio ocupado que a 226 Hz se ve normal y solo
    la sonda de 1000 Hz delata es un caso que se arma a propósito. 'auto'
    --el default, y lo que traen los casos viejos-- sigue derivándolo de la
    letra de Jerger.
    """
    # Forzado: manda lo declarado, sea cual sea la letra.
    for letra in ('A', 'As', 'Ad', 'C', 'Cs', 'B', 'N'):
        assert map_letter_for_probe(letra, '1000', seed_key=('x', letra),
                                    forzado='positivo') == 'A'
        assert map_letter_for_probe(letra, '1000', seed_key=('x', letra),
                                    forzado='negativo') == 'B'

    # Auto: la letra manda, como siempre. Una A casi siempre da positivo y
    # una B casi siempre negativo, sobre muchas semillas.
    positivos_a = sum(map_letter_for_probe('A', '1000', seed_key=('a', i)) == 'A'
                      for i in range(200))
    positivos_b = sum(map_letter_for_probe('B', '1000', seed_key=('b', i)) == 'A'
                      for i in range(200))
    assert positivos_a > 170, positivos_a
    assert positivos_b < 30, positivos_b

    # Y la sonda de 226 Hz no se entera de este campo: su hallazgo es otro.
    assert map_letter_for_probe('B', '226', edad_meses=2, forzado='negativo') == 'A'


def test_el_campo_del_caso_se_lee_con_su_default():
    """Caso viejo o campo sin cargar: 'auto', que es como se comportaba."""
    assert z1000_del_caso(None, 'OD') == 'auto'
    assert z1000_del_caso({}, 'OD') == 'auto'
    assert z1000_del_caso({'Z1000_OD': 'positivo'}, 'OD') == 'positivo'
    assert z1000_del_caso({'Z1000_OD': 'negativo'}, 'OD') == 'negativo'
    assert z1000_del_caso({'Z1000_OD': 'cualquiera'}, 'OD') == 'auto'
    # Cada oído el suyo.
    data = {'Z1000_OD': 'positivo', 'Z1000_OI': 'negativo'}
    assert z1000_del_caso(data, 'OD') == 'positivo'
    assert z1000_del_caso(data, 'OI') == 'negativo'


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")