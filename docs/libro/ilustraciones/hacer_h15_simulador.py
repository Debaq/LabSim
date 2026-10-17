#!/usr/bin/env python3
"""h15-simulador-frenzel.png (H15, examen vestibular): un paciente simulado con una neuritis vestibular
superior izquierda a las 6 horas, sin fijación. A la izquierda, la cara con las lentes de Frenzel puestas;
a la derecha, el ojo derecho de cerca, como lo ve la cámara de una VNG. Sin nada de la interfaz.

Se hace con labyrinthus3d, que NO se toca: se sirve de solo lectura y se maneja por el protocolo de
DevTools de chromium sin cabeza, con reloj virtual. Se esconde todo menos la escena 3D (el ojo de cerca
es una vista más del mismo lienzo), se recorta la cara sin los laberintos de los lados y se arma con PIL.

    python3 -m http.server 8911 -d ~/Escritorio/Proyectos/labyrinthus3d &
    chromium --headless=new --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \\
        --window-size=1600,900 --remote-debugging-port=9911 --user-data-dir=/tmp/h15prof about:blank &
    python3 hacer_h15_simulador.py <carpeta de trabajo>      (DEVTOOLS=<puerto> para otro chromium)"""
import asyncio
import base64
import json
import os
import pathlib
import sys
import urllib.request

import websockets
from PIL import Image, ImageDraw

AQUI = pathlib.Path(__file__).parent
HTTP, DEVTOOLS = 8911, int(os.environ.get('DEVTOOLS', 9911))
OCULTA = ('body *{visibility:hidden!important} #lab-canvas{visibility:visible!important}'
          ' html,body,.laberinto,.lab-cuerpo,#lab-escena{background:#fff!important}')
# La cara, sin los laberintos que el simulador dibuja a cada lado (px de CSS, vista centrada).
CARA = (398, 185, 842, 885)
BORDE = (207, 204, 197)

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


async def captura(carpeta):
    c = C()
    await c.start(f'http://localhost:{HTTP}/index.html')
    await c.ev("window.__paso(5,0.05)")
    await c.ev("document.querySelector('[data-modulo-abre=laberinto]').click()")
    await c.ev("window.__paso(20,0.05)")
    await c.ev("document.querySelector('[data-vista=patologia]:not([data-modulo])').click()")
    await c.ev("window.__paso(10,0.05)")
    await c.ev("""(()=>{const s=(i,v)=>{const e=document.getElementById(i); e.value=v; e.dispatchEvent(new Event('change', {bubbles: true}))};
      s('lab-caso','neuritis_superior');
      const d=document.getElementById('lab-pat-der'); d.checked=false; d.dispatchEvent(new Event('change', {bubbles: true}));
      s('lab-tiempo','1');
      document.getElementById('lab-fija-no').click()})()""")
    await c.boton('A los lados')
    await c.ev("document.getElementById('lab-centrar').click()")
    await c.ev(f"(()=>{{const s=document.createElement('style'); s.textContent={OCULTA!r}; document.head.appendChild(s)}})()")
    print(await c.ev("document.getElementById('lab-tiempo-texto').textContent.slice(0, 40)"), flush=True)
    await c.ev("window.__paso(12,0.25)")
    ojo = json.loads(await c.ev("JSON.stringify(document.getElementById('lab-ojos-vista').getBoundingClientRect())"))
    await asyncio.sleep(1)
    crudo = carpeta / 'h15_crudo.png'
    await c.shot(crudo)
    return crudo, (ojo['x'], ojo['y'], ojo['x'] + ojo['width'], ojo['y'] + ojo['height'])


def blanquea(im, umbral=14):
    """El fondo gris del lienzo 3D, a blanco: se rellena desde las cuatro esquinas."""
    for p in [(0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)]:
        ImageDraw.floodfill(im, p, (255, 255, 255), thresh=umbral)
    return im


def arma(crudo, caja_ojo):
    im = Image.open(crudo).convert('RGB')
    k = im.width / 1600
    cara = blanquea(im.crop(tuple(round(v * k) for v in CARA)))
    x0, y0, x1, y1 = caja_ojo
    ojo = im.crop((round((x0 + 2) * k), round((y0 + 2) * k), round((x1 - 2) * k), round((y1 - 2) * k)))
    ancho_ojo = round(cara.width * 0.95)
    ojo = ojo.resize((ancho_ojo, round(ojo.height * ancho_ojo / ojo.width)), Image.LANCZOS)
    sep = round(cara.width * 0.12)
    out = Image.new('RGB', (cara.width + sep + ojo.width + 4, cara.height), (255, 255, 255))
    out.paste(cara, (0, 0))
    # El ojo de cerca, a la altura de los ojos de la cara.
    oy = round(cara.height * 0.39 - ojo.height / 2)
    ox = cara.width + sep
    out.paste(ojo, (ox, oy))
    ImageDraw.Draw(out).rectangle((ox - 1, oy - 1, ox + ojo.width, oy + ojo.height), outline=BORDE, width=2)
    return out


def main():
    carpeta = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/h15')
    carpeta.mkdir(parents=True, exist_ok=True)
    crudo, caja = asyncio.run(captura(carpeta))
    im = arma(crudo, caja)
    im.thumbnail((1600, 1600), Image.LANCZOS)
    im.save(AQUI / 'h15-simulador-frenzel.png', optimize=True)
    print('h15-simulador-frenzel.png', im.size)


if __name__ == '__main__':
    main()
