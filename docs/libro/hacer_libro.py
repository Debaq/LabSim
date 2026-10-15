#!/usr/bin/env python3
"""Arma el PDF del libro desde capitulos/*.md.

    python3 docs/libro/hacer_libro.py            -> docs/libro/libro.pdf
    python3 docs/libro/hacer_libro.py 11         -> solo el capítulo 11 (libro-11.pdf)

Cada {{caso <nombre>}} del capítulo se expande a la ficha del paciente:
encabezado, antecedentes del caso, otoscopía y las figuras del motor
(figuras/salida/<nombre>_*.svg, en el orden del pedido; hay que haberlas
hecho antes con figuras/hacer_figuras.py). Los "> ✍ ..." son huecos para el
texto del autor y salen marcados en el PDF, para que no se escapen.

Mismo diagramador que el manual (markdown + WeasyPrint, fuentes del manual).
"""
import html
import json
import math
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

import markdown

AQUI = pathlib.Path(__file__).resolve().parent
CAPITULOS = AQUI / 'capitulos'
CASOS = AQUI / 'casos'
SALIDA_FIG = AQUI / 'figuras' / 'salida'
ROSTROS = AQUI / 'rostros'
OTOSCOPIAS = AQUI / 'otoscopias'
FUENTES = AQUI.parent / 'manual' / 'fuentes'
CASOS_DEMO = AQUI.parent / 'manual' / 'capturas' / 'casos_demo.json'

TITULO = 'Casos clínicos en audiología y electrofisiología'
BAJADA = 'Razonamiento clínico con LabSim'
AUTORES = ['Nicolás Baier Quezada']
LICENCIA = 'CC BY-NC-SA 4.0'

NOMBRE_FIGURA = {
    'audiograma': 'Audiometría tonal', 'acumetria': 'Acumetría', 'logoaudiometria': 'Logoaudiometría', 'timpanograma': 'Timpanometría',
    'reflejos': 'Reflejos estapediales', 'teoae': 'Emisiones otoacústicas transitorias',
    'dpoae': 'Productos de distorsión', 'abr': 'Potenciales evocados auditivos de tronco',
    'ecochg': 'Electrococleografía', 'vemp': 'VEMP',
}
ANTECEDENTES = {
    'hipoacusia_familiar': 'hipoacusia familiar', 'ototoxicos': 'ototóxicos', 'trauma_acustico': 'trauma acústico',
    'otitis': 'otitis', 'meningitis': 'meningitis', 'tce': 'TEC', 'diabetes': 'diabetes', 'hta': 'HTA',
}


class CasoPendiente(Exception):
    pass


def cargar(nombre):
    if not (CASOS / f'{nombre}.json').exists():
        raise CasoPendiente(nombre)
    spec = json.loads((CASOS / f'{nombre}.json').read_text(encoding='utf-8'))
    if isinstance(spec['caso'], dict):
        gen = CASOS / 'generados' / f'{nombre}.json'
        if not gen.exists():
            raise CasoPendiente(nombre)
        datos = json.loads(gen.read_text(encoding='utf-8'))['data']
    else:
        tipo, _, clave = spec['caso'].partition(':')
        datos = json.loads(CASOS_DEMO.read_text(encoding='utf-8'))[clave] if tipo == 'demo' else {}
        datos = datos.get('data', datos)
    return spec, datos


def hace(dias):
    d = abs(int(dias))
    if d >= 365:
        n = round(d / 365)
        return f'Hace {n} año{"s" if n > 1 else ""}'
    if d >= 60:
        return f'Hace {round(d / 30)} meses'
    return f'Hace {d} días'


def historia(texto):
    """'{{-500}} texto' por línea -> 'Hace 1 año: texto'."""
    out = []
    for linea in (texto or '').splitlines():
        m = re.match(r'\s*\{\{(-?\d+)\}\}\s*(.*)', linea)
        if m:
            out.append(f'<li><span class="cuando">{hace(m[1])}</span> {html.escape(m[2])}</li>')
        elif linea.strip():
            out.append(f'<li>{html.escape(linea.strip())}</li>')
    return f'<ul class="historia">{"".join(out)}</ul>' if out else ''


