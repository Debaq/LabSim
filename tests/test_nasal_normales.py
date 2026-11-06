"""El caso sin bloque nasal o de sueño es normal (nasal/normales.py).

1. Sin NASAL, OLFATO, PRICK, ESPIRO o SUENO, o con el bloque mal escrito,
   cada `desde_caso` da el paciente normal (el error es de la base de
   datos, el equipo no lo avisa); sin caso (None) no hay paciente.
2. Lo normal es normal según los criterios del mismo equipo: olfato sobre
   el percentil 10 de la edad, histamina positiva y ningún alérgeno,
   espirometría sobre el LIN, IAH bajo 5, la nariz de RinoSim normal.
"""

import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.base import context  # noqa: E402,F401  (crea la QApplication)
from nasal import espirometria as E  # noqa: E402
from nasal import modelo  # noqa: E402
from nasal import olfatometria as O  # noqa: E402
from nasal import prick as P  # noqa: E402
from nasal import sesion  # noqa: E402
from nasal import sueno as Z  # noqa: E402

CASOS = [{'id': 7, 'edad': e, 'gender': g} for e in (8, 15, 30, 55, 80) for g in (0, 1)]


# --- 1 -----------------------------------------------------------------------

def test_sin_caso_sin_paciente():
    for f in (sesion.desde_caso, O.desde_caso, P.desde_caso, E.desde_caso, Z.desde_caso):
        assert f(None) is None, f


def test_mal_escrito_da_el_normal():
    assert sesion.desde_caso({'edad': 30, 'NASAL': {'lados': {'D': {'narina': 'x'}}}}) == sesion.desde_caso({'edad': 30})
    assert O.desde_caso({'edad': 30, 'OLFATO': {'lados': 'x'}}) == O.desde_caso({'edad': 30})
    assert P.desde_caso({'edad': 30, 'PRICK': {'histamina': 'x'}}) == P.desde_caso({'edad': 30})
    assert E.desde_caso({'edad': 30, 'ESPIRO': {'pre': {'fvc': 99}}})['bloque'] == E.desde_caso({'edad': 30})['bloque']
    assert Z.desde_caso({'id': 3, 'SUENO': {'perfil': 'x'}}) == Z.desde_caso({'id': 3})


def test_sin_edad_usa_adulto():
    assert O.desde_caso({'id': 1})['edad'] == 30.0
    assert E.desde_caso({'id': 1, 'edad': 'x'})['edad'] == 30.0


# --- 2 -----------------------------------------------------------------------

def test_nariz_normal():
    p = sesion.desde_caso({'id': 1, 'edad': 30})
    assert p is not None
    normal = modelo.paciente_normal()
    assert p['lados'] == normal['lados'] and p['ciclo'] == normal['ciclo']
    assert sesion.SesionNasal({'id': 1}, 5).hay_paciente


def test_olfato_normal():
    for d in CASOS:
        c = O.desde_caso(d)
        assert c is not None, d
        for lado in ('D', 'I'):
            v = c['olfato']['lados'][lado]
            tdi = v['T'] + v['D'] + v['I']
            assert tdi > O.p10(d['edad']), (d, tdi)
        if d['edad'] >= 11:
            assert O.categoria(tdi) in ('normosmia', 'hiposmia'), tdi
    assert O.categoria(sum(O.desde_caso({'edad': 30})['olfato']['lados']['D'].values())) == 'normosmia'


def test_prick_normal():
    c = P.desde_caso({'edad': 30})
    assert c['piel']['histamina'] >= P.UMBRAL_MM
    assert all(v == 0 for v in c['piel']['alergenos'].values())
    assert c['piel']['dermografismo'] == 0 and c['piel']['farmaco'] is None


def test_espirometria_normal():
    for d in CASOS:
        c = E.desde_caso(d)
        assert c is not None, d
        b, sexo = c['bloque'], c['sexo']
        assert 'bd' not in b
        for par, v in (('FVC', b['pre']['fvc']), ('FEV1', b['pre']['fev1']),
                       ('FEV1FVC', b['pre']['fev1'] / b['pre']['fvc'])):
            z = E.zscore(sexo, par, v, d['edad'], b['talla'])
            assert E.gravedad(z) == 'normal', (d, par, z)


def test_sueno_normal():
    c = Z.desde_caso({'id': 7, 'edad': 45})
    assert c is not None and c['sueno']['perfil'] == 'personalizado'
    assert c == Z.desde_caso({'id': 7, 'edad': 45})          # la misma noche
    for estudio in ('psg', 'pg'):
        R = Z.resumen(Z.noche(c['sueno'], estudio), estudio)
        iah = R['IAH'] if estudio == 'psg' else R['REI']
        assert iah is not None and iah < 5, (estudio, R)
        assert Z.gravedad_clave(iah) == 'normal'


if __name__ == '__main__':
    for nombre, f in list(globals().items()):
        if nombre.startswith('test_') and callable(f):
            f()
            print(f'  {nombre} OK')
    print('TODOS LOS TESTS PASARON')
