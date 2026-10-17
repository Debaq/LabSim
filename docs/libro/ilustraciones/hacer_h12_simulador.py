#!/usr/bin/env python3
"""h12-vias.png y h12-vias-neuritis.png (H12, VEMP): las vías del cVEMP y del oVEMP de un paciente
simulado, de frente (a la izquierda de la figura queda el lado derecho del paciente), sana y con el
nervio vestibular superior derecho perdido. Solo el esquema, sin nada de la interfaz.

Se hace con labyrinthus3d, que NO se toca: se sirve de solo lectura y se maneja por el protocolo de
DevTools de chromium sin cabeza, con reloj virtual. El esquema es un <canvas> propio: se lee entero con
toDataURL (no lleva los botones que flotan encima) y se pone sobre blanco.

    python3 -m http.server 8911 -d ~/Escritorio/Proyectos/labyrinthus3d &
    chromium --headless=new --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \\
        --window-size=1600,900 --remote-debugging-port=9911 --user-data-dir=/tmp/h12prof about:blank &
    python3 hacer_h12_simulador.py"""
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


async def lienzo(c, nombre):
    url = await c.ev("document.getElementById('lab-via').toDataURL('image/png')")
    im = Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGBA')
    fondo = Image.new('RGBA', im.size, (255, 255, 255, 255))
    fondo.alpha_composite(im)
    fondo.convert('RGB').save(AQUI / nombre, optimize=True)
    print(nombre, im.size, flush=True)


async def capturas():
    c = C()
    await c.start(f'http://localhost:{HTTP}/index.html')
    await c.ev("window.__paso(5,0.05)")
    await c.ev("document.querySelector('[data-modulo-abre=laberinto]').click()")
    await c.ev("window.__paso(20,0.05)")
    await c.ev("document.querySelector('[data-vista=via]:not([data-modulo])').click()")
    await c.ev("window.__paso(20,0.05)")
    filtro = """(()=>{const e=document.getElementById('lab-via-filtro'); e.value='otolitos';
      e.dispatchEvent(new Event('change', {bubbles: true}))})()"""
    await c.ev(filtro)
    await c.ev("window.__paso(60,0.05)")
    await lienzo(c, 'h12-vias.png')
    # La neuritis del nervio vestibular superior derecho, sitio por sitio en Patología.
    await c.ev("""(()=>{const e=document.querySelector('select[data-canal="nsup_der"]'); e.value='arreflexia';
      e.dispatchEvent(new Event('change', {bubbles: true}))})()""")
    await c.ev("window.__paso(20,0.05)")
    await c.ev(filtro)
    await c.ev("window.__paso(60,0.05)")
    await lienzo(c, 'h12-vias-neuritis.png')


if __name__ == '__main__':
    asyncio.run(capturas())