def ficha(nombre, numero, cap):
    spec, d = cargar(nombre)
    pac = d.get('paciente_snapshot') or {}
    quien = ' '.join(x for x in (pac.get('nombre', '').split(' ')[0], pac.get('apellido', '').split(' ')[0]) if x) or nombre
    edad = d.get('edad')
    horas = d.get('edad_horas')
    try:
        horas = float(horas) if horas not in (None, '') else None
    except (TypeError, ValueError):
        horas = None
    if edad:
        edad_txt = f'{edad} años'
    elif horas is not None and horas >= 24 * 60:
        edad_txt = f'{round(horas / 720)} meses'
    elif horas is not None and horas >= 72:
        edad_txt = f'{round(horas / 24)} días'
    elif horas is not None:
        edad_txt = f'{horas:g} horas de vida'
    else:
        edad_txt = ''
    sexo = 'mujer' if str(d.get('gender')) == '1' else 'hombre'
    iniciales = ''.join(p[0] for p in quien.split()[:2]).upper()
    foto = next((p for p in (ROSTROS / f'{nombre}.png', ROSTROS / f'{nombre}.jpg') if p.exists()), None)
    rostro = (f'<img class="rostro" src="{foto.as_uri()}">' if foto
              else f'<div class="rostro vacio">{html.escape(iniciales)}</div>')
    es_demo = isinstance(spec['caso'], str) and spec['caso'].startswith('demo:')
    practica = ' <span class="estrella">★ paciente de práctica</span>' if es_demo else ''

    an = d.get('Anamnesis') or {}
    marcados = [v for k, v in ANTECEDENTES.items() if (an.get('antecedentes') or {}).get(k)]
    partes = []
    if an.get('otros'):
        partes.append(f'<p>{html.escape(an["otros"])}</p>')
    if marcados:
        partes.append(f'<p><strong>Antecedentes:</strong> {", ".join(marcados)}.</p>')
    for k, rot in (('medicamentos', 'Medicamentos'), ('cirugias', 'Cirugías')):
        if an.get(k):
            partes.append(f'<p><strong>{rot}:</strong> {html.escape(an[k])}</p>')
    hc = historia(d.get('historia_clinica'))
    if hc:
        partes.append('<p class="rotulo-chico">Historia clínica</p>' + hc)
    # Sin anamnesis en el caso (los armados por cuadro): la cuenta el texto del capítulo
    anamnesis = ''.join(partes)

    otos, hay_otoscopia = [], False
    for lado in ('od', 'oi'):
        f = next((p for p in OTOSCOPIAS.glob(f'{nombre}_{lado}.*')), None) if OTOSCOPIAS.exists() else None
        hay_otoscopia = hay_otoscopia or f is not None
        otos.append(f'<figure class="oto"><img src="{f.as_uri()}"><figcaption>{lado.upper()}</figcaption></figure>' if f
                    else f'<div class="oto vacia">Otoscopía {lado.upper()}</div>')

    cab = f'''<section class="caso">
<div class="caso-cab">{rostro}<div><p class="caso-num">Caso {cap}.{numero}{practica}</p>
<p class="caso-quien">{html.escape(quien)}</p><p class="caso-datos">{edad_txt} · {sexo}</p></div></div>
<div class="anamnesis">{anamnesis}</div>
{f'<div class="otoscopia">{"".join(otos)}</div>' if hay_otoscopia else ''}
</section>'''
    return cab


