#!/usr/bin/env python3
"""h10-generadores.svg (H10, PEAT): A, la vía auditiva de un paciente simulado, de la cóclea a la
corteza, de frente (a la izquierda de la figura queda el lado derecho); B, su PEAT a 80 dB con las
ondas I a V y los interpicos.

A es el esquema de labyrinthus3d, que NO se toca: se sirve de solo lectura, se maneja por el protocolo
de DevTools de chromium sin cabeza con reloj virtual, y del <canvas> de la vía se recorta solo el
esquema (sin el recuadro de la fuente sonora ni nada de la interfaz). B es un dibujo propio con las
latencias y amplitudes del modelo del simulador (js/auditiva.js corrido con node): órdenes de
magnitud docentes, no valores de referencia.

    python3 -m http.server 8911 -d ~/Escritorio/Proyectos/labyrinthus3d &
    chromium --headless=new --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \\
        --window-size=1600,900 --remote-debugging-port=9911 --user-data-dir=/tmp/h10prof about:blank &
    python3 hacer_h10_simulador.py [ruta a labyrinthus3d]"""
import asyncio
import base64
import io
import json
import os
import math
import pathlib
import subprocess
import sys
import tempfile
import urllib.request

import websockets
from PIL import Image

SIM = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path.home() / 'Escritorio/Proyectos/labyrinthus3d')
AQUI = pathlib.Path(__file__).parent
HTTP, DEVTOOLS = 8911, int(os.environ.get('DEVTOOLS', 9911))

# Reloj virtual: la animación avanza solo cuando se le pide, con pasos fijos.
INIT = """
(()=>{ let vt=1000; const cbs=[]; performance.now=()=>vt;
 window.requestAnimationFrame=(cb)=>{cbs.push(cb);return cbs.length};
 window.cancelAnimationFrame=()=>{};
 window.__paso=(n,dt)=>{ for(let i=0;i<n;i++){ vt+=dt*1000; const l=cbs.splice(0); for(const f of l) f(vt);} return vt; };
})();
"""


class C:
    async def start(self, url):
        tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{DEVTOOLS}/json'))
        t = [x for x in tabs if x['type'] == 'page'][0]
        self.ws = await websockets.connect(t['webSocketDebuggerUrl'], max_size=None)
        self.i = 0
        await self.send('Page.enable')
        await self.send('Runtime.enable')
        # La página trae una CSP que bloquea el <style> inyectado.
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

    async def shot(self, path):
        r = await self.send('Page.captureScreenshot', format='png')
        pathlib.Path(path).write_bytes(base64.b64decode(r['result']['data']))

    async def boton(self, texto):
        return await self.ev(f"(()=>{{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.trim()==={texto!r});"
                             " if(b){b.click();return 1} return 0})()")


TINTA, TENUE, GRILLA = '#24101a', '#8a8a90', '#e7e5e0'
TRAZO = '#c0571c'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
# Lo que se recorta del <canvas> de la vía (en px de CSS; el lienzo va a ×2): el esquema, sin el
# recuadro de la fuente sonora de arriba a la derecha.
CAJA = (0, 140, 505, 712)


async def via():
    """El <canvas> de la vía auditiva (pestaña del tronco), recortado y sobre blanco, como PNG."""
    c = C()
    await c.start(f'http://localhost:{HTTP}/index.html')
    await c.ev("window.__paso(5,0.05)")
    await c.ev("document.querySelector('[data-modulo-abre=audicion]').click()")
    await c.ev("window.__paso(20,0.05)")
    await c.ev("document.querySelector('[data-vista=tronco][data-modulo=audicion]').click()")
    await c.ev("window.__paso(60,0.05)")
    url = await c.ev("document.getElementById('lab-aud').toDataURL('image/png')")
    im = Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGBA')
    k = im.width / 718
    im = im.crop(tuple(round(v * k) for v in CAJA))
    fondo = Image.new('RGBA', im.size, (255, 255, 255, 255))
    fondo.alpha_composite(im)
    buf = io.BytesIO()
    fondo.convert('RGB').save(buf, 'PNG', optimize=True)
    return buf.getvalue(), fondo.size


