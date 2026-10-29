"""Audiometría previa de los pacientes del libro, como la dibuja el libro.

    python3 -I scripts/libro/previos.py

Escribe resources/libro/previos/<ficha>.svg con la hoja auditiva del libro
(audiograma con Fowler, logoaudiometría y supraliminares) de cada paciente
del Tomo II que la tiene. La ficha clínica de la práctica libre la muestra
como una atención previa cuando el procedimiento del paciente no incluye la
audiometría: el paciente llega con ella hecha (ver core/ficha.py y
docs/decisiones.md, "Audiometría previa en la práctica libre").

Sale de los mismos datos que se cargaron en el backend (generados/, no
propios/: sql_practica.py carga los generados) y de los demo 33-42. Se
vuelve a correr cuando cambia un caso o el dibujo del libro.
"""
import json
import pathlib
import sys

LABSIM = pathlib.Path(__file__).resolve().parents[2]
LIBRO = pathlib.Path.home() / 'Escritorio/Proyectos/libro-orl'
CASOS = LIBRO / 'material/casos'
sys.path.insert(0, str(LIBRO / 'material/figuras'))

from motor import audio_supra  # noqa: E402
from motor.datos import cargar_caso  # noqa: E402

# Los mismos capítulos que sql_practica.py deja fuera (vestibulares y nasales)
FUERA = {21, 22, 23, 24, 25, 26, 27, 31, 32, 35, 36, 37, 38}
ids = json.loads((pathlib.Path(__file__).with_name('ids_libro.json')).read_text(encoding='utf-8'))
salida = LABSIM / 'resources/libro/previos'
salida.mkdir(parents=True, exist_ok=True)

hechas = {}
for spec_path in sorted(CASOS.glob('cap[0-9][0-9]_*.json')):
    clave = spec_path.stem
    if int(clave[3:5]) in FUERA:
        continue
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    if not any(f['tipo'] == 'audiosupra' for f in spec['figuras']):
        continue
    if isinstance(spec['caso'], str):
        origen, ficha = spec['caso'], spec['caso'].split(':')[1]       # demo:34
    else:
        origen, ficha = f"archivo:{CASOS / 'generados' / f'{clave}.json'}", ids.get(clave)
    if ficha is None:
        print('sin ficha en el backend:', clave)
        continue
    if ficha in hechas:
        continue          # un demo que sale en varios capítulos: son los mismos datos
    (salida / f'{ficha}.svg').write_text(audio_supra.dibujar(cargar_caso(origen)), encoding='utf-8')
    hechas[ficha] = clave

print(len(hechas), 'audiometrías en', salida.relative_to(LABSIM))
