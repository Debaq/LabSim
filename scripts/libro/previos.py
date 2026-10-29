"""Exámenes previos de los pacientes del libro, como los dibuja el libro.

    QT_QPA_PLATFORM=offscreen ~/.local/share/labsim/libro-venv/bin/python -I scripts/libro/previos.py
    ... previos.py --solo-historia     (rehace solo las hojas de la historia)
    ... previos.py --examen EOA        (rehace solo las hojas de ese examen)

(el PEATC necesita PySide6 y pyqtgraph: el python del libro, ver
libro.python_figuras.)

Escribe resources/libro/previos/<ficha>/<examen>.svgz con la hoja de cada
examen que el libro muestra de ese paciente (audiometría, impedanciometría,
emisiones, PEATC, ECochG, VEMP, corticales), las hojas de los exámenes que
cuenta su historia clínica (historia_examenes.json, al lado de este script) y
resources/libro/previos/indice.json. Comprimidas (svgz, que Qt lee directo):
1,7 MB en vez de 8,5; con la fecha del gzip fija, una hoja que no cambió da
el mismo archivo y no viaja en la actualización.

    {"<ficha>": {"trae": {"Audiometría": "<ficha>/audiometria.svgz", ...},
                 "por_procedimiento": {"PEATC": ["Audiometría", "Impedanciometría"], ...},
                 "historia": [{"dias": -138, "examen": "Audiometría",
                               "svg": "<ficha>/historia_138_audiometria.svgz"}, ...]}}

En historia_examenes.json cada línea de la historia que cuenta un examen
lleva su hoja: "tamizaje" (una tarjeta con pasa/refiere por oído, lo mismo
que dice la línea), "actual" (el examen de entonces da lo mismo que hoy) o
"anterior" (un estado distinto: los datos de material/casos/generados/<caso>.json
del libro; provisorios mientras no se regeneren, ver pendientes_urgentes.md
del libro).

La ficha clínica de la práctica libre muestra como exámenes que el paciente
trae los que su procedimiento no nombra (core/ficha.py; el procedimiento lo
pone el foco del capítulo, ver FOCO en sql_practica.py). Ver
docs/audiometria_previa.md.

Sale de los mismos datos que se cargaron en el backend (generados/, no
propios/: sql_practica.py carga los generados) y de los demo 33-42. Se
vuelve a correr cuando cambia un caso o el dibujo del libro.
"""
import gzip
import json
import pathlib
import re
import sys

LABSIM = pathlib.Path(__file__).resolve().parents[2]
LIBRO = pathlib.Path.home() / 'Escritorio/Proyectos/libro-orl'
CASOS = LIBRO / 'material/casos'
sys.path.insert(0, str(LIBRO / 'material/figuras'))

import hacer_figuras  # noqa: E402
from motor import audio_supra  # noqa: E402
from motor import estilo as E  # noqa: E402
from motor.datos import cargar_caso  # noqa: E402
from motor.svg import Svg  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from procedimientos import capitulo, procedimiento  # noqa: E402

# Los mismos capítulos que sql_practica.py deja fuera (vestibulares y nasales)
FUERA = {21, 22, 23, 24, 25, 26, 27, 31, 32, 35, 36, 37, 38}
# Figura del libro -> examen (como lo nombra el procedimiento) y archivo.
# Acumetría y campo libre no: no son un informe que el paciente traiga.
EXAMEN = {
    'audiosupra': 'Audiometría', 'audiograma': 'Audiometría', 'logoaudiometria': 'Audiometría',
    'impedancia': 'Impedanciometría', 'timpanograma': 'Impedanciometría', 'reflejos': 'Impedanciometría',
    'teoae': 'EOA', 'dpoae': 'EOA', 'abr': 'PEATC', 'ecochg': 'ECochG', 'vemp': 'VEMP',
    'cortical': 'Corticales',
}
ARCHIVO = {'Audiometría': 'audiometria', 'Impedanciometría': 'impedanciometria', 'EOA': 'eoa',
           'PEATC': 'peatc', 'ECochG': 'ecochg', 'VEMP': 'vemp', 'Corticales': 'corticales',
           'Tamizaje': 'tamizaje'}
# Figura por defecto de un examen que el libro no dibuja de ese paciente
POR_DEFECTO = {'Impedanciometría': [{'tipo': 'impedancia'}], 'PEATC': [{'tipo': 'abr', 'niveles': [80, 60, 40]}]}

ids = json.loads((pathlib.Path(__file__).with_name('ids_libro.json')).read_text(encoding='utf-8'))
salida = LABSIM / 'resources/libro/previos'


