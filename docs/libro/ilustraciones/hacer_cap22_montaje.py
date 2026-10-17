#!/usr/bin/env python3
"""Arma cap22-apogeotropico-sim.png con dos capturas de labyrinthus3d (giro
supino en un paciente simulado con cupulolitiasis del canal lateral derecho,
vista desde arriba). Las capturas se sacan con hacer_h18_capturas.py:

    ... hacer_h18_capturas.py rolido der lat cupulolitiasis <prefijo> "desde arriba" 12

    python3 hacer_cap22_montaje.py <carpeta> <prefijo>"""
import pathlib
import sys

from hacer_h18_montajes import montaje, recuadro

carpeta, pre = pathlib.Path(sys.argv[1]), sys.argv[2]
CAJA = (590, 345, 840, 610)
tiles = [recuadro(carpeta / f'{pre}_1_desde_arriba.png', CAJA, 1,
                  'Cabeza girada 90° a la derecha (oído derecho abajo): nistagmo débil, hacia la izquierda.', con_ojo=True, alto=420, dy=38),
         recuadro(carpeta / f'{pre}_3_desde_arriba.png', CAJA, 2,
                  'Cabeza girada 90° a la izquierda: nistagmo más fuerte, hacia la derecha.', con_ojo=True, alto=420, dy=38)]
montaje(tiles, 2, 'cap22-apogeotropico-sim.png')
