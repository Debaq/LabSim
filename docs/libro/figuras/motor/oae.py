"""Emisiones otoacústicas con los generadores de la app (src/oae/generators).

Se llaman con los mismos argumentos que usan los paneles (nivel, barridos,
L1/L2 por defecto de la normativa) y con cases.data['EOAS'][oído]: la
semilla es la de la app (stable_seed + huella del caso), así que el libro
muestra lo mismo que el equipo con ese paciente.
"""
from . import estilo as E
from .datos import en_raiz
from .svg import Svg

F_MIN, F_MAX = 500, 8000


def teoae(caso, lado):
    from oae.generators.teoae import TeoaeGenerator
    with en_raiz():
        g = TeoaeGenerator()
        n = g.normative
        return g.generate(level_db=n['default_level_db_spl'], n_sweeps=n['default_n_sweeps'],
                          ear=lado, case=caso['EOAS'][lado])


def dpoae(caso, lado):
    from oae.generators.dpoae import DpoaeGenerator
    with en_raiz():
        g = DpoaeGenerator()
        n = g.normative
        return g.generate(l1_db=n['default_l1_db_spl'], l2_db=n['default_l2_db_spl'],
                          ear=lado, case=caso['EOAS'][lado])


def _ejes(s, x0, mt, pw, ph, y_min, y_max, titulo, con_numeros):
    import math

    def X(f):
        return x0 + math.log2(f / F_MIN) / math.log2(F_MAX / F_MIN) * pw

    def Y(db):
        return mt + ph - (max(y_min, min(y_max, db)) - y_min) / (y_max - y_min) * ph

    for f in (500, 1000, 2000, 4000, 8000):
        s.linea(X(f), mt, X(f), mt + ph, E.GRILLA, 1)
        s.texto(X(f), mt + ph + 14, {1000: '1k', 2000: '2k', 4000: '4k', 8000: '8k'}.get(f, f), E.T_EJE, E.TENUE)
    for db in range(y_min, y_max + 1, 10):
        s.linea(x0, Y(db), x0 + pw, Y(db), E.GRILLA_FUERTE if db == 0 else E.GRILLA, 1)
        if con_numeros:
            s.texto(x0 - 7, Y(db) + 3, db, E.T_EJE, E.TENUE, 'end')
    s.texto(x0, mt - 12, titulo, E.T_TITULO, E.TINTA, 'start', 600)
    return X, Y


def dibujar_teoae(caso, oidos=('OD', 'OI')):
    """Respuesta y ruido por frecuencia; bandas que pasan = punto lleno."""
    pw, ph, ml, mt, sep = 230, 150, 40, 30, 34
    s = Svg(ml + len(oidos) * pw + (len(oidos) - 1) * sep + 12, mt + ph + 66)
    y_min, y_max = -30, 30
    for k, lado in enumerate(oidos):
        col = E.COLOR_LADO[lado]
        r = teoae(caso, lado)
        x0 = ml + k * (pw + sep)
        X, Y = _ejes(s, x0, mt, pw, ph, y_min, y_max, E.NOMBRE_LADO[lado], k == 0)
        fs = [(f, rd, nd) for f, rd, nd in zip(r['freqs'], r['spectrum_db'], r['noise_db']) if F_MIN <= f <= F_MAX]
        # ruido: lavado gris desde el piso; respuesta: línea del oído
        piso = [(X(f), Y(y_min)) for f, _, _ in fs]
        ruido = [(X(f), Y(nd)) for f, _, nd in fs]
        d = 'M' + ' L'.join(f'{x:.2f},{y:.2f}' for x, y in ruido + piso[::-1]) + ' Z'
        s.crudo(f'<path d="{d}" fill="{E.GRILLA}" stroke="none"/>')
        s.trazo([(X(f), Y(rd)) for f, rd, _ in fs], col, E.LINEA)
        for banda, snr in r['snr_per_band'].items():
            f = float(banda)
            pasa = bool(r['pass_per_band'].get(banda, False))
            y = Y(min(y_max, max(y_min, _interp(f, [q[0] for q in fs], [q[1] for q in fs]))))
            s.circulo(X(f), y, 3.8, col, col if pasa else E.PAPEL, 1.4)
            s.ancla(f'{lado} {int(f)}', X(f), y)
        res = [('Reproducibilidad', f"{r['reproducibility_pct']:.0f} %"),
               ('Bandas que pasan', f"{r['n_pass']} de {len(r['snr_per_band'])}")]
        for i, (rot, val) in enumerate(res):
            s.texto(x0 + i * pw / 2, mt + ph + 42, rot, E.T_CHICO, E.TENUE, 'start')
            s.texto(x0 + i * pw / 2, mt + ph + 54, val, E.T_ROTULO, E.TINTA_2, 'start', 600)
    s.texto(s.ancho / 2, mt + ph + 28, 'Frecuencia (Hz)', E.T_EJE, E.TENUE)
    s.texto(12, mt + ph / 2, 'dB SPL', E.T_EJE, E.TENUE, extra=f'transform="rotate(-90 12 {mt + ph / 2:.1f})"')
    return s.svg()