def _specs():
    """(clave, ficha, origen, figuras) de cada caso de la práctica, el Tomo II
    primero: de ahí sale la figura de cada examen si el caso sale en varios."""
    tomo2 = sorted(CASOS.glob('cap[0-9][0-9]_*.json'))
    tomo1 = sorted(p for p in CASOS.glob('h[0-9]*_*.json'))
    for spec_path in tomo2 + tomo1:
        clave = spec_path.stem
        if clave.startswith('cap') and int(clave[3:5]) in FUERA:
            continue
        spec = json.loads(spec_path.read_text(encoding='utf-8'))
        if isinstance(spec['caso'], str):
            origen, ficha = spec['caso'], spec['caso'].split(':')[1]       # demo:34
        else:
            origen, ficha = f"archivo:{CASOS / 'generados' / f'{clave}.json'}", ids.get(clave)
        if ficha is not None:
            yield clave, ficha, origen, spec['figuras']


def _guardar(ruta, svg):
    (salida / ruta).write_bytes(gzip.compress(svg.encode('utf-8'), 9, mtime=0))


def _apilar(svgs, titulos=()):
    """Dos hojas una sobre otra (las emisiones: TEOAE y DPOAE en un informe).
    Cada una entra como un grupo desplazado, no como un <svg> dentro de otro:
    el lector de Qt (SVG Tiny) no dibuja los anidados y la hoja salía en blanco."""
    partes, alto, ancho = [], 0.0, 0.0
    for i, svg in enumerate(svgs):
        if i < len(titulos):
            # En el libro lo dice el pie de figura; en el informe, un rótulo
            partes.append(f'<text x="12" y="{alto + 15}" font-size="{E.T_TITULO}" font-weight="700" '
                          f'fill="{E.TINTA}" font-family="{E.FUENTE}">{titulos[i]}</text>')
            alto += 24
        raiz = re.match(r'<svg ([^>]*)>', svg)
        at = dict(re.findall(r'([\w-]+)="([^"]*)"', raiz.group(1)))
        w, h = float(at['width']), float(at['height'])
        vx, vy, vw, vh = (float(v) for v in at.get('viewBox', f'0 0 {w} {h}').split())
        cuerpo = svg[raiz.end():svg.rindex('</svg>')]
        cuerpo = re.sub(r'<metadata[^>]*>.*?</metadata>', '', cuerpo, flags=re.S)
        fuente = f' font-family="{at["font-family"]}"' if 'font-family' in at else ''
        partes.append(f'<g transform="translate(0,{alto}) scale({w / vw},{h / vh}) translate({-vx},{-vy})"{fuente}>'
                      f'{cuerpo}</g>')
        alto += h + 12
        ancho = max(ancho, w)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto - 12}" '
            f'viewBox="0 0 {ancho} {alto - 12}"><rect width="100%" height="100%" fill="#ffffff"/>'
            + ''.join(partes) + '</svg>')


def _hoja(caso, examen, figuras):
    if examen == 'Audiometría':
        # La hoja auditiva completa (audiograma, logo, supraliminares), aunque
        # el capítulo muestre solo el audiograma
        return audio_supra.dibujar(caso)
    if examen == 'Impedanciometría':
        f = next(f for f in figuras if f['tipo'] in ('impedancia', 'timpanograma'))
        return hacer_figuras.figura(caso, {'tipo': 'impedancia', 'sonda': f.get('sonda', 226)})
    if examen == 'EOA':
        return _apilar([hacer_figuras.figura(caso, {'tipo': t, 'tomo2': True}) for t in ('teoae', 'dpoae')],
                       ('Emisiones otoacústicas transitorias (TEOAE)', 'Productos de distorsión (DPOAE)'))
    f = next(f for f in figuras if EXAMEN.get(f['tipo']) == examen)
    return hacer_figuras.figura(caso, {**f, 'tomo2': True})


def tarjeta_tamizaje(prueba, od, oi):
    """Un tamizaje como lo entrega el equipo: el resultado de cada oído y nada
    más (no hay curva que mirar). Con los colores de oído del libro."""
    s = Svg(360, 128)
    s.texto(20, 28, prueba, tam=E.T_TITULO, color=E.TINTA, ancla='start', peso=700)
    for i, (lado, resultado) in enumerate((('OD', od), ('OI', oi))):
        x = 20 + i * 170
        s.rect(x, 46, 150, 62, E.LAVADO, extra='rx="8"')
        s.texto(x + 14, 68, E.NOMBRE_LADO[lado], tam=E.T_ROTULO, color=E.COLOR_LADO[lado], ancla='start', peso=700)
        bien = resultado.lower() in ('pasa', 'normal')
        s.texto(x + 14, 94, resultado.capitalize(), tam=13, color=E.TINTA if bien else E.COLOR_LADO[lado],
                ancla='start', peso=700)
    return s.svg()


