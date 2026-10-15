#!/usr/bin/env python3
"""Arma las figuras del libro a partir de los casos de docs/libro/casos/.

    micromamba run -n labsim python docs/libro/figuras/hacer_figuras.py            # todos
    micromamba run -n labsim python docs/libro/figuras/hacer_figuras.py cap11_*    # algunos

Cada caso es un JSON con el paciente y las figuras que lleva:

    {"caso": "demo:39",
     "figuras": [{"tipo": "audiograma"},
                 {"tipo": "timpanograma"},
                 {"tipo": "reflejos"},
                 {"tipo": "abr", "niveles": [80, 60, 40], "marcar": ["I", "III", "V"]}]}

Salida: figuras/salida/<caso>_<tipo>.svg (con sufijo si un tipo se repite)
y figuras/salida/index.html, una hoja para revisarlas todas juntas.
El entorno labsim hace falta por el ABR (PySide6); el resto es Python puro.
"""
import fnmatch
import json
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from motor import abr, audiograma, impedancia  # noqa: E402
from motor.datos import cargar_caso  # noqa: E402

CASOS = AQUI.parent / 'casos'
SALIDA = AQUI / 'salida'
FUENTES = AQUI.parents[1] / 'manual' / 'fuentes'


def figura(caso, f):
    tipo = f['tipo']
    if tipo == 'audiograma':
        return audiograma.dibujar(caso, estudio=f.get('estudio', True), ldl=f.get('ldl', True),
                                  oidos=tuple(f.get('oidos', ('OD', 'OI'))))
    if tipo == 'timpanograma':
        return impedancia.timpanograma(caso, oidos=tuple(f.get('oidos', ('OD', 'OI'))),
                                       escala_ml=f.get('escala_ml', 2.0), sonda=f.get('sonda', 226))
    if tipo == 'reflejos':
        return impedancia.reflejos(caso)
    if tipo == 'abr':
        curvas = abr.capturar(caso, f.get('oidos', ['OD', 'OI']), f.get('niveles', [80, 60, 40]),
                              estimulo=f.get('estimulo'), promediaciones=f.get('promediaciones', 2000))
        return abr.dibujar(curvas, marcar=tuple(f.get('marcar', ('I', 'III', 'V'))),
                           ms_max=f.get('ms_max', 12.0))
    raise ValueError(f'Tipo de figura desconocido: {tipo!r}')


def main(patrones):
    SALIDA.mkdir(exist_ok=True)
    archivos = sorted(CASOS.glob('*.json'))
    if patrones:
        archivos = [a for a in archivos if any(fnmatch.fnmatch(a.stem, p) for p in patrones)]
    hechas = []
    for arch in archivos:
        spec = json.loads(arch.read_text(encoding='utf-8'))
        caso = cargar_caso(spec['caso'])
        vistos = {}
        for f in spec['figuras']:
            n = vistos[f['tipo']] = vistos.get(f['tipo'], 0) + 1
            nombre = f"{arch.stem}_{f['tipo']}" + (f'_{n}' if n > 1 else '') + '.svg'
            (SALIDA / nombre).write_text(figura(caso, f), encoding='utf-8')
            hechas.append((arch.stem, nombre))
            print('  ', nombre)
    _hoja(hechas)
    print(f'{len(hechas)} figuras en {SALIDA}')


def _hoja(hechas):
    """index.html con todas las figuras, para revisarlas en el navegador."""
    rel = pathlib.Path('../../../manual/fuentes')
    filas, actual = [], None
    for caso, nombre in hechas:
        if caso != actual:
            filas.append(f'<h2>{caso}</h2>')
            actual = caso
        svg = (SALIDA / nombre).read_text(encoding='utf-8')
        filas.append(f'<figure>{svg}<figcaption>{nombre}</figcaption></figure>')
    (SALIDA / 'index.html').write_text(f'''<!doctype html><meta charset="utf-8"><title>Figuras del libro</title>
<style>@font-face{{font-family:'Plus Jakarta Sans';src:url('{rel}/plus-jakarta-sans-latin.woff2')}}
body{{font-family:'Plus Jakarta Sans',sans-serif;margin:24px;color:#1d1d1f;background:#fff}}
h2{{font-size:15px;margin:32px 0 8px;border-top:1px solid #e7e5e0;padding-top:16px}}
figure{{display:inline-block;margin:0 24px 16px 0;vertical-align:top}}
figure svg{{zoom:1.5;display:block}} figcaption{{font-size:11px;color:#8a8a90}}</style>
{''.join(filas)}''', encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1:])
