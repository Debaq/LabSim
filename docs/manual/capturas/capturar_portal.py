#!/usr/bin/env python3
"""Capturas del portal web del estudiante, por Chromium headless + DevTools.

Lo llama capturar_portal.sh con el servidor ya levantado y la base sembrada
(sembrar_portal.php). Se usa DevTools en vez de `chromium --screenshot` para
poder recortar cada tarjeta por su título, abrir las secciones plegables y
mantener la sesión del alumno entre páginas.

    capturar_portal.py <url base> <dir salida> <dir perfil chromium> <json del sembrado>

Cada captura queda en <dir salida>/web-*.png. Los PDF (informes y ficha de
estudio) se bajan con la cookie de la sesión y se pasan a PNG con pdftoppm.
"""

import asyncio
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

import websockets

BASE, SALIDA, PERFIL, SEMBRADO = sys.argv[1:5]
DATOS = json.loads(SEMBRADO)
UID = DATOS["alumna"]
CITAS = DATOS["citas"]
INFORMES = DATOS["informes"]
ANCHO = 1300


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Cdp:
    """Lo mínimo de DevTools: mandar comandos y esperar eventos."""

    def __init__(self, ws):
        self.ws = ws
        self.n = 0
        self.eventos = []

    async def cmd(self, metodo, **params):
        self.n += 1
        mi = self.n
        await self.ws.send(json.dumps({"id": mi, "method": metodo, "params": params}))
        while True:
            msg = json.loads(await asyncio.wait_for(self.ws.recv(), 60))
            if msg.get("id") == mi:
                if "error" in msg:
                    raise RuntimeError(f"{metodo}: {msg['error']}")
                return msg.get("result", {})
            self.eventos.append(msg)

    async def esperar(self, evento, timeout=30):
        fin = time.time() + timeout
        while time.time() < fin:
            for i, e in enumerate(self.eventos):
                if e.get("method") == evento:
                    del self.eventos[i]
                    return e
            try:
                msg = json.loads(await asyncio.wait_for(self.ws.recv(), max(0.1, fin - time.time())))
            except asyncio.TimeoutError:
                break
            self.eventos.append(msg)
        raise TimeoutError(evento)

    async def ir(self, url, espera=0.6):
        self.eventos.clear()
        await self.cmd("Page.navigate", url=url)
        await self.esperar("Page.loadEventFired")
        await asyncio.sleep(espera)

    async def js(self, expr):
        r = await self.cmd("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r:
            raise RuntimeError(f"JS: {r['exceptionDetails']}\n{expr}")
        return r["result"].get("value")

    async def ancho(self, ancho, alto=900, movil=False):
        await self.cmd("Emulation.setDeviceMetricsOverride", width=ancho, height=alto,
                       deviceScaleFactor=1, mobile=movil)

    async def foto(self, nombre, clip=None):
        """Página entera (clip=None) o el rectángulo {x,y,width,height}."""
        if clip is None:
            alto = await self.js("Math.ceil(document.documentElement.scrollHeight)")
            ancho = await self.js("document.documentElement.clientWidth")
            clip = {"x": 0, "y": 0, "width": ancho, "height": alto}
        clip = dict(clip, scale=1)
        r = await self.cmd("Page.captureScreenshot", format="png", clip=clip, captureBeyondViewport=True)
        ruta = os.path.join(SALIDA, nombre)
        with open(ruta, "wb") as f:
            f.write(base64.b64decode(r["data"]))
        print("  ", nombre)

    async def rect(self, expr_elementos, margen=12):
        """Rectángulo que junta los elementos que devuelve la expresión JS (lista)."""
        r = await self.js(f"""(() => {{
            const els = ({expr_elementos}).filter(Boolean);
            if (!els.length) return null;
            let x1 = 1e9, y1 = 1e9, x2 = 0, y2 = 0;
            for (const el of els) {{
                const b = el.getBoundingClientRect();
                x1 = Math.min(x1, b.left); y1 = Math.min(y1, b.top + scrollY);
                x2 = Math.max(x2, b.right); y2 = Math.max(y2, b.bottom + scrollY);
            }}
            return {{x: x1, y: y1, width: x2 - x1, height: y2 - y1}};
        }})()""")
        if r is None:
            raise RuntimeError(f"sin elementos: {expr_elementos}")
        x = max(0, r["x"] - margen)
        y = max(0, r["y"] - margen)
        ancho_pag = await self.js("document.documentElement.clientWidth")
        return {"x": x, "y": y, "width": min(r["x"] + r["width"] + margen, ancho_pag) - x,
                "height": r["y"] + r["height"] + margen - y}


# Ayudas JS para ubicar tarjetas y títulos por su texto.
JS_AYUDAS = r"""
window.tarjeta = (t) => [...document.querySelectorAll('.card')].find(c => {
    const h = c.querySelector('h2'); return h && h.textContent.trim().startsWith(t);
});
window.titulo = (t) => [...document.querySelectorAll('h1')].find(h => h.textContent.trim().startsWith(t));
window.siguiente = (el, sel) => { let n = el && el.nextElementSibling;
    while (n && !n.matches(sel)) n = n.nextElementSibling; return n; };
"""


def pdf_a_png(cookie, url, prefijo, paginas):
    """Baja el PDF con la sesión del alumno y deja una PNG por página."""
    req = urllib.request.Request(BASE + url, headers={"Cookie": cookie})
    with urllib.request.urlopen(req, timeout=120) as r:
        tipo = r.headers.get("Content-Type", "")
        cuerpo = r.read()
    if "pdf" not in tipo:
        raise RuntimeError(f"{url} no devolvió un PDF ({tipo}): {cuerpo[:300]!r}")
    with tempfile.TemporaryDirectory() as tmp:
        pdf = os.path.join(tmp, "x.pdf")
        with open(pdf, "wb") as f:
            f.write(cuerpo)
        info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
        total = int(next(l.split()[-1] for l in info.splitlines() if l.startswith("Pages:")))
        for p in range(1, min(paginas, total) + 1):
            subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", str(p), "-l", str(p),
                            "-singlefile", pdf, os.path.join(tmp, "p")], check=True)
            nombre = f"{prefijo}-{p}.png" if paginas > 1 else f"{prefijo}.png"
            shutil.move(os.path.join(tmp, "p.png"), os.path.join(SALIDA, nombre))
            print("  ", nombre, f"(página {p} de {total})")
        return total


