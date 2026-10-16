"""Audiometría de campo libre: sin audífono (S) y, si se pide, con audífono (A).

LabSim todavía no mide en campo libre (H8), así que la figura se calcula del
caso con la regla que el capítulo explica: el parlante le habla a la cabeza y
contesta el oído mejor, frecuencia por frecuencia. Es la vía aérea del mejor
de los dos oídos, redondeada a 5 dB como la anota el audiómetro.

Los umbrales con audífono NO salen del caso: dependen del audífono y de su
ajuste. La ganancia funcional (dB por frecuencia) la declara el capítulo, y
la figura solo la resta del umbral sin audífono.

Símbolos: S sin audífono y A con audífono, en verde como en el laboratorio
(contesta el oído mejor, no uno en particular). Con un solo audífono puesto
(audifono='OD' u 'OI'), la A va en rojo o azul según el lado del audífono.
"""
import math

from . import estilo as E
from .audiograma import (FRECUENCIAS, LIMITE_NORMAL, NIVEL_MAXIMO, OCTAVA_PX, ROTULO,
                         SIN_RESPUESTA, _flecha, _num, _tramos)
from .datos import por_oido
from .svg import Svg

# Las del juego condicionado y la VRA (AAA 2020): sin 125 ni 8 kHz, que los
# parlantes de una sala no reproducen bien.
FRECUENCIAS_CL = [250, 500, 1000, 2000, 3000, 4000, 6000]


def umbrales_sin_audifono(caso):
    """{Hz: dB HL o None}: el oído mejor en cada frecuencia (None = no responde)."""
    aerea = por_oido(caso['Aerea'])
    out = {}
    for i, f in enumerate(FRECUENCIAS):
        if f not in FRECUENCIAS_CL:
            continue
        vals = [v for v in (_num(aerea['OD'][i]), _num(aerea['OI'][i]))
                if v is not None and v < SIN_RESPUESTA]
        out[f] = 5 * round(min(vals) / 5) if vals else None
    return out


def dibujar(caso, ganancia=None, audifono=None):
    """ganancia: {Hz: dB de ganancia funcional}; sin ella, solo la curva S.
    audifono: 'OD' u 'OI' si se evaluó un solo audífono (la A toma su color);
    None, los dos o binaural (verde)."""
    color_a = E.COLOR_LADO.get(audifono, E.CAMPO_LIBRE)
    sin = umbrales_sin_audifono(caso)
    con = None
    if ganancia:
        con = {f: (max(-10, v - ganancia[f]) if v is not None and f in ganancia else None)
               for f, v in sin.items()}

    db_px = OCTAVA_PX / 20
    x_min, x_max = 125, 8000
    pw, ph = math.log2(x_max / x_min) * OCTAVA_PX, 130 * db_px
    # Con la curva A, la leyenda va en una segunda línea bajo el título.
    ml, mt, mb = 36, (42 if con is not None else 30), 40
    s = Svg(ml + pw + 14, mt + ph + mb)

    def X(f):
        return ml + math.log2(f / x_min) * OCTAVA_PX

    def Y(db):
        return mt + (max(-10.0, min(float(NIVEL_MAXIMO), db)) + 10) * db_px

    s.rect(ml, Y(-10), pw, Y(LIMITE_NORMAL) - Y(-10), E.LAVADO)
    for db in range(-10, 121, 10):
        fuerte = db in (0, LIMITE_NORMAL)
        s.linea(ml, Y(db), ml + pw, Y(db), E.GRILLA_FUERTE if fuerte else E.GRILLA,
                1 if (fuerte or db % 20 == 0) else 0.5)
        if db % 20 == 0:
            s.texto(ml - 7, Y(db) + 3, db, E.T_EJE, E.TENUE, 'end')
    for f in FRECUENCIAS:
        mayor = f not in (3000, 6000)
        s.linea(X(f), Y(-10), X(f), Y(120), E.GRILLA, 1 if mayor else 0.5)
        s.texto(X(f), Y(120) + 14, ROTULO.get(f, f), E.T_EJE if mayor else E.T_CHICO,
                E.TENUE if mayor else E.MUY_TENUE)
    s.texto(ml, (mt - 22) if con is not None else (mt - 12), 'Campo libre', E.T_TITULO, E.TINTA, 'start', 600)

    for curva, letra, guiones, color in ((sin, 'S', None, E.CAMPO_LIBRE), (con, 'A', '4 3', color_a)):
        if curva is None:
            continue
        pts = [(X(f), Y(v)) if v is not None else None for f, v in sorted(curva.items())]
        for tramo in _tramos(pts):
            s.trazo(tramo, color, 1.2, guiones=guiones)
        for f, v in sorted(curva.items()):
            y = Y(NIVEL_MAXIMO if v is None else v)
            s.circulo(X(f), y, 5.2, E.PAPEL, E.PAPEL, 0)
            s.texto(X(f), y + 3.2, letra, E.T_ROTULO, color, peso=700)
            s.ancla(f'{letra} {f}', X(f), y)
            if v is None:
                _flecha(s, X(f), y, color, 1)

    if con is not None:
        lado = {'OD': ' (audífono OD)', 'OI': ' (audífono OI)'}.get(audifono, '')
        s.texto(ml, mt - 8, f'S sin audífono · A con audífono{lado}', E.T_CHICO, E.TENUE, 'start')
    s.texto(14, mt + ph / 2, 'dB HL', E.T_EJE, E.TENUE,
            extra=f'transform="rotate(-90 14 {mt + ph / 2:.1f})"')
    s.texto(s.ancho / 2, mt + ph + 34, 'Frecuencia (Hz)', E.T_EJE, E.TENUE)
    return s.svg()