def peat():
    """Las ondas del PEAT a 80 dB del oído derecho, del modelo del simulador."""
    js = """import { pathToFileURL } from 'node:url';
const A = await import(pathToFileURL(process.argv[2] + '/js/auditiva.js').href);
console.log(JSON.stringify(A.peat(80, 'der')));"""
    with tempfile.NamedTemporaryFile('w', suffix='.mjs', delete=False) as t:
        t.write(js)
    r = subprocess.run(['node', t.name, str(SIM)], capture_output=True, text=True, check=True)
    pathlib.Path(t.name).unlink()
    return json.loads(r.stdout)


def onda(p, t):
    return sum(x['amplitud'] * math.exp(-(((t - x['latencia']) / 0.28) ** 2)) for x in p['ondas'].values() if x)


def svg(png, tam, p):
    W, H = 900, 470
    o = []

    def tx(x, y, s, size=11, color=TINTA, anchor='middle', peso=400):
        o.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size}" fill="{color}" '
                 f'text-anchor="{anchor}" font-weight="{peso}">{s}</text>')

    def ln(x1, y1, x2, y2, color=TINTA, w=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}"{d}/>')

    # A: la vía, del simulador.
    alto = 440
    ancho = tam[0] * alto / tam[1]
    ax, ay = 22, 18
    o.append(f'<image x="{ax}" y="{ay}" width="{ancho:.1f}" height="{alto}" '
             f'href="data:image/png;base64,{base64.b64encode(png).decode()}"/>')
    tx(10, 22, 'A', 15, peso=700, anchor='start')
    # B: el PEAT, dibujo propio.
    x0, x1, t1 = ax + ancho + 50, W - 20, 8.0
    X = lambda t: x0 + (x1 - x0) * t / t1
    cero, esc = 250, 300
    Y = lambda v: cero - v * esc
    tx(x0 - 30, 22, 'B', 15, peso=700, anchor='start')
    tx(x0, 44, 'PEAT, clic a 80 dB, oído derecho', 11, TENUE, anchor='start')
    ln(x0, cero, x1, cero, GRILLA, 1)
    pts = ' '.join(f'{X(t):.1f},{Y(onda(p, t)):.1f}' for t in [i * t1 / 400 for i in range(401)])
    o.append(f'<polyline points="{pts}" fill="none" stroke="{TRAZO}" stroke-width="2.2" stroke-linejoin="round"/>')
    for n, x in p['ondas'].items():
        if x:
            tx(X(x['latencia']), Y(x['amplitud']) - 9, n, 13, peso=700)
    # Eje del tiempo.
    ye = cero + 22
    ln(x0, ye, x1, ye, TENUE, 1)
    for t in range(0, int(t1) + 1, 2):
        ln(X(t), ye, X(t), ye + 5, TENUE, 1)
        tx(X(t), ye + 18, f'{t} ms', 10, TENUE)
    # Los interpicos, bajo el eje.
    lat = {n: x['latencia'] for n, x in p['ondas'].items() if x}
    for a, b, y in [('I', 'III', ye + 56), ('III', 'V', ye + 56), ('I', 'V', ye + 96)]:
        xa, xb = X(lat[a]), X(lat[b])
        for xx in (xa, xb):
            ln(xx, Y(0) + 4, xx, y, GRILLA, 1, '2 3')
        ln(xa, y, xb, y, TINTA, 1.4)
        ln(xa, y - 5, xa, y + 5, TINTA, 1.4)
        ln(xb, y - 5, xb, y + 5, TINTA, 1.4)
        d = f'{lat[b] - lat[a]:.1f}'.replace('.', ',')
        tx((xa + xb) / 2, y - 7, f'{a}-{b}: {d} ms', 10.5)
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
         f'viewBox="0 0 {W} {H}" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="#fff"/>'
         + ''.join(o) + '</svg>')
    (AQUI / 'h10-generadores.svg').write_text(s, encoding='utf-8')
    print('h10-generadores.svg', 'A en', (ax, ay, round(ancho), alto), 'de', (W, H))


def main():
    png, tam = asyncio.run(via())
    svg(png, tam, peat())


if __name__ == '__main__':
    main()
