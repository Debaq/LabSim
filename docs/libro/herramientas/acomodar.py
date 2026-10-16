"""Acomodo de figuras: que el texto suba cuando una figura no cabe.

WeasyPrint no tiene "figuras flotantes": una figura que no cabe en lo que
queda de página salta entera a la siguiente y deja un hueco. Este módulo
compone el documento, busca esos huecos y adelanta el párrafo que sigue a la
figura para que lo llene, como haría un diagramador. Repite hasta que no
quedan huecos grandes o ya no hay qué mover.

Solo mueve párrafos y listas (nunca títulos, recuadros ni casos), y solo los
que vienen inmediatamente después de la figura: el orden del texto no cambia,
solo la figura queda un poco más abajo.
"""
import logging

import lxml.html
from weasyprint import HTML

HUECO_MAX = 0.30        # fracción de página vacía al pie que ya se considera hueco
ARRIBA_PX = 40          # la figura "salta" si empieza en los primeros px del contenido
VUELTAS = 8
MOVIBLES = ('p', 'ul', 'ol')


def _es_figura(el):
    """Bloques que no se parten y por eso pueden dejar hueco: figuras y
    recuadros."""
    clases = (el.get('class') or '').split()
    return ('figobs' in clases or (el.tag == 'figure' and 'ilustracion' in clases)
            or (el.tag == 'aside' and 'caja' in clases))


def _cajas(caja):
    """Las cajas del contenido de la página (sin entrar a los márgenes, donde
    van el número de página y el título corrido)."""
    if type(caja).__name__ == 'MarginBox':
        return
    yield caja
    for hija in getattr(caja, 'children', None) or []:
        yield from _cajas(hija)


def _hueco(pagina):
    """Fracción vacía al pie del área de contenido de una página."""
    pb = pagina._page_box
    arriba, alto = pb.content_box_y(), pb.height
    fondo = arriba
    for c in _cajas(pb):
        nombre = type(c).__name__
        if nombre in ('PageBox', 'MarginBox') or not hasattr(c, 'position_y'):
            continue
        if nombre in ('LineBox', 'InlineReplacedBox', 'BlockReplacedBox', 'TableBox') and c.height:
            fondo = max(fondo, c.position_y + c.height)
    return max(0.0, (arriba + alto - fondo) / alto) if alto else 0.0


def _unidad(el):
    """Lo que se puede subir empezando en `el`: un párrafo o lista, o un
    subtítulo (h3/h4) junto con el párrafo que lo sigue (nunca un subtítulo
    solo, que quedaría huérfano)."""
    if el is None:
        return []
    if el.tag in MOVIBLES:
        return [el]
    if el.tag in ('h3', 'h4'):
        nxt = el.getnext()
        if nxt is not None and nxt.tag in MOVIBLES:
            return [el, nxt]
    return []


def _clases(el):
    return (el.get('class') or '').split() if el is not None else []


def _subir_siguiente(fig):
    """Pone antes de la figura el texto que la sigue (saltando hasta dos
    figuras seguidas). Devuelve False si no hay nada movible."""
    sig, saltadas = fig.getnext(), 0
    while sig is not None and _es_figura(sig) and saltadas < 2:
        sig, saltadas = sig.getnext(), saltadas + 1
    origen_col = None
    if sig is not None and 'dos-col' in _clases(sig):
        origen_col = sig
        sig = sig[0] if len(sig) else None
    unidad = _unidad(sig)
    if not unidad:
        return False
    for el in unidad:
        el.getparent().remove(el)
    previo = fig.getprevious()
    if origen_col is not None:
        # venía de una sección a dos columnas: se suma a la columna anterior
        # a la figura, o abre una nueva
        if previo is not None and 'dos-col' in _clases(previo):
            destino = previo
        else:
            destino = lxml.html.Element('div', {'class': 'dos-col'})
            fig.addprevious(destino)
        for el in unidad:
            destino.append(el)
        if not len(origen_col) and not (origen_col.text or '').strip():
            origen_col.getparent().remove(origen_col)
    else:
        for el in unidad:
            fig.addprevious(el)
    return True


def _puntaje(render):
    """Cuánto hueco grande hay (sin contar la última página, que termina el
    capítulo donde le toca)."""
    return sum(h for h in (_hueco(p) for p in render.pages[:-1]) if h >= HUECO_MAX)


def componer(doc, base_url):
    """Compone `doc` (HTML completo) acomodando figuras y recuadros. Devuelve
    el documento de WeasyPrint ya compuesto (para write_pdf o leer páginas).
    Cada movida se acepta solo si baja el total de huecos; si no, se deshace."""
    import copy
    logging.getLogger('weasyprint').setLevel(logging.ERROR)
    raiz = lxml.html.document_fromstring(doc)
    bloques = [el for el in raiz.iter() if isinstance(el.tag, str) and _es_figura(el)]
    if not bloques:
        return HTML(string=doc, base_url=base_url).render()
    for i, el in enumerate(bloques):
        el.set('id', el.get('id') or f'acomodo-{i}')

    def render_de(r):
        return HTML(string=lxml.html.tostring(r, encoding='unicode', doctype='<!doctype html>'),
                    base_url=base_url).render()

    mejor = render_de(raiz)
    puntaje = _puntaje(mejor)
    intentadas = set()
    for _ in range(VUELTAS):
        if puntaje == 0:
            break
        candidata = None
        for p, pagina in enumerate(mejor.pages[1:], start=1):
            if _hueco(mejor.pages[p - 1]) < HUECO_MAX:
                continue
            arriba = pagina._page_box.content_box_y()
            for ancla, (x, y, *_r) in pagina.anchors.items():
                if ancla.startswith('acomodo-') and ancla not in intentadas and y - arriba <= ARRIBA_PX:
                    candidata = ancla
                    break
            if candidata:
                break
        if not candidata:
            break
        prueba = copy.deepcopy(raiz)
        intentadas.add(candidata)
        if not _subir_siguiente(prueba.get_element_by_id(candidata)):
            continue
        render = render_de(prueba)
        nuevo = _puntaje(render)
        if nuevo < puntaje:
            raiz, mejor, puntaje = prueba, render, nuevo
            intentadas.discard(candidata)      # puede necesitar otro párrafo más
    return mejor
