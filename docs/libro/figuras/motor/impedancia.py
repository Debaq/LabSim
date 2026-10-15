"""Timpanograma y reflejos, con los generadores del impedanciómetro de la app.

El timpanograma sale de Z_225 (src/impedanciometria/z_generator.py) con la
misma semilla de paciente que usa Z.preCharger: (id, oído, sonda). Lo que
imprime el libro es lo que el alumno ve al abrir el equipo con ese paciente.
"""
from . import estilo as E
from .datos import fijar_azar
from .svg import Svg

FRECS_REFLEJO = ['500', '1000', '2000', '4000', 'NBN']
ROTULO_FRECS = ['500', '1k', '2k', '4k', 'NBN']
SIN_REFLEJO = 130
# Impedanciometría no realizable en ese oído: la sonda no va (ver
# CaseBuilder::Z_NO_REALIZABLE en el backend). No hay curva ni reflejos.
NO_REALIZABLE = 'NR'


def _curva(caso, lado, sonda=226):
    from impedanciometria.z_generator import (Z_225, edad_meses_del_caso,
                                              map_letter_for_probe, z1000_del_caso)
    # La app maneja la sonda como texto ('226'/'1000', ver Z.set_probe_freq):
    # con un entero map_letter_for_probe no reconoce la de 1000 y la semilla
    # sale distinta de la que ve el alumno.
    sonda = str(sonda)
    letra = caso.get(f'Z_{lado}')
    try:
        vol = caso['volume'][0 if lado == 'OD' else 1]
    except (KeyError, IndexError, TypeError):
        vol = None
    if not letra or vol in (None, ''):
        return None
    clave = (caso.get('id'), lado, sonda)
    letra = map_letter_for_probe(letra, sonda, seed_key=clave,
                                 edad_meses=edad_meses_del_caso(caso),
                                 forzado=z1000_del_caso(caso, lado))
    fijar_azar('timpanograma', caso.get('id'), lado, sonda)
    x, y, c, p, g, v, _ = Z_225(letter=letra, vol=vol, seed_key=clave).getDataSet()
    return {'x': x, 'y': y, 'compliancia': c, 'presion': p, 'gradiente': g, 'volumen': v}


def timpanograma(caso, oidos=('OD', 'OI'), escala_ml=2.0, sonda=226):
    pw, ph = 230, 150
    ml, mt, sep, mb = 40, 30, 36, 62
    s = Svg(ml + len(oidos) * pw + (len(oidos) - 1) * sep + 12, mt + ph + mb)
    x_min, x_max = -400, 200

    for k, lado in enumerate(oidos):
        col = E.COLOR_LADO[lado]
        x0 = ml + k * (pw + sep)

        def X(p):
            return x0 + (p - x_min) / (x_max - x_min) * pw

        def Y(ml_):
            return mt + ph - max(0.0, min(escala_ml, ml_)) / escala_ml * ph

        for p in range(x_min, x_max + 1, 100):
            s.linea(X(p), mt, X(p), mt + ph, E.GRILLA_FUERTE if p == 0 else E.GRILLA, 1)
            s.texto(X(p), mt + ph + 14, p, E.T_EJE, E.TENUE)
        for i in range(0, int(escala_ml * 10) + 1, 5):
            v = i / 10
            s.linea(x0, Y(v), x0 + pw, Y(v), E.GRILLA, 1 if i % 10 == 0 else 0.5)
            if k == 0:
                s.texto(x0 - 7, Y(v) + 3, f'{v:.1f}'.replace('.', ','), E.T_EJE, E.TENUE, 'end')
        s.texto(x0, mt - 12, E.NOMBRE_LADO[lado], E.T_TITULO, E.TINTA, 'start', 600)

        if caso.get(f'Z_{lado}') == NO_REALIZABLE:
            s.ancla(f'{lado} no realizable', x0 + pw / 2, mt + ph / 2)
            s.texto(x0 + pw / 2, mt + ph / 2, 'No realizable', E.T_TITULO, col, peso=600)
            s.texto(x0 + pw / 2, mt + ph / 2 + 16, 'la sonda no va en este oído', E.T_ROTULO, E.TENUE)
            continue
        d = _curva(caso, lado, sonda)
        if d is None:
            s.texto(x0 + pw / 2, mt + ph / 2, 'Sin timpanograma en el caso', E.T_ROTULO, E.TENUE)
            continue
        pts = sorted(zip(d['x'], d['y']))
        px, py = max(pts, key=lambda q: q[1])
        s.ancla(f'{lado} pico', X(px), Y(py))
        s.trazo([(X(px), Y(py)) for px, py in pts if x_min <= px <= x_max], col, E.LINEA)
        if _f(d['compliancia']) and _f(d['compliancia']) > escala_ml:
            s.texto(x0 + pw - 4, mt + 10, f'se sale de la escala de {escala_ml:g} mL', E.T_CHICO, E.TENUE, 'end')
        # Sin pico (B) no hay presión ni gradiente que leer
        sin_pico = (_f(d['compliancia']) or 0.0) < 0.05
        datos = [('Vol.', _ml(d['volumen'])), ('Compl.', _ml(d['compliancia'])),
                 ('Presión', 'Sin pico' if sin_pico else _dapa(d['presion'])),
                 ('Grad.', '—' if sin_pico else _dec(d['gradiente']))]
        xx = x0
        for rot, val in datos:
            s.texto(xx, mt + ph + 44, rot, E.T_CHICO, E.TENUE, 'start')
            s.texto(xx, mt + ph + 56, val, E.T_ROTULO, E.TINTA_2, 'start', 600)
            xx += pw / 4

    s.texto(s.ancho / 2, mt + ph + 28, 'Presión (daPa)', E.T_EJE, E.TENUE)
    s.texto(12, mt + ph / 2, 'mL', E.T_EJE, E.TENUE, extra=f'transform="rotate(-90 12 {mt + ph / 2:.1f})"')
    return s.svg()


