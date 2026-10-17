#!/usr/bin/env python3
"""Capturas de labyrinthus3d para el capítulo 27 (PPPD: dependencia visual en la vista postural).

labyrinthus3d es software libre del autor y NO se toca: se sirve de solo lectura.

    python3 -m http.server 18814 -d ~/Escritorio/Proyectos/labyrinthus3d &
    chromium --headless=new --use-gl=angle --use-angle=swiftshader \\
        --enable-unsafe-swiftshader --window-size=1400,900 \\
        --remote-debugging-port=19814 --user-data-dir=/tmp/c27prof about:blank &
    python3 hacer_cap27_capturas.py <carpeta de salida>

Reloj virtual (igual que hacer_h19_capturas.py). Saca la posturografía de un paciente sano y del
caso 'PPPD' del simulador (dependencia visual marcada, vestíbulo sano)."""
import asyncio, base64, json, sys, urllib.request
import websockets

OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/c27/cap'
PUERTO = 19814
INIT = """
(()=>{ let vt=1000; const cbs=[]; performance.now=()=>vt;
 window.requestAnimationFrame=(cb)=>{cbs.push(cb);return cbs.length};
 window.cancelAnimationFrame=()=>{};
 window.__paso=(n,dt)=>{ for(let i=0;i<n;i++){ vt+=dt*1000; const l=cbs.splice(0); for(const f of l) f(vt);} return vt; };
})();
"""
class C:
    async def start(self, url):
        tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{PUERTO}/json'))
        t = [x for x in tabs if x['type'] == 'page'][0]
        self.ws = await websockets.connect(t['webSocketDebuggerUrl'], max_size=None); self.i = 0
        await self.send('Page.enable'); await self.send('Runtime.enable')
        await self.send('Page.addScriptToEvaluateOnNewDocument', source=INIT)
        await self.send('Emulation.setDeviceMetricsOverride', width=1400, height=900, deviceScaleFactor=1, mobile=False)
        await self.send('Page.navigate', url=url)
        await asyncio.sleep(9)
    async def send(self, m, **p):
        self.i += 1; i = self.i
        await self.ws.send(json.dumps({'id': i, 'method': m, 'params': p}))
        while True:
            r = json.loads(await self.ws.recv())
            if r.get('id') == i: return r
    async def ev(self, js):
        r = await self.send('Runtime.evaluate', expression=js, awaitPromise=True, returnByValue=True)
        return r.get('result', {}).get('result', {}).get('value', r)
    async def shot(self, name):
        r = await self.send('Page.captureScreenshot', format='png')
        open(f'{OUT}/{name}.png', 'wb').write(base64.b64decode(r['result']['data']))
    async def click(self, js):
        return await self.ev(f"(()=>{{const b={js}; if(b){{b.click();return 1}} return 0}})()")

async def poner_caso(c, caso):
    await c.ev(f"""(()=>{{const e=document.getElementById('post-caso'); e.value='{caso}'; e.dispatchEvent(new Event('change'))}})()""")
    await c.ev("window.__paso(30,0.05)")

async def main():
    c = C(); await c.start('http://localhost:18814/index.html')
    await c.ev("window.__paso(5,0.05)")
    await c.click("document.querySelector('[data-modulo-abre=postural]')")
    await c.ev("window.__paso(30,0.05)")
    print(await c.ev("[...document.getElementById('post-caso').options].map(o=>o.value+':'+o.text).join('|')"))
    for caso in ('sano', 'pppd'):
        await c.click("document.querySelector('[data-vista=lesiones]')")
        await c.ev("window.__paso(10,0.05)")
        await poner_caso(c, caso)
        await c.click("document.querySelector('[data-vista=posturografia]')")
        await c.ev("window.__paso(30,0.05)")
        await c.click("document.getElementById('post-sot-rapido')")
        await c.ev("window.__paso(400,0.05)")
        await c.shot(f'sot_{caso}')
        print(caso, await c.ev("document.getElementById('post-sot-texto').innerText"))
asyncio.run(main())
