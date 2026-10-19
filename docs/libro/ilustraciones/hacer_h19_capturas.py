#!/usr/bin/env python3
"""Saca las capturas de labyrinthus3d que usa H19 (se corre aparte, no en el armado).

labyrinthus3d es software libre del autor y NO se toca: se sirve de solo
lectura y se maneja con el protocolo de DevTools de chromium sin cabeza:

    python3 -m http.server 8834 -d ~/Escritorio/Proyectos/labyrinthus3d &
    chromium --headless=new --use-gl=angle --use-angle=swiftshader \\
        --enable-unsafe-swiftshader --window-size=1400,900 \\
        --remote-debugging-port=9334 --user-data-dir=/tmp/h18prof about:blank &
    python3 hacer_h18_capturas.py <maniobra> <lado> <canal> <tipo> <prefijo> "<vistas>" <seg>

Reloj virtual: se reemplazan requestAnimationFrame y performance.now para
avanzar la simulación a pasos fijos, de modo que cada captura cae en el
instante pedido (`seg` segundos después de llegar a cada postura) sin
depender de la velocidad de la máquina. Las capturas son de 1400x900;
hacer_h18_montajes.py las recorta y las junta."""
import asyncio
import base64
import json
import sys
import urllib.request

import websockets

class C:
    async def start(self, url):
        tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9334/json'))
        t = [x for x in tabs if x['type']=='page'][0]
        self.ws = await websockets.connect(t['webSocketDebuggerUrl'], max_size=None)
        self.i=0
        await self.send('Page.enable'); await self.send('Runtime.enable')
        await self.send('Emulation.setDeviceMetricsOverride', width=1400,height=900,deviceScaleFactor=1,mobile=False)
        await self.send('Page.navigate', url=url)
        await asyncio.sleep(6)
    async def send(self, m, **p):
        self.i+=1; i=self.i
        await self.ws.send(json.dumps({'id':i,'method':m,'params':p}))
        while True:
            r=json.loads(await self.ws.recv())
            if r.get('id')==i: return r
    async def ev(self, js):
        r=await self.send('Runtime.evaluate', expression=js, awaitPromise=True, returnByValue=True)
        return r.get('result',{}).get('result',{}).get('value', r)
    async def shot(self, path):
        r=await self.send('Page.captureScreenshot', format='png')
        open(path,'wb').write(base64.b64decode(r['result']['data']))

INIT = """
(()=>{ let vt=1000; const cbs=[]; window.__vt=()=>vt;
 performance.now=()=>vt;
 window.requestAnimationFrame=(cb)=>{cbs.push(cb);return cbs.length};
 window.cancelAnimationFrame=()=>{};
 window.__paso=(n,dt)=>{ for(let i=0;i<n;i++){ vt+=dt*1000; const l=cbs.splice(0); for(const f of l) f(vt);} return vt; };
})();
"""
async def start_virtual(c, url):
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9334/json'))
    t = [x for x in tabs if x['type']=='page'][0]
    c.ws = await websockets.connect(t['webSocketDebuggerUrl'], max_size=None); c.i=0
    await c.send('Page.enable'); await c.send('Runtime.enable')
    await c.send('Page.addScriptToEvaluateOnNewDocument', source=INIT)
    await c.send('Emulation.setDeviceMetricsOverride', width=1400,height=900,deviceScaleFactor=1,mobile=False)
    await c.send('Page.navigate', url=url)
    await asyncio.sleep(9)

async def setup(canal='post', lado='der', tipo='canalitiasis'):
    c=C(); await start_virtual(c,'http://localhost:8834/index.html')
    await c.ev("window.__paso(5,0.05)")
    await c.ev("[...document.querySelectorAll('button')].find(x=>/^Vestibular/.test(x.textContent.trim())).click()")
    await c.ev("window.__paso(20,0.05)")
    await c.ev("[...document.querySelectorAll('button')].find(x=>x.textContent.trim()==='VPPB').click()")
    await c.ev("window.__paso(20,0.05)")
    await poner(c,tipo,canal,lado)
    return c
async def poner(c,tipo,canal,lado):
    await c.ev(f"""(()=>{{const s=(i,v)=>{{const e=document.getElementById(i); e.value=v; e.dispatchEvent(new Event('change'))}};
      s('lab-vppb-tipo','{tipo}'); s('lab-vppb-canal','{canal}'); s('lab-vppb-lado','{lado}')}})()""")
    await c.ev("window.__paso(10,0.05)")
async def click(c, texto):
    return await c.ev(f"(()=>{{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.trim()==={texto!r}); if(b){{b.click();return 1}} return 0}})()")
async def maniobra(c, id, lado):
    await c.ev(f"""(()=>{{const s=(i,v)=>{{const e=document.getElementById(i); e.value=v; e.dispatchEvent(new Event('change'))}};
      s('lab-maniobra','{id}'); s('lab-maniobra-lado','{lado}'); document.getElementById('lab-maniobra-ir').click()}})()""")
async def main():
    mid, lado, canal, tipo, pre, vistas = sys.argv[1:7]
    off = float(sys.argv[7]) if len(sys.argv)>7 else 8
    c=await setup(canal, lado, tipo)
    await click(c,'la sala')
    info = await c.ev(f"""import('/js/vppb.js').then(m=>JSON.stringify(m.MANIOBRAS['{mid}'].pasos.map(p=>[p.nombre,p.mueve,p.queda])))""")
    pasos=json.loads(info); print(pasos)
    await maniobra(c, mid, lado)
    # el nombre de lado: 'der'/'izq'
    t=0; dt=0.1
    for i,(n,mu,qu) in enumerate(pasos):
        target = t+mu+min(off,qu)   # momento de captura
        steps=round((target-t)/dt)
        await c.ev(f"window.__paso({steps},{dt})")
        t=target
        for v in vistas.split(','):
            await click(c,v)
            await c.ev("window.__paso(2,0.001)")
            await c.shot(f'{pre}_{i}_{v.replace(" ","_")}.png')
        print(i, await c.ev("document.getElementById('lab-vppb-estado').textContent"))
        # terminar el paso
        rest = (mu+qu) - (mu+min(off,qu))
        await c.ev(f"window.__paso({round(rest/dt)},{dt})"); t+=rest
asyncio.run(main())
