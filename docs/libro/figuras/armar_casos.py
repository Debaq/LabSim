#!/usr/bin/env python3
"""La mitad Chromium de armar_casos.sh (ver ahí). No se corre sola.

    armar_casos.py <base> <contenedor> <sembrado json> [patrón…]
"""
import asyncio
import fnmatch
import hashlib
import json
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

import websockets

BASE, CONTENEDOR, SEMBRADO = sys.argv[1:4]
PATRONES = sys.argv[4:]
DOCENTE = json.loads(SEMBRADO)['docente']
CASOS = pathlib.Path(__file__).resolve().parents[1] / 'casos'
GENERADOS = CASOS / 'generados'

# Math.random sembrado (mulberry32), inyectado antes que los scripts de la
# página: mismo JSON, mismo caso.
AZAR = """(function(){var s=%d>>>0;Math.random=function(){s=s+0x6D2B79F5|0;
var t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;
return((t^t>>>14)>>>0)/4294967296;};})();"""


class Cdp:
    """Lo mínimo de DevTools (como en docs/manual/capturas/capturar_portal.py)."""

    def __init__(self, ws):
        self.ws, self.n, self.eventos = ws, 0, []

    async def cmd(self, metodo, **params):
        self.n += 1
        mi = self.n
        await self.ws.send(json.dumps({'id': mi, 'method': metodo, 'params': params}))
        while True:
            msg = json.loads(await asyncio.wait_for(self.ws.recv(), 60))
            if msg.get('id') == mi:
                if 'error' in msg:
                    raise RuntimeError(f"{metodo}: {msg['error']}")
                return msg.get('result', {})
            self.eventos.append(msg)

    async def esperar(self, evento, timeout=30):
        fin = time.time() + timeout
        while time.time() < fin:
            for i, e in enumerate(self.eventos):
                if e.get('method') == evento:
                    del self.eventos[i]
                    return e
            try:
                msg = json.loads(await asyncio.wait_for(self.ws.recv(), max(0.1, fin - time.time())))
            except asyncio.TimeoutError:
                break
            self.eventos.append(msg)
        raise TimeoutError(evento)

    async def ir(self, url):
        self.eventos.clear()
        await self.cmd('Page.navigate', url=url)
        await self.esperar('Page.loadEventFired')
        await asyncio.sleep(0.5)

    async def js(self, expr):
        r = await self.cmd('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if 'exceptionDetails' in r:
            raise RuntimeError(f"JS: {r['exceptionDetails']}\n{expr}")
        return r['result'].get('value')


def semilla(*partes):
    h = hashlib.blake2b('|'.join(map(str, partes)).encode(), digest_size=4)
    return int.from_bytes(h.digest(), 'big')


def pedidos():
    for arch in sorted(CASOS.glob('*.json')):
        if PATRONES and not any(fnmatch.fnmatch(arch.stem, p) for p in PATRONES):
            continue
        spec = json.loads(arch.read_text(encoding='utf-8'))
        if isinstance(spec.get('caso'), dict) and 'cuadro' in spec['caso']:
            yield arch.stem, spec['caso']


def llenar_js(p):
    """El formulario como lo llenaría el docente en el armado rápido."""
    cuadro = {k.lower(): v for k, v in p['cuadro'].items()}
    grado = {k.lower(): v for k, v in (p.get('grado') or {}).items()}
    sexo = '1' if str(p.get('sexo', 'hombre')).lower() in ('1', 'mujer', 'f') else '0'
    return f"""(function(){{
  function fijar(el, v){{ el.value = v; el.dispatchEvent(new Event('input', {{bubbles:true}}));
                          el.dispatchEvent(new Event('change', {{bubbles:true}})); }}
  var g = document.querySelector('#case-form input[name="gender"][value="{sexo}"]');
  g.checked = true; g.dispatchEvent(new Event('change', {{bubbles:true}}));
  fijar(document.getElementById('patient-age'), {json.dumps(str(p.get('edad', 30)))});
  if ({json.dumps(p.get('edad_valor') is not None)}) {{
    fijar(document.getElementById('patient-edad-unidad'), {json.dumps(p.get('edad_unidad', 'horas'))});
    fijar(document.getElementById('patient-edad-valor'), {json.dumps(str(p.get('edad_valor', '')))});
  }}
  var ig = document.getElementById('armado-igualar');
  if (ig.checked) {{ ig.checked = false; ig.dispatchEvent(new Event('change', {{bubbles:true}})); }}
  var cuadro = {json.dumps(cuadro)}, grado = {json.dumps(grado)}, faltan = [];
  ['od','oi'].forEach(function(l){{
    // La categoría del propio cuadro: con "al azar" el generador sortea otra
    // al apretar Generar y pisa el cuadro elegido.
    var clave = cuadro[l] || 'normal', esc = window.CASE_CONST.escenarios[clave];
    if (!esc) {{ faltan.push(l+':'+clave+' (no existe)'); return; }}
    fijar(document.querySelector('.perfil-categoria[data-lado="'+l+'"]'), esc.categoria);
    var e = document.querySelector('.perfil-escenario[data-lado="'+l+'"]');
    if (![].some.call(e.options, function(o){{ return o.value === clave; }})) {{ faltan.push(l+':'+clave); return; }}
    fijar(e, clave);
    var gr = document.querySelector('.perfil-grado[data-lado="'+l+'"]');
    if (grado[l]) {{
      if (![].some.call(gr.options, function(o){{ return o.value === grado[l]; }})) {{ faltan.push(l+':grado '+grado[l]); return; }}
      fijar(gr, grado[l]);
    }}
  }});
  if (faltan.length) {{ return 'NO: ' + faltan.join(', '); }}
  document.getElementById('perfil-generar').click();
  var an = {json.dumps(p.get('anamnesis') or {})};
  function campo(sel, v){{ var e = document.querySelector('#case-form ' + sel); if (e && v !== undefined) fijar(e, v); }}
  if (an.otros !== undefined) campo('[name="otros"]', an.otros);
  if (an.historia !== undefined) campo('[name="historia_clinica"]', an.historia);
  if (an.medicamentos) campo('[name="medicamentos"]', an.medicamentos);
  if (an.cirugias) campo('[name="cirugias"]', an.cirugias);
  (an.hist || []).forEach(function(k){{ var c = document.querySelector('#case-form [name="hist[' + k + ']"]');
    if (c && !c.checked) {{ c.checked = true; c.dispatchEvent(new Event('change', {{bubbles:true}})); }} }});
  var quedo = ['od','oi'].map(function(l){{ return document.querySelector('.perfil-escenario[data-lado="'+l+'"]').value; }});
  if (quedo[0] !== (cuadro.od || 'normal') || quedo[1] !== (cuadro.oi || 'normal')) {{
    return 'NO: el editor dejó ' + quedo.join(' / ');
  }}
  return 'ok';
}})()"""


async def armar(c, nombre, p):
    s = p.get('semilla', semilla(nombre))
    ident = (await c.cmd('Page.addScriptToEvaluateOnNewDocument', source=AZAR % s))['identifier']
    try:
        await c.ir(f'{BASE}/fake_login_admin.php?uid={DOCENTE}')
        r = await c.js(llenar_js(p))
        if r != 'ok':
            raise RuntimeError(f'{nombre}: el editor no ofrece {r[4:]} (¿cuadro, grado o edad?)')
        await asyncio.sleep(0.4)
        estado = await c.js("(document.getElementById('armado-estado')||{}).textContent||''")
        # El Resumen exige tildar las fichas como revisadas antes de guardar
        # (y CaseForm lo valida igual): en el libro el armado lo acepta quien
        # escribe el pedido, y lo que salió queda en generados/ para mirarlo.
        await c.js("document.querySelectorAll('.resumen-check').forEach(function(k){"
                   "if(!k.checked){k.checked=true;k.dispatchEvent(new Event('change',{bubbles:true}));}})")
        invalidos = await c.js("[].filter.call(document.querySelectorAll('#case-form [name]'),"
                               " function(e){return e.willValidate && !e.checkValidity();})"
                               ".map(function(e){return e.name + ' (' + e.validationMessage + ')';}).join(', ')")
        if invalidos:
            raise RuntimeError(f'{nombre}: el formulario no valida: {invalidos}')
        c.eventos.clear()
        await c.js("document.querySelector('#case-form button[value=\"create_case\"]').click()")
        try:
            await c.esperar('Page.loadEventFired', 20)
        except TimeoutError:
            dialogo = next((e for e in c.eventos if e.get('method') == 'Page.javascriptDialogOpening'), None)
            raise RuntimeError(f"{nombre}: no se envió el formulario"
                               + (f" (diálogo: {dialogo['params'].get('message')})" if dialogo else ''))
        await asyncio.sleep(0.3)
        errores = await c.js("[].map.call(document.querySelectorAll('.error, .alert-error, .flash-error'),"
                             " function(e){return e.textContent.trim();}).join(' | ')")
        if errores and 'case_create.php' in await c.js('location.href'):
            raise RuntimeError(f'{nombre}: no se guardó: {errores}')
    finally:
        await c.cmd('Page.removeScriptToEvaluateOnNewDocument', identifier=ident)
    datos = subprocess.run(['podman', 'exec', CONTENEDOR, 'php', '/app/_libro/ultimo_caso.php'],
                           check=True, capture_output=True, text=True).stdout
    data = json.loads(datos)
    # El id entra en las semillas de la app (timpanograma, ABR): uno estable
    # por nombre, no el autoincremental de una base que se tira.
    data['id'] = 9000 + semilla(nombre) % 1000
    GENERADOS.mkdir(exist_ok=True)
    (GENERADOS / f'{nombre}.json').write_text(
        json.dumps({'pedido': p, 'semilla': s, 'data': data}, ensure_ascii=False, indent=1),
        encoding='utf-8')
    print(f'   {nombre}: {estado.strip() or "generado"}')


async def main():
    with socket.socket() as so:
        so.bind(('127.0.0.1', 0))
        puerto = so.getsockname()[1]
    perfil = tempfile.mkdtemp(prefix='labsim_libro_chromium_')
    chromium = subprocess.Popen([
        'chromium', '--headless=new', '--no-sandbox', '--disable-gpu', '--lang=es-CL',
        f'--remote-debugging-port={puerto}', f'--user-data-dir={perfil}', 'about:blank',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = None
        for _ in range(100):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{puerto}/json/list', timeout=2) as r:
                    pags = [t for t in json.load(r) if t['type'] == 'page']
                if pags:
                    ws_url = pags[0]['webSocketDebuggerUrl']
                    break
            except OSError:
                pass
            await asyncio.sleep(0.2)
        if not ws_url:
            raise RuntimeError('Chromium no levantó DevTools')
        async with websockets.connect(ws_url, max_size=64 * 2 ** 20) as ws:
            c = Cdp(ws)
            await c.cmd('Page.enable')
            hechos = 0
            for nombre, p in pedidos():
                await armar(c, nombre, p)
                hechos += 1
            print(f'{hechos} casos en {GENERADOS}')
    finally:
        chromium.terminate()
        chromium.wait()
        shutil.rmtree(perfil, ignore_errors=True)


if __name__ == '__main__':
    asyncio.run(main())
