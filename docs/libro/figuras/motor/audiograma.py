"""Audiograma tonal, un panel por oído.

Las reglas clínicas son las de CaseCharts::audiogram (labsim_backend), que es
lo que ve el alumno en la ficha: qué símbolo va enmascarado, dónde se mide
la vía ósea, cómo se dibuja el "no responde" y el LDL. Lo que cambia es solo
el dibujo.
"""
import math

from . import estilo as E
from .datos import por_oido
from .svg import Svg

FRECUENCIAS = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000]
FRECUENCIAS_OSEA = [250, 500, 1000, 2000, 3000, 4000]
ATENUACION_AEREA = [35, 40, 40, 40, 40, 45, 45, 50, 50]   # CaseCharts::ATENUACION_AEREA_POR_FREQ
GAP_ENMASCARA_OSEA = 10
SIN_RESPUESTA = 130
NIVEL_MAXIMO = 120
TOPE_OSEA = 70            # el vibrador no pasa de acá (CaseCharts::TOPE_OSEA_DB)
LIMITE_NORMAL = 20
CORRIMIENTO_OSEA = 9      # px: OD a la izquierda, OI a la derecha
ROTULO = {1000: '1k', 2000: '2k', 3000: '3k', 4000: '4k', 6000: '6k', 8000: '8k'}
OCTAVA_PX = 34            # una octava mide lo mismo que 20 dB (ASHA)
R = 4.0                   # radio de los símbolos


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def sombra(aerea, osea):
    """Lo que mide quien NO enmascara: el oído mejor contesta por el peor.

    Por aérea el tono cruza con la atenuación interaural de la frecuencia
    (ATENUACION_AEREA, la misma regla de enmascaramiento de la ficha) y lo
    oye la cóclea contraria, que se mide por su ósea; por ósea la atenuación
    es casi nula, así que contesta la mejor ósea de las dos."""
    otro = {'OD': 'OI', 'OI': 'OD'}
    a2, o2 = {}, {}
    for lado in ('OD', 'OI'):
        a2[lado], o2[lado] = [], []
        for i in range(len(FRECUENCIAS)):
            a, o, oo = _num(aerea[lado][i]), _num(osea[lado][i]), _num(osea[otro[lado]][i])
            cruce = oo + ATENUACION_AEREA[i] if oo is not None else None
            a2[lado].append(min(a, cruce) if a is not None and cruce is not None else a)
            o2[lado].append(min(o, oo) if o is not None and oo is not None else o)
    return a2, o2


def dibujar(caso, estudio=True, ldl=True, oidos=('OD', 'OI'), sin_enmascarar=False):
    """estudio=True: la ósea no aparece donde el aéreo de ese oído es normal
    (como en la ficha de estudio; un examen real no la busca ahí).
    sin_enmascarar=True: lo que anota quien no enmascara (curva sombra)."""
    aerea = por_oido(caso['Aerea'])
    osea = por_oido(caso['Osea'])
    if sin_enmascarar:
        aerea, osea = sombra(aerea, osea)
        ldl = False
    ldl_d = por_oido(caso['LDL']) if ldl and caso.get('LDL') else None
    otro = {'OD': 'OI', 'OI': 'OD'}

    db_px = OCTAVA_PX / 20
    pw, ph = 6 * OCTAVA_PX, 130 * db_px
    ml, mt, sep, mb = 36, 30, 34, 40
    s = Svg(ml + len(oidos) * pw + (len(oidos) - 1) * sep + 14, mt + ph + mb)

    for k, lado in enumerate(oidos):
        col = E.COLOR_LADO[lado]
        x0 = ml + k * (pw + sep)

        def X(f):
            return x0 + math.log2(f / 125) * OCTAVA_PX

        def Y(db):
            return mt + (max(-10.0, min(float(NIVEL_MAXIMO), db)) + 10) * db_px

        # Fondo: zona de audición normal y grilla
        s.rect(x0, Y(-10), pw, Y(LIMITE_NORMAL) - Y(-10), E.LAVADO)
        for db in range(-10, 121, 10):
            fuerte = db in (0, LIMITE_NORMAL)
            s.linea(x0, Y(db), x0 + pw, Y(db), E.GRILLA_FUERTE if fuerte else E.GRILLA,
                    1 if (fuerte or db % 20 == 0) else 0.5)
            if k == 0 and db % 20 == 0:
                s.texto(x0 - 7, Y(db) + 3, db, E.T_EJE, E.TENUE, 'end')
        for f in FRECUENCIAS:
            mayor = f not in (3000, 6000)
            s.linea(X(f), Y(-10), X(f), Y(120), E.GRILLA, 1 if mayor else 0.5)
            s.texto(X(f), Y(120) + 14, ROTULO.get(f, f), E.T_EJE if mayor else E.T_CHICO,
                    E.TENUE if mayor else E.MUY_TENUE)
        s.texto(x0, mt - 12, E.NOMBRE_LADO[lado], E.T_TITULO, E.TINTA, 'start', 600)

        a = [_num(v) for v in aerea[lado]]
        o = [_num(v) for v in osea[lado]]
        o_otro = [_num(v) for v in osea[otro[lado]]]

        # Vía aérea: línea por los tramos con umbral (el "no responde" no se une)
        for tramo in _tramos([(X(f), Y(v)) if v is not None and v < SIN_RESPUESTA else None
                              for f, v in zip(FRECUENCIAS, a)]):
            s.trazo(tramo, col, 1.4)

        # Vía ósea: punteada, solo donde se mide
        idx_osea = [i for i, f in enumerate(FRECUENCIAS) if f in FRECUENCIAS_OSEA
                    and o[i] is not None
                    and (not estudio or (a[i] is not None and a[i] > LIMITE_NORMAL))]
        desp = -CORRIMIENTO_OSEA if lado == 'OD' else CORRIMIENTO_OSEA
        for tramo in _tramos([(X(FRECUENCIAS[i]) + desp, Y(o[i])) if i in idx_osea and o[i] <= TOPE_OSEA else None
                              for i in range(len(FRECUENCIAS))]):
            s.trazo(tramo, col, 0.9, guiones='1 2.5')

        # LDL: guiones largos, solo si se midió
        if ldl_d and any(_num(v) is not None and _num(v) < SIN_RESPUESTA for v in ldl_d[lado]):
            l = [_num(v) for v in ldl_d[lado]]
            pts = [(X(f), Y(l[i])) if f in FRECUENCIAS_OSEA and l[i] is not None and l[i] < SIN_RESPUESTA else None
                   for i, f in enumerate(FRECUENCIAS)]
            for tramo in _tramos(pts):
                s.trazo(tramo, col, 0.9, guiones='4 3')
            for i, f in enumerate(FRECUENCIAS):
                if f in FRECUENCIAS_OSEA and l[i] is not None:
                    y = Y(min(l[i], NIVEL_MAXIMO))
                    _ldl(s, X(f), y, col, -1 if lado == 'OD' else 1)
                    if l[i] >= SIN_RESPUESTA:
                        _flecha(s, X(f), y, col, -1 if lado == 'OD' else 1)

        # Símbolos (encima de las líneas)
        for i, f in enumerate(FRECUENCIAS):
            if a[i] is None:
                continue
            sin = a[i] >= SIN_RESPUESTA
            x, y = X(f), Y(NIVEL_MAXIMO if sin else a[i])
            enmascarada = (not sin_enmascarar and o_otro[i] is not None
                           and (a[i] - o_otro[i]) >= ATENUACION_AEREA[i])
            _simbolo_aereo(s, lado, x, y, col, enmascarada)
            s.ancla(f'{lado} {f}', x, y)
            if sin:
                _flecha(s, x, y, col, -1 if lado == 'OD' else 1)
        for i in idx_osea:
            sin = o[i] > TOPE_OSEA
            x, y = X(FRECUENCIAS[i]) + desp, Y(TOPE_OSEA if sin else o[i])
            enmascarada = not sin_enmascarar and a[i] is not None and (a[i] - o[i]) >= GAP_ENMASCARA_OSEA
            _simbolo_oseo(s, lado, x, y, col, enmascarada)
            s.ancla(f'{lado} osea {FRECUENCIAS[i]}', x, y)
            if sin:
                _flecha(s, x, y, col, -1 if lado == 'OD' else 1)

    if sin_enmascarar:
        s.texto(s.ancho - 14, 14, 'sin enmascarar', E.T_CHICO, E.TENUE, 'end')
    s.texto(14, mt + ph / 2, 'dB HL', E.T_EJE, E.TENUE,
            extra=f'transform="rotate(-90 14 {mt + ph / 2:.1f})"')
    s.texto(s.ancho / 2, mt + ph + 34, 'Frecuencia (Hz)', E.T_EJE, E.TENUE)
    return s.svg()


