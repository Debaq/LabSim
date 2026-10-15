"""Logoaudiograma con el motor de la app (audiometria.logoaudiometry.CalculateLogo).

`enmascarado=True` dibuja la curva propia de cada oído (lo que mide un
examen bien enmascarado, con el rollover si hay reclutamiento). Con False,
lo que anota un alumno que NO enmascara: el oído mejor contesta por el peor
desde que la voz cruza el cráneo. Ojo: el 0 % de la curva lo calcula la app
desde el audiograma (los dos mejores umbrales), no desde el SDT del caso.
"""
from . import estilo as E
from .datos import en_raiz
from .svg import Svg

NIVELES = list(range(0, 115, 5))


def curvas(caso, enmascarado=True):
    from audiometria.logoaudiometry import CalculateLogo
    with en_raiz():
        L = CalculateLogo(caso, caso['UMD'])
        out = {}
        for i, lado in enumerate(('OD', 'OI')):
            if enmascarado:
                datos = {int(k): float(v) for k, v in L.data[i].items()}
                out[lado] = [(db, datos[db]) for db in sorted(datos) if db <= 110]
            else:
                out[lado] = [(db, float(L.get(i, False, db))) for db in NIVELES if db <= 100]
    return out


def dibujar(caso, enmascarado=True, oidos=('OD', 'OI')):
    c = curvas(caso, enmascarado)
    pw, ph, ml, mt = 330, 190, 44, 40
    s = Svg(ml + pw + 70, mt + ph + 44)

    def X(db):
        return ml + db / 110 * pw

    def Y(p):
        return mt + ph - p / 100 * ph

    for db in range(0, 111, 10):
        s.linea(X(db), mt, X(db), mt + ph, E.GRILLA, 1 if db % 20 == 0 else 0.5)
        if db % 20 == 0:
            s.texto(X(db), mt + ph + 14, db, E.T_EJE, E.TENUE)
    for p in range(0, 101, 20):
        s.linea(ml, Y(p), ml + pw, Y(p), E.GRILLA, 1)
        s.texto(ml - 7, Y(p) + 3, p, E.T_EJE, E.TENUE, 'end')

    # Leyenda (dos series: siempre, además de los rótulos directos)
    lx = ml
    for lado in oidos:
        _simbolo(s, lado, lx + 4, mt - 18)
        s.texto(lx + 13, mt - 15, E.NOMBRE_LADO[lado], E.T_ROTULO, E.TINTA_2, 'start')
        lx += 110
    if not enmascarado:
        s.texto(ml + pw, mt - 15, 'sin enmascarar', E.T_CHICO, E.TENUE, 'end')

    for lado in oidos:
        col = E.COLOR_LADO[lado]
        pts = c[lado]
        s.trazo([(X(db), Y(p)) for db, p in pts], col, E.LINEA)
        for db, p in pts:
            s.ancla(f'{lado} {db}', X(db), Y(p))
            if db % 10 == 0:
                _simbolo(s, lado, X(db), Y(p))
        # rótulo de la máxima, una sola vez por curva
        db_max, p_max = max(pts, key=lambda q: (q[1], -q[0]))
        s.ancla(f'{lado} max', X(db_max), Y(p_max))
        # arriba de la curva, salvo pegado al techo (ahí iría sobre la leyenda)
        dy = 14 if p_max >= 90 else -9
        s.texto(X(db_max) + 6, Y(p_max) + dy, f'{p_max:.0f} %', E.T_CHICO, E.TINTA_2, 'start')

    s.texto(ml + pw / 2, mt + ph + 30, 'Intensidad (dB HL)', E.T_EJE, E.TENUE)
    s.texto(12, mt + ph / 2, '% de discriminación', E.T_EJE, E.TENUE,
            extra=f'transform="rotate(-90 12 {mt + ph / 2:.1f})"')
    return s.svg()


def _simbolo(s, lado, x, y, r=3.4):
    col = E.COLOR_LADO[lado]
    if lado == 'OD':
        s.circulo(x, y, r, col, ancho=1.4)
    else:
        s.camino(f'M{x - r:.2f},{y - r:.2f} L{x + r:.2f},{y + r:.2f} M{x - r:.2f},{y + r:.2f} L{x + r:.2f},{y - r:.2f}',
                 col, 1.4)
