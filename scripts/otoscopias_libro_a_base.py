#!/usr/bin/env python3
"""Sube a la base de otoscopias de prod (admin/otoscopias.php) las fotos de
los bancos que usa el libro (libro-orl/material/otoscopias/CREDITOS*.md).

Sube el ORIGINAL del banco, no la copia del libro (que puede estar
reflejada): el lado anterior lo marca una persona en el panel, junto con el
giro. Cada foto entra "sin clasificar" pero con el tipo ya puesto (sale del
hallazgo del libro o, si no, de la carpeta del banco) y en las notas el
hallazgo, lo que se ve (DESCRIPCIONES.md), dónde la usa el libro y el
crédito del banco. Volver a correrlo no duplica: la consola reconoce la foto
por su ruta en el banco.

    python3 scripts/otoscopias_libro_a_base.py --ver     # qué subiría, sin subir
    python3 scripts/otoscopias_libro_a_base.py           # sube
    python3 scripts/otoscopias_libro_a_base.py --normales 10   # todas las alteradas y solo 10 normales
    python3 scripts/otoscopias_libro_a_base.py --normales 10 --hasta 10
        # además completa cada tipo alterado hasta 10 con fotos del banco que el libro no usa
"""
import argparse
import base64
import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path

OTOS = Path.home() / 'Escritorio/Proyectos/libro-orl/material/otoscopias'
BANCOS = OTOS / 'bancos'

CREDITO_BANCO = {
    'kpj': 'KPJ, Zaka Ur Rehman, CC BY-NC-SA 4.0',
    'viscaino': 'Viscaino M, Auat Cheein F. Ear imagery database (figshare 2020), CC0 1.0',
    'basaran': 'Polat K. eardrum (figshare 2021), CC BY 4.0',
}

# Del hallazgo escrito en el libro; el orden importa ("crónica ... perforación" es perforación).
POR_HALLAZGO = [
    ('sin colesteatoma', 'omc'),
    ('colesteatoma', 'colesteatoma'),
    ('perforaci', 'perforacion'),
    ('cerumen', 'cerumen'),
    ('efusi', 'ome'),
    ('retra', 'retraccion'),
    ('otitis externa', 'otitis_externa'),
    ('miringoescl', 'timpanoesclerosis'),
    ('timpanoescl', 'timpanoesclerosis'),
    ('tubo', 'tubo'),
    ('aguda', 'oma'),
    ('crónica', 'omc'),
    ('normal', 'normal'),
]
# De la carpeta del banco, si el hallazgo no dice nada reconocible.
POR_CARPETA = [
    ('cholesteatoma', 'colesteatoma'),
    ('chronic inactive', 'perforacion'),
    ('chronic', 'omc'),
    ('csom', 'omc'),
    ('effusion', 'ome'),
    ('acute otitis', 'oma'),
    ('/aom/', 'oma'),
    ('earwax', 'cerumen'),
    ('myringosclerosis', 'timpanoesclerosis'),
    ('miringoskleroz', 'timpanoesclerosis'),
    ('otitiseksterna', 'otitis_externa'),
    ('tympanostomy', 'tubo'),
    ('normal', 'normal'),
]


def tipo_de(hallazgo: str, ruta: str) -> str:
    h = hallazgo.lower()
    for clave, tipo in POR_HALLAZGO:
        if clave in h:
            return tipo
    r = '/' + ruta.lower() + '/'
    for clave, tipo in POR_CARPETA:
        if clave in r:
            return tipo
    return 'otra'


def tablas():
    """Filas de todas las tablas de CREDITOS*.md como dict columna -> valor."""
    for f in sorted(OTOS.glob('CREDITOS*.md')):
        cab = None
        for linea in f.read_text(encoding='utf-8').splitlines():
            if not linea.startswith('|'):
                cab = None
                continue
            celdas = [c.strip() for c in linea.strip().strip('|').split('|')]
            if cab is None:
                cab = [c.lower() for c in celdas]
                continue
            if set(linea) <= set('|-: '):
                continue
            yield f.name, dict(zip(cab, celdas))


