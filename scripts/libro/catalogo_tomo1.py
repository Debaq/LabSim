"""Catálogo del Tomo I: herramienta -> pacientes en orden, con su origen y figuras."""
import importlib.util, json, pathlib, re, sys
LIBRO = pathlib.Path.home() / 'Escritorio/Proyectos/libro-orl'
sys.path.insert(0, str(LIBRO / 'herramientas'))
indice = (LIBRO / 'texto/indice.md').read_text()
titulos = {m.group(1): re.sub(r'\s*\*\(.*?\)\*', '', m.group(2)).strip()
           for m in re.finditer(r'^### ([HB]\d+)\. (.+)$', indice, re.M)}
salida = []
for py in sorted(LIBRO.glob('texto/capitulos/[HB][0-9]*.py'), key=lambda p: (p.name[0], int(re.match(r'[HB](\d+)', p.name).group(1)))):
    clave_cap = re.match(r'([HB]\d+)', py.name).group(1)
    num = clave_cap[0] + str(int(clave_cap[1:]))            # H03 -> H3
    spec = importlib.util.spec_from_file_location(clave_cap, py); mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print('ERROR', py.name, e); continue
    pacientes = []
    for c in getattr(mod, 'CASOS', []):
        clave = f'{num.lower()}_' + c['nombre']
        caso = c['caso']
        origen = caso if isinstance(caso, str) else ('generado' if (LIBRO / 'material/casos/generados' / f'{clave}.json').exists() else '??')
        pacientes.append({'clave': clave, 'origen': origen, 'figuras': [f['tipo'] for f in c['figuras']]})
    if pacientes:
        salida.append({'cap': num, 'titulo': titulos.get(num, '?'), 'pacientes': pacientes})
json.dump(salida, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
for c in salida:
    print(f"{c['cap']:4} {c['titulo'][:40]:40} " + ', '.join(f"{p['clave'].split('_',1)[1]}[{p['origen'] if p['origen']!='generado' else 'g'}]" for p in c['pacientes']))
