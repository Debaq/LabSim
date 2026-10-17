#!/usr/bin/env python3
"""Dibuja la ilustración del capítulo 19 (el paciente que no calza):

    cap19-stenger.svg  el efecto Stenger con dos barras de nivel de sensación por oído

SVG propio, no IA. Los niveles son ilustrativos (esquema, no datos)."""
import pathlib

TINTA, TENUE, GRILLA = '#24101a', '#8a8a90', '#e7e5e0'
ROJO, AZUL, AVISO, OK = '#c0392b', '#2a55b0', '#c62f3a', '#21796c'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
out = []


def t(x, y, s, size=11, color=TINTA, anchor='middle', peso=400):
    out.append(f'<text x="{x}" y="{y}" {F} font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{peso}">{s}</text>')


def panel(x0, titulo, umbral_od, tono_od, umbral_oi, tono_oi, resultado, color):
    """Cada oído: columna con su umbral verdadero (línea) y el tono (barra sobre el umbral = nivel de sensación)."""
    t(x0 + 150, 28, titulo, 13, TINTA, 'middle', 700)
    base, alto = 250, 180          # y de 0 dB y alto de la escala 0-100 dB
    esc = alto / 100
    for dB in (0, 50, 100):
        y = base - dB * esc
        out.append(f'<line x1="{x0 + 10}" y1="{y}" x2="{x0 + 290}" y2="{y}" stroke="{GRILLA}"/>')
        t(x0 + 4, y + 4, str(dB), 9, TENUE, 'end')
    for cx, nombre, col, umbral, tono in ((x0 + 90, 'Oído derecho', ROJO, umbral_od, tono_od),
                                          (x0 + 220, 'Oído izquierdo', AZUL, umbral_oi, tono_oi)):
        t(cx, base + 22, nombre, 11, col, 'middle', 700)
        yt, yu = base - tono * esc, base - umbral * esc
        out.append(f'<rect x="{cx - 22}" y="{yt}" width="44" height="{base - yt}" fill="{col}" fill-opacity=".25" stroke="{col}"/>')
        out.append(f'<line x1="{cx - 36}" y1="{yu}" x2="{cx + 36}" y2="{yu}" stroke="{TINTA}" stroke-width="2.5" stroke-dasharray="5 3"/>')
        sl = tono - umbral
        if sl > 0:
            out.append(f'<line x1="{cx + 30}" y1="{yu}" x2="{cx + 30}" y2="{yt}" stroke="{col}" stroke-width="1.5"/>')
            t(cx + 34, (yu + yt) / 2 + 4, f'{sl} dB SL', 10, col, 'start', 700)
        else:
            t(cx, yt - 8, 'bajo el umbral', 10, TENUE)
    t(x0 + 150, base + 52, resultado, 11, color, 'middle', 700)


panel(30, 'Pérdida real en el OD', 80, 70, 0, 10, 'Se oye en el OI: responde (Stenger negativo)', OK)
panel(360, 'Pérdida no orgánica en el OD', 0, 70, 0, 10, 'Se oye en el OD: no responde (Stenger positivo)', AVISO)
t(340, 335, 'Línea punteada: umbral verdadero. Barra: nivel del tono. El tono que gana en nivel de sensación (SL) es el que se oye.', 10, TENUE)
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 350" width="680" height="350">'
       f'<rect width="680" height="350" fill="#fff"/>' + ''.join(out) + '</svg>')
(pathlib.Path(__file__).parent / 'cap19-stenger.svg').write_text(svg, encoding='utf-8')