def descripciones():
    d = {}
    for linea in (OTOS / 'DESCRIPCIONES.md').read_text(encoding='utf-8').splitlines():
        m = re.match(r'\|\s*(\S+)\s*\|\s*(.+?)\s*\|\s*$', linea)
        if m:
            d[m[1]] = m[2]
    return d


def pool():
    desc = descripciones()
    fotos = {}
    for _archivo_md, fila in tablas():
        ruta_col = next((v for k, v in fila.items() if k.startswith('ruta')), '')
        m = re.search(r'`([^`]+)`', ruta_col)
        if not m:
            continue
        ruta = m[1]
        if not (BANCOS / ruta).is_file():
            continue  # p. ej. la foto de la atresia, que no es de un banco
        hallazgo = next((v for k, v in fila.items() if k.startswith('hallazgo')), '')
        archivo = fila.get('archivo', '')
        panel = fila.get('panel', '')
        reflejada = fila.get('reflejada', '').lower().startswith('s')
        f = fotos.setdefault(ruta, {'ruta': ruta, 'hallazgos': [], 'usos': [], 'desc': ''})
        if hallazgo and hallazgo not in f['hallazgos']:
            f['hallazgos'].append(hallazgo)
        uso = archivo + (f' panel {panel}' if panel else '') + (' (reflejada)' if reflejada else '')
        f['usos'].append(uso)
        clave = archivo.removesuffix('.jpg')
        if not f['desc'] and clave in desc:
            f['desc'] = desc[clave]
    for f in fotos.values():
        f['tipo'] = tipo_de(' '.join(f['hallazgos']), f['ruta'])
        partes = []
        if f['hallazgos']:
            partes.append('Hallazgo: ' + '; '.join(f['hallazgos']) + '.')
        if f['desc']:
            partes.append('Se ve: ' + f['desc'])
        partes.append('Libro: ' + ', '.join(f['usos']) + '.')
        partes.append('Banco: ' + CREDITO_BANCO.get(f['ruta'].split('/')[0], f['ruta'].split('/')[0]) + '.')
        f['notas'] = ' '.join(partes)[:500]
    return sorted(fotos.values(), key=lambda f: (f['tipo'] != 'normal', f['tipo'], f['ruta']))


# Carpetas de los bancos por tipo, para completar con fotos que el libro no usa.
CARPETAS = {
    'cerumen': ['viscaino/Datos/Training-validation/Earwax plug', 'basaran/eardrum/Abnormal/Earwax'],
    'colesteatoma': ['kpj/chronic otitis media with cholesteatoma'],
    'oma': ['kpj/Acute otitis media', 'basaran/eardrum/Abnormal/AOM'],
    'omc': ['kpj/chronic active otitis media without cholesteatoma',
            'viscaino/Datos/Training-validation/Chronic otitis media'],
    'ome': ['kpj/otitis media effusion'],
    'otitis_externa': ['basaran/eardrum/Abnormal/OtitisEksterna'],
    'perforacion': ['kpj/chronic inactive otitis media', 'basaran/eardrum/Abnormal/CSOM'],
    'timpanoesclerosis': ['viscaino/Datos/Training-validation/Myringosclerosis', 'basaran/eardrum/Abnormal/Miringoskleroz'],
    'tubo': ['basaran/eardrum/Abnormal/TympanostomyTubes'],
}