def resultados(nombre, numero, cap):
    spec, _ = cargar(nombre)
    figs, vistos = [], {}
    for k, f in enumerate(spec.get('figuras', []), start=1):
        t = f['tipo']
        vistos[t] = vistos.get(t, 0) + 1
        archivo = SALIDA_FIG / (f'{nombre}_{t}' + (f'_{vistos[t]}' if vistos[t] > 1 else '') + '.svg')
        rot = NOMBRE_FIGURA.get(t, t)
        if t == 'logoaudiometria' and f.get('enmascarado') is False:
            rot += ' sin enmascarar'
        if archivo.exists():
            svg = re.sub(r'<svg ', '<svg class="grafico" ', archivo.read_text(encoding='utf-8'), count=1)
            svg = re.sub(r'<metadata id="anclas">.*?</metadata>', '', svg)
            figs.append(f'<figure class="fig">{svg}<figcaption>Figura {cap}.{numero}.{k}. {rot}.</figcaption></figure>')
        else:
            figs.append(f'<p class="pendiente">Falta la figura {archivo.name}: correr figuras/hacer_figuras.py {nombre}</p>')

    return '<p class="rotulo-chico">Resultados</p>' + ''.join(figs)


CAJAS = {
    'objetivos': 'En este capítulo', 'ayuda': 'Ayuda memoria', 'sabias': '¿Sabías que?',
    'ojo': 'Ojo clínico', 'pregunta': 'Pregunta abierta', 'comentario': 'Comentario',
}
SECCIONES_DOS_COLUMNAS = ('Técnica', 'Técnica en foco', 'Fisiología', 'Patología', 'Razonamiento',
                          'Para qué sirve', 'Fundamento', 'Antes de empezar', 'Paso a paso',
                          'Cómo se informa', 'Errores frecuentes', 'En LabSim')


GRILLAS = ('#e7e5e0', '#cfccc5', '#f4f2ee')
R_GLOBO = 7.5


def obstaculos(svg):
    """Puntos de lo dibujado (trazos, símbolos, textos), para que un globo
    no tape un valor. La grilla y los fondos no cuentan."""
    pts = []

    def tramo(x1, y1, x2, y2):
        n = max(1, int(math.hypot(x2 - x1, y2 - y1) / 3))
        pts.extend((x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n) for i in range(n + 1))

    for d in re.findall(r'<path d="([^"]+)"', svg):
        previo = None
        for cmd, x, y in re.findall(r'([MLZ]?)\s*(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', d):
            x, y = float(x), float(y)
            if previo and cmd != 'M':
                tramo(*previo, x, y)
            else:
                pts.append((x, y))
            previo = (x, y)
    for cx, cy, r in re.findall(r'<circle cx="([\d.-]+)" cy="([\d.-]+)" r="([\d.]+)"', svg):
        cx, cy, r = float(cx), float(cy), float(r)
        pts.extend((cx + r * math.cos(a / 4 * math.pi), cy + r * math.sin(a / 4 * math.pi)) for a in range(8))
        pts.append((cx, cy))
    for x1, y1, x2, y2, color in re.findall(
            r'<line x1="([\d.-]+)" y1="([\d.-]+)" x2="([\d.-]+)" y2="([\d.-]+)" stroke="([^"]+)"', svg):
        if color not in GRILLAS:
            tramo(float(x1), float(y1), float(x2), float(y2))
    for x, y, tam, ancla, texto in re.findall(
            r'<text x="([\d.-]+)" y="([\d.-]+)" font-size="([\d.]+)"[^>]*?text-anchor="(\w+)"[^>]*>([^<]*)</text>', svg):
        x, y, tam = float(x), float(y), float(tam)
        w = len(html.unescape(texto)) * tam * 0.56
        x0 = x - w if ancla == 'end' else x - w / 2 if ancla == 'middle' else x
        for i in range(int(w / 3) + 1):
            pts.append((x0 + i * 3, y - tam * 0.35))
    return pts


