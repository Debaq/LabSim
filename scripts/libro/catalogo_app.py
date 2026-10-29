"""Catálogo de la práctica libre dentro de la app, para entrar sin cuenta.

    python3 -I scripts/libro/catalogo_app.py

Escribe resources/libro/catalogo.json.gz: las mismas carpetas y pacientes que
la práctica libre del backend (sql_practica.py), con el caso completo de cada
uno, para que el modo invitado funcione sin red ni API (ver
core/invitado.py y docs/roadmap_practica_libro.md, F1 y F3).

    {"carpetas": [{"id", "nombre", "orden"}],
     "items": [{"id", "folder_id", "carpeta", "case_id", "orden", "procedimiento",
                "nombre", "apellido", "rut", "fecha_nac"}],
     "casos": {"<ficha>": <cases.data>}}

Sale de los mismos datos que se cargaron en prod: material/casos/generados/
y pacientes_demo.json del libro (los casos son inventados: nada privado).
Se vuelve a correr cuando cambia un caso o una carpeta del libro.
"""
import gzip
import json
import pathlib
import subprocess
import sys
import tempfile

AQUI = pathlib.Path(__file__).resolve().parent
LABSIM = AQUI.parents[1]
LIBRO = pathlib.Path.home() / 'Escritorio/Proyectos/libro-orl'
CASOS = LIBRO / 'material/casos'
sys.path.insert(0, str(AQUI))
from procedimientos import procedimiento  # noqa: E402

# Los mismos que sql_practica.py: capítulos fuera y RUT cambiados al cargar
FUERA = {21, 22, 23, 24, 25, 26, 27, 31, 32, 35, 36, 37, 38}
RUT_NUEVO = {'cap12_esclerosis_multiple': '18087953', 'cap24_gentamicina': '12518779',
             'cap17_rubeola_congenita': '28268815', 'cap17_asfixia_perinatal': '28268816',
             'h10_lactante': '28267995'}


def _catalogos():
    """Los catálogos del Tomo I y II, con los scripts de siempre."""
    tmp = pathlib.Path(tempfile.mkdtemp())
    salida = []
    for script, nombre in (('catalogo_tomo1.py', 't1.json'), ('catalogo_tomo2.py', 't2.json')):
        subprocess.run([sys.executable, '-I', str(AQUI / script), str(tmp / nombre)],
                       check=True, capture_output=True)
        salida += json.loads((tmp / nombre).read_text(encoding='utf-8'))
    return salida


def main():
    ids = json.loads((AQUI / 'ids_libro.json').read_text(encoding='utf-8'))
    demos = json.loads((CASOS / 'pacientes_demo.json').read_text(encoding='utf-8'))
    carpetas, items, casos = [], [], {}
    for cap in _catalogos():
        tomo1 = isinstance(cap['cap'], str)
        if not tomo1 and cap['cap'] in FUERA:
            continue
        pacientes = [dict(p, n=n) for n, p in enumerate(cap['pacientes'], 1)]
        if not pacientes:
            continue
        nombre = f"{cap['cap']} · {cap['titulo']}" if tomo1 else f"Cap. {cap['cap']} · {cap['titulo']}"
        # El Tomo I va antes que el II, como en el libro
        orden = -100 + int(cap['cap'][1:]) if tomo1 else cap['cap']
        folder_id = len(carpetas) + 1
        carpetas.append({'id': folder_id, 'nombre': nombre, 'orden': orden})
        for p in pacientes:
            if p['origen'].startswith('demo:'):
                ficha = p['origen'].split(':')[1]
                demo = demos[ficha]
                data = dict(demo.get('data', demo))
            else:
                ficha = ids.get(p['clave'])
                if ficha is None:
                    continue
                data = dict(json.loads((CASOS / 'generados' / f"{p['clave']}.json").read_text(encoding='utf-8'))['data'])
            snap = dict(data.get('paciente_snapshot') or {})
            if p['clave'] in RUT_NUEVO:
                snap['rut'] = RUT_NUEVO[p['clave']]
            data['paciente_snapshot'] = snap
            data['id'] = int(ficha)
            casos[ficha] = data
            items.append({
                'id': len(items) + 1, 'folder_id': folder_id, 'carpeta': nombre, 'case_id': ficha,
                'orden': p['n'], 'procedimiento': procedimiento(p['figuras'], p['clave'], cap['cap']),
                'nombre': snap.get('nombre', ''), 'apellido': snap.get('apellido', ''),
                'rut': snap.get('rut', ''), 'fecha_nac': snap.get('fecha_nac', ''),
            })
    carpetas.sort(key=lambda c: c['orden'])
    orden_carpeta = {c['id']: i for i, c in enumerate(carpetas)}
    items.sort(key=lambda it: (orden_carpeta[it['folder_id']], it['orden']))
    catalogo = {'carpetas': carpetas, 'items': items, 'casos': casos}
    destino = LABSIM / 'resources/libro/catalogo.json.gz'
    texto = json.dumps(catalogo, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    # mtime fijo: un catálogo que no cambió da el mismo archivo (no viaja en la actualización)
    destino.write_bytes(gzip.compress(texto, 9, mtime=0))
    print(f'{len(carpetas)} carpetas, {len(items)} pacientes, {len(casos)} fichas, '
          f'{len(texto) // 1024} KB -> {destino.stat().st_size // 1024} KB comprimido')


if __name__ == '__main__':
    main()
