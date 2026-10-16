#!/usr/bin/env python3
"""Ilustración H8.2: campo libre con y sin audífonos sobre la zona del habla.

Usa el motor del libro (figuras/motor/campo_libre.py) con el caso de Adrián
(cap. 10, GJB2) y la misma ganancia funcional que declara ese capítulo: S y A
en verde, como se anotan en campo libre (contesta el oído mejor)."""
import json
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / 'figuras'))
from motor import campo_libre  # noqa: E402
from motor.datos import cargar_caso  # noqa: E402

GANANCIA = {250: 25, 500: 35, 1000: 40, 2000: 45, 3000: 45, 4000: 50, 6000: 45}   # la de cap. 10

caso = cargar_caso(f"archivo:{AQUI.parent / 'casos' / 'generados' / 'cap10_gjb2.json'}")
svg = campo_libre.dibujar(caso, ganancia=GANANCIA, banana=True)
(AQUI / 'h08-campo-libre-audifono.svg').write_text(svg, encoding='utf-8')
print('h08-campo-libre-audifono.svg')