def ubicar_globo(x, y, pts, puestos, ancho, alto):
    """La posición alrededor de (x, y) que menos tapa: prueba ángulos y
    distancias y se queda con la de menos puntos dibujados debajo."""
    mejor = None
    for dist in (16, 21, 27, 34, 42, 52):
        for paso in range(12):
            ang = math.radians(-45 + paso * 30)        # parte arriba a la derecha
            gx, gy = x + dist * math.cos(ang), y + dist * math.sin(ang)
            if not (R_GLOBO + 1 < gx < ancho - R_GLOBO - 1 and R_GLOBO + 1 < gy < alto - R_GLOBO - 1):
                continue
            tapa = sum(1 for px, py in pts if (px - gx) ** 2 + (py - gy) ** 2 < (R_GLOBO + 3) ** 2)
            choca = sum(1 for bx, by in puestos if (bx - gx) ** 2 + (by - gy) ** 2 < (2 * R_GLOBO + 4) ** 2)
            puntaje = tapa * 10 + choca * 1000 + dist * 0.25 + paso * 0.05
            if mejor is None or puntaje < mejor[0]:
                mejor = (puntaje, gx, gy)
    return (mejor[1], mejor[2]) if mejor else (x + 13, y - 15)


def figura_con_globos(nombre, tipo, n, lineas, numero_fig):
    """Una figura del motor con globos numerados y las observaciones abajo.

    Cada línea es '- @ANCLA | texto' (con globo sobre el gráfico) o '- texto'.
    Las anclas las deja el motor en el SVG (<metadata id="anclas">).
    """
    archivo = SALIDA_FIG / (f'{nombre}_{tipo}' + (f'_{n}' if n > 1 else '') + '.svg')
    if not archivo.exists():
        return f'<p class="pendiente">Falta la figura {archivo.name}: correr figuras/hacer_figuras.py {nombre}</p>'
    svg = archivo.read_text(encoding='utf-8')
    m = re.search(r'<metadata id="anclas">(.*?)</metadata>', svg)
    anclas = json.loads(m[1]) if m else {}
    globos, obs, k = [], [], 0
    pts = obstaculos(svg)
    puestos = []
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    ancho, alto = (float(vb[1]), float(vb[2])) if vb else (600.0, 400.0)
    for linea in lineas:
        linea = re.sub(r'^\s*[-*]\s*', '', linea).strip()
        if not linea:
            continue
        if linea.startswith('@'):
            ref, _, texto = linea[1:].partition('|')
            ref = ref.strip()
            if ref not in anclas:
                cerca = [a for a in anclas if a.split(' ')[0] == ref.split(' ')[0]][:12]
                raise SystemExit(f'{archivo.name}: no hay ancla "{ref}". Algunas: {", ".join(cerca)}')
            k += 1
            x, y = anclas[ref]
            gx, gy = ubicar_globo(x, y, pts, puestos, ancho, alto)
            puestos.append((gx, gy))
            gx, gy = round(gx, 2), round(gy, 2)
            # la guía termina 4 px antes del dato, para no taparlo
            d = math.hypot(gx - x, gy - y) or 1
            lx, ly = round(x + (gx - x) * 4 / d, 2), round(y + (gy - y) * 4 / d, 2)
            globos.append(f'<line x1="{lx}" y1="{ly}" x2="{gx}" y2="{gy}" stroke="#24101a" stroke-width="0.9"/>'
                          f'<circle cx="{gx}" cy="{gy}" r="7.5" fill="#24101a" stroke="#ffffff" stroke-width="1.5"/>'
                          f'<text x="{gx}" y="{gy + 3.2}" font-size="9" font-weight="700" fill="#ffffff" '
                          f'text-anchor="middle">{k}</text>')
            obs.append(f'<li><span class="globo">{k}</span>{markdown.markdown(texto.strip())[3:-4]}</li>')
        else:
            obs.append(f'<li class="sin-globo">{markdown.markdown(linea)[3:-4]}</li>')
    svg = re.sub(r'<metadata id="anclas">.*?</metadata>', '', svg)   # ya se usaron; ids repetidos en la página
    svg = svg.replace('</svg>', ''.join(globos) + '</svg>')
    svg = re.sub(r'<svg ', '<svg class="grafico" ', svg, count=1)
    rot = NOMBRE_FIGURA.get(tipo, tipo)
    if 'sin enmascarar' in svg and 'sin enmascarar' not in rot:
        rot += ' sin enmascarar'
    return (f'<div class="figobs"><figure class="fig">{svg}<figcaption>Figura {numero_fig}. {rot}.</figcaption></figure>'
            f'<ol class="obs">{"".join(obs)}</ol></div>')


