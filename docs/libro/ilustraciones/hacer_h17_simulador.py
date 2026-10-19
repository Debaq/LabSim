#!/usr/bin/env python3
"""h17-simulador-calorica.png (H17, prueba calórica): un paciente simulado acostado en la posición de
la calórica, con la cabeza 30° arriba, visto del lado del oído derecho que se irriga, con el laberinto
agrandado al lado: el canal lateral queda vertical. Sin nada de la interfaz.

Se hace con labyrinthus3d, que NO se toca: se sirve de solo lectura y se maneja por el protocolo de
DevTools de chromium sin cabeza, con reloj virtual (la captura cae a los 45 s de irrigación con agua
tibia, sin depender de la máquina). Se esconde todo menos la escena 3D y se recorta a la cabeza.

    python3 -m http.server 8911 -d ~/Escritorio/Proyectos/labyrinthus3d &
    chromium --headless=new --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \\
        --window-size=1600,900 --remote-debugging-port=9911 --user-data-dir=/tmp/h16prof about:blank &
    python3 hacer_h16_simulador.py <carpeta de trabajo>"""
import asyncio
import base64
import json
import pathlib
import re
import sys
import urllib.request

import websockets
from PIL import Image, ImageChops, ImageDraw

AQUI = pathlib.Path(__file__).parent
HTTP, DEVTOOLS = 8911, 9911
SEG = 45
# Solo la escena 3D, sobre blanco.
OCULTA = ('body *{visibility:hidden!important} #lab-canvas{visibility:visible!important}'
          ' html,body,.laberinto,.lab-cuerpo,#lab-escena{background:#fff!important}')

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
    await c.ev("document.querySelector('[data-modulo-abre=\"laberinto\"]').click()")
    await c.ev("window.__paso(20,0.05)")
    await c.ev("document.querySelector('[data-vista=\"pruebas\"]:not([data-modulo])').click()")
    await c.ev("window.__paso(20,0.05)")
    await c.ev("""(()=>{const s=(i,v)=>{const e=document.getElementById(i); e.value=v; e.dispatchEvent(new Event('change'))};
      s('lab-prov-oido','der'); s('lab-cal-agua','tibia');
      const r=document.getElementById('lab-cal-rapido'); r.checked=false; r.dispatchEvent(new Event('change'));
      document.getElementById('lab-cal-irrigar').click()})()""")
    # Sin el ojo de cerca, que el lienzo 3D dibuja en un rincón.
    await c.ev("document.getElementById('lab-vng').click()")
    await c.ev(f"(()=>{{const s=document.createElement('style'); s.textContent={OCULTA!r}; document.head.appendChild(s)}})()")
    # Se acuesta, se aquieta y se irriga: se avanza hasta los SEG segundos de agua (la cabeza ya no se
    # mueve; la hora solo cambia el nistagmo, que no sale en la figura). Pasos gruesos: cada cuadro con
    # swiftshader es lento.
    for _ in range(2000):
        estado = await c.ev("window.__paso(4,0.25), document.getElementById('lab-cal-estado').textContent")
        m = re.search(r': (\d+) s de', estado)
        if m and int(m.group(1)) >= SEG:
            break
    print(estado, flush=True)
    await c.ev("window.__paso(2,0.01)")
    await asyncio.sleep(1)
    crudo = carpeta / 'h17_crudo.png'
    await c.shot(crudo)
    return crudo


def blanquea(im, umbral=14):
    """El fondo gris del lienzo 3D, a blanco: se rellena desde las cuatro esquinas."""
    # El color del fondo del lienzo: el más común, que no sea el blanco de la página.
    fondo = max((c for c in im.getcolors(im.width * im.height) if c[1] != (255, 255, 255)), key=lambda c: c[0])[1]
    for p in [(0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)]:
        ImageDraw.floodfill(im, p, (255, 255, 255), thresh=umbral)
    # Y el fondo que queda encerrado (dentro de los anillos de los canales).
    gris = Image.new('RGB', im.size, fondo)
    mascara = ImageChops.difference(im, gris).convert('L').point(lambda v: 255 if v <= 6 else 0)
    im.paste((255, 255, 255), mask=mascara)
    return im


def recorta(crudo, margen=40):
    im = blanquea(Image.open(crudo).convert('RGB'))
    fondo = Image.new('RGB', im.size, (255, 255, 255))
    caja = ImageChops.difference(im, fondo).convert('L').point(lambda v: 255 if v > 12 else 0).getbbox()
    x0, y0, x1, y1 = caja
    return im.crop((max(0, x0 - margen), max(0, y0 - margen), min(im.width, x1 + margen), min(im.height, y1 + margen)))


def main():
    carpeta = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/h16')
    carpeta.mkdir(parents=True, exist_ok=True)
    im = recorta(asyncio.run(captura(carpeta)))
    im.thumbnail((1400, 1400), Image.LANCZOS)
    im.save(AQUI / 'h17-simulador-calorica.png', optimize=True)
    print('h17-simulador-calorica.png', im.size)


if __name__ == '__main__':
    main()
