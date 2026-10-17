#!/usr/bin/env python3
"""Ilustracion del capitulo 14:

    cap14-temperatura.svg   cuanto se alarga el interpico I-V al enfriar el cuerpo

Esquema calculado, no datos de un paciente: parte de un I-V de 4,1 ms a 36 C y aplica la regla
publicada de Markand y cols. (1987): el I-V crece cerca de 7 % por cada grado que baja la
temperatura y se duplica hacia los 26 C. Todas las ondas siguen presentes sobre 23 C y faltan
bajo 20 C (mismos autores)."""
import pathlib

TINTA, TENUE, GRILLA, ROJO, AZUL = '#24101a', '#8a8a90', '#e7e5e0', '#c62f3a', '#2a5d9f'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent
W, H = 640, 330
X0, X1, Y0, Y1 = 70, 600, 270, 40          # ejes en pixeles
T_MIN, T_MAX, L_MIN, L_MAX = 24.0, 37.0, 3.0, 9.0


def px(t):
    return X1 - (t - T_MIN) / (T_MAX - T_MIN) * (X1 - X0)   # la temperatura baja hacia la derecha


def py(l):
    return Y0 - (l - L_MIN) / (L_MAX - L_MIN) * (Y0 - Y1)


o = []
t = lambda x, y, s, size=11, color=TINTA, anchor='middle', peso=400: o.append(
    f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{peso}">{s}</text>')
l = lambda x1, y1, x2, y2, color=GRILLA, w=1, dash='': o.append(
    f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}"'
    + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')

for T in range(24, 38, 2):
    l(px(T), Y0, px(T), Y1)
    t(px(T), Y0 + 16, f'{T}', 10, TENUE)
for L in range(3, 10):
    l(X0, py(L), X1, py(L))
    t(X0 - 8, py(L) + 4, f'{L}', 10, TENUE, 'end')
t((X0 + X1) / 2, Y0 + 36, 'Temperatura corporal (°C)', 11, TENUE)
o.append(f'<text transform="translate(22 {(Y0 + Y1) / 2}) rotate(-90)" {F} font-size="11" fill="{TENUE}" text-anchor="middle">Interpico I-V (ms)</text>')

pts = []
T = 36.0
while T >= 26.0 - 1e-9:
    pts.append((px(T), py(4.1 * 1.07 ** (36 - T))))
    T -= 0.25
o.append('<polyline points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
         + f'" fill="none" stroke="{ROJO}" stroke-width="2.4" stroke-linejoin="round"/>')
for T in (36, 33, 30, 26):
    x, y = px(T), py(4.1 * 1.07 ** (36 - T))
    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#fff" stroke="{ROJO}" stroke-width="2"/>')
    t(x, y - 10, f'{4.1 * 1.07 ** (36 - T):.1f}'.replace('.', ','), 10, ROJO, 'middle', 600)

# Zona donde ya no hay onda (bajo 20 C) fuera del eje: se avisa con texto
t(px(36), py(3.4), 'Normotermia', 10, TENUE)
t(px(26), py(8.7), 'El I-V se duplica', 10, ROJO)
t(px(30.5), py(3.55), 'Sobre 23 °C siguen todas las ondas;', 10, AZUL, 'start')
t(px(30.5), py(3.2), 'bajo 20 °C no queda ninguna.', 10, AZUL, 'start')
t(X0, 24, 'Esquema: regla de ~7 % por °C desde 4,1 ms a 36 °C (Markand y cols., 1987)', 10.5, TINTA, 'start', 600)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
       f'<rect width="{W}" height="{H}" fill="#fff"/>' + ''.join(o) + '</svg>')
(AQUI / 'cap14-temperatura.svg').write_text(svg, encoding='utf-8')
print('cap14-temperatura.svg')
