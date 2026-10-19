#!/usr/bin/env python3
"""b1-lam-*.svg (B1, vías centrales): láminas de varios paneles con los esquemas de la vía de labyrinthus3d,
una escena por panel (arcos del VOR por canal, otolitos, vestibuloespinal, flóculo fijando y ocluido, mirada,
tálamo y corteza, oculomotor, vía auditiva con lesiones y su PEAT, y el modo Patología caso por caso).
De frente: a la izquierda de cada esquema queda el lado DERECHO del paciente. Solo el esquema, sin interfaz.

labyrinthus3d NO se toca: se sirve de solo lectura y se maneja por el protocolo de DevTools de chromium
sin cabeza, con reloj virtual (se reutiliza la clase C de hacer_b1_vias_simulador.py). Las constantes del
simulador son órdenes de magnitud docentes, no valores de referencia.

    python3 -m http.server 8921 -d ~/Escritorio/Proyectos/labyrinthus3d &
    chromium --headless=new --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \\
        --window-size=1600,900 --remote-debugging-port=9921 --user-data-dir=/tmp/b1prof about:blank &
    python3 hacer_b1_laminas.py [lámina ...]      # sin argumentos, todas"""
import asyncio
import base64
import io
import pathlib
import sys

from PIL import Image, ImageChops

import hacer_b1_vias_simulador as B

AQUI = pathlib.Path(__file__).parent
TINTA, TENUE = '#24101a', '#8a8a90'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
IND = {0: 0, 0.25: 1, 1: 2, 3: 3, 7: 4, 14: 5, 30: 6, 90: 7}  # días desde la lesión -> índice del deslizador


async def pat(c, caso='sano', der=False, lesiones=None, dias=None, fija=True):
    """Deja la patología armada: un caso del simulador, o sitios a medida."""
    await c.vista('patologia')
    await c.elige('lab-caso', 'sano')
    await c.ev(f"(()=>{{const e=document.getElementById('lab-pat-der'); if(e.checked!=={str(der).lower()}) e.click()}})()")
    if caso != 'sano':
        await c.elige('lab-caso', caso)
    for sitio, estado in (lesiones or {}).items():
        await c.ev(f"(()=>{{const e=document.querySelector('select[data-canal=\"{sitio}\"]'); e.value='{estado}';"
                   "e.dispatchEvent(new Event('change',{bubbles:true}))})()")
    if dias is not None:
        await c.ev(f"(()=>{{const e=document.getElementById('lab-tiempo'); e.value='{IND[dias]}';"
                   "e.dispatchEvent(new Event('input',{bubbles:true})); e.dispatchEvent(new Event('change',{bubbles:true}))})()")
    await c.ev(f"document.getElementById('{'lab-fija-si' if fija else 'lab-fija-no'}').click()")
    await c.paso(10)


async def via(c, filtro, mov=None, n=12, **k):
    """El esquema de la vía con un filtro, con un impulso de cabeza a medio camino si se pide."""
    await pat(c, **k)
    await c.vista('via')
    await c.elige('lab-via-filtro', filtro)
    if mov:
        await c.elige('lab-lentitud', '10')
        await c.ev(f"document.querySelector('#lab-movimientos [data-mov={mov}]').click()")
        await c.paso(n)
    else:
        await c.paso(60)
    return await c.lienzo('lab-via')


async def ocu(c, tipo, filtro, eje=None, antes=None, n=80, **k):
    """Oculomotor: un estímulo y el filtro de la vía; `antes` es un guion JS previo (la silla, por ejemplo)."""
    await pat(c, **k)
    await c.vista('oculomotor')
    await c.elige('lab-est-tipo', tipo)
    if eje:
        await c.elige('lab-est-eje', eje)
    await c.elige('lab-est-via', filtro)
    if antes:
        await c.ev(antes)
    await c.paso(n)
    return await c.lienzo('lab-via')


def lam_vor():
    return [
        ('A', 'Canal lateral derecho excitado', 'giro de la cabeza a la derecha', lambda c: via(c, 'lateral', 'der')),
        ('B', 'Canal lateral derecho inhibido', 'giro de la cabeza a la izquierda', lambda c: via(c, 'lateral', 'izq')),
        ('C', 'Canales verticales: plano LARP', 'excita el anterior izquierdo, inhibe el posterior derecho', lambda c: via(c, 'larp', 'larp_abajo')),
        ('D', 'Canales verticales: plano RALP', 'excita el anterior derecho, inhibe el posterior izquierdo', lambda c: via(c, 'ralp', 'ralp_abajo')),
    ]


