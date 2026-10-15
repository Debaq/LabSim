"""Acumetría: Weber y Rinne por frecuencia, con la convención de la ficha.

Weber: dos flechas fijas por fila, la izquierda SIEMPRE roja (OD) y la
derecha SIEMPRE azul (OI); se dibuja la del lado al que lateraliza, o las
dos si no lateraliza (CaseSheetPdf::acumetria). Rinne: positivo (CA > CO),
negativo (CO > CA) o falso negativo (sensorioneural profunda: contesta el
oído contrario por vía ósea).
"""
from . import estilo as E
from .svg import Svg

FRECUENCIAS = ['500', '1000']
RINNE = {'positivo': ('+', 'Positivo'), 'negativo': ('−', 'Negativo'), 'falso_negativo': ('−*', 'Falso negativo')}


def dibujar(caso):
    weber = caso.get('Weber') or {}
    rinne = caso.get('Rinne') or {}
    fila, ml, mt = 58, 92, 40
    s = Svg(560, mt + fila * len(FRECUENCIAS) + 34)
    cx = ml + 120                                  # centro de la cabeza
    s.texto(cx, mt - 18, 'Weber', E.T_TITULO, E.TINTA, peso=600)
    s.texto(cx - 62, mt - 4, 'OD', E.T_CHICO, E.OD, peso=600)
    s.texto(cx + 62, mt - 4, 'OI', E.T_CHICO, E.OI, peso=600)
    s.texto(ml + 330, mt - 18, 'Rinne', E.T_TITULO, E.TINTA, peso=600)
    s.texto(ml + 300, mt - 4, 'OD', E.T_CHICO, E.OD, peso=600)
    s.texto(ml + 380, mt - 4, 'OI', E.T_CHICO, E.OI, peso=600)
    for i, f in enumerate(FRECUENCIAS):
        y = mt + 12 + i * fila + fila / 2 - 10
        if i % 2 == 0:
            s.rect(0, y - fila / 2 + 4, s.ancho, fila - 8, E.LAVADO)
        s.texto(14, y + 4, f'{int(f):,} Hz'.replace(',', '.'), E.T_ROTULO, E.TINTA_2, 'start', 600)
        # cabeza vista de frente: un círculo con las dos orejas
        s.circulo(cx, y, 15, E.TENUE, E.PAPEL, 1)
        s.rect(cx - 19, y - 5, 4, 10, E.TENUE)
        s.rect(cx + 15, y - 5, 4, 10, E.TENUE)
        w = str(weber.get(f, '')).lower()
        for lado, signo, col in (('od', -1, E.OD), ('oi', 1, E.OI)):
            if w in (lado, 'centrado'):
                x0, x1 = cx + signo * 24, cx + signo * 56
                s.linea(x0, y, x1, y, col, 1.8)
                s.camino(f'M{x1 - signo * 7:.1f},{y - 5:.1f} L{x1:.1f},{y:.1f} L{x1 - signo * 7:.1f},{y + 5:.1f}', col, 1.8)
        lectura = {'od': 'lateraliza al OD', 'oi': 'lateraliza al OI', 'centrado': 'no lateraliza'}.get(w, 'sin dato')
        s.texto(cx, y + 28, lectura, E.T_CHICO, E.TENUE)
        s.ancla(f'weber {f}', cx, y - 16)
        for lado, x in (('od', ml + 300), ('oi', ml + 380)):
            v = str((rinne.get(f) or {}).get(lado, '')).lower()
            simbolo, texto = RINNE.get(v, ('?', 'sin dato'))
            col = E.OD if lado == 'od' else E.OI
            s.circulo(x, y - 2, 12, col, E.PAPEL, 1.4)
            s.texto(x, y + 3, simbolo, 12, col, peso=700)
            s.texto(x, y + 26, texto, E.T_CHICO, E.TENUE)
            s.ancla(f'rinne {lado.upper()} {f}', x, y - 2)
    s.texto(ml + 330, s.alto - 8, '+ conducción aérea mejor que la ósea · − ósea mejor que aérea · −* falso negativo',
            E.T_CHICO, E.TENUE)
    return s.svg()
