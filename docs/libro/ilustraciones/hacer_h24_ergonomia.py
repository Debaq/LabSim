#!/usr/bin/env python3
"""Dibuja el esquema de ergonomía del examinador de H24:

    h24-ergo-puesto.svg   A) puesto sentado en cabina/consola con los umbrales de postura del protocolo TMERT (v3);
                          B) examen de un niño: agachado (a evitar) frente a sentado a su altura (a preferir)

SVG propio, no IA. Los ángulos (cuello <= 25 grados, rodilla entre 90 y 135, brazo sin apoyo < 20 grados) son los
criterios de "condición aceptable" del Protocolo de Vigilancia Ocupacional TMERT v3 (MINSAL, Res. Ex. 1697/2025,
tabla III); las figuras son esquemas, no medidas."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h24 import Lienzo, TINTA, TENUE, GRILLA, FUERTE, ROJO, AZUL, VERDE, NARANJA  # noqa: E402


def cuerpo(c, pts, color=TINTA, w=3.2):
    """Segmentos del cuerpo (lista de puntos), con extremos redondeados."""
    c.poli(pts, color, w)


def cabeza(c, x, y, r=15, color=TINTA):
    c.circ(x, y, r, '#fff', color, 2.6)


def arco(c, cx, cy, r, a0, a1, color):
    """Arco de a0 a a1 grados (0 = derecha, antihorario negativo en pantalla) alrededor de (cx, cy)."""
    import math
    p0 = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
    p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
    barrido = 1 if a1 > a0 else 0
    c.out.append(f'<path d="M{p0[0]:.1f},{p0[1]:.1f} A{r},{r} 0 0 {barrido} {p1[0]:.1f},{p1[1]:.1f}" '
                 f'fill="none" stroke="{color}" stroke-width="1.8"/>')


def guia(c, x1, y1, x2, y2, color=TENUE):
    c.l(x1, y1, x2, y2, color, 1, '3 3')


def esquema():
    c = Lienzo(820, 350)
    suelo = 300

    # ----------------------------------------------------------- A) puesto sentado
    c.t(14, 20, 'A. Puesto sentado (cabina o consola)', 10.5, TINTA, 'start', 700)
    c.l(10, suelo, 345, suelo, FUERTE, 2)
    # silla: asiento, respaldo y pie
    c.l(88, 232, 150, 232, TENUE, 4)
    c.l(88, 232, 80, 150, TENUE, 4)
    c.l(118, 232, 118, suelo, TENUE, 3)
    c.l(100, suelo, 136, suelo, TENUE, 3)
    # mesa y pantalla
    c.rect(158, 192, 187, 7, '#e7e5e0', FUERTE, 1)
    c.l(190, 199, 190, suelo, FUERTE, 3)
    c.l(330, 199, 330, suelo, FUERTE, 3)
    c.rect(278, 112, 9, 64, '#fff', TINTA, 1.6)               # pantalla de lado
    c.l(280, 176, 280, 192, TENUE, 3)
    # cuerpo: cadera (104,224) rodilla (176,224) tobillo (176,294) punta (204,294)
    cuerpo(c, [(104, 224), (176, 224), (176, 294), (204, 294)])
    cuerpo(c, [(104, 224), (108, 142)])                         # tronco
    cuerpo(c, [(108, 142), (118, 120)], w=3)                    # cuello
    cabeza(c, 126, 104, 16)
    c.circ(134, 101, 1.8, TINTA, None)                          # ojo
    cuerpo(c, [(108, 146), (122, 190), (190, 189)])             # brazo: hombro, codo (apoyado), mano
    # mirada hacia la pantalla
    c.l(136, 101, 276, 124, VERDE, 1.4, '5 3')
    # ángulos
    guia(c, 108, 146, 108, 96)
    arco(c, 108, 146, 40, -90, -66, VERDE)
    c.t(40, 50, 'cuello ≤ 25°', 9, VERDE, 'start', 700)
    c.l(84, 54, 114, 100, VERDE, 1)
    arco(c, 176, 224, 22, 90, 180, VERDE)
    c.t(214, 262, 'rodilla 90°-135°', 9, VERDE, 'start', 700)
    c.l(212, 258, 190, 240, VERDE, 1)
    for i, t in enumerate(('pantalla de frente,', 'borde superior a la', 'altura de los ojos')):
        c.t(338, 62 + 12 * i, t, 9, TINTA, 'end')
    c.l(300, 86, 284, 112, TENUE, 1)
    for i, t in enumerate(('antebrazo apoyado,', 'hombros relajados')):
        c.t(152, 164 + 12 * i, t, 9, TINTA, 'start')
    for i, t in enumerate(('respaldo que', 'sostiene la', 'curva lumbar')):
        c.t(70, 160 + 12 * i, t, 9, TINTA, 'end')
    c.t(176, 322, 'pies apoyados; tronco y cuello simétricos, sin giro', 9, TENUE)

    # ----------------------------------------------------------- B) niño
    c.t(380, 20, 'B. Examen de un niño sentado frente a ti', 10.5, TINTA, 'start', 700)
    c.l(372, suelo, 812, suelo, FUERTE, 2)

    def nino(x):
        c.l(x + 100, 250, x + 160, 250, TENUE, 4)                 # silla del niño
        c.l(x + 104, 250, x + 104, suelo, TENUE, 3)
        c.l(x + 156, 250, x + 156, suelo, TENUE, 3)
        cuerpo(c, [(x + 104, 296), (x + 104, 246), (x + 140, 246), (x + 132, 200)], TENUE, 5)
        cabeza(c, x + 126, 184, 12, TENUE)
        c.circ(x + 119, 184, 2.2, '#fff', TENUE, 1.4)              # oído
        c.l(x + 104, 188, x + 116, 185, TINTA, 2)                  # sonda

    # --- a evitar: agachado, brazo extendido sin apoyo
    x = 380
    nino(x)
    cuerpo(c, [(x + 58, 296), (x + 46, 296)], ROJO)
    cuerpo(c, [(x + 46, 296), (x + 66, 258), (x + 32, 272), (x + 50, 214)], ROJO)   # pierna, muslo, tronco
    cuerpo(c, [(x + 50, 214), (x + 64, 197)], ROJO, 3)
    cabeza(c, x + 74, 184, 13, ROJO)
    cuerpo(c, [(x + 50, 218), (x + 104, 190)], ROJO)                                 # brazo extendido
    for i, t in enumerate(('cuclillas, cuello flexionado,', 'brazo extendido sin apoyo')):
        c.t(x + 4, 120 + 12 * i, t, 9, ROJO, 'start', 700)
    c.l(x + 28, 140, x + 40, 178, ROJO, 1)
    c.t(x + 100, 322, 'agachado o de rodillas: evitar', 9.5, ROJO, 'middle', 700)

    # --- a preferir: taburete con ruedas, a la altura del niño, codo apoyado
    x = 600
    nino(x)
    c.l(x + 6, 250, x + 54, 250, TENUE, 4)                    # taburete
    c.l(x + 30, 250, x + 30, suelo, TENUE, 3)
    c.l(x + 12, suelo, x + 48, suelo, TENUE, 3)
    cuerpo(c, [(x + 30, 244), (x + 72, 244), (x + 72, 296), (x + 90, 296)], VERDE)
    cuerpo(c, [(x + 30, 244), (x + 34, 188)], VERDE)
    cuerpo(c, [(x + 34, 188), (x + 40, 170)], VERDE, 3)
    cabeza(c, x + 46, 156, 13, VERDE)
    c.circ(x + 54, 154, 1.8, VERDE, None)
    cuerpo(c, [(x + 36, 192), (x + 62, 224), (x + 98, 190)], VERDE)
    c.rect(x + 44, 227, 40, 5, '#e7e5e0', FUERTE, 1)           # mesa auxiliar o carro
    c.l(x + 76, 232, x + 76, suelo, FUERTE, 2)
    for i, t in enumerate(('a su altura, codo apoyado,', 'cuello neutro')):
        c.t(x + 4, 102 + 12 * i, t, 9, VERDE, 'start', 700)
    c.l(x + 40, 118, x + 44, 140, VERDE, 1)
    c.t(x + 100, 322, 'sentado a su altura: preferir', 9.5, VERDE, 'middle', 700)
    c.guardar('h24-ergo-puesto.svg')


if __name__ == '__main__':
    esquema()
