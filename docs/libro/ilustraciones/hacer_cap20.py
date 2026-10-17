#!/usr/bin/env python3
"""Ilustraciones del capítulo 20 (VEMP). Los trazos salen del motor del VEMP de LabSim
(src/vemp, importado SOLO PARA LEER), promediado como en la ventana del equipo, y se dibujan
en SVG propio con el estilo del libro. No son de un paciente real.

    cap20-ramas.svg   el mismo montaje con la lesión en cada rama: nervio superior,
                      nervio inferior y laberinto completo (LabSim no trae la neuritis como
                      cuadro: se arma aquí cambiando el tipo de lesión del oído derecho)
    cap20-oseo.svg    la otoesclerosis bilateral del caso 20.4 por vía aérea y por vía ósea

Las escalas de intensidad (dB SPL del aéreo, dB FL del vibrador) son las del simulador: se
rotulan como tales y no son valores de la literatura."""
import copy
import json
import pathlib
import sys

import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
LIBRO = AQUI.parent
RAIZ = LIBRO.parents[1]
sys.path.insert(0, str(LIBRO / 'figuras'))
from motor import estilo as E  # noqa: E402
from motor.datos import en_raiz, semilla  # noqa: E402
from motor.svg import Svg  # noqa: E402

CAMINO = LIBRO / 'casos' / 'generados'
SUBTIPOS = {'CVEMP': ('Rotación cefálica sostenida', {'p13': 13, 'n23': 23}, 'cVEMP'),
            'OVEMP': ('Mirada superior ~30°', {'n10': 10, 'p16': 16}, 'oVEMP')}
ROTULO = {'p13': 'P13', 'n23': 'N23', 'n10': 'n10', 'p16': 'p16'}


def caso(nombre):
    return json.loads((CAMINO / f'cap20_{nombre}.json').read_text(encoding='utf-8'))['data']


def con_oido(data, lado, tipo, cvemp, ovemp):
    """Copia del caso con el tipo de lesión y los umbrales del VEMP de un oído."""
    d = copy.deepcopy(data)
    o = d['VEMP'][lado]
    o['type'] = tipo
    o['subtipos']['CVEMP']['umbral'] = cvemp
    o['subtipos']['OVEMP']['umbral'] = ovemp
    return d


def registrar(data, lado, clave, transductor='aereo', intensidad=100, promedios=200, etiqueta=''):
    from vemp import engine, patient, protocol
    from vemp.engine import Ajustes, MotorVemp
    from vemp.session import Sesion
    maniobra, bases, _ = SUBTIPOS[clave]
    sub = getattr(protocol, clave)
    with en_raiz():
        pac = patient.desde_caso(data)
        mot = MotorVemp(pac, rng=np.random.default_rng(semilla('cap20', etiqueta, lado, clave, transductor)))
        aju = Ajustes(subtipo=sub, lado=lado, intensidad=intensidad, promedios=promedios, maniobra=maniobra,
                      transductor=protocol.OSEO if transductor == 'oseo' else protocol.AEREO)
        ses = Sesion()
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
        return {'x': [float(v) for v in reg.x], 'y': [float(v) for v in reg.y], 'marcas': marcas,
                'p2p': float(reg.p2p()), 'corr': float(reg.p2p_corregida())}


def panel(s, x0, y0, w, h, r, lado, lim, ms_max, rotulos=True):
    col = E.COLOR_LADO[lado]

    def X(t):
        return x0 + t / ms_max * w

    def Y(v):
        return y0 + h / 2 - v / lim * (h / 2)

    for t in range(0, int(ms_max) + 1, 10):
        s.linea(X(t), y0, X(t), y0 + h, E.GRILLA, 1)
    s.linea(x0, Y(0), x0 + w, Y(0), E.GRILLA_FUERTE, 1)
    s.trazo([(X(t), Y(v)) for t, v in zip(r['x'], r['y']) if 0 <= t <= ms_max], col, E.LINEA)
    for p, (lat, amp) in r['marcas'].items():
        arriba = amp >= 0
        s.linea(X(lat), Y(amp) + (-3 if arriba else 3), X(lat), Y(amp) + (-8 if arriba else 8), E.TINTA_2, 0.8)
        s.texto(X(lat), Y(amp) + (-10 if arriba else 16), ROTULO[p], E.T_CHICO, E.TINTA, peso=600)
    s.texto(x0, y0 + h + 24, f"{r['p2p']:.0f} µV  ·  corregida {r['corr']:.2f}".replace('.', ','),
            E.T_CHICO, E.TINTA_2, 'start', 600)
    return