def dibujar_dpoae(caso, oidos=('OD', 'OI')):
    """DP-grama: nivel del producto de distorsión sobre el piso de ruido."""
    pw, ph, ml, mt, sep = 230, 150, 40, 30, 34
    s = Svg(ml + len(oidos) * pw + (len(oidos) - 1) * sep + 12, mt + ph + 66)
    y_min, y_max = -30, 20
    for k, lado in enumerate(oidos):
        col = E.COLOR_LADO[lado]
        r = dpoae(caso, lado)
        x0 = ml + k * (pw + sep)
        X, Y = _ejes(s, x0, mt, pw, ph, y_min, y_max, E.NOMBRE_LADO[lado], k == 0)
        f2 = [float(f) for f in r['f2_list']]
        piso = [(X(f), Y(nf)) for f, nf in zip(f2, r['noise_floors_db_spl'])]
        d = ('M' + ' L'.join(f'{x:.2f},{y:.2f}' for x, y in piso)
             + f' L{piso[-1][0]:.2f},{Y(y_min):.2f} L{piso[0][0]:.2f},{Y(y_min):.2f} Z')
        s.crudo(f'<path d="{d}" fill="{E.GRILLA}" stroke="none"/>')
        s.trazo([(X(f), Y(dp)) for f, dp in zip(f2, r['dp_levels_db_spl'])], col, E.LINEA)
        for p in r['points']:
            s.circulo(X(float(p['f2_hz'])), Y(p['dp_db']), 3.8, col, col if p['passed'] else E.PAPEL, 1.4)
            s.ancla(f"{lado} {int(float(p['f2_hz']))}", X(float(p['f2_hz'])), Y(p['dp_db']))
        s.texto(x0, mt + ph + 42, 'Frecuencias que pasan', E.T_CHICO, E.TENUE, 'start')
        s.texto(x0, mt + ph + 54, f"{r['n_pass']} de {r['n_total']}  ·  L1/L2 {r['l1_db']:g}/{r['l2_db']:g} dB SPL",
                E.T_ROTULO, E.TINTA_2, 'start', 600)
    s.texto(s.ancho / 2, mt + ph + 28, 'f2 (Hz)', E.T_EJE, E.TENUE)
    s.texto(12, mt + ph / 2, 'dB SPL', E.T_EJE, E.TENUE, extra=f'transform="rotate(-90 12 {mt + ph / 2:.1f})"')
    return s.svg()


def _interp(x, xs, ys):
    for i in range(1, len(xs)):
        if xs[i] >= x:
            t = (x - xs[i - 1]) / ((xs[i] - xs[i - 1]) or 1)
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]
