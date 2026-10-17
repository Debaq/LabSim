#!/usr/bin/env python3
"""Ilustraciones del capítulo 28 (El primer audífono).

    cap28-campo-dinamico.svg   el campo dinámico del OD del caso 28.2 (umbral y LDL leídos del caso
                               armado en casos/generados/cap28_reacio.json) frente a los ~30 dB del habla
    cap28-cros.svg             esquema de la sombra de la cabeza y del encaminamiento CROS (no son datos)

SVG propios, no IA. El esquema del CROS es un dibujo de principio, sin escala; el del campo
dinámico usa los números del caso y los ~30 dB del habla de Dillon (2012) como orden de magnitud."""
import json
import math
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
LIBRO = AQUI.parent
sys.path.insert(0, str(LIBRO / 'figuras'))
from motor import estilo as E  # noqa: E402
from motor.svg import Svg  # noqa: E402

FREC = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000]
TECHO = 120


def campo_dinamico():
    d = json.loads((LIBRO / 'casos' / 'generados' / 'cap28_reacio.json').read_text(encoding='utf-8'))['data']
    umbral = {f: d['Aerea'][i][0] for i, f in enumerate(FREC)}
    ldl = {f: d['LDL'][i][0] for i, f in enumerate(FREC)}
    cols = [500, 1000, 2000, 3000, 4000]
    ml, mt, pw, ph = 52, 40, 330, 250
    s = Svg(ml + pw + 150, mt + ph + 62)

    def Y(db):
        return mt + db / TECHO * ph

    def X(i):
        return ml + 30 + i * (pw - 40) / (len(cols) - 1)

    s.texto(ml - 40, 16, 'Campo dinámico del OD del caso 28.2: del umbral al LDL', E.T_TITULO, E.TINTA, 'start', 700)
    for db in range(0, TECHO + 1, 20):
        s.linea(ml, Y(db), ml + pw, Y(db), E.GRILLA_FUERTE if db == 0 else E.GRILLA, 1)
        s.texto(ml - 6, Y(db) + 3, db, E.T_EJE, E.TENUE, 'end')
    s.texto(14, mt + ph / 2, 'dB HL', E.T_EJE, E.TENUE, 'middle', 400, f'transform="rotate(-90 14 {mt + ph / 2})"')
    ancho = 34
    for i, f in enumerate(cols):
        x = X(i)
        u, l = umbral[f], ldl[f]
        sin_ldl = l >= TECHO
        # lo que no se oye (de 0 al umbral) y el campo dinámico (del umbral al LDL)
        s.rect(x - ancho / 2, Y(0), ancho, Y(u) - Y(0), E.LAVADO, E.GRILLA_FUERTE, 0.6)
        s.rect(x - ancho / 2, Y(u), ancho, Y(l) - Y(u), '#f1c9cc', E.OD, 1.2)
        s.texto(x, Y(u) + (Y(l) - Y(u)) / 2 + 3, (f'≥ {l - u}' if sin_ldl else f'{l - u}'), E.T_ROTULO, E.TINTA, 'middle', 700)
        s.texto(x, Y(u) - 5, u, E.T_CHICO, E.OD, 'middle', 600)
        s.texto(x, mt + ph + 26, f'{f / 1000:g} k'.replace('.', ','), E.T_EJE, E.TENUE)
        if sin_ldl:
            s.texto(x, Y(l) + 11, 'sin LDL', E.T_CHICO, E.TENUE)
        else:
            s.texto(x, Y(l) + 11, l, E.T_CHICO, E.OD, 'middle', 600)
    s.texto(ml + pw / 2, mt + ph + 46, 'Frecuencia (Hz)', E.T_EJE, E.TENUE)
    # el habla, a la misma escala: un tramo de 30 dB
    xb = ml + pw + 24
    y0 = Y(umbral[3000])
    s.linea(xb, y0, xb, y0 + 30 / TECHO * ph, E.TINTA, 1.6)
    s.linea(xb - 4, y0, xb + 4, y0, E.TINTA, 1.6)
    s.linea(xb - 4, y0 + 30 / TECHO * ph, xb + 4, y0 + 30 / TECHO * ph, E.TINTA, 1.6)
    s.texto(xb + 10, y0 + 30 / TECHO * ph / 2 - 4, 'El habla ocupa', E.T_ROTULO, E.TINTA, 'start', 700)
    s.texto(xb + 10, y0 + 30 / TECHO * ph / 2 + 8, 'unos 30 dB', E.T_ROTULO, E.TINTA, 'start', 700)
    s.texto(xb + 10, y0 + 30 / TECHO * ph / 2 + 22, '(misma escala)', E.T_CHICO, E.TENUE, 'start')
    s.texto(ml + pw + 4, Y(0) + 10, 'campo dinámico en dB', E.T_CHICO, E.OD, 'start', 600)
    s.texto(ml + pw + 4, Y(0) + 21, '= LDL − umbral', E.T_CHICO, E.OD, 'start', 600)
    return s


