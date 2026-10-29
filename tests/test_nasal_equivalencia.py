"""Equivalencia del modelo nasal en Python con el JS de RinoSim.

tests/data/nasal_referencia.json lo genera node con el código REAL de
RinoSim (scripts/nasal/exportar_referencia.mjs; el comando exacto está en la
clave `_regenerar` del propio JSON). Cada registro trae los argumentos y lo
que devolvió el JS; acá se repite la llamada con src/nasal y se compara.

Qué se compara: la secuencia del generador y las semillas (bit a bit), los
pacientes, perfiles, curvas de rinomanometría y rinometría, tablas de
resistencias, lecturas, avisos y errores de técnica.

Tolerancia: relativa 1e-9, con piso absoluto 1e-12. Los números salen casi
idénticos (la mayoría bit a bit); lo que puede diferir es el último bit de
sin/cos/exp/pow, que V8 y la libm de Python no calculan igual. Al final se
imprime la diferencia relativa máxima que hubo.

Reglas que comparten el exportador y este test:
  * claves camelCase del JS -> snake_case de Python (cvEntreCiclos);
  * claves numéricas del JS (75, 150) llegan como texto; en Python son int;
  * Infinity/NaN viajan en el JSON como texto;
  * los textos del JS que dicen H24/H25 se leen como H26/H27 (renumeración
    del libro: rinomanometría H26, rinometría H27);
  * listas de números o textos de más de 60 elementos se comparan de a una
    de cada 4, salvo en los registros con completo: true.
"""

import json
import math
import os
import re
import sys

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from nasal import azar, modelo, rinomanometria as rm, rinometria as ra  # noqa: E402

RUTA = os.path.join(os.path.dirname(__file__), 'data', 'nasal_referencia.json')
with open(RUTA, encoding='utf-8') as _f:
    REF = json.load(_f)

REL = 1e-9
PISO = 1e-12
_NO_FINITOS = {'Infinity': math.inf, '-Infinity': -math.inf, 'NaN': math.nan}
_peor = {'rel': 0.0, 'donde': ''}


# ── comparación ─────────────────────────────────────────────────────────────

def _snake(k):
    return re.sub(r'(?<=[a-z0-9])([A-Z])', lambda m: '_' + m.group(1).lower(), k)


def _reduce(v):
    """La misma regla de listas largas del exportador."""
    if isinstance(v, (list, tuple)):
        if len(v) > 60 and all(isinstance(e, (int, float, str)) and not isinstance(e, bool) for e in v):
            return list(v[::4])
        return [_reduce(e) for e in v]
    if isinstance(v, dict):
        return {k: _reduce(x) for k, x in v.items()}
    return v


def _claves(d):
    return {str(k): k for k in d}


def compara(esp, act, donde='$'):
    """Falla con la ruta exacta de la primera diferencia."""
    if isinstance(esp, str) and esp in _NO_FINITOS and isinstance(act, (int, float)):
        esp = _NO_FINITOS[esp]
    if isinstance(esp, dict):
        assert isinstance(act, dict), f'{donde}: se esperaba dict y vino {type(act).__name__}'
        ka = _claves(act)
        ke = {_snake(k): k for k in esp}
        assert set(ke) == set(ka), f'{donde}: claves distintas {sorted(set(ke) ^ set(ka))}'
        for k, orig in ke.items():
            compara(esp[orig], act[ka[k]], f'{donde}.{k}')
    elif isinstance(esp, list):
        assert isinstance(act, (list, tuple)), f'{donde}: se esperaba lista y vino {type(act).__name__}'
        assert len(esp) == len(act), f'{donde}: largo {len(act)} y el JS dio {len(esp)}'
        for i, (e, a) in enumerate(zip(esp, act)):
            compara(e, a, f'{donde}[{i}]')
    elif esp is None:
        assert act is None, f'{donde}: se esperaba None y vino {act!r}'
    elif isinstance(esp, bool):
        assert act is esp, f'{donde}: {act!r} != {esp!r}'
    elif isinstance(esp, (int, float)):
        assert isinstance(act, (int, float)) and not isinstance(act, bool), f'{donde}: no es número: {act!r}'
        if esp == act or (esp != esp and act != act):
            return
        if math.isinf(esp) or math.isinf(act) or esp != esp or act != act:
            raise AssertionError(f'{donde}: {act!r} != {esp!r}')
        rel = abs(esp - act) / max(abs(esp), abs(act), PISO / REL)
        if rel > _peor['rel']:
            _peor['rel'] = rel
            _peor['donde'] = donde
        assert abs(esp - act) <= max(PISO, REL * max(abs(esp), abs(act))), \
            f'{donde}: {act!r} != {esp!r} (rel {rel:.2e})'
    else:
        # Los textos al usuario citan H26/H27 (el libro renumeró H24/H25).
        if isinstance(esp, str):
            esp = esp.replace('H24', 'H26').replace('H25', 'H27')
        assert esp == act, f'{donde}: {act!r} != {esp!r}'


