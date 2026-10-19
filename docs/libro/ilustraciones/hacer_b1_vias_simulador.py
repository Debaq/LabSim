#!/usr/bin/env python3
"""b1-sim-*.png y b1-sim-patologia-a/b.svg (B1, vías centrales): los esquemas de la vía de labyrinthus3d
(auditiva, arco del reflejo vestíbulo-ocular, otolitos, mirada y fase rápida, tálamo y corteza,
sacadas y seguimiento) y un panel de lesiones con el modo Patología. De frente: a la izquierda de cada
esquema queda el lado DERECHO del paciente. Solo el esquema, sin nada de la interfaz.

labyrinthus3d NO se toca: se sirve de solo lectura y se maneja por el protocolo de DevTools de
chromium sin cabeza, con reloj virtual. Cada esquema es un <canvas> propio: se lee entero con
toDataURL y se pone sobre blanco. Las constantes del simulador son órdenes de magnitud docentes.

    python3 -m http.server 8921 -d ~/Escritorio/Proyectos/labyrinthus3d &
    chromium --headless=new --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \\
        --window-size=1600,900 --remote-debugging-port=9921 --user-data-dir=/tmp/b1prof about:blank &
    python3 hacer_b1_vias_simulador.py"""
import asyncio
import base64
import io
import json
import os
import pathlib
import urllib.request

import websockets
from PIL import Image

AQUI = pathlib.Path(__file__).parent
HTTP, DEVTOOLS = int(os.environ.get('HTTP', 8921)), int(os.environ.get('DEVTOOLS', 9921))

INIT = """
(()=>{ let vt=1000; const cbs=[]; performance.now=()=>vt;
 window.requestAnimationFrame=(cb)=>{cbs.push(cb);return cbs.length};
 window.cancelAnimationFrame=()=>{};
 window.__paso=(n,dt)=>{ for(let i=0;i<n;i++){ vt+=dt*1000; const l=cbs.splice(0); for(const f of l) f(vt);} return vt; };
})();
"""
# Del <canvas> de la vía auditiva (px de CSS; el lienzo va a x2): el esquema, sin el recuadro de la fuente.
CAJA_AUD = (0, 140, 505, 712)


class C:
    async def start(self, url):
        tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{DEVTOOLS}/json'))
        t = [x for x in tabs if x['type'] == 'page'][0]
        self.ws = await websockets.connect(t['webSocketDebuggerUrl'], max_size=None)
        self.i = 0
        await self.send('Page.enable')
        await self.send('Runtime.enable')
        await self.send('Page.setBypassCSP', enabled=True)
        await self.send('Page.addScriptToEvaluateOnNewDocument', source=INIT)
        await self.send('Emulation.setDeviceMetricsOverride', width=1600, height=900, deviceScaleFactor=2, mobile=False)
        await self.send('Page.navigate', url=url)
        await asyncio.sleep(9)

    async def send(self, m, **p):
        self.i += 1
        i = self.i
        await self.ws.send(json.dumps({'id': i, 'method': m, 'params': p}))
        while True:
            r = json.loads(await self.ws.recv())
            if r.get('id') == i:
                return r

    async def ev(self, js):
        r = await self.send('Runtime.evaluate', expression=js, awaitPromise=True, returnByValue=True)
        return r.get('result', {}).get('result', {}).get('value', r)

    async def paso(self, n=60):
        await self.ev(f'window.__paso({n},0.05)')

    async def elige(self, id_, valor):
        await self.ev(f"(()=>{{const e=document.getElementById('{id_}'); e.value='{valor}';"
                      "e.dispatchEvent(new Event('change',{bubbles:true}))})()")

    async def vista(self, v, modulo=None):
        sel = f'[data-vista={v}][data-modulo={modulo}]' if modulo else f'[data-vista={v}]:not([data-modulo])'
        await self.ev(f"document.querySelector('{sel}').click()")
        await self.paso(15)

    async def lienzo(self, id_, caja=None):
        url = await self.ev(f"document.getElementById('{id_}').toDataURL('image/png')")
        im = Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGBA')
        if caja:
            k = im.width / 718
            im = im.crop(tuple(round(v * k) for v in caja))
        fondo = Image.new('RGBA', im.size, (255, 255, 255, 255))
        fondo.alpha_composite(im)
        return fondo.convert('RGB')


def guarda(im, nombre):
    im.save(AQUI / nombre, optimize=True)
    print(nombre, im.size, flush=True)


async def capturas():
    c = C()
    await c.start(f'http://localhost:{HTTP}/index.html')
    await c.paso(5)

    # Audición: la vía auditiva (pestaña Tronco).
    await c.ev("document.querySelector('[data-modulo-abre=audicion]').click()")
    await c.paso(20)
    await c.vista('tronco', 'audicion')
    await c.paso(60)
    guarda(await c.lienzo('lab-aud', CAJA_AUD), 'b1-sim-auditiva.png')

    # Vestibular, modo Vía: un filtro por imagen.
    await c.ev("document.querySelector('[data-modulo-abre=laberinto]').click()")
    await c.paso(20)
    await c.vista('via')
    for filtro, nombre in [('lateral', 'vor'), ('otolitos', 'otolitos'), ('mirada', 'mirada'), ('percepcion', 'percepcion')]:
        await c.elige('lab-via-filtro', filtro)
        await c.paso(60)
        guarda(await c.lienzo('lab-via'), f'b1-sim-{nombre}.png')

    # Oculomotor: la vía de las sacadas y la del seguimiento (con el estímulo que las usa).
    await c.vista('oculomotor')
    for tipo, filtro, nombre in [('saltos', 'sacadas', 'sacadas'), ('seno', 'seguimiento', 'seguimiento')]:
        await c.elige('lab-est-tipo', tipo)
        await c.elige('lab-est-via', filtro)
        await c.paso(60)
        guarda(await c.lienzo('lab-via'), f'b1-sim-{nombre}.png')

    # Patología: cada lesión, con el filtro que la muestra. Lado izquierdo (a la derecha del esquema).
    crudos = {}
    for caso, filtro in PANELES:
        await c.vista('patologia')
        await c.elige('lab-caso', caso)
        await c.paso(10)
        await c.vista('via')
        await c.elige('lab-via-filtro', filtro)
        await c.paso(60)
        crudos[caso] = await c.lienzo('lab-via')
    return crudos