async def main():
    puerto = puerto_libre()
    if os.path.exists(PERFIL):
        PERFIL_USO = tempfile.mkdtemp(prefix="perfil_", dir=PERFIL)
    else:
        os.makedirs(PERFIL)
        PERFIL_USO = PERFIL
    chromium = subprocess.Popen([
        "chromium", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
        "--force-color-profile=srgb", "--lang=es-CL", "--window-size=1300,1800",
        f"--remote-debugging-port={puerto}", f"--user-data-dir={PERFIL_USO}", "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = None
        for _ in range(100):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/json/list", timeout=2) as r:
                    paginas = [t for t in json.load(r) if t["type"] == "page"]
                if paginas:
                    ws_url = paginas[0]["webSocketDebuggerUrl"]
                    break
            except OSError:
                pass
            await asyncio.sleep(0.2)
        if not ws_url:
            raise RuntimeError("Chromium no levantó DevTools")
        async with websockets.connect(ws_url, max_size=64 * 2**20) as ws:
            c = Cdp(ws)
            await c.cmd("Page.enable")
            await c.cmd("Network.enable")
            await c.cmd("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
            await c.ancho(ANCHO)
            await c.cmd("Page.addScriptToEvaluateOnNewDocument", source=JS_AYUDAS)

            # Sin sesión: lo que ve el alumno si el enlace venció.
            print("Sesión vencida")
            await c.ir(f"{BASE}/student/mis_pacientes.php")
            await c.foto("web-sesion-vencida.png", await c.rect("[document.querySelector('h1'), ...document.querySelectorAll('p')]", 40))

            # Desde la actividad del curso: launch LTI -> "Ingreso correcto".
            print("Ingreso por la actividad (LTI)")
            # fake_lti_launch.php se envía solo: se espera a estar en launch.php.
            await c.cmd("Page.navigate", url=f"{BASE}/fake_lti_launch.php")
            for _ in range(100):
                await asyncio.sleep(0.2)
                if "lti/launch.php" in (await c.js("location.href")) and await c.js("document.readyState") == "complete":
                    break
            else:
                raise RuntimeError("El launch LTI no llegó a lti/launch.php")
            await asyncio.sleep(2.5)                  # Chart.js baja del CDN
            # En headless la animación de las barras no avanza: se redibuja sin ella.
            await c.js("window.Chart && Object.values(Chart.instances).forEach(ch => { ch.options.animation = false; ch.update('none'); })")
            await asyncio.sleep(0.3)
            await c.foto("web-ingreso-lti.png")
            # El botón "Ver mis pacientes" abre student/sso.php en otra
            # pestaña; se sigue su enlace acá mismo (el flujo real).
            href = await c.js("[...document.querySelectorAll('a')].find(a => a.textContent.includes('Ver mis pacientes')).href")
            await c.ir(href)
            if "mis_pacientes.php" not in await c.js("location.href"):
                raise RuntimeError("El SSO no llevó a mis_pacientes.php")

            # --- Mis pacientes ------------------------------------------------
            print("Mis pacientes")
            await c.foto("web-mis-pacientes.png")
            await c.foto("web-como-vas.png", await c.rect("[document.querySelector('header'), titulo('Cómo vas'), document.querySelector('.kpis')]"))
            await c.foto("web-objetivos.png", await c.rect("[tarjeta('Objetivos de')]"))
            await c.foto("web-tecnica-grafico.png", await c.rect("[tarjeta('Tu técnica de audiometría')]"))
            await c.foto("web-lista-atenciones.png", await c.rect(
                "[titulo('Pacientes que has atendido'), siguiente(titulo('Pacientes que has atendido'), '.atenciones')]"))
            await c.foto("web-practica-libre.png", await c.rect(
                "[titulo('Práctica libre'), siguiente(titulo('Práctica libre'), '.atenciones')]"))
            # Pasar el mouse por un punto del gráfico muestra fecha, paciente y %.
            # (el title nativo no sale en la captura; se deja anotado en el informe)

            # En el celular (el alumno suele abrirlo ahí).
            await c.ancho(412, 915, movil=True)
            await c.ir(f"{BASE}/student/mis_pacientes.php")
            await c.foto("web-mis-pacientes-movil.png", {"x": 0, "y": 0, "width": 412, "height": 915})
            await c.ancho(ANCHO)

            # --- Detalle de una atención de práctico (Carolina) ---------------
            print("Atención de Carolina")
            await c.ir(f"{BASE}/student/atencion.php?appointment_id={CITAS['carolina']}")
            await c.foto("web-atencion.png")
            await c.foto("web-atencion-datos.png", await c.rect(
                "[document.querySelector('a.back'), document.querySelector('main h1'), tarjeta('Datos de la atención'), tarjeta('Tu evolución registrada')]"))
            await c.foto("web-atencion-tecnica.png", await c.rect("[tarjeta('Pasos de la técnica de audiometría')]"))
            # Solo la última prueba (los óseos) abierta: con las tres, la
            # tarjeta no cabe en una hoja del manual.
            await c.js("[...document.querySelectorAll('#tecnica details')].slice(-1).forEach(d => d.open = true)")
            await asyncio.sleep(0.3)
            await c.foto("web-atencion-tecnica-abierta.png", await c.rect("[tarjeta('Pasos de la técnica de audiometría')]"))
            await c.js("document.querySelectorAll('#tecnica details').forEach(d => d.open = false)")
            await c.foto("web-atencion-informes.png", await c.rect("[tarjeta('Tus informes')]"))
            await c.foto("web-atencion-ficha.png", await c.rect("[tarjeta('Ficha clínica')]"))
            await c.foto("web-atencion-conversacion.png", await c.rect("[tarjeta('Conversación con el paciente')]"))

            # Mensajes de la OIRS simulada (Hernán: sugerencia; Tomás: felicitación).
            print("Mensajes recibidos")
            await c.ir(f"{BASE}/student/atencion.php?appointment_id={CITAS['hernan']}")
            await c.foto("web-atencion-mensaje-sugerencia.png", await c.rect("[tarjeta('Mensajes recibidos')]"))
            await c.foto("web-atencion-conversacion-acompanante.png", await c.rect("[tarjeta('Conversación con el paciente')]"))
            await c.ir(f"{BASE}/student/atencion.php?appointment_id={CITAS['tomas']}")
            await c.foto("web-atencion-mensaje-felicitacion.png", await c.rect("[tarjeta('Mensajes recibidos')]"))

            # Intento de práctica libre con ficha de estudio (Jorge, 2º intento).
            print("Intento de práctica")
            await c.ir(f"{BASE}/student/atencion.php?appointment_id={CITAS['jorge2']}")
            await c.foto("web-atencion-practica.png", await c.rect(
                "[document.querySelector('a.back'), document.querySelector('main h1'), tarjeta('Ficha de estudio'), tarjeta('Datos de la atención')]"))

            # --- PDF: informes y ficha de estudio -----------------------------
            galletas = (await c.cmd("Network.getCookies", urls=[BASE]))["cookies"]
            cookie = "; ".join(f"{g['name']}={g['value']}" for g in galletas)
            print("PDF")
            pdf_a_png(cookie, f"/student/informe.php?id={INFORMES['abr_carolina']}", "web-informe-abr", 1)
            pdf_a_png(cookie, f"/student/informe.php?id={INFORMES['otoscopia_carolina']}", "web-informe-otoscopia", 1)
            pdf_a_png(cookie, f"/student/ficha_estudio.php?appointment_id={CITAS['jorge2']}", "web-ficha-estudio", 2)
    finally:
        chromium.terminate()
        try:
            chromium.wait(10)
        except subprocess.TimeoutExpired:
            chromium.kill()


asyncio.run(asyncio.wait_for(main(), 600))