def capitulo(md_texto):
    cap = re.match(r'#\s+([A-Z]?\d+)\.', md_texto)
    cap = cap[1] if cap else '0'
    marcas, contador, actual, nfig = {}, [0], {}, {}

    def guardar(h):
        clave = f'@@BLOQUE{len(marcas)}@@'
        marcas[clave] = h
        return f'\n\n{clave}\n\n'

    def pendiente(nombre):
        return guardar(f'<p class="pendiente"><span>Caso pendiente</span> {nombre}: correr el generador del capítulo</p>')

    def caso(nombre):
        contador[0] += 1
        actual[nombre] = contador[0]
        try:
            return guardar(ficha(nombre, contador[0], cap))
        except CasoPendiente:
            return pendiente(nombre)

    def res(nombre):
        try:
            return guardar(resultados(nombre, actual.get(nombre, 0), cap))
        except CasoPendiente:
            return pendiente(nombre)

    def fig(nombre, tipo, n, cuerpo_fig):
        num = actual.get(nombre, 0)
        nfig[num] = nfig.get(num, 0) + 1
        return guardar(figura_con_globos(nombre, tipo, int(n or 1), cuerpo_fig.splitlines(),
                                         f'{cap}.{num}.{nfig[num]}'))

    def caja(m):
        tipo, titulo, dentro = m[1], (m[2] or '').strip(), m[3]
        ancho = tipo.endswith('-ancho')
        tipo = tipo.replace('-ancho', '')
        titulo = titulo or CAJAS.get(tipo, '')
        cuerpo_caja = markdown.markdown(dentro, extensions=['tables'])
        return guardar(f'<aside class="caja caja-{tipo}{" ancho" if ancho else ""}">'
                       f'<p class="caja-titulo">{html.escape(titulo)}</p>{cuerpo_caja}</aside>')

    # En orden de aparición: la ficha numera el caso y sus figuras toman ese número
    patron = re.compile(r'\{\{caso\s+([a-z0-9_]+)\}\}|\{\{resultados\s+([a-z0-9_]+)\}\}'
                        r'|^:::figura\s+([a-z0-9_]+)\s+([a-z]+)(?:\s+(\d+))?\s*\n(.*?)^:::\s*$', re.M | re.S)

    def uno(m):
        if m[1]:
            return caso(m[1])
        if m[2]:
            return res(m[2])
        return fig(m[3], m[4], m[5], m[6])

    texto = patron.sub(uno, md_texto)
    texto = re.sub(r'^:::([a-z-]+)(?:[ \t]+(.*?))?\n(.*?)^:::\s*$', caja, texto, flags=re.M | re.S)
    cuerpo = markdown.markdown(texto, extensions=['tables'])
    for clave, h in marcas.items():
        cuerpo = cuerpo.replace(f'<p>{clave}</p>', h)
    # Técnica, Fisiología, Patología y Razonamiento a dos columnas
    partes = re.split(r'(<h2>.*?</h2>)', cuerpo)
    for i in range(1, len(partes) - 1, 2):
        if re.sub(r'<.*?>', '', partes[i]).strip() in SECCIONES_DOS_COLUMNAS:
            partes[i + 1] = f'<div class="dos-col">{partes[i + 1]}</div>'
    cuerpo = ''.join(partes)
    # Ilustraciones (dibujos tipo BioRender): ![descripción](ilustraciones/x.png).
    # Si el archivo todavía no existe sale un recuadro con la descripción,
    # para que se vea dónde va y qué tiene que mostrar.
    nilu = [0]

    def ilustracion(m):
        alt, src = html.unescape(m[1]), m[2]
        nilu[0] += 1
        ruta = AQUI / src
        pie = f'<figcaption>Ilustración {cap}.{nilu[0]}. {html.escape(alt)}</figcaption>'
        if ruta.exists():
            return f'<figure class="ilustracion"><img src="{ruta.as_uri()}">{pie}</figure>'
        # pendiente: la descripción completa va en el recuadro; el pie, solo la primera frase
        corto = re.split(r'(?<=[.:;])\s', alt, maxsplit=1)[0].rstrip('.:;')
        pie = f'<figcaption>Ilustración {cap}.{nilu[0]}. {html.escape(corto)}.</figcaption>'
        return (f'<figure class="ilustracion"><div class="ilu-pendiente"><span>Ilustración pendiente</span>'
                f'{html.escape(alt)}<br><small>{html.escape(src)}</small></div>{pie}</figure>')

    cuerpo = re.sub(r'<p>\s*<img alt="([^"]*)" src="([^"]*)"\s*/?>\s*</p>', ilustracion, cuerpo)
    # huecos del autor
    cuerpo = re.sub(r'<blockquote>\s*<p>✍\s*(.*?)</p>\s*</blockquote>',
                    r'<div class="pendiente"><span>Falta texto</span> \1</div>', cuerpo, flags=re.S)
    cuerpo = cuerpo.replace('<h1>', '<h1 class="capitulo">', 1)
    return cuerpo