def lam_oto():
    sac = {'sac_izq': 'arreflexia', 'sac_der': 'arreflexia'}
    utr = {'utr_izq': 'arreflexia', 'utr_der': 'arreflexia'}
    return [
        ('A', 'Utrículo y sáculo sanos', 'las dos vías juntas', lambda c: via(c, 'otolitos')),
        ('B', 'Solo utrículo', 'sin sáculos: queda la vía hacia los ojos (oVEMP)', lambda c: via(c, 'otolitos', lesiones=sac)),
        ('C', 'Solo sáculo', 'sin utrículos: queda la vía hacia el cuello (cVEMP)', lambda c: via(c, 'otolitos', lesiones=utr)),
        ('D', 'Neuritis del nervio superior izquierdo', 'cae el utrículo, queda el sáculo', lambda c: via(c, 'otolitos', caso='neuritis_superior')),
    ]


def lam_flo():
    n = {'nsup_izq': 'arreflexia'}
    nf = {'nsup_izq': 'arreflexia', 'floculo_izq': 'arreflexia', 'floculo_der': 'arreflexia'}
    return [
        ('A', 'Neuritis izquierda, fijando', 'el flóculo frena los núcleos', lambda c: via(c, 'lateral', lesiones=n, dias=1, fija=True)),
        ('B', 'Neuritis izquierda, ocluido', 'sin blanco, el freno se apaga', lambda c: via(c, 'lateral', lesiones=n, dias=1, fija=False)),
        ('C', 'Neuritis y sin flóculos, fijando', 'no hay quién frene', lambda c: via(c, 'lateral', lesiones=nf, dias=1, fija=True)),
        ('D', 'Neuritis y sin flóculos, ocluido', 'igual que sin fijar', lambda c: via(c, 'lateral', lesiones=nf, dias=1, fija=False)),
    ]


def lam_mir():
    return [
        ('A', 'En reposo', 'integradores y generadores sanos', lambda c: via(c, 'mirada')),
        ('B', 'Sacada horizontal', 'durante la sacada: FRPP, omnipausa e integrador', lambda c: ocu(c, 'saltos', 'mirada', eje='horizontal')),
        ('C', 'Sacada vertical', 'durante la sacada: riMLF, omnipausa e integrador', lambda c: ocu(c, 'saltos', 'mirada', eje='vertical')),
        ('D', 'Integradores a medias', 'evocado por la mirada', lambda c: via(c, 'mirada', caso='integrador')),
    ]


def lam_perc():
    return [
        ('A', 'Sano', 'sensación de giro: ninguna; vertical recta', lambda c: via(c, 'percepcion')),
        ('B', 'Neuritis recién instalada', 'sensación de giro y vertical torcida', lambda c: via(c, 'percepcion', caso='neuritis_superior')),
        ('C', 'Pérdida unilateral compensada', 'a los 3 meses la sensación se fue', lambda c: via(c, 'percepcion', caso='perdida_unilateral')),
        ('D', 'Corteza vestibular izquierda lesionada', 'el laberinto y el tronco, sanos', lambda c: via(c, 'percepcion', lesiones={'pivc_izq': 'arreflexia'})),
    ]


def lam_oc1():
    return [
        ('A', 'Seguimiento lento', 'blanco que va y viene', lambda c: ocu(c, 'seno', 'seguimiento')),
        ('B', 'Sacadas voluntarias', 'blanco que salta', lambda c: ocu(c, 'saltos', 'sacadas')),
        ('C', 'Supresión del VOR', 'silla con un blanco que gira con ella', lambda c: ocu(c, 'supresion', 'seguimiento')),
        ('D', 'Optocinético', 'barras que corren', lambda c: ocu(c, 'optocinetico', 'optocinetico')),
    ]


def lam_oc2():
    g = "document.getElementById('lab-silla-der').click()"
    gf = g + ";window.__paso(200,0.05);document.getElementById('lab-silla-frena').click()"
    return [
        ('A', 'Silla rotatoria, girando a la derecha', 'se carga el almacenamiento de velocidad', lambda c: ocu(c, 'rotatoria', 'optocinetico', antes=g, n=120)),
        ('B', 'Al frenar', 'el almacenamiento descarga: post-rotatorio', lambda c: ocu(c, 'rotatoria', 'optocinetico', antes=gf, n=40, fija=False)),
        ('C', 'Sacudida cefálica', 'diez segundos a 2 Hz', lambda c: ocu(c, 'sacudida', 'optocinetico', n=100, fija=False)),
        ('D', 'Sin nódulo, al frenar', 'el almacenamiento no se descarga', lambda c: ocu(c, 'rotatoria', 'optocinetico', antes=gf, n=40, caso='nodulo', fija=False)),
    ]


