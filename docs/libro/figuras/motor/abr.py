"""ABR con el equipo de la app: se abre la ventana ABR sin pantalla, se
captura cada nivel como lo haría el alumno, y se dibuja el resultado.

Las ondas se rotulan donde el generador las puso (metadata 'waves'), sobre
el pico real de la curva promediada: nunca a ojo.
"""
import os

from . import estilo as E
from .datos import RAIZ, fijar_azar
from .svg import Svg

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

_VENTANA = {}

# Nombre corto del libro -> valor del equipo (AbrAdvanceSettings.TRANSDUCERS
# y el combo de polaridad de la ventana).
TRANSDUCTORES = {'insercion': 'insert_earphone', 'copa': 'TDH39_headphone',
                 'oseo': 'bone_vibrator'}
POLARIDADES = {'alternada': 'Alternada', 'condensacion': 'Condensación',
               'rarefaccion': 'Rarefacción'}

# Una onda se rotula si sobresale del ruido residual del promedio (el de la
# diferencia A-B): con el umbral fijo de 0,02 µV se marcaba una "V" donde
# solo había ruido. Y nunca debajo de AMP_MIN_UV, aunque el ruido sea bajo.
SNR_ROTULO = 3.0
AMP_MIN_UV = 0.05


def _ventana(caso, promediaciones, transductor='insercion', tasa=21.1):
    from core.base import context  # noqa: F401  (crea el QApplication)
    from abr.AbrMainWindow import AbrMainWindow
    w = AbrMainWindow({'name': 'Libro', 'user': 'libro', 'permission': 'admin'})
    w.la_super(caso, caso.get('id'))
    if transductor not in TRANSDUCTORES:
        raise ValueError(f'Transductor {transductor!r}; hay: ' + ', '.join(TRANSDUCTORES))
    # Lo mismo que hace Aceptar en Parámetros avanzados (active_advance_setting).
    w.technical = dict(w.technical, transducer=TRANSDUCTORES[transductor])
    w.apply_window()
    w.control.sb_prom.setValue(promediaciones)
    w.control.sb_rate.setValue(tasa)
    # Banda de rutina: el equipo arranca abierto a propósito (lo configura
    # el alumno); para el libro se registra ya bien puesto.
    for combo, texto in ((w.control.cb_filter_up, '100'), (w.control.cb_filter_down, '3000')):
        i = combo.findText(texto)
        if i >= 0:
            combo.setCurrentIndex(i)
    return w


def _elegir(combo, texto):
    if texto is None:
        return
    for i in range(combo.count()):
        if texto.lower() in combo.itemText(i).lower():
            combo.setCurrentIndex(i)
            return
    raise ValueError(f'No existe la opción {texto!r}; hay: '
                     + ', '.join(combo.itemText(i) for i in range(combo.count())))


def capturar(caso, lados, niveles, estimulo=None, promediaciones=2000,
             transductor='insercion', polaridad='alternada', tasa=21.1):
    """Devuelve {lado: [{'db', 'x', 'y', 'a', 'b', 'ondas', 'visibles'}]}.

    transductor: 'insercion', 'copa' u 'oseo' (el vibrador llega a 55 dB nHL);
    polaridad: 'alternada', 'condensacion' o 'rarefaccion'; tasa en estímulos/s.
    """
    # La app abre sus recursos (resources/) con rutas relativas a la raíz
    antes = os.getcwd()
    os.chdir(RAIZ)
    try:
        return _capturar(caso, lados, niveles, estimulo, promediaciones,
                         transductor, polaridad, tasa)
    finally:
        os.chdir(antes)


def _capturar(caso, lados, niveles, estimulo, promediaciones, transductor, polaridad, tasa):
    if polaridad not in POLARIDADES:
        raise ValueError(f'Polaridad {polaridad!r}; hay: ' + ', '.join(POLARIDADES))
    w = _ventana(caso, promediaciones, transductor, tasa)
    _elegir(w.control.cb_stim, estimulo)
    _elegir(w.control.cb_pol, POLARIDADES[polaridad])
    out = {}
    for lado in lados:
        g = w.graph_r if lado == 'OD' else w.graph_l
        out[lado] = []
        for db in niveles:
            fijar_azar('abr', caso.get('id'), lado, db, estimulo,
                       *(() if (transductor, polaridad, tasa) == ('insercion', 'alternada', 21.1)
                         else (transductor, polaridad, tasa)))
            i = w.control.cb_side.findText(lado)
            if i >= 0:
                w.control.cb_side.setCurrentIndex(i)
            w.control.sb_intencity.setValue(db)
            w.control.start_capture()
            for _ in range(2000):
                w.capture()
                if w.state_capture != 'record':
                    break
            else:
                raise RuntimeError('la captura no terminó')
            v = g.data[list(g.data)[-1]]
            meta = w.last_metadata or {}
            out[lado].append({
                'db': v['intencity'],
                'x': [float(t) for t in v['ipsi_xy'][0]],
                'y': [float(t) for t in v['ipsi_xy'][1]],
                'a': [float(t) for t in v['sub_a'][1]],
                'b': [float(t) for t in v['sub_b'][1]],
                'ondas': meta.get('waves') or {},
                'visibles': bool(meta.get('waves_visible')),
            })
    w.close()
    return out