CSS = f"""
@font-face {{ font-family: Fraunces; src: url('{(FUENTES / 'fraunces-latin.woff2').as_uri()}'); }}
@font-face {{ font-family: 'Plus Jakarta Sans'; src: url('{(FUENTES / 'plus-jakarta-sans-latin.woff2').as_uri()}'); }}
@font-face {{ font-family: 'Plus Jakarta Sans'; src: url('{(FUENTES / 'plus-jakarta-sans-latin-ext.woff2').as_uri()}'); }}
@page {{ size: A4; margin: 17mm 16mm 18mm 16mm;
        @bottom-right {{ content: counter(page); font: 8pt 'Plus Jakarta Sans'; color: #8f7a83; }}
        @bottom-left {{ content: "{TITULO}"; font: 8pt 'Plus Jakarta Sans'; color: #8f7a83; }} }}
@page portada {{ margin: 0; background: #24101a; @bottom-left {{ content: none; }} @bottom-right {{ content: none; }} }}
html {{ font: 9.8pt/1.55 'Plus Jakarta Sans', sans-serif; color: #2a1a20; }}
.portada {{ page: portada; height: 297mm; color: #F8F1F3; text-align: center; padding-top: 70mm; box-sizing: border-box; }}
.portada h1 {{ font: 700 34pt/1.1 Fraunces, serif; color: #F8F1F3; margin: 0 22mm 6mm; }}
.portada .bajada {{ font: 14pt 'Plus Jakarta Sans'; color: #E7A7BA; margin: 0 0 40mm; }}
.portada .autores {{ font: 600 11pt 'Plus Jakarta Sans'; color: #F8F1F3; }}
.portada .licencia {{ font: 8.5pt 'Plus Jakarta Sans'; color: #A68F98; margin-top: 4mm; }}
h1.capitulo {{ break-before: page; font: 700 26pt/1.1 Fraunces, serif; color: #24101a; margin: 0 0 6mm;
              padding-bottom: 3mm; border-bottom: 2pt solid #8e2a4a; }}
h2 {{ font: 600 15pt/1.2 Fraunces, serif; color: #24101a; margin: 8mm 0 2.5mm; break-after: avoid; }}
h3 {{ font: 600 12pt/1.25 Fraunces, serif; color: #641c34; margin: 5mm 0 1.5mm; break-after: avoid; }}
h4 {{ font: 700 8.5pt 'Plus Jakarta Sans'; letter-spacing: .8pt; text-transform: uppercase; color: #7a2341;
      margin: 4mm 0 1mm; break-after: avoid; }}
p {{ margin: 0 0 2.4mm; }}
ol, ul {{ margin: 0 0 2.5mm; padding-left: 5mm; }}
li {{ margin-bottom: .8mm; }}
h3 + ol li {{ font-size: 8.4pt; line-height: 1.4; }}
.pendiente {{ background: #fff6d6; border-left: 2pt solid #d9a400; padding: 2mm 3mm; margin: 1mm 0 3mm;
              font-size: 8.8pt; color: #5c4a00; border-radius: 0 1.5mm 1.5mm 0; }}
.pendiente span {{ font-weight: 700; text-transform: uppercase; letter-spacing: .6pt; font-size: 7.5pt; margin-right: 2mm; }}
.caso {{ border-top: 1.2pt solid #8e2a4a; margin: 8mm 0 3mm; padding-top: 4mm; }}
.caso-cab {{ display: flex; align-items: center; gap: 5mm; break-after: avoid; }}
.rostro {{ width: 24mm; height: 24mm; border-radius: 50%; object-fit: cover; flex: none; }}
.rostro.vacio {{ background: #f1e4e9; color: #8e2a4a; font: 700 15pt Fraunces, serif; display: flex;
                 align-items: center; justify-content: center; }}
.caso-num {{ font: 700 8pt 'Plus Jakarta Sans'; letter-spacing: 1pt; text-transform: uppercase; color: #8e2a4a; margin: 0; }}
.caso-quien {{ font: 600 15pt/1.2 Fraunces, serif; color: #24101a; margin: 0; }}
.caso-datos {{ color: #7d6670; margin: 0; }}
.estrella {{ color: #b08900; letter-spacing: 0; text-transform: none; font-weight: 600; }}
.anamnesis {{ margin: 3mm 0; }}
.rotulo-chico {{ font: 700 7.5pt 'Plus Jakarta Sans'; letter-spacing: 1pt; text-transform: uppercase; color: #8f7a83;
                 margin: 3mm 0 1mm; break-after: avoid; }}
.historia {{ list-style: none; padding: 0; font-size: 8.8pt; }}
.historia .cuando {{ font-weight: 700; color: #7a2341; margin-right: 1.5mm; }}
.otoscopia {{ display: flex; gap: 6mm; margin: 2mm 0 4mm; }}
.oto {{ width: 38mm; margin: 0; }}
.oto img {{ width: 38mm; height: 38mm; border-radius: 50%; object-fit: cover; }}
.oto.vacia {{ height: 38mm; border-radius: 50%; border: .8pt dashed #c9b3bc; color: #a8939b; font-size: 8pt;
              display: flex; align-items: center; justify-content: center; }}
.dos-col {{ column-count: 2; column-gap: 7mm; }}
.dos-col h3 {{ break-after: avoid; }}
.dos-col .ancho, .dos-col table.ancho {{ column-span: all; }}
/* fichas y figuras relatadas van siempre a todo el ancho, aunque caigan en una sección a dos columnas */
.dos-col .caso, .dos-col .figobs, .dos-col .caja-pregunta.ancho {{ column-span: all; }}
.caja {{ break-inside: avoid; border-radius: 2mm; padding: 2.6mm 3.4mm 1.4mm; margin: 2mm 0 4mm; font-size: 8.9pt; line-height: 1.45; }}
.caja p, .caja li {{ margin-bottom: 1.2mm; }}
.caja ul, .caja ol {{ padding-left: 4.5mm; }}
.caja-titulo {{ font: 700 7.6pt 'Plus Jakarta Sans'; letter-spacing: 1pt; text-transform: uppercase; margin: 0 0 1.5mm !important; }}
.caja table {{ font-size: 8pt; width: 100%; border-collapse: collapse; }}
.caja td, .caja th {{ padding: .9mm 1.4mm; border-bottom: .4pt solid rgba(0,0,0,.12); text-align: left; }}
.caja-objetivos {{ background: #24101a; color: #f8eef1; }}
.caja-objetivos .caja-titulo {{ color: #E7A7BA; }}
.caja-objetivos strong {{ color: #fff; }}
.caja-ayuda {{ background: #eef4fb; border-left: 2.4pt solid #2c5cb0; }}
.caja-ayuda .caja-titulo {{ color: #2c5cb0; }}
.caja-sabias {{ background: #f4f1fb; border-left: 2.4pt solid #6a4fb3; }}
.caja-sabias .caja-titulo {{ color: #6a4fb3; }}
.caja-ojo {{ background: #fdf0ef; border-left: 2.4pt solid #c62f3a; }}
.caja-ojo .caja-titulo {{ color: #c62f3a; }}
.caja-pregunta {{ background: #fff8e6; border: .8pt dashed #c99400; }}
.caja-pregunta .caja-titulo {{ color: #9a7100; }}
.caja-comentario {{ background: #f3f3f1; border-left: 2.4pt solid #8a8a90; font-style: italic; }}
.caja-comentario .caja-titulo {{ color: #55555b; font-style: normal; }}
.figobs {{ break-inside: avoid; margin: 3mm 0 5mm; }}
.figobs .fig {{ margin: 0 0 1mm; }}
ol.obs {{ list-style: none; padding: 2.4mm 3mm 1mm; margin: 0; background: #f7f3f4; border-radius: 2mm;
          column-count: 2; column-gap: 6mm; font-size: 8.7pt; line-height: 1.42; }}
ol.obs li {{ break-inside: avoid; margin: 0 0 1.8mm; padding-left: 6.5mm; position: relative; }}
ol.obs li.sin-globo {{ padding-left: 0; }}
.globo {{ position: absolute; left: 0; top: .2mm; width: 4.6mm; height: 4.6mm; border-radius: 50%; background: #24101a;
          color: #fff; font: 700 7.4pt/4.6mm 'Plus Jakarta Sans'; text-align: center; }}
.ilustracion {{ margin: 2mm 0 4mm; break-inside: avoid; text-align: center; }}
.ilustracion img {{ max-width: 100%; max-height: 95mm; }}
.ilu-pendiente {{ border: 1pt dashed #b9a3ac; border-radius: 2mm; background: #fbf8f9; color: #6f5a63; padding: 8mm 5mm;
                  font-size: 8.8pt; }}
.ilu-pendiente span {{ display: block; font: 700 7.5pt 'Plus Jakarta Sans'; letter-spacing: 1pt; text-transform: uppercase;
                       color: #8e2a4a; margin-bottom: 1.5mm; }}
.fig {{ margin: 2mm 0 5mm; break-inside: avoid; }}
.fig svg.grafico {{ display: block; max-width: 100%; height: auto; margin: 0 auto; }}
figcaption {{ font-size: 7.8pt; color: #7d6670; margin-top: 1.2mm; text-align: center; }}
strong {{ color: #24101a; }}
"""


