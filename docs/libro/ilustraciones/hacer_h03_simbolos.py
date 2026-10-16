#!/usr/bin/env python3
"""Dibuja ilustraciones/h03-simbolos.svg: la lámina de símbolos de H3.

Usa las MISMAS funciones de dibujo del motor (figuras/motor/audiograma.py),
así cada símbolo es idéntico al de las figuras de los casos. Incluye lo que
se usa más adelante (LDL, Fowler, acumetría, campo libre): la lámina es la
referencia de todo el libro.

    python3 docs/libro/ilustraciones/hacer_h03_simbolos.py
"""
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / 'figuras'))
from motor import estilo as E  # noqa: E402
from motor.audiograma import _flecha, _ldl, _simbolo_aereo, _simbolo_oseo  # noqa: E402
from motor.svg import Svg  # noqa: E402

W = 540
C_ROT, C_OD, C_OI = 14, 290, 440        # columnas: rótulo, OD, OI
FILA = 34
s = Svg(W, 10)
filas = []          # (rótulo, dibujo OD, dibujo OI, nota) ; dibujo = función(x, y)
y = 50


def cabecera():
    s.texto(C_OD, 30, 'Oído derecho', E.T_TITULO, E.OD, peso=700)
    s.texto(C_OI, 30, 'Oído izquierdo', E.T_TITULO, E.OI, peso=700)


def fila(rotulo, od=None, oi=None, ambos=None, nota=None, alto=FILA):
    """ambos: un dibujo centrado entre las dos columnas (no es de un oído)."""
    global y
    top = y - FILA / 2
    if (len(filas_hechas) % 2) == 0:
        s.rect(8, top, W - 16, alto, E.LAVADO)
    yc = top + alto / 2
    s.texto(C_ROT, yc + 3, rotulo, E.T_ROTULO, E.TINTA, 'start', 600)
    if nota:
        s.texto(C_ROT, yc + 14, nota, E.T_CHICO, E.TENUE, 'start')
    if ambos:
        ambos((C_OD + C_OI) / 2, yc)
    else:
        if od:
            grande(od, C_OD, yc)
        if oi:
            grande(oi, C_OI, yc)
    filas_hechas.append(rotulo)
    y += alto


def seccion(titulo):
    global y
    y += 8
    s.texto(C_ROT, y - FILA / 2 + 8, titulo.upper(), E.T_CHICO, E.TENUE, 'start', 700)
    y += 16


filas_hechas = []
cabecera()
K = 1.7   # los símbolos más grandes que en el audiograma, para que se lean


def grande(dibujo, x, yy):
    s.crudo(f'<g transform="translate({x:.1f} {yy:.1f}) scale({K}) translate({-x:.1f} {-yy:.1f})">')
    dibujo(x, yy)
    s.crudo('</g>')


def aereo(lado, masc):
    col = E.COLOR_LADO[lado]
    return lambda x, yy: _simbolo_aereo(s, lado, x, yy, col, masc)


def oseo(lado, masc):
    col = E.COLOR_LADO[lado]
    return lambda x, yy: _simbolo_oseo(s, lado, x, yy, col, masc)


def sin_resp(lado, f):
    col = E.COLOR_LADO[lado]
    signo = -1 if lado == 'OD' else 1

    def d(x, yy):
        f(x, yy - 4)
        _flecha(s, x, yy - 4, col, signo)
    return d


def ldl(lado, flecha=False):
    col = E.COLOR_LADO[lado]
    signo = -1 if lado == 'OD' else 1

    def d(x, yy):
        _ldl(s, x, yy - 3, col, signo)
        if flecha:
            _flecha(s, x, yy - 3, col, signo)
    return d


def linea(lado, guiones, ancho, marca):
    col = E.COLOR_LADO[lado]

    def d(x, yy):
        # se dibuja dentro de grande(): coordenadas a escala 1/K
        a, b = (x - 34 / K, yy + 3), (x + 34 / K, yy - 3)
        s.trazo([a, b], col, ancho, guiones=guiones)
        marca(lado)(*a)
        marca(lado)(*b)
    return d


def campo_libre(x, yy):
    for dx, letra in ((-18, 'S'), (18, 'A')):
        s.texto(x + dx, yy + 3, letra, 15, E.CAMPO_LIBRE, peso=700)
    s.texto(x, yy + 15, 'S sin audífono · A con audífono', E.T_CHICO, E.TENUE)