def dibujar(curvas, marcar=('I', 'III', 'V'), ms_max=12.0, uv_px=80):
    lados = [l for l in ('OD', 'OI') if l in curvas]
    n = max(len(curvas[l]) for l in lados)
    # Separación entre trazos según la amplitud real: que no se pisen
    # y aire fijo para el rótulo de la onda, que no choque con la de arriba
    p2p = max((max(c['y']) - min(c['y'])) for l in lados for c in curvas[l])
    sep_px = min(1.4, max(0.45, p2p)) * uv_px + (18 if marcar else 6)
    ms_px = 22
    pw = ms_max * ms_px
    ml, mt, gap = 70, 58, 40
    ph = (n - 1) * sep_px + 50
    s = Svg(ml + len(lados) * pw + (len(lados) - 1) * gap + 64, mt + ph + 40)

    for k, lado in enumerate(lados):
        col = E.COLOR_LADO[lado]
        x0 = ml + k * (pw + gap)

        def X(t):
            return x0 + t * ms_px

        s.texto(x0, mt - 40, E.NOMBRE_LADO[lado], E.T_TITULO, E.TINTA, 'start', 600)
        for t in range(0, int(ms_max) + 1):
            s.linea(X(t), mt - 8, X(t), mt + ph, E.GRILLA, 1 if t % 2 == 0 else 0.5)
            if t % 2 == 0:
                s.texto(X(t), mt + ph + 14, t, E.T_EJE, E.TENUE)
        for j, c in enumerate(sorted(curvas[lado], key=lambda c: -c['db'])):
            base = mt + 14 + j * sep_px
            dentro = [(t, y) for t, y in zip(c['x'], c['y']) if t <= ms_max]
            m = sum(y for _, y in dentro) / len(dentro)

            def P(ys):
                return [(X(t), base - (y - m) * uv_px) for t, y in zip(c['x'], ys) if t <= ms_max]

            s.trazo(P(c['a']), col, E.LINEA_FINA, E.OPACIDAD_SECUNDARIA)
            s.trazo(P(c['b']), col, E.LINEA_FINA, E.OPACIDAD_SECUNDARIA)
            s.trazo(P(c['y']), col, E.LINEA)
            s.ancla(f"{lado} {c['db']:g}", X(ms_max) - 4, base)
            if k == 0:
                s.texto(ml - 12, base + 3, f"{c['db']:g} dB", E.T_ROTULO, E.TINTA_2, 'end')
            if c['visibles']:
                for onda in marcar:
                    pico = _pico(c, onda)
                    if pico is None:
                        continue
                    t, y = pico
                    px, py = X(t), base - (y - m) * uv_px
                    s.ancla(f"{lado} {c['db']:g} {onda}", px, py)
                    s.linea(px, py - 4, px, py - 10, E.TINTA_2, 0.8)
                    s.texto(px, py - 13, onda, E.T_CHICO, E.TINTA, peso=600)

    # Barra de escala: 0,5 µV
    xb, yb = s.ancho - 44, mt + ph
    s.linea(xb, yb, xb, yb - 0.5 * uv_px, E.TINTA_2, 1.2)
    s.texto(xb + 5, yb - 0.25 * uv_px + 3, '0,5 µV', E.T_CHICO, E.TENUE, 'start')
    s.texto(ml + (s.ancho - ml) / 2 - 8, mt + ph + 30, 'Latencia (ms)', E.T_EJE, E.TENUE)
    return s.svg()


def _ruido(c):
    """Ruido residual del promedio (µV RMS): la mitad de la diferencia A-B."""
    d = [(a - b) / 2 for a, b in zip(c['a'], c['b'])]
    if not d:
        return 0.0
    m = sum(d) / len(d)
    return (sum((v - m) ** 2 for v in d) / len(d)) ** 0.5


def _pico(c, onda, ventana_ms=0.35):
    """Máximo de la curva promediada cerca de la latencia que usó el generador."""
    o = c['ondas'].get(onda)
    if not o or o.get('amp', 0) < max(AMP_MIN_UV, SNR_ROTULO * _ruido(c)):
        return None
    lat, xs, ys = o['lat'], c['x'], c['y']
    # Solo un máximo local de verdad: el borde de la ventana sobre una
    # pendiente no es un pico, y ahí se deja la onda sin rotular.
    picos = [(xs[i], ys[i]) for i in range(1, len(xs) - 1)
             if abs(xs[i] - lat) <= ventana_ms and ys[i] >= ys[i - 1] and ys[i] >= ys[i + 1]]
    if not picos:
        return None
    return max(picos, key=lambda p: p[1])