PANELES = [('neuritis_superior', 'otolitos'), ('neuritis_inferior', 'otolitos'), ('aica', 'todos'),
           ('nucleos_vestibulares', 'lateral'), ('flm', 'mirada'), ('floculos', 'mirada'), ('integrador', 'mirada')]
TITULOS = {
    'neuritis_superior': ('A', 'Neuritis vestibular superior izquierda', 'nervio superior: lateral, anterior y utrículo'),
    'neuritis_inferior': ('B', 'Neuritis vestibular inferior izquierda', 'nervio inferior: posterior y sáculo'),
    'aica': ('C', 'Infarto de la AICA izquierda', 'laberinto entero y flóculo del mismo lado'),
    'nucleos_vestibulares': ('D', 'Núcleos vestibulares izquierdos', 'tronco (bulbar lateral); el nervio queda sano'),
    'flm': ('E', 'Oftalmoplejía internuclear izquierda', 'el FLM interrumpido'),
    'floculos': ('F', 'Degeneración cerebelosa', 'los dos flóculos'),
    'integrador': ('G', 'Evocado por la mirada', 'integradores a medias (NPH y Cajal)'),
}
TINTA, TENUE = '#24101a', '#8a8a90'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""


def panel_svg(crudos):
    """Dos figuras de dos columnas: A-D (nervio, laberinto y núcleos) y E-G (FLM, cerebelo,
    integradores), esta con la clave de lectura en la cuarta celda."""
    grupos = [('b1-sim-patologia-a.svg', ['neuritis_superior', 'neuritis_inferior', 'aica', 'nucleos_vestibulares'], 2),
              ('b1-sim-patologia-b.svg', ['flm', 'floculos', 'integrador'], 2)]
    marco_t = 62
    for nombre, casos, cols in grupos:
        ancho = 1000 // cols
        filas = (len(casos) + cols - 1) // cols
        w = ancho - 16
        hs = [round(w * crudos[c].height / crudos[c].width) for c in casos]
        alto = max(hs) + marco_t
        W, H = cols * ancho + 20, filas * alto + 10
        o = []
        for n, caso in enumerate(casos):
            im = crudos[caso]
            col, fila = n % cols, n // cols
            x, y = 10 + col * ancho, 6 + fila * alto
            letra, tit, sub = TITULOS[caso]
            tam = 21 if cols == 2 else 17
            o.append(f'<text x="{x + 4}" y="{y + 22}" {F} font-size="{tam}" font-weight="700" fill="{TINTA}">{letra}  {tit}</text>')
            o.append(f'<text x="{x + 4}" y="{y + 44}" {F} font-size="{tam - 6}" fill="{TENUE}">{sub}</text>')
            h = round(w * im.height / im.width)
            buf = io.BytesIO()
            im.resize((w * 2, h * 2), Image.LANCZOS).save(buf, 'PNG', optimize=True)
            o.append(f'<image x="{x + 8}" y="{y + marco_t - 8}" width="{w}" height="{h}" '
                     f'href="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"/>')
        if len(casos) % cols:
            x, y = 10 + ancho + 40, 6 + (filas - 1) * alto + 140
            lineas = [('Cómo se lee', True), ('Izquierda del esquema: lado derecho', False), ('del paciente.', False), ('', False),
                      ('Cruz verde: sitio perdido.', False), ('Raya verde: sitio a medias.', False), ('', False),
                      ('Trazos rojizos: la vía dispara', False), ('más que en reposo; azules,', False),
                      ('menos; grises, como en reposo.', False)]
            for k, (txt, neg) in enumerate(lineas):
                o.append(f'<text x="{x}" y="{y + k * 30}" {F} font-size="{21 if neg else 18}" '
                         f'font-weight="{700 if neg else 400}" fill="{TINTA}">{txt}</text>')
        s = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" '
             f'width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="#fff"/>' + ''.join(o) + '</svg>')
        (AQUI / nombre).write_text(s, encoding='utf-8')
        print(nombre, (W, H))


def crudos_de(carpeta):
    """Para rehacer solo los paneles con lienzos ya capturados: <carpeta>/<caso>_<filtro>.png."""
    return {c: Image.open(pathlib.Path(carpeta) / f'{c}_{f}.png').convert('RGB') for c, f in PANELES}


if __name__ == '__main__':
    import sys
    # Con un argumento, solo rehace los paneles a partir de lienzos ya capturados en esa carpeta.
    panel_svg(crudos_de(sys.argv[1]) if len(sys.argv) > 1 else asyncio.run(capturas()))