def lienzo(filas, columnas, titulo_filas, titulo_cols, regs, ms=(50, 40), fuera=''):
    """filas x columnas de paneles. regs[(i, j)] = registro; columnas = (clave, lado)."""
    pw, ph, gx, gy, ml, mt = 150, 70, 14, 40, 118, 34
    ancho = ml + len(columnas) * pw + (len(columnas) - 1) * gx + 10
    alto = mt + len(titulo_filas) * (ph + gy) + 8
    s = Svg(ancho, alto)
    # límites comunes por subtipo
    lims = {}
    for (i, j), r in regs.items():
        clave = columnas[j][0]
        m = max(abs(min(r['y'])), abs(max(r['y'])))
        lims[clave] = max(lims.get(clave, 0), m)
    for j, (clave, lado) in enumerate(columnas):
        x0 = ml + j * (pw + gx)
        s.texto(x0, 14, titulo_cols[j][0], E.T_TITULO, E.COLOR_LADO[lado], 'start', 700)
        s.texto(x0, 25, titulo_cols[j][1], E.T_CHICO, E.TENUE, 'start')
    for i, nom in enumerate(titulo_filas):
        y0 = mt + i * (ph + gy)
        for k, linea in enumerate(nom):
            s.texto(ml - 10, y0 + ph / 2 - 4 + k * 11, linea, E.T_ROTULO if k == 0 else E.T_CHICO,
                    E.TINTA if k == 0 else E.TENUE, 'end', 700 if k == 0 else 400)
        for j, (clave, lado) in enumerate(columnas):
            panel(s, ml + j * (pw + gx), y0, pw, ph, regs[(i, j)], lado, lims[clave] * 1.2, ms[0] if clave == 'CVEMP' else ms[1])
    s.texto(ancho - 10, alto - 2, fuera, E.T_CHICO, E.TENUE, 'end')
    return s


def ramas():
    base = caso('meniere')                      # el OI es normal
    # Los tres oídos derechos: el OI sigue siendo el mismo, normal
    escenas = [
        (['Rama superior', 'oVEMP cae'], con_oido(base, 'OD', 'utricular', 65, 95)),
        (['Rama inferior', 'cVEMP cae'], con_oido(base, 'OD', 'sacular', 95, 65)),
        (['Laberinto o nervio', 'los dos caen'], con_oido(base, 'OD', 'neural', 95, 95)),
    ]
    columnas = [('CVEMP', 'OD'), ('CVEMP', 'OI'), ('OVEMP', 'OD'), ('OVEMP', 'OI')]
    cab = [('cVEMP · OD', 'cuello derecho'), ('cVEMP · OI', 'cuello izquierdo'),
           ('oVEMP · OD', 'bajo el ojo izquierdo'), ('oVEMP · OI', 'bajo el ojo derecho')]
    regs = {}
    for i, (_, d) in enumerate(escenas):
        for j, (clave, lado) in enumerate(columnas):
            regs[(i, j)] = registrar(d, lado, clave, etiqueta=f'ramas{i}')
    s = lienzo(3, columnas, [e[0] for e in escenas], cab, regs,
               fuera='Registros simulados; las líneas verticales marcan cada 10 ms.')
    return s, regs


def oseo():
    d = caso('otoesclerosis')
    columnas = [('CVEMP', 'OD'), ('CVEMP', 'OI'), ('OVEMP', 'OD'), ('OVEMP', 'OI')]
    cab = [('cVEMP · OD', 'cuello derecho'), ('cVEMP · OI', 'cuello izquierdo'),
           ('oVEMP · OD', 'bajo el ojo izquierdo'), ('oVEMP · OI', 'bajo el ojo derecho')]
    filas = [['Vía aérea', '100 dB SPL (LabSim)'], ['Vía ósea', '70 dB FL (LabSim)']]
    regs = {}
    for j, (clave, lado) in enumerate(columnas):
        regs[(0, j)] = registrar(d, lado, clave, 'aereo', 100, etiqueta='oseo')
        regs[(1, j)] = registrar(d, lado, clave, 'oseo', 70, etiqueta='oseo')
    s = lienzo(2, columnas, filas, cab, regs,
               fuera='Registros simulados; las escalas de intensidad son las del simulador.')
    return s, regs


if __name__ == '__main__':
    for nombre, f in (('cap20-ramas.svg', ramas), ('cap20-oseo.svg', oseo)):
        s, regs = f()
        (AQUI / nombre).write_text(s.svg(), encoding='utf-8')
        print(nombre)
        for (i, j), r in sorted(regs.items()):
            print(' ', i, j, f"{r['p2p']:.0f} uV corr {r['corr']:.2f}", {k: round(v[0], 1) for k, v in r['marcas'].items()})
