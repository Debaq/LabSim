"""Catálogo del Tomo II del libro: capítulo -> pacientes en orden, con su origen y figuras.

    python3 -I scripts/libro/catalogo_tomo2.py CARPETA/catalogo_tomo2.json
"""
import importlib.util, json, pathlib, re, sys, collections
LIBRO = pathlib.Path.home() / 'Escritorio/Proyectos/libro-orl'
sys.path.insert(0, str(LIBRO / 'herramientas'))
caps = sorted(LIBRO.glob('texto/capitulos/[0-9][0-9]-*.py'))
indice = (LIBRO / 'texto/indice.md').read_text()
titulos = {int(m.group(1)): m.group(2).strip() for m in re.finditer(r'^### (\d+)\. (.+)$', indice, re.M)}
salida, tipos = [], collections.Counter()
for py in caps:
    num = int(py.name[:2])
    spec = importlib.util.spec_from_file_location(f'cap{num}', py)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print('ERROR', py.name, e); continue
    pacientes = []
    for c in getattr(mod, 'CASOS', []):
        clave = f'cap{num:02d}_' + c['nombre']
        caso = c['caso']
        if isinstance(caso, str):
            origen = caso
        else:
            origen = 'generado' if (LIBRO / 'material/casos/generados' / f'{clave}.json').exists() else '??'
        figs = [f['tipo'] for f in c['figuras']]
        tipos.update(figs)
        pacientes.append({'clave': clave, 'origen': origen, 'figuras': figs})
    salida.append({'cap': num, 'titulo': titulos.get(num, '?'), 'pacientes': pacientes})
json.dump(salida, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
for c in salida:
    print(f"{c['cap']:2} {c['titulo'][:34]:34} " + ', '.join(f"{p['clave'].split('_',1)[1]}[{p['origen'] if p['origen']!='generado' else 'g'}]" for p in c['pacientes']))
print(tipos.most_common())
