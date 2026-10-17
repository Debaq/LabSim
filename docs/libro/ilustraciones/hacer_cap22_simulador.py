#!/usr/bin/env python3
"""cap22-apogeotropico-sim.png (cap. 22, gira al acostarse): el giro supino de un paciente simulado con
cupulolitiasis del canal lateral derecho, en las dos posturas, sin nada de la interfaz.

Se hace con labyrinthus3d, que NO se toca: este script lo sirve de solo lectura (con un solo cambio al
vuelo: no se dibuja el rótulo «ampolla» del canal en 2D, que el simulador encima sobre la ampolla cuando
queda arriba) y lo maneja por el protocolo de DevTools de chromium sin cabeza, con reloj virtual: cada
captura cae a los `SEG` segundos de llegar a la postura, sin depender de la máquina. De cada postura
quedan dos cosas: la cabeza vista desde arriba (con los laberintos por transparencia), con toda la
interfaz escondida, y el canal lateral en 2D con las partículas en la cúpula. El ojo y sus trazas no se
usan (van en cap22-trazas-*.svg).

    chromium --headless=new --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \\
        --window-size=1400,900 --remote-debugging-port=9913 --user-data-dir=/tmp/c22prof about:blank &
    python3 hacer_cap22_simulador.py <carpeta de trabajo>"""
import asyncio
import base64
import functools
import http.server
import threading
import json
import pathlib
import sys
import urllib.request

import websockets
from PIL import Image, ImageDraw, ImageFont

AQUI = pathlib.Path(__file__).parent
HTTP, DEVTOOLS = 8913, 9913
SEG = 12
REPO = pathlib.Path.home() / 'Escritorio/Proyectos/labyrinthus3d'
CAJA_CABEZA = (640, 398, 800, 530)   # en px CSS de la ventana de 1400x900
OCULTA = 'body *{visibility:hidden!important} #lab-canvas{visibility:visible!important}'
TINTA, BORDE = (36, 16, 26), (207, 204, 197)
LETRA = '/usr/share/fonts/TTF/DejaVuSans.ttf'
NEGRITA = '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf'

INIT = """
(()=>{ let vt=1000; const cbs=[]; performance.now=()=>vt;
 window.requestAnimationFrame=(cb)=>{cbs.push(cb);return cbs.length};
 window.cancelAnimationFrame=()=>{};
 window.__paso=(n,dt)=>{ for(let i=0;i<n;i++){ vt+=dt*1000; const l=cbs.splice(0); for(const f of l) f(vt);} return vt; };
})();
"""


class Servidor(http.server.SimpleHTTPRequestHandler):
    """Sirve el repo tal cual, salvo el rótulo de la ampolla en js/vppb.js."""
    def do_GET(self):
        if self.path.split('?')[0] != '/js/vppb.js':
            return super().do_GET()
        js = (REPO / 'js/vppb.js').read_text(encoding='utf-8')
        linea = "rotulo(tx('ampolla'), ...hacia(ax, ay, luz + 12 * dpr));"
        assert linea in js
        cuerpo = js.replace(linea, '').encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/javascript')
        self.send_header('Content-Length', str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *a):
        pass


def sirve():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', HTTP), functools.partial(Servidor, directory=str(REPO)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()


class C:
    async def start(self, url):
        tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{DEVTOOLS}/json'))
        t = [x for x in tabs if x['type'] == 'page'][0]
        self.ws = await websockets.connect(t['webSocketDebuggerUrl'], max_size=None)
        self.i = 0
        await self.send('Page.enable')
        await self.send('Runtime.enable')
        await self.send('Page.setBypassCSP', enabled=True)   # para poder inyectar el CSS que esconde la interfaz
        await self.send('Network.enable')
        await self.send('Network.setCacheDisabled', cacheDisabled=True)        # que llegue el vppb.js de este servidor
        await self.send('Network.setBypassServiceWorker', bypass=True)
        await self.send('Page.addScriptToEvaluateOnNewDocument', source=INIT)
        await self.send('Emulation.setDeviceMetricsOverride', width=1400, height=900, deviceScaleFactor=1, mobile=False)
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

    async def escala(self, k):
        await self.send('Emulation.setDeviceMetricsOverride', width=1400, height=900, deviceScaleFactor=k, mobile=False)
        await self.ev("window.dispatchEvent(new Event('resize')); window.__paso(3,0.001)")

    async def shot(self, path):
        r = await self.send('Page.captureScreenshot', format='png')
        pathlib.Path(path).write_bytes(base64.b64decode(r['result']['data']))

    async def boton(self, texto):
        return await self.ev(f"(()=>{{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.trim()==={texto!r});"
                             " if(b){b.click();return 1} return 0})()")