def contra(esp, act, donde, completo=False):
    compara(esp, act if completo else _reduce(act), donde)


def _paciente(r):
    p = modelo.paciente(r['cuadro'], r.get('semilla'))
    for ruta, valor in r.get('edita') or []:
        modelo.escribe(p, ruta, valor)
    return p


def _tupla(l):
    return [tuple(x) if isinstance(x, list) else x for x in l]


# ── azar ────────────────────────────────────────────────────────────────────

def test_semillas_fnv_identicas():
    for r in REF['azar_semilla']:
        assert azar.semilla(r['entrada']) == r['valor'], r['entrada']


def test_secuencias_del_generador_identicas():
    for r in REF['azar_secuencia']:
        g = azar.generador(r['semilla'])
        if 'largo' in r:
            lista = [g.uniforme() for _ in range(r['largo'])]
            assert lista[-5:] == r['ultimos'], 'los últimos de la secuencia larga'
            tot = 0
            for u in lista:
                tot += u
            compara(r['suma'], tot, 'suma')
            continue
        # uniforme: bit a bit; normal usa log/cos de libm, tolerancia.
        assert [g.uniforme() for _ in range(25)] == r['uniforme'], r['semilla']
        compara(r['normal'], [g.normal() for _ in range(25)], f"normal {r['semilla']}")
        compara(r['normal2'], [g.normal(5, 2) for _ in range(10)], 'normal(5,2)')
        compara(r['entre'], [g.entre(1, 3) for _ in range(10)], 'entre')


# ── modelo ──────────────────────────────────────────────────────────────────

def test_rejilla_y_constantes():
    c = REF['modelo_constantes']
    assert len(modelo.REJILLA) == c['REJILLA']
    assert modelo.REJILLA[-1] == c['ultimo']
    assert [modelo.REJILLA[i] for i in (1, 2, 3, 77, 199, 480)] == c['muestra']


def test_pacientes_identicos():
    for r in REF['paciente']:
        compara(r['out'], modelo.paciente(r['cuadro'], r['semilla']), f"paciente {r['cuadro']}/{r['semilla']}")


def test_normaliza_identico():
    for r in REF['normaliza']:
        compara(r['out'], modelo.normaliza(r['entrada']), 'normaliza')


def test_congestion_identica():
    for r in REF['congestion']:
        p = modelo.paciente(r['cuadro'], r['semilla'])
        act = {l: {'reposo': [modelo.congestion(p, l, {'minuto': m}) for m in (0, 10, 37.5, 75, 150, 200)],
                   'vc': modelo.congestion(p, l, {'vc': True, 'minuto': 40}),
                   'sin_estado': modelo.congestion(p, l)} for l in modelo.LADOS}
        compara(r['out'], act, f"congestion {r['cuadro']}/{r['semilla']}")


def test_perfiles_identicos():
    for r in REF['perfil']:
        p = modelo.paciente(r['cuadro'], r['semilla'])
        act = modelo.perfil(p, r['lado'], r['estado'], r['colapso'])
        contra(r['out'], act, f"perfil {r['cuadro']}/{r['semilla']}/{r['lado']}/{r['estado']}")


def test_piezas_identicas():
    for r in REF['piezas']:
        p = modelo.paciente(r['cuadro'], r['semilla'])
        act = {l: [[modelo.piezas(p['lados'][l], x, c) for c in r['cs']] for x in r['xs']] for l in modelo.LADOS}
        compara(r['out'], act, f"piezas {r['cuadro']}")


# ── rinomanometría ──────────────────────────────────────────────────────────

def test_rohrer_y_puros_identicos():
    pu = REF['rm_puros']
    for r in pu['flujo_presion']:
        v = rm.flujo(r['k1'], r['k2'], r['dP'])
        compara(r['flujo'], v, 'flujo')
        compara(r['presion'], rm.presion(r['k1'], r['k2'], v), 'presion')
        compara(r['presion_V'], rm.presion(r['k1'], r['k2'], r['dP']), 'presion(V)')
    for r in pu['total']:
        a, b = (_NO_FINITOS.get(v, v) if isinstance(v, str) else v for v in (r['a'], r['b']))
        compara(r['out'], rm.resistencia_total(a, b), f"total {r['a']},{r['b']}")
    for r in pu['vasoconstrictor']:
        act = (rm.lectura_vasoconstrictor(r['a'], r['b']) if r['ref'] is None
               else rm.lectura_vasoconstrictor(r['a'], r['b'], r['ref']))
        compara(r['out'], act, f"vasoconstrictor {r['a']},{r['b']}")
    assert rm.I_COANA == pu['constantes']['I_COANA']
    assert rm.UMBRAL_SIN_CAMBIO == pu['constantes']['UMBRAL_SIN_CAMBIO']
    cu = pu['curvas']
    c = cu['curva']
    for r in cu['lee_en']:
        compara(r['out'], rm.lee_en(c, r['P']), f"lee_en {r['P']}")
    compara(cu['broms'], rm.broms(c), 'broms')
    compara(cu['broms_300'], rm.broms(c, 300), 'broms 300')
    compara(cu['broms_9999'], rm.broms(c, 9999), 'broms 9999')