def main():
    hojas = {}          # ficha -> {examen: (origen, figuras)}
    for clave, ficha, origen, figuras in _specs():
        de_la_ficha = hojas.setdefault(ficha, {})
        for f in figuras:
            examen = EXAMEN.get(f['tipo'])
            if examen and examen not in de_la_ficha:
                de_la_ficha[examen] = (clave, origen, [g for g in figuras if EXAMEN.get(g['tipo']) == examen])
    indice = {}
    solo = sys.argv[sys.argv.index('--examen') + 1] if '--examen' in sys.argv else None
    if '--solo-historia' in sys.argv or solo:
        # Las hojas de lo que traen ya están (dibujarlas tarda: el PEATC)
        viejo = json.loads((salida / 'indice.json').read_text(encoding='utf-8'))
        indice = {f: {'trae': v['trae']} for f, v in viejo.items() if v.get('trae')}
    for ficha, examenes in sorted(hojas.items(), key=lambda x: int(x[0])):
        if indice and not solo:
            break
        (salida / ficha).mkdir(parents=True, exist_ok=True)
        for examen, (clave, origen, figuras) in examenes.items():
            if solo and examen != solo:
                continue
            ruta = f'{ficha}/{ARCHIVO[examen]}.svgz'
            _guardar(ruta, _hoja(cargar_caso(origen), examen, figuras))
            indice.setdefault(ficha, {}).setdefault('trae', {})[examen] = ruta
            print(f'  {ruta:30} {clave}')
    # Qué trae en cada carpeta: lo que muestra la ficha del libro en ese
    # capítulo, más la audiometría, que va antes de todo lo demás. Un demo sale
    # en varias carpetas (el 34 en H2, H3, H7, H12 y el cap. 4): sin esto
    # traía a la de impedanciometría el VEMP de H12. La app quita lo que el
    # procedimiento nombra; la clave es el procedimiento, que es distinto en
    # cada carpeta del mismo paciente.
    for clave, ficha, _, figuras in _specs():
        tipos = [f['tipo'] for f in figuras]
        examenes = ['Audiometría'] + [EXAMEN[t] for t in tipos if t in EXAMEN]
        trae = indice.get(ficha, {}).get('trae', {})
        lista = [e for e in ARCHIVO if e in examenes and e in trae]
        if lista:
            indice[ficha].setdefault('por_procedimiento', {})[procedimiento(tipos, clave, capitulo(clave))] = lista
    origenes = {ficha: origen for _, ficha, origen, _ in _specs()}
    tabla = json.loads(pathlib.Path(__file__).with_name('historia_examenes.json').read_text(encoding='utf-8'))
    for h in tabla:
        ficha, examen = h['ficha'], h['examen']
        trae = indice.get(ficha, {}).get('trae', {})
        ruta = f"{ficha}/historia_{-h['dias']}_{ARCHIVO[examen]}.svgz"
        if h['hoja'] == 'tamizaje':
            svg = tarjeta_tamizaje(h['prueba'], h['OD'], h['OI'])
        elif h['hoja'] == 'actual' and examen in trae:
            ruta, svg = trae[examen], None
        else:
            origen = (origenes[ficha] if h['hoja'] == 'actual'
                      else f"archivo:{CASOS / 'generados' / (h['caso'] + '.json')}")
            figuras = hojas.get(ficha, {}).get(examen, (None, None, POR_DEFECTO.get(examen, [])))[2]
            svg = _hoja(cargar_caso(origen), examen, figuras)
        if svg is not None:
            (salida / ficha).mkdir(parents=True, exist_ok=True)
            _guardar(ruta, svg)
        entrada = {'dias': h['dias'], 'examen': examen, 'svg': ruta}
        if h.get('revisar'):
            entrada['revisar'] = True
        indice.setdefault(ficha, {}).setdefault('historia', []).append(entrada)
        print(f"  {ruta:34} {h['hoja']}")
    (salida / 'indice.json').write_text(json.dumps(indice, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(len(indice), 'fichas,', sum(len(v.get('trae', {})) for v in indice.values()), 'hojas que traen,',
          len(tabla), 'de la historia')


if __name__ == '__main__':
    main()