def lam_pat1():
    return [('A', 'Neuritis vestibular superior izquierda', 'nervio superior', lambda c: via(c, 'otolitos', caso='neuritis_superior')),
            ('B', 'Neuritis vestibular inferior izquierda', 'nervio inferior', lambda c: via(c, 'otolitos', caso='neuritis_inferior')),
            ('C', 'Pérdida vestibular unilateral compensada', 'los dos nervios, a los 3 meses', lambda c: via(c, 'otolitos', caso='perdida_unilateral')),
            ('D', 'Infarto de la AICA izquierda', 'laberinto y flóculo', lambda c: via(c, 'todos', caso='aica'))]


def lam_pat2():
    return [('A', 'Núcleos vestibulares izquierdos', 'bulbo lateral; el nervio queda sano', lambda c: via(c, 'lateral', caso='nucleos_vestibulares')),
            ('B', 'Oftalmoplejía internuclear izquierda', 'FLM', lambda c: via(c, 'mirada', caso='flm')),
            ('C', 'Parálisis de la mirada horizontal izquierda', 'FRPP', lambda c: via(c, 'mirada', caso='frpp')),
            ('D', 'Nistagmo hacia arriba', 'los dos tractos tegmentales ventrales', lambda c: via(c, 'mirada', caso='upbeat'))]


def lam_pat3():
    return [('A', 'Degeneración cerebelosa', 'los dos flóculos', lambda c: via(c, 'mirada', caso='floculos')),
            ('B', 'Evocado por la mirada', 'integradores a medias', lambda c: via(c, 'mirada', caso='integrador')),
            ('C', 'Hipofunción bilateral', 'los dos laberintos a la mitad', lambda c: via(c, 'otolitos', caso='hipofuncion_bilateral')),
            ('D', 'Arreflexia bilateral', 'los dos laberintos perdidos', lambda c: via(c, 'otolitos', caso='arreflexia_bilateral'))]


def lam_pat4():
    return [('A', 'Neuritis superior, 6 horas', 'sin compensar', lambda c: via(c, 'lateral', caso='neuritis_superior', dias=0.25)),
            ('B', '3 días', 'el reposo se va equilibrando', lambda c: via(c, 'lateral', caso='neuritis_superior', dias=3)),
            ('C', '2 semanas', 'el núcleo recupera su disparo', lambda c: via(c, 'lateral', caso='neuritis_superior', dias=14)),
            ('D', '3 meses', 'compensada', lambda c: via(c, 'lateral', caso='neuritis_superior', dias=90))]


# Audición y postural usan otro módulo: sus láminas corren aparte.
async def aud_via(c, caso, vista='tronco'):
    await c.vista('audpat', 'audicion')
    await c.elige('aud-caso', caso)
    await c.paso(10)
    await c.vista(vista, 'audicion')
    await c.paso(40)
    return await c.lienzo('lab-aud', B.CAJA_AUD if vista == 'tronco' else None)


def lam_aud():
    return [('A', 'Vía auditiva sana', 'las dos vías, con sus cruces', lambda c: aud_via(c, 'sano')),
            ('B', 'Nervio: schwannoma del VIII izquierdo', 'el nervio a medias', lambda c: aud_via(c, 'schwannoma')),
            ('C', 'Tronco: complejo olivar izquierdo', 'perdido', lambda c: aud_via(c, 'tronco')),
            ('D', 'Colículo inferior izquierdo', 'perdido', lambda c: aud_via(c, 'coliculo'))]


def lam_peat():
    return [('A', 'Vía sana', 'ondas I a V, los dos oídos', lambda c: aud_via(c, 'sano', 'peat')),
            ('B', 'Nervio: schwannoma izquierdo', 'la I queda y todo lo siguiente se atrasa', lambda c: aud_via(c, 'schwannoma', 'peat')),
            ('C', 'Tronco: complejo olivar izquierdo', 'la IV disminuye', lambda c: aud_via(c, 'tronco', 'peat')),
            ('D', 'Colículo inferior izquierdo', 'las ondas del modelo no cambian', lambda c: aud_via(c, 'coliculo', 'peat'))]