def test_fosa_flujo_y_resistencia_identicos():
    for r in REF['rm_fosa']:
        p = modelo.paciente(r['cuadro'], r['semilla'])
        f = rm.fosa(p, r['lado'], r['estado'])
        act = {'flujo': [rm.flujo_fosa(f, P) for P in r['Ps']],
               'resistencia': [rm.resistencia_fosa(f, P) for P in (75, 150, 300)],
               'A': f.A, 'congestion': f.congestion}
        contra(r['out'], act, f"fosa {r['cuadro']}/{r['lado']}")


def test_coeficientes_de_tramos_identicos():
    for r in REF['rm_coeficientes']:
        p = modelo.paciente(r['cuadro'], r['semilla'])
        g = rm.fosa(p, r['lado'], r['estado'])
        act = [[g.coef(P, a, b) for a, b in r['cortes']] for P in r['Ps']]
        compara(r['out'], act, f"coef {r['cuadro']}/{r['lado']}")


def test_red_identica():
    for r in REF['rm_red']:
        p = modelo.paciente(r['cuadro'], r['semilla'])
        otro = 'I' if r['lado'] == 'D' else 'D'
        fm = rm.fosa(p, r['lado'], r['estado'])
        fo = rm.fosa(p, otro, r['estado'])
        act = [rm.resuelve_red(fm, fo, P, p['perforacion'], r['errores']) for P in r['Ps']]
        compara(r['out'], act, f"red {r['cuadro']}/{r['lado']}/{r['errores']}")


def test_medicion_identica():
    for r in REF['rm_mide']:
        p = _paciente(r)
        act = rm.mide_fosa(p, r['lado'], r['estado'], r['opciones'])
        contra(r['out'], act, f"rm {r['cuadro']}/{r['semilla']}/{r['lado']}/{r['estado']}/{r['opciones']}", r['completo'])


def test_examen_identico():
    for r in REF['rm_examen']:
        p = modelo.paciente(r['cuadro'], r['semilla'])
        contra(r['out'], rm.examen(p, r['estado'], r['opciones']), f"examen {r['cuadro']}")


# ── rinometría ──────────────────────────────────────────────────────────────

def test_curva_del_equipo_identica():
    for r in REF['ra_equipo']:
        p = _paciente(r)
        act = ra.curva_del_equipo(p, r['lado'], r['estado'], r['errores'])
        contra(r['out'], act, f"equipo {r['cuadro']}/{r['lado']}/{r['estado']}/{r['errores']}")


def test_rinometria_medicion_identica():
    for r in REF['ra_mide']:
        p = _paciente(r)
        act = ra.mide_fosa(p, r['lado'], r['estado'], r['opciones'])
        contra(r['out'], act, f"ra {r['cuadro']}/{r['semilla']}/{r['lado']}/{r['estado']}/{r['opciones']}", r['completo'])


def test_volumen_y_medidas_identicos():
    pu = REF['ra_puros']
    x = [i * 0.025 for i in range(401)]
    llana = [2 for _ in x]
    dos = [2 - 1.4 * math.exp(-0.5 * ((v - 1.5) / 0.3) ** 2) - math.exp(-0.5 * ((v - 3.5) / 0.4) ** 2) for v in x]
    uno = [2 - 1.4 * math.exp(-0.5 * ((v - 1.5) / 0.3) ** 2) for v in x]
    creciente = [0.5 + 0.3 * v for v in x]
    for r in pu['volumen']:
        compara(r['llana'], ra.volumen(x, llana, r['a'], r['b']), 'vol llana')
        compara(r['dos'], ra.volumen(x, dos, r['a'], r['b']), 'vol dos')
    for nombre, A in (('dos', dos), ('uno', uno), ('creciente', creciente), ('llana', llana)):
        compara(pu['medidas'][nombre], ra.medidas(x, A), f'medidas {nombre}')
    assert ra.CRITERIO_REPETICION == pu['constantes']['CRITERIO_REPETICION']
    assert ra.AREA_CRITICA == pu['constantes']['AREA_CRITICA']
    assert ra.X_CURVA == pu['constantes']['X_CURVA']


if __name__ == '__main__':
    fallos = 0
    total = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith('test_') and callable(fn):
            total += 1
            try:
                fn()
                print(f'  {nombre} OK')
            except AssertionError as exc:
                fallos += 1
                print(f'  {nombre} FALLÓ: {exc}')
    print(f"diferencia relativa máxima contra el JS: {_peor['rel']:.2e} en {_peor['donde']}")
    print('TODOS LOS TESTS PASARON' if not fallos else f'{fallos} FALLARON')
    print(f'{total - fallos}/{total}')
