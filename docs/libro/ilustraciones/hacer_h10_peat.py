#!/usr/bin/env python3
"""Captura de labyrinthus3d para la figura H10.1 (generadores I-V del PEAT).

labyrinthus3d es software libre del autor y NO se toca: se sirve de solo
lectura y se maneja con el protocolo de DevTools de chromium sin cabeza:

    python3 -m http.server 8835 -d ~/Escritorio/Proyectos/labyrinthus3d &
    chromium --headless=new --use-gl=angle --use-angle=swiftshader \\
        --enable-unsafe-swiftshader --window-size=1400,900 \\
        --remote-debugging-port=9335 --user-data-dir=/tmp/h10prof about:blank &
    python3 hacer_h10_peat.py [salida.png] [vista: peat | tronco]

Abre el módulo Auditivo en la pestaña pedida y saca la pantalla de 1400x900."""
import asyncio
import base64
import json
import sys
import urllib.request

import websockets

PUERTO_WEB, PUERTO_CDP = 8835, 9335


async def main(salida, vista='peat'):
    tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{PUERTO_CDP}/json'))
    t = [x for x in tabs if x['type'] == 'page'][0]
    ws = await websockets.connect(t['webSocketDebuggerUrl'], max_size=None)
    n = [0]

    async def send(m, **p):
        n[0] += 1
        await ws.send(json.dumps({'id': n[0], 'method': m, 'params': p}))
        while True:
            r = json.loads(await ws.recv())
            if r.get('id') == n[0]:
                return r

    async def ev(js):
        r = await send('Runtime.evaluate', expression=js, awaitPromise=True, returnByValue=True)
        return r.get('result', {}).get('result', {}).get('value')

    await send('Page.enable')
    await send('Runtime.enable')
    await send('Emulation.setDeviceMetricsOverride', width=1400, height=900, deviceScaleFactor=1, mobile=False)
    await send('Page.navigate', url=f'http://localhost:{PUERTO_WEB}/index.html')
    await asyncio.sleep(8)
    print(await ev("(document.querySelector('[data-modulo-abre=\"audicion\"]')||{click(){}}).click(), 'ok'"))
    await asyncio.sleep(3)
    print(await ev("(document.querySelector('[data-vista=\"" + vista + "\"][data-modulo=\"audicion\"]')||{click(){}}).click(), 'ok'"))
    await asyncio.sleep(4)
    r = await send('Page.captureScreenshot', format='png')
    open(salida, 'wb').write(base64.b64decode(r['result']['data']))
    print('captura', salida)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else 'h10-peat-crudo.png',
                     sys.argv[2] if len(sys.argv) > 2 else 'peat'))
