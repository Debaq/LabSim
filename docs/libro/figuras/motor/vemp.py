"""VEMP con el motor de la app (src/vemp), promediado como en la ventana.

La ventana arma MotorVemp sin semilla (cada corrida sale distinta); el
libro le pasa una propia por paciente, oído y subtipo para que la figura no
cambie al rehacerla. El promediado replica _tick_registro de la ventana
(EMG instantáneo por tick + lote + acumular), y las marcas y la asimetría
son las de la sesión del equipo (pico_cercano, Sesion.resumen).
"""
from . import estilo as E
from .datos import en_raiz, semilla
from .svg import Svg

SUBTIPOS = {
    'cvemp': ('CVEMP', 'Rotación cefálica sostenida', {'p13': 13, 'n23': 23}),
    'ovemp': ('OVEMP', 'Mirada superior ~30°', {'n10': 10, 'p16': 16}),
}
ROTULO = {'p13': 'P13', 'n23': 'N23', 'n10': 'n10', 'p16': 'p16'}


def registrar(caso, subtipo='cvemp', intensidad=100, promedios=200):
    import numpy as np
    from vemp import engine, patient, protocol
    from vemp.engine import Ajustes, MotorVemp
    from vemp.session import Sesion
    clave, maniobra, bases = SUBTIPOS[subtipo]
    sub = getattr(protocol, clave)
    with en_raiz():
        pac = patient.desde_caso(caso)
        ses = Sesion()
        out = {}
        for lado in ('OD', 'OI'):
            mot = MotorVemp(pac, rng=np.random.default_rng(semilla('vemp', caso.get('id'), lado, clave)))
            aju = Ajustes(subtipo=sub, lado=lado, intensidad=intensidad, promedios=promedios, maniobra=maniobra)
            reg = ses.nuevo(aju, mot.eje(sub))
            seg = 0.0
            bpt = max(int(round(aju.promedios / min(max(aju.promedios / 12.0, 14), 70))), 1)
            while reg.aceptados < aju.promedios:
                emg = mot.emg_instantaneo(sub, maniobra, seg)
                reg.acumular(mot.lote(aju, emg, min(bpt, aju.promedios - reg.aceptados)))
                seg += engine.duracion_segundos(bpt, aju.tasa)
            marcas = {}
            for p in reg.picos_esperados:
                lat, amp = reg.pico_cercano(bases[p], p)
                reg.marcar(p, lat, amp)
                marcas[p] = (float(lat), float(amp))
            x, y = reg.x, reg.y
            out[lado] = {'x': [float(v) for v in x], 'y': [float(v) for v in y], 'marcas': marcas,
                         'p2p': float(reg.p2p()), 'p2p_corr': float(reg.p2p_corregida())}
        out['resumen'] = ses.resumen(sub)
    return out


def dibujar(caso, subtipo='cvemp', intensidad=100, promedios=200, ms_max=50.0):
    r = registrar(caso, subtipo, intensidad, promedios)
    pw, ph, ml, mt, sep = 240, 140, 40, 30, 34
    s = Svg(ml + 2 * pw + sep + 12, mt + ph + 80)
    todos = [v for l in ('OD', 'OI') for t, v in zip(r[l]['x'], r[l]['y']) if 0 <= t <= ms_max]
    lim = max(abs(min(todos)), abs(max(todos))) * 1.2
    for k, lado in enumerate(('OD', 'OI')):
        col = E.COLOR_LADO[lado]
        x0 = ml + k * (pw + sep)

        def X(t):
            return x0 + t / ms_max * pw

        def Y(v):
            return mt + ph / 2 - v / lim * (ph / 2)

        for t in range(0, int(ms_max) + 1, 10):
            s.linea(X(t), mt, X(t), mt + ph, E.GRILLA, 1)
            s.texto(X(t), mt + ph + 14, t, E.T_EJE, E.TENUE)
        s.linea(x0, Y(0), x0 + pw, Y(0), E.GRILLA_FUERTE, 1)
        s.texto(x0, mt - 12, E.NOMBRE_LADO[lado], E.T_TITULO, E.TINTA, 'start', 600)
        d = r[lado]
        s.trazo([(X(t), Y(v)) for t, v in zip(d['x'], d['y']) if 0 <= t <= ms_max], col, E.LINEA)
        for p, (lat, amp) in d['marcas'].items():
            arriba = amp >= 0
            s.linea(X(lat), Y(amp) + (-4 if arriba else 4), X(lat), Y(amp) + (-10 if arriba else 10), E.TINTA_2, 0.8)
            s.texto(X(lat), Y(amp) + (-13 if arriba else 20), ROTULO.get(p, p), E.T_CHICO, E.TINTA, peso=600)
        res = [('Amplitud pico a pico', f"{d['p2p']:.0f} µV"),
               ('Corregida por EMG', f"{d['p2p_corr']:.2f}".replace('.', ','))]
        for i, (rot, val) in enumerate(res):
            s.texto(x0 + i * pw / 2, mt + ph + 42, rot, E.T_CHICO, E.TENUE, 'start')
            s.texto(x0 + i * pw / 2, mt + ph + 54, val, E.T_ROTULO, E.TINTA_2, 'start', 600)
    ratio = r['resumen'].get('ratio')
    if ratio is not None:
        s.texto(ml, mt + ph + 74, f'Razón de asimetría (amplitud corregida): {ratio:.0f} %'.replace('.', ','),
                E.T_ROTULO, E.TINTA_2, 'start')
    s.texto(s.ancho / 2, mt + ph + 28, 'Latencia (ms)', E.T_EJE, E.TENUE)
    return s.svg()