def cabeza(s, cx, cy, r, sordo='der'):
    """Vista desde arriba: nariz hacia arriba, oído derecho del paciente a la derecha del dibujo."""
    s.circulo(cx, cy, r, E.TINTA_2, '#fbfaf8', 1.4)
    s.camino(f'M{cx - 7},{cy - r + 1} L{cx},{cy - r - 12} L{cx + 7},{cy - r + 1}', E.TINTA_2, 1.4)
    for lado, dx in (('izq', -1), ('der', 1)):
        malo = lado == sordo
        col = E.OD if malo else E.OI
        s.crudo(f'<ellipse cx="{cx + dx * (r + 4)}" cy="{cy}" rx="5" ry="12" fill="#ffffff" stroke="{col}" stroke-width="2"/>')
        s.texto(cx + dx * (r + 4), cy + 28, 'OD' if lado == 'der' else 'OI', 11, col, 'middle', 700)
        s.texto(cx + dx * (r + 4), cy + 39, 'sordo' if malo else 'normal', 9.5, col)


def fuente(s, x, y, color=E.TINTA):
    s.circulo(x, y, 9, color, '#ffffff', 1.6)
    s.circulo(x, y, 3, color, color, 1)


def ondas(s, x0, y0, x1, y1, color, n=3, dash=None):
    s.trazo([(x0, y0), (x1, y1)], color, 1.4, 1.0, dash)


def cros():
    TC, TR, TT = 9.5, 11, 12.5
    s = Svg(600, 250)
    r = 46
    # A: sin audífono
    cxa, cy = 120, 120
    s.texto(10, 16, 'A · Sin audífono: la cabeza hace sombra', TT, E.TINTA, 'start', 700)
    cabeza(s, cxa, cy, r)
    fuente(s, cxa + 98, cy - 4)
    s.texto(cxa + 98, cy - 20, 'voz', TC, E.TINTA)
    # camino corto hacia el oído sordo y rodeo hacia el sano
    s.trazo([(cxa + 88, cy - 4), (cxa + r + 12, cy - 2)], E.OD, 1.6)
    s.camino(f'M{cxa + 92},{cy - 10} Q{cxa},{cy - r - 44} {cxa - r - 14},{cy - 6}', E.OI, 1.6)
    s.texto(cxa, cy - r - 30, 'rodea la cabeza: llega', TC, E.OI, 'middle', 600)
    s.texto(cxa, cy - r - 20, 'más débil, sobre todo en agudos', TC, E.OI, 'middle', 600)
    s.texto(cxa, cy + r + 40, 'el oído sano oye poco a quien habla', TC, E.TENUE)
    s.texto(cxa, cy + r + 50, 'desde el lado sordo', TC, E.TENUE)
    # B: CROS
    cxb = 410
    s.texto(290, 16, 'B · CROS: el micrófono va en el lado sordo', TT, E.TINTA, 'start', 700)
    cabeza(s, cxb, cy, r)
    fuente(s, cxb + 140, cy - 4)
    s.texto(cxb + 140, cy - 20, 'voz', TC, E.TINTA)
    s.trazo([(cxb + 130, cy - 4), (cxb + r + 17, cy - 3)], E.OD, 1.6)
    # micrófono en el OD y receptor en el OI, con el enlace por arriba (sin cable por la cabeza)
    s.rect(cxb + r + 9, cy - 9, 7, 18, E.OD, E.OD, 1)
    s.rect(cxb - r - 16, cy - 9, 7, 18, E.OI, E.OI, 1)
    s.camino(f'M{cxb + r + 12},{cy - 10} Q{cxb},{cy - r - 40} {cxb - r - 12},{cy - 10}', E.CAMPO_LIBRE, 1.8)
    s.texto(cxb, cy - r - 26, 'enlace inalámbrico', TC, E.CAMPO_LIBRE, 'middle', 600)
    s.texto(cxb + r + 24, cy - 9, 'micrófono', TC, E.OD, 'start', 600)
    s.texto(cxb - r - 28, cy + 4, 'receptor', TC, E.OI, 'end', 600)
    s.texto(cxb, cy + r + 40, 'el sonido del lado sordo se oye', TC, E.TENUE)
    s.texto(cxb, cy + r + 50, 'por el oído sano (conducto abierto)', TC, E.TENUE)
    return s


if __name__ == '__main__':
    for nombre, f in (('cap28-campo-dinamico.svg', campo_dinamico), ('cap28-cros.svg', cros)):
        (AQUI / nombre).write_text(f().svg(), encoding='utf-8')
        print(nombre)
