#!/usr/bin/env python3
"""Imágenes de H19 hechas con labyrinthus3d, sin su interfaz:

    h19-romberg.png   paciente simulado sano de pie en la plataforma, su centro de presión y los dos balanceos
    h19-sot.png       las seis condiciones del SOT, los puntajes y el análisis sensorial de un paciente simulado sano

labyrinthus3d (~/Escritorio/Proyectos/labyrinthus3d) NO se toca: se sirve de solo lectura y se maneja
por el protocolo de DevTools de chromium sin cabeza, con el reloj virtual de hacer_h19_capturas.py
(cada captura cae en el mismo instante de la simulación). Se esconden los botones flotantes que
caen encima de los gráficos y se recortan solo la escena 3D y los lienzos de los gráficos: sin
pestañas, menús, botones ni el texto del panel. El script levanta y apaga el servidor y chromium.

    python3 docs/libro/ilustraciones/hacer_h19_simulador.py [carpeta-de-trabajo]

Los puntajes y las razones son del modelo del simulador, no valores normativos."""
import asyncio
import base64
import io
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request

import websockets
from PIL import Image, ImageDraw

AQUI = pathlib.Path(__file__).parent
REPO = pathlib.Path(os.environ.get('LABYRINTHUS3D', pathlib.Path.home() / 'Escritorio/Proyectos/labyrinthus3d'))
TRABAJO = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/h19_simulador')
PUERTO_WEB, PUERTO_CDP = 8912, 9812
DPR = 2

INIT = """
(()=>{ let vt=1000; const cbs=[]; performance.now=()=>vt;
 window.requestAnimationFrame=(cb)=>{cbs.push(cb);return cbs.length};
 window.cancelAnimationFrame=()=>{};
 window.__paso=(n,dt)=>{ for(let i=0;i<n;i++){ vt+=dt*1000; const l=cbs.splice(0); for(const f of l) f(vt);} return vt; };
})();
"""
# Los botones flotantes del visor de gráficos (ampliar, panel, paciente) caen sobre el lienzo.
ESCONDE = """(()=>{ for (const [x,y] of [[1038,75],[1038,115],[1038,155]]) {
  let e = document.elementFromPoint(x,y); while (e && e.tagName !== 'BUTTON' && e.parentElement) e = e.parentElement;
  if (e && e.tagName === 'BUTTON') e.style.visibility = 'hidden'; } return 1 })()"""


class C:
    async def start(self, url):
        tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{PUERTO_CDP}/json'))
        t = [x for x in tabs if x['type'] == 'page'][0]
        self.ws = await websockets.connect(t['webSocketDebuggerUrl'], max_size=None)
        self.i = 0
        await self.send('Page.enable')
        await self.send('Runtime.enable')
        await self.send('Page.addScriptToEvaluateOnNewDocument', source=INIT)
        await self.send('Emulation.setDeviceMetricsOverride', width=1400, height=900, deviceScaleFactor=DPR, mobile=False)
        await self.send('Page.navigate', url=url)
        await asyncio.sleep(10)

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

    async def shot(self):
        # que el compositor alcance a presentar lo que se dibujó con el reloj virtual
        await self.ev('window.__paso(2,0.001)')
        await asyncio.sleep(3)
        r = await self.send('Page.captureScreenshot', format='png')
        return Image.open(io.BytesIO(base64.b64decode(r['result']['data']))).convert('RGB')

    async def click(self, js):
        return await self.ev(f"(()=>{{const b={js}; if(b){{b.click();return 1}} return 0}})()")


def recorte(im, caja):
    return im.crop(tuple(round(v * DPR) for v in caja))


async def capturas():
    c = C()
    await c.start(f'http://localhost:{PUERTO_WEB}/index.html')
    await c.ev('window.__paso(5,0.05)')
    await c.click("document.querySelector('[data-modulo-abre=postural]')")
    await c.ev('window.__paso(30,0.05)')
    await c.click("document.querySelector('[data-vista=romberg]')")
    await c.ev('window.__paso(30,0.05)')
    await c.click("document.getElementById('post-romberg')")
    await c.ev('window.__paso(300,0.05)')
    await c.ev(ESCONDE)
    romberg = await c.shot()
    print('romberg:', await c.ev("document.getElementById('post-resultados').innerText"))
    await c.click("document.querySelector('[data-vista=posturografia]')")
    await c.ev('window.__paso(30,0.05)')
    await c.click("document.getElementById('post-sot-rapido')")
    await c.ev('window.__paso(400,0.05)')
    await c.ev(ESCONDE)
    sot = await c.shot()
    print('sot:', await c.ev("document.getElementById('post-sot-texto').innerText"))
    return romberg, sot


def montar(romberg, sot):
    TRABAJO.mkdir(parents=True, exist_ok=True)
    romberg.save(TRABAJO / 'romberg_completo.png')
    sot.save(TRABAJO / 'sot_completo.png')
    # Romberg: el paciente en la plataforma (escena 3D) y, al lado, el estabilograma y los balanceos
    # (el lienzo, sin su título, la condición ni la nota de abajo, que van en el pie).
    paciente = recorte(romberg, (95, 235, 420, 880))
    graficos = recorte(romberg, (520, 98, 1056, 874))
    alto = graficos.height
    paciente = paciente.resize((round(paciente.width * alto / paciente.height), alto), Image.LANCZOS)
    fondo = graficos.getpixel((graficos.width - 4, 4))
    m = Image.new('RGB', (paciente.width + graficos.width, alto), fondo)
    m.paste(paciente, (0, 0))
    m.paste(graficos, (paciente.width, 0))
    m.save(AQUI / 'h19-romberg.png', optimize=True)
    print('h19-romberg.png', m.size)
    # SOT: las seis condiciones, los puntajes, el análisis sensorial y el compuesto.
    s = recorte(sot, (520, 98, 1056, 578))
    s.save(AQUI / 'h19-sot.png', optimize=True)
    print('h19-sot.png', s.size)


def main():
    perfil = TRABAJO / 'perfil-chromium'
    web = subprocess.Popen([sys.executable, '-m', 'http.server', str(PUERTO_WEB), '-d', str(REPO)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cr = subprocess.Popen(['chromium', '--headless=new', '--use-gl=angle', '--use-angle=swiftshader',
                           '--enable-unsafe-swiftshader', '--window-size=1400,900',
                           f'--remote-debugging-port={PUERTO_CDP}', f'--user-data-dir={perfil}', 'about:blank'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(4)
        romberg, sot = asyncio.run(capturas())
        montar(romberg, sot)
    finally:
        cr.terminate()
        web.terminate()


if __name__ == '__main__':
    main()