def fowler(x, yy):
    """Escalera: la referencia (OD sano) a la izquierda y el oído en estudio
    (OI) a la derecha; cada línea une dos niveles que suenan igual. Las
    líneas que se juntan hacia arriba son el reclutamiento."""
    xr, xe = x - 70, x + 70
    def Yd(db):
        return yy - 52 + (db - 10) * 1.45
    s.texto(xr - 16, Yd(10) + 3, 'referencia', E.T_CHICO, E.OD, 'end', 600)
    s.texto(xe + 16, Yd(40) + 3, 'en estudio', E.T_CHICO, E.OI, 'start', 600)
    for ref, est in ((10, 40), (30, 55), (50, 70), (70, 85)):
        s.linea(xr, Yd(ref), xe, Yd(est), E.TENUE, 1)
        grande(lambda a, b: _simbolo_aereo(s, 'OD', a, b, E.OD, False), xr, Yd(ref))
        grande(lambda a, b: _simbolo_aereo(s, 'OI', a, b, E.OI, False), xe, Yd(est))
    s.texto(x, Yd(85) + 18, 'cada línea une dos niveles que suenan igual; si se juntan, hay reclutamiento',
            E.T_CHICO, E.TENUE)




def nueva():
    global s, y, filas_hechas
    s = Svg(W, 10)
    y, filas_hechas = 50, []
    cabecera()


def guardar(nombre):
    s.alto = y + 6
    (AQUI / nombre).write_text(s.svg(), encoding='utf-8')
    print(nombre)


# Lámina 1: el audiograma
nueva()
seccion('Audiograma')
fila('Aérea sin enmascarar', aereo('OD', False), aereo('OI', False))
fila('Aérea enmascarada', aereo('OD', True), aereo('OI', True))
fila('Ósea sin enmascarar', oseo('OD', False), oseo('OI', False), nota='en mastoides; el OD a la izquierda de la línea, el OI a la derecha')
fila('Ósea enmascarada', oseo('OD', True), oseo('OI', True))
fila('Sin respuesta', sin_resp('OD', aereo('OD', False)), sin_resp('OI', aereo('OI', False)),
     nota='al máximo del equipo; flecha hacia abajo, hacia afuera')
fila('Umbral de molestia (LDL)', ldl('OD'), ldl('OI'))
fila('LDL: sin molestia al máximo', ldl('OD', True), ldl('OI', True))

seccion('Líneas')
fila('Aérea: continua', linea('OD', None, 1.4, lambda l: aereo(l, False)),
     linea('OI', None, 1.4, lambda l: aereo(l, False)))
fila('Ósea: punteada', linea('OD', '1 2.5', 0.9, lambda l: oseo(l, False)),
     linea('OI', '1 2.5', 0.9, lambda l: oseo(l, False)))
fila('LDL: guiones', linea('OD', '4 3', 0.9, lambda l: ldl(l)), linea('OI', '4 3', 0.9, lambda l: ldl(l)))
fila('Campo libre', ambos=campo_libre, nota='no es de un oído: lo oye el mejor (→ H8)', alto=40)
guardar('h03-simbolos.svg')

# Lámina 2: supraliminares y acumetría
nueva()
seccion('Supraliminares')
fila('Fowler (ABLB)', ambos=fowler, nota='escalera entre los dos oídos (→ H6)', alto=136)

seccion('Acumetría')


def cabeza(x, yy):
    s.circulo(x, yy, 11, E.TENUE, E.PAPEL, 1)
    s.rect(x - 14.5, yy - 4, 3, 8, E.TENUE)
    s.rect(x + 11.5, yy - 4, 3, 8, E.TENUE)


def flecha_weber(x, yy, signo, col):
    x0, x1 = x + signo * 18, x + signo * 40
    s.linea(x0, yy, x1, yy, col, 1.8)
    s.camino(f'M{x1 - signo * 6:.1f},{yy - 4:.1f} L{x1:.1f},{yy:.1f} L{x1 - signo * 6:.1f},{yy + 4:.1f}', col, 1.8)


def weber(x, yy):
    for dx, cual, txt in ((-112, 'od', 'lateraliza al OD'), (0, 'centro', 'no lateraliza'),
                          (112, 'oi', 'lateraliza al OI')):
        cx = x + dx
        cabeza(cx, yy - 4)
        if cual in ('od', 'centro'):
            flecha_weber(cx, yy - 4, -1, E.OD)
        if cual in ('oi', 'centro'):
            flecha_weber(cx, yy - 4, 1, E.OI)
        s.texto(cx, yy + 18, txt, E.T_CHICO, E.TENUE)


fila('Weber', ambos=weber, nota='flecha roja = OD, azul = OI', alto=50)


def rinne(lado):
    col = E.COLOR_LADO[lado]

    def d(x, yy):
        for dx, sim, txt in ((-52, '+', 'positivo'), (0, '−', 'negativo'), (52, '−*', 'falso neg.')):
            s.circulo(x + dx, yy - 4, 10, col, E.PAPEL, 1.3)
            s.texto(x + dx, yy + 0.5, sim, 11, col, peso=700)
            s.texto(x + dx, yy + 18, txt, E.T_CHICO, E.TENUE)
    return d


fila('Rinne', ambos=lambda x, yy: (rinne('OD')(C_OD, yy), rinne('OI')(C_OI, yy)),
     nota='+ aérea mejor que ósea · − ósea mejor', alto=50)
guardar('h03-simbolos-2.svg')