def main():
    pedido = sys.argv[1:]

    def clave(x):
        # 'H04' -> 'H4', '011' -> '11'
        return re.sub(r'^([A-Za-z]?)0*', r'\1', str(x)).upper()

    # orden del libro: Bases (B1...), Caja de herramientas (H1...), capítulos clínicos
    archivos = sorted(CAPITULOS.glob('*.md'), key=lambda a: ({'B': 0, 'H': 1}.get(a.name[:1].upper(), 2), a.name))
    if pedido:
        archivos = [a for a in archivos if clave(a.name.split('-')[0]) in {clave(p) for p in pedido}]
    if not archivos:
        sys.exit('No hay capítulos que armar en capitulos/')
    portada = (f'<section class="portada"><h1>{TITULO}</h1><p class="bajada">{BAJADA}</p>'
               f'<p class="autores">{" · ".join(AUTORES)}</p><p class="licencia">{LICENCIA}</p></section>')
    cuerpo = portada + ''.join(capitulo(a.read_text(encoding='utf-8')) for a in archivos)
    doc = f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{TITULO}</title><style>{CSS}</style></head><body>{cuerpo}</body></html>'
    destino = AQUI / ('libro.pdf' if not pedido else f'libro-{"-".join(pedido)}.pdf')
    weasy = shutil.which('weasyprint') or str(pathlib.Path.home() / '.local' / 'bin' / 'weasyprint')
    with tempfile.NamedTemporaryFile('w', suffix='.html', encoding='utf-8', delete=False) as f:
        f.write(doc)
    try:
        subprocess.run([weasy, '-u', str(AQUI) + '/', f.name, str(destino)], check=True)
    finally:
        pathlib.Path(f.name).unlink()
    print(destino)


if __name__ == '__main__':
    main()