async def capturas(carpeta):
    """Corre el giro supino y devuelve, por postura, la captura de la escena (sin interfaz) y el canal en 2D."""
    sirve()
    c = C()
    await c.start(f'http://localhost:{HTTP}/index.html')
    await c.ev("window.__paso(5,0.05)")
    await c.ev("[...document.querySelectorAll('button')].find(x=>/^Vestibular/.test(x.textContent.trim())).click()")
    await c.ev("window.__paso(20,0.05)")
    await c.boton('VPPB')
    await c.ev("window.__paso(20,0.05)")
    await c.ev("""(()=>{const s=(i,v)=>{const e=document.getElementById(i); e.value=v; e.dispatchEvent(new Event('change'))};
      s('lab-vppb-tipo','cupulolitiasis'); s('lab-vppb-canal','lat'); s('lab-vppb-lado','der')})()""")
    await c.ev("window.__paso(10,0.05)")
    await c.boton('la sala')
    await c.ev("window.__paso(5,0.05)")
    await c.boton('desde arriba')
    await c.ev("window.__paso(60,0.05)")
    # sin los ojos de cerca (no se usan y duplican el trabajo de cada cuadro)
    await c.ev("(()=>{const b=document.getElementById('lab-vng'); if(b.getAttribute('aria-pressed')==='true') b.click()})()")
    await c.ev("window.__paso(5,0.05)")
    assert 'ampolla' not in await c.ev("fetch('/js/vppb.js').then(r=>r.text()).then(t=>t.slice(t.indexOf('const hacia = (x, y, d)'), t.indexOf('if (a.cruz)')))")
    pasos = json.loads(await c.ev("import('/js/vppb.js').then(m=>JSON.stringify(m.MANIOBRAS['rolido'].pasos.map(p=>[p.mueve,p.queda])))"))
    await c.ev("""(()=>{const s=(i,v)=>{const e=document.getElementById(i); e.value=v; e.dispatchEvent(new Event('change'))};
      s('lab-maniobra','rolido'); s('lab-maniobra-lado','der'); document.getElementById('lab-maniobra-ir').click()})()""")
    # fuera toda la interfaz: queda solo la escena 3D
    await c.ev(f"(()=>{{const s=document.createElement('style'); s.textContent={OCULTA!r}; document.head.appendChild(s)}})()")
    dt, salida = 0.1, []
    for i, (mueve, queda) in enumerate(pasos):
        hasta = mueve + min(SEG, queda)
        await c.ev(f"window.__paso({round(hasta / dt)},{dt})")
        if i in (1, 3):
            await c.escala(3)
            escena = carpeta / f'c22_{i}_escena.png'
            await c.shot(escena)
            canal = carpeta / f'c22_{i}_canal.png'
            url = await c.ev("document.getElementById('lab-canal-lienzo').toDataURL('image/png')")
            canal.write_bytes(base64.b64decode(url.split(',', 1)[1]))
            await c.escala(1)
            salida.append((escena, canal))
            print(i, await c.ev("document.getElementById('lab-vppb-estado').textContent"), flush=True)
        await c.ev(f"window.__paso({round((queda - min(SEG, queda)) / dt)},{dt})")
    return salida


def opaca(ruta):
    """La imagen sobre fondo blanco (el lienzo del canal es transparente)."""
    im = Image.open(ruta).convert('RGBA')
    fondo = Image.new('RGBA', im.size, (255, 255, 255, 255))
    return Image.alpha_composite(fondo, im).convert('RGB')


def recuadro(escena, canal, numero, texto, alto=380):
    """La cabeza (recorte de la escena, capturada al triple) y, a su derecha, el canal en 2D."""
    im = opaca(escena)
    k = im.width / 1400
    cabeza = im.crop(tuple(round(v * k) for v in CAJA_CABEZA))
    cabeza = cabeza.resize((round(cabeza.width * alto / cabeza.height), alto), Image.LANCZOS)
    canal = opaca(canal)
    canal = canal.resize((round(canal.width * alto / canal.height), alto), Image.LANCZOS)
    ancho = cabeza.width + 8 + canal.width
    franja = 40
    t = Image.new('RGB', (ancho, alto + franja), (255, 255, 255))
    t.paste(cabeza, (0, 0))
    t.paste(canal, (cabeza.width + 8, 0))
    d = ImageDraw.Draw(t)
    d.line((cabeza.width + 4, 0, cabeza.width + 4, alto), fill=BORDE, width=1)
    d.ellipse((6, 6, 44, 44), fill=TINTA)
    d.text((25, 25), str(numero), fill=(255, 255, 255), font=ImageFont.truetype(NEGRITA, 26), anchor='mm')
    d.text((10, alto + 9), texto, fill=TINTA, font=ImageFont.truetype(LETRA, 21))
    d.rectangle((0, 0, ancho - 1, alto + franja - 1), outline=BORDE)
    return t


def main():
    carpeta = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/c22')
    carpeta.mkdir(parents=True, exist_ok=True)
    if '--solo-montaje' in sys.argv:   # rearma con las capturas que ya están en la carpeta
        caps = [(carpeta / f'c22_{i}_escena.png', carpeta / f'c22_{i}_canal.png') for i in (1, 3)]
    else:
        caps = asyncio.run(capturas(carpeta))
    textos = ['Cabeza girada 90° a la derecha', 'Cabeza girada 90° a la izquierda']
    tiles = [recuadro(e, c, k + 1, textos[k]) for k, (e, c) in enumerate(caps)]
    w, h = max(t.width for t in tiles), max(t.height for t in tiles)
    m = Image.new('RGB', (2 * w + 12, h), (255, 255, 255))
    for k, t in enumerate(tiles):
        m.paste(t, (k * (w + 12), 0))
    m.save(AQUI / 'cap22-apogeotropico-sim.png', optimize=True)
    print('cap22-apogeotropico-sim.png', m.size)


if __name__ == '__main__':
    main()
