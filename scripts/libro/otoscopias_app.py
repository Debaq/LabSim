"""Fotos de otoscopía de los pacientes del libro, dentro de la app.

    QT_QPA_PLATFORM=offscreen ~/.local/share/labsim/libro-venv/bin/python -I scripts/libro/otoscopias_app.py

Escribe resources/libro/otoscopias/<ficha>_<od|oi>.jpg (fase 0, a lo más 600
px, JPEG 78) desde material/otoscopias/<caso>_<od|oi>.jpg del libro: las
mismas que se subieron a prod. Las usa el modo invitado, que no puede
pedirlas a la API (core/invitado.foto_otoscopia). Un paciente que sale en
varios capítulos lleva la del primero (el Tomo II antes que el I).
"""
import json
import pathlib
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

AQUI = pathlib.Path(__file__).resolve().parent
LABSIM = AQUI.parents[1]
LIBRO = pathlib.Path.home() / 'Escritorio/Proyectos/libro-orl'
FOTOS = LIBRO / 'material/otoscopias'
LADO_MAX = 600


def main():
    QApplication.instance() or QApplication(sys.argv)
    ids = json.loads((AQUI / 'ids_libro.json').read_text(encoding='utf-8'))
    claves = {}                              # ficha -> claves del libro, en orden
    for spec in sorted((LIBRO / 'material/casos').glob('cap[0-9][0-9]_*.json')) + \
            sorted((LIBRO / 'material/casos').glob('h[0-9]*_*.json')):
        caso = json.loads(spec.read_text(encoding='utf-8'))['caso']
        ficha = caso.split(':')[1] if isinstance(caso, str) else ids.get(spec.stem)
        if ficha is not None:
            claves.setdefault(ficha, []).append(spec.stem)
    salida = LABSIM / 'resources/libro/otoscopias'
    salida.mkdir(parents=True, exist_ok=True)
    hechas = 0
    for ficha, lista in sorted(claves.items(), key=lambda x: int(x[0])):
        for lado in ('od', 'oi'):
            origen = next((FOTOS / f'{c}_{lado}.jpg' for c in lista if (FOTOS / f'{c}_{lado}.jpg').exists()), None)
            if origen is None:
                continue
            imagen = QImage(str(origen))
            if max(imagen.width(), imagen.height()) > LADO_MAX:
                imagen = imagen.scaled(LADO_MAX, LADO_MAX, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
            imagen.save(str(salida / f"{ficha}_{lado}.jpg"), "JPG", 78)
            hechas += 1
    peso = sum(f.stat().st_size for f in salida.glob('*.jpg'))
    print(f'{hechas} fotos, {peso // 1024} KB')


if __name__ == '__main__':
    main()
