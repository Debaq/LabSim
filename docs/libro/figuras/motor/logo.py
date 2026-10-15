"""Logoaudiograma con el motor de la app (audiometria.logoaudiometry.CalculateLogo).

`enmascarado=True` dibuja la curva propia de cada oído (lo que mide un
examen bien enmascarado): audiometria.logo_curva.pct_logo, la misma curva
que el PDF del caso y el editor, anclada al SRT de la ficha (ahí pasa la
mitad de su máximo), con el máximo en la UMD y el rollover que le da el
componente retrococlear del perfil. Con False, lo que anota un alumno que NO
enmascara: el oído mejor contesta por el peor desde que la voz cruza el
cráneo (CalculateLogo.get, de 5 en 5 dB como el dial).
"""
from . import estilo as E
from .datos import en_raiz
from .svg import Svg

NIVELES = list(range(0, 115, 5))


def curvas(caso, enmascarado=True):
    from audiometria.logo_curva import pct_logo
    from audiometria.logoaudiometry import CalculateLogo
    with en_raiz():
        L = CalculateLogo(caso, caso['UMD'])
        out = {}
        for i, lado in enumerate(('OD', 'OI')):
            if enmascarado:
                # de a 1 dB hasta el techo del canal de habla (100 dB)
                out[lado] = [(db, round(pct_logo(L.cfg[i], float(db)), 1)) for db in range(0, 101)]
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

    trazos = {lado: [(X(db), Y(p)) for db, p in c[lado]] for lado in oidos}
    ocupados = []
    for lado in oidos:
        col = E.COLOR_LADO[lado]
        pts = c[lado]
        s.trazo(trazos[lado], col, E.LINEA)
        for db, p in pts:
            s.ancla(f'{lado} {db}', X(db), Y(p))
            if db % 10 == 0:
                _simbolo(s, lado, X(db), Y(p))
        # rótulo de la máxima, una sola vez por curva, donde no pise ninguna
        # de las dos curvas ni el otro rótulo (en el 36 el "92 %" quedaba
        # debajo de la curva del OI)
        db_max, p_max = max(pts, key=lambda q: (q[1], -q[0]))
        s.ancla(f'{lado} max', X(db_max), Y(p_max))
        texto = f'{p_max:.0f} %'
        otras = [t for o, t in trazos.items() if o != lado]
        x, y, ancla, caja = _lugar_rotulo(X(db_max), Y(p_max), texto, trazos.values(), ocupados,
                                          (ml, mt, ml + pw, mt + ph), otras)
        ocupados.append(caja)
        # del color del oído: si el único lugar libre queda del otro lado de
        # la otra curva (paciente 40, dos curvas pegadas), igual se sabe de
        # quién es
        s.texto(x, y, texto, E.T_CHICO, col, ancla)

    s.texto(ml + pw / 2, mt + ph + 30, 'Intensidad (dB HL)', E.T_EJE, E.TENUE)
    s.texto(12, mt + ph / 2, '% de discriminación', E.T_EJE, E.TENUE,
            extra=f'transform="rotate(-90 12 {mt + ph / 2:.1f})"')
    return s.svg()


# Dónde probar el rótulo del máximo, en orden de preferencia: (dx, dy, ancla)
# respecto del punto. Arriba primero, que es donde se lee un máximo.
_LUGARES = [(6, -9, 'start'), (-6, -9, 'end'), (0, -12, 'middle'), (6, 14, 'start'),
            (-6, 14, 'end'), (0, 18, 'middle'), (8, -20, 'start'), (-8, -20, 'end'),
            (8, 26, 'start'), (-8, 26, 'end'), (0, -30, 'middle'), (0, 36, 'middle')]


def _caja_texto(x, y, texto, ancla, tam=E.T_CHICO):
    """Caja aproximada (x0, y0, x1, y1) de un texto con su línea de base en y."""
    ancho = 0.56 * tam * len(texto)
    x0 = {'start': x, 'end': x - ancho, 'middle': x - ancho / 2}[ancla]
    return (x0, y - 0.8 * tam, x0 + ancho, y + 0.25 * tam)


def _pisa(caja, trazos, ocupados, margen=2.5):
    x0, y0, x1, y1 = caja[0] - margen, caja[1] - margen, caja[2] + margen, caja[3] + margen
    for otra in ocupados:
        if not (x1 < otra[0] or otra[2] < x0 or y1 < otra[1] or otra[3] < y0):
            return True
    for puntos in trazos:
        for (ax, ay), (bx, by) in zip(puntos, puntos[1:]):
            pasos = max(1, int(max(abs(bx - ax), abs(by - ay))))
            for k in range(pasos + 1):
                px = ax + (bx - ax) * k / pasos
                py = ay + (by - ay) * k / pasos
                if x0 <= px <= x1 and y0 <= py <= y1:
                    return True
    return False


def _y_en(puntos, x):
    """Altura (px) de una curva en x, o None si x queda fuera."""
    for (ax, ay), (bx, by) in zip(puntos, puntos[1:]):
        if ax <= x <= bx and bx > ax:
            return ay + (by - ay) * (x - ax) / (bx - ax)
    return None


def _lugar_rotulo(px, py, texto, trazos, ocupados, area, otras=()):
    """El primer lugar de _LUGARES que queda dentro del gráfico y no pisa
    ninguna curva ni otro rótulo; si ninguno sirve, el menos malo (el
    primero que entra en el gráfico). Si la otra curva pasa por ARRIBA de
    este máximo, se prueba primero por debajo: así cada rótulo queda del
    lado de su propia curva y no entre las dos."""
    trazos = list(trazos)
    lugares = _LUGARES
    if any((_y_en(t, px) is not None and _y_en(t, px) < py) for t in otras):
        lugares = [q for q in _LUGARES if q[1] > 0] + [q for q in _LUGARES if q[1] <= 0]
    dentro = None
    for dx, dy, ancla in lugares:
        x, y = px + dx, py + dy
        caja = _caja_texto(x, y, texto, ancla)
        if caja[0] < area[0] or caja[2] > area[2] + 30 or caja[1] < area[1] or caja[3] > area[3]:
            continue
        if dentro is None:
            dentro = (x, y, ancla, caja)
        if not _pisa(caja, trazos, ocupados):
            return x, y, ancla, caja
    if dentro is not None:
        return dentro
    dx, dy, ancla = _LUGARES[0]
    return px + dx, py + dy, ancla, _caja_texto(px + dx, py + dy, texto, ancla)


def _simbolo(s, lado, x, y, r=3.4):
    col = E.COLOR_LADO[lado]
    if lado == 'OD':
        s.circulo(x, y, r, col, ancho=1.4)
    else:
        s.camino(f'M{x - r:.2f},{y - r:.2f} L{x + r:.2f},{y + r:.2f} M{x - r:.2f},{y + r:.2f} L{x + r:.2f},{y - r:.2f}',
                 col, 1.4)