def _tramos(puntos):
    tramo = []
    for p in puntos:
        if p is None:
            if len(tramo) > 1:
                yield tramo
            tramo = []
        else:
            tramo.append(p)
    if len(tramo) > 1:
        yield tramo


def _simbolo_aereo(s, lado, x, y, col, enmascarada):
    if lado == 'OD':
        if enmascarada:      # triángulo
            s.camino(f'M{x:.2f},{y - R:.2f} L{x - R:.2f},{y + R * .8:.2f} L{x + R:.2f},{y + R * .8:.2f} Z',
                     col, E.LINEA, E.PAPEL)
        else:                # círculo
            s.circulo(x, y, R, col)
    else:
        if enmascarada:      # cuadrado
            s.rect(x - R * .85, y - R * .85, R * 1.7, R * 1.7, E.PAPEL, col, E.LINEA)
        else:                # cruz
            r = R * .85
            s.camino(f'M{x - r:.2f},{y - r:.2f} L{x + r:.2f},{y + r:.2f} M{x - r:.2f},{y + r:.2f} L{x + r:.2f},{y - r:.2f}',
                     col)


def _simbolo_oseo(s, lado, x, y, col, enmascarada):
    r = R
    d = -1 if lado == 'OD' else 1      # OD abre a la derecha: "<" y "["
    if enmascarada:
        d_ = (f'M{x - d * r * .6:.2f},{y - r:.2f} L{x + d * r:.2f},{y - r:.2f} '
              f'L{x + d * r:.2f},{y + r:.2f} L{x - d * r * .6:.2f},{y + r:.2f}')
    else:
        d_ = f'M{x - d * r * .7:.2f},{y - r:.2f} L{x + d * r * .7:.2f},{y:.2f} L{x - d * r * .7:.2f},{y + r:.2f}'
    s.camino(d_, col)


def _ldl(s, x, y, col, lado):
    xc, xp = x + lado * 1.8, x + lado * 6.6
    s.camino(f'M{xc:.2f},{y - 3:.2f} L{xc:.2f},{y + 3:.2f} L{xp:.2f},{y + 3:.2f} Z', col, 1, col)


def _flecha(s, x, y, col, lado):
    x1, y1 = x + lado * 3, y + 4
    x2, y2 = x1 + lado * 5, y1 + 7
    s.camino(f'M{x1:.2f},{y1:.2f} L{x2:.2f},{y2:.2f} M{x2:.2f},{y2:.2f} L{x2 - lado * 3.4:.2f},{y2 - .6:.2f} '
             f'M{x2:.2f},{y2:.2f} L{x2 - lado * .6:.2f},{y2 - 3.4:.2f}', col, 1.2)