def reflejos(caso):
    """Tabla de umbrales del reflejo estapedial (dB SPL), por sonda.

    En el caso cada umbral está por SONDA (columna 0 = sonda OD): en el
    contralateral el tono entra por el otro oído, y eso se escribe en el
    rótulo para que no haya que adivinarlo.
    """
    r = caso.get('Reflex')
    filas = []
    if isinstance(r, dict):
        for modo, nombre in (('ipsi', 'Ipsilateral'), ('contra', 'Contralateral')):
            datos = r.get(modo) or []
            for j, lado in enumerate(('OD', 'OI')):
                otro = 'OI' if lado == 'OD' else 'OD'
                sub = f'sonda {lado}' if modo == 'ipsi' else f'sonda {lado} · tono {otro}'
                vals = []
                for i in range(len(FRECS_REFLEJO)):
                    try:
                        vals.append(float(datos[i][j]))
                    except (IndexError, TypeError, ValueError):
                        vals.append(None)
                # Un oído NR no recibe ni la sonda ni el auricular del tono
                nr = NO_REALIZABLE in (caso.get(f'Z_{lado}'), caso.get(f'Z_{lado if modo == "ipsi" else otro}'))
                filas.append((nombre, sub, lado, ['NR'] * len(vals) if nr else vals))

    cw, rh, ml, mt = 54, 26, 170, 34
    s = Svg(ml + cw * len(FRECS_REFLEJO) + 10, mt + rh * max(len(filas), 1) + 22)
    for i, f in enumerate(ROTULO_FRECS):
        s.texto(ml + cw * i + cw / 2, mt - 10, f, E.T_EJE, E.TENUE)
    if not filas:
        s.texto(s.ancho / 2, mt + 14, 'Sin reflejos en el caso', E.T_ROTULO, E.TENUE)
        return s.svg()
    for n, (nombre, sub, lado, vals) in enumerate(filas):
        y = mt + n * rh
        if n % 2 == 0:
            s.rect(0, y, s.ancho, rh, E.LAVADO)
        s.rect(4, y + 7, 3, rh - 14, E.COLOR_LADO[lado])
        s.texto(14, y + rh / 2 + 3, nombre, E.T_ROTULO, E.TINTA, 'start', 600)
        s.texto(92, y + rh / 2 + 3, sub, E.T_EJE, E.TINTA_2, 'start')
        for i, v in enumerate(vals):
            cx = ml + cw * i + cw / 2
            # al costado derecho del valor: el globo apunta al dato sin taparlo
            s.ancla(f"{'ipsi' if nombre == 'Ipsilateral' else 'contra'} {lado} {FRECS_REFLEJO[i]}", cx + 16, y + rh / 2)
            if i == 4 and nombre == 'Ipsilateral' and v in (None, 'NR'):
                s.texto(cx, y + rh / 2 + 3, '·', E.T_ROTULO, E.MUY_TENUE)
            elif v == 'NR':
                s.texto(cx, y + rh / 2 + 3, 'NR', E.T_CHICO, E.TENUE)
            elif v is None or v >= SIN_REFLEJO:
                s.texto(cx, y + rh / 2 + 3, 'Ausente', E.T_CHICO, E.TENUE)
            else:
                s.texto(cx, y + rh / 2 + 3, f'{v:g}', E.T_ROTULO, E.TINTA, peso=600)
    pie = 'Umbral del reflejo en dB SPL'
    if any(v == 'NR' for *_, vals in filas for v in vals):
        pie += ' · NR = no realizable (la sonda o el auricular no van en ese oído)'
    s.texto(ml if len(pie) < 40 else 14, s.alto - 6, pie, E.T_CHICO, E.TENUE, 'start')
    return s.svg()


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _ml(v):
    v = _f(v)
    return 'N/D' if v is None else f'{v:.2f} mL'.replace('.', ',')


def _dapa(v):
    v = _f(v)
    return 'N/D' if v is None else f'{v:.0f} daPa'


def _dec(v):
    v = _f(v)
    return 'N/D' if v is None else f'{v:.2f}'.replace('.', ',')