def completar(fotos, hasta):
    """Fotos del banco (no usadas por el libro) hasta llegar a `hasta` por tipo alterado.

    Dentro de cada carpeta se toman archivos espaciados a lo largo de la lista
    ordenada, no los primeros: en KPJ los nombres seguidos suelen ser la misma
    sesión (el mismo oído varias veces).
    """
    usadas = {f['ruta'] for f in fotos}
    extra = []
    for tipo, carpetas in CARPETAS.items():
        faltan = hasta - sum(1 for f in fotos if f['tipo'] == tipo)
        if faltan <= 0:
            continue
        candidatas = []
        for c in carpetas:
            archivos = sorted(p for p in (BANCOS / c).iterdir()
                              if p.suffix.lower() in ('.jpg', '.jpeg', '.png')
                              and str(p.relative_to(BANCOS)) not in usadas)
            paso = max(1, len(archivos) // max(1, faltan))
            candidatas.append(archivos[::paso])
        i = 0
        while faltan > 0 and any(candidatas):
            lista = candidatas[i % len(candidatas)]
            if lista:
                p = lista.pop(0)
                ruta = str(p.relative_to(BANCOS))
                banco = ruta.split('/')[0]
                rotulo = p.parent.name
                extra.append({
                    'ruta': ruta, 'tipo': tipo,
                    'notas': f'Rótulo del banco: {rotulo} (no la usa el libro; revisar). '
                             f'Banco: {CREDITO_BANCO.get(banco, banco)}.',
                })
                faltan -= 1
            i += 1
    return extra


def elegir_normales(fotos, n):
    """n normales repartidas por turno entre los bancos, para que haya variedad de equipo y de luz."""
    por_banco = {}
    for f in fotos:
        if f['tipo'] == 'normal':
            por_banco.setdefault(f['ruta'].split('/')[0], []).append(f)
    elegidas = []
    listas = [por_banco[b] for b in sorted(por_banco)]
    i = 0
    while len(elegidas) < n and any(listas):
        lista = listas[i % len(listas)]
        if lista:
            elegidas.append(lista.pop(0))
        i += 1
    return elegidas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--ver', action='store_true', help='solo mostrar qué subiría')
    ap.add_argument('--normales', type=int, default=None,
                    help='cuántas normales subir (repartidas entre los bancos); sin esto, todas')
    ap.add_argument('--hasta', type=int, default=None,
                    help='completar cada tipo alterado hasta este número con fotos del banco que el libro no usa')
    a = ap.parse_args()
    fotos = pool()
    if a.normales is not None:
        fotos = [f for f in fotos if f['tipo'] != 'normal'] + elegir_normales(fotos, a.normales)
    if a.hasta is not None:
        fotos += completar(fotos, a.hasta)
    print(f'{len(fotos)} fotos:', dict(Counter(f['tipo'] for f in fotos)))
    if a.ver:
        for f in fotos:
            print(f"{f['tipo']:18} {f['ruta']}\n{'':18} {f['notas']}")
        return

    spec = importlib.util.spec_from_file_location('consola', Path(__file__).with_name('consola.py'))
    consola = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consola)
    url, token, _ = consola._cargar_env(None)
    nuevas = ya = 0
    errores = []
    for i, f in enumerate(fotos, 1):
        cuerpo = {
            'accion': 'foto', 'tipo': 'biblioteca', 'nombre': f['ruta'], 'clase': f['tipo'], 'notas': f['notas'],
            'imagen': base64.b64encode((BANCOS / f['ruta']).read_bytes()).decode('ascii'),
        }
        try:
            r = consola._llamar(url, token, cuerpo)
        except (SystemExit, Exception) as e:  # _llamar corta con sys.exit ante un error del servidor
            errores.append(f"{f['ruta']}: {e}")
            if 'otoscopia o rostro' in str(e):
                print('El servidor todavía no tiene el comando "biblioteca" de la consola: falta subir '
                      'src/Consola.php, src/OtoscopiaBiblioteca.php y public/api/consola.php.')
                sys.exit(1)
            continue
        if r.get('nuevo'):
            nuevas += 1
        else:
            ya += 1
        print(f"[{i}/{len(fotos)}] #{r['id']} {'subida' if r.get('nuevo') else 'ya estaba'}  {f['tipo']:16} {f['ruta']}", flush=True)
    print(f'\n{nuevas} subidas, {ya} ya estaban, {len(errores)} con error')
    for e in errores:
        print('  ', e)
    sys.exit(1 if errores else 0)


if __name__ == '__main__':
    main()