async def post_via(c, capa, mov=None, ap=None):
    await c.vista('postvia', 'postural')
    await c.elige('post-via-capa', capa)
    if mov == 'mano':
        await c.ev("(()=>{const e=document.getElementById('post-inclina'); e.value='6';e.dispatchEvent(new Event('input',{bubbles:true}))})()")
    if ap is not None:
        await c.elige('post-via-mov', 'ap')
    await c.paso(60)
    return await c.lienzo('lab-post')


def lam_esp():
    return [('A', 'Vestibuloespinal, inclinado a un lado', 'canales, otolitos, núcleos vestibulares, cuello y piernas', lambda c: post_via(c, 'vestibular', 'mano')),
            ('B', 'Vestibuloespinal, adelante y atrás', 'sáculo, núcleos vestibulares, cuello y piernas', lambda c: post_via(c, 'vestibular', ap=1)),
            ('C', 'La vía propioceptiva', 'del tobillo al cerebelo y la corteza', lambda c: post_via(c, 'propioceptiva')),
            ('D', 'Lo que las junta', 'laberinto, propiocepción y vista', lambda c: post_via(c, 'integracion'))]


LAMINAS = {  # nombre: (módulo, función, paneles por fila)
    'vor': ('laberinto', lam_vor), 'oto': ('laberinto', lam_oto), 'flo': ('laberinto', lam_flo), 'mir': ('laberinto', lam_mir),
    'perc': ('laberinto', lam_perc), 'oc1': ('laberinto', lam_oc1), 'oc2': ('laberinto', lam_oc2),
    'pat1': ('laberinto', lam_pat1), 'pat2': ('laberinto', lam_pat2), 'pat3': ('laberinto', lam_pat3), 'pat4': ('laberinto', lam_pat4),
    'aud': ('audicion', lam_aud), 'peat': ('audicion', lam_peat), 'esp': ('postural', lam_esp),
}


def recorta(im, margen=14):
    """Quita el blanco que sobra alrededor del esquema."""
    caja = ImageChops.difference(im.convert('RGB'), Image.new('RGB', im.size, (255, 255, 255))).getbbox()
    if not caja:
        return im
    x0, y0, x1, y1 = caja
    return im.crop((max(0, x0 - margen), max(0, y0 - margen), min(im.width, x1 + margen), min(im.height, y1 + margen)))


def compone(nombre, paneles):
    paneles = [(a, b, c, recorta(im)) for a, b, c, im in paneles]
    cols, marco_t, ancho = 2, 62, 500
    w = ancho - 16
    hs = [round(w * im.height / im.width) for *_, im in paneles]
    fila_h = [max(hs[i:i + cols]) + marco_t for i in range(0, len(hs), cols)]
    W, H = cols * ancho + 20, sum(fila_h) + 10
    o = []
    for n, (letra, tit, sub, im) in enumerate(paneles):
        col, fila = n % cols, n // cols
        x, y = 10 + col * ancho, 6 + sum(fila_h[:fila])
        o.append(f'<text x="{x + 4}" y="{y + 22}" {F} font-size="20" font-weight="700" fill="{TINTA}">{letra}  {tit}</text>')
        o.append(f'<text x="{x + 4}" y="{y + 44}" {F} font-size="15" fill="{TENUE}">{sub}</text>')
        h = round(w * im.height / im.width)
        buf = io.BytesIO()
        im.resize((w * 2, h * 2), Image.LANCZOS).save(buf, 'JPEG', quality=86, optimize=True)
        o.append(f'<image x="{x + 8}" y="{y + marco_t - 8}" width="{w}" height="{h}" '
                 f'href="data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"/>')
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" '
         f'width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="#fff"/>' + ''.join(o) + '</svg>')
    (AQUI / f'b1-lam-{nombre}.svg').write_text(s, encoding='utf-8')
    print(f'b1-lam-{nombre}.svg', (W, H), flush=True)


async def main(quienes):
    c = B.C()
    await c.start(f'http://localhost:{B.HTTP}/index.html')
    await c.paso(5)
    for modulo in ('laberinto', 'audicion', 'postural'):
        nombres = [n for n in quienes if LAMINAS[n][0] == modulo]
        if not nombres:
            continue
        await c.ev(f"document.querySelector('[data-modulo-abre={modulo}]').click()")
        await c.paso(20)
        for n in nombres:
            paneles = []
            for letra, tit, sub, f in LAMINAS[n][1]():
                paneles.append((letra, tit, sub, await f(c)))
            compone(n, paneles)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:] or list(LAMINAS)))
