#!/usr/bin/env python3
"""Arma el PDF del libro desde capitulos/*.md.

    python3 docs/libro/herramientas/hacer_libro.py      -> docs/libro/libro.pdf (el libro completo)
    python3 docs/libro/herramientas/hacer_libro.py 11   -> salida/capitulo-11.pdf y DESPUÉS el
                                                           libro completo, para que libro.pdf
                                                           quede siempre al día
    ... 11 --sin-completo                               -> solo el capítulo (pruebas rápidas)

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
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

import markdown

AQUI = pathlib.Path(__file__).resolve().parent        # docs/libro/herramientas
LIBRO = AQUI.parent                                   # docs/libro
RAIZ = LIBRO.parents[1]
SALIDA = LIBRO / 'salida'                             # PDF de capítulos sueltos (no se versiona)
CAPITULOS = LIBRO / 'capitulos'
CASOS = LIBRO / 'casos'
SALIDA_FIG = LIBRO / 'figuras' / 'salida'
ROSTROS = LIBRO / 'rostros'
OTOSCOPIAS = LIBRO / 'otoscopias'
FUENTES = LIBRO.parent / 'manual' / 'fuentes'
CASOS_DEMO = LIBRO.parent / 'manual' / 'capturas' / 'casos_demo.json'

# Formato de página. 'a4': para imprimir y anillar ya (margen interior más
# ancho del lado del anillado, alternando páginas pares e impares). 'libro':
# para enviar a imprenta; el tamaño se ajusta al libro de referencia cuando se
# decida (python3 docs/libro/herramientas/hacer_libro.py --formato libro).
FORMATOS = {
    'a4': {'tamano': 'A4', 'interior': '24mm', 'exterior': '14mm', 'arriba': '17mm', 'abajo': '18mm'},
    'libro': {'tamano': '210mm 280mm', 'interior': '22mm', 'exterior': '15mm', 'arriba': '18mm', 'abajo': '20mm'},
}
FORMATO = FORMATOS['a4']

# Título elegido por él el 2026-10-15: un solo libro que crece por secciones
# (audición, equilibrio, nariz, rehabilitación). Los simuladores (LabSim,
# trainHIT, labyrinthus3d) son herramientas de apoyo, no el título.
TITULO = 'Evaluación y rehabilitación en otorrinolaringología'
BAJADA = 'Un libro de casos clínicos'
# Autores: por ahora no van en el libro (decisión 2026-10-15). Los previstos,
# para cuando se agreguen: pasarlos a AUTORES y vuelven a la portada, la
# portada interior, los créditos, la página de autores y la contraportada.
AUTORES_PREVISTOS = ['Baier-Quezada', 'López-Moncada', 'Uribe-Hernández', 'Vargas-Bustamante', 'Catipillán-Ulloa']
AUTORES = []
LICENCIA = 'CC BY-NC-SA 4.0'
EDICION = 'Primera edición'
SELLO = ['TecMedHub', 'Universidad Austral de Chile', 'Sede Puerto Montt']
CIUDAD = 'Puerto Montt'
LOGOS = LIBRO / 'logos'
PRELIMINARES = LIBRO / 'preliminares'

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


def clave_rostro(nombre, spec):
    """Un rostro por persona: el paciente de práctica (demo:NN) es el mismo en
    todos los capítulos (rostros/demo-NN.png); un caso armado por cuadro usa
    el nombre del caso. Los genera herramientas/rostros.py."""
    if isinstance(spec['caso'], str) and spec['caso'].startswith('demo:'):
        return 'demo-' + spec['caso'].split(':', 1)[1]
    return nombre


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
    rostro_de = clave_rostro(nombre, spec)
    foto = next((p for p in (ROSTROS / f'{rostro_de}.png', ROSTROS / f'{rostro_de}.jpg') if p.exists()), None)
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
    'docente': 'Para el docente', 'truco': 'Truco del oficio',
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
        # figuras del motor hechas a mano (versionadas): ilustraciones/
        archivo = LIBRO / 'ilustraciones' / archivo.name
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


def imagen_con_globos(ruta, titulo, lineas, numero, ancho=None):
    """Una imagen (dibujo o captura de LabSim) con globos numerados encima.

    Líneas '- @x,y | texto' (x e y en % del ancho y el alto de la imagen) o
    '- texto' sin globo. La ruta es relativa a docs/libro/ (o absoluta al
    repo con '/docs/...'). `ancho` (p. ej. '60%' o '80mm') achica la imagen;
    sin él ocupa lo que dé la columna."""
    archivo = (RAIZ / ruta.lstrip('/')) if ruta.startswith('/') else (LIBRO / ruta)
    if not archivo.exists():
        return f'<p class="pendiente"><span>Falta la imagen</span> {html.escape(ruta)}</p>'
    globos, obs, k = [], [], 0
    for linea in lineas:
        linea = re.sub(r'^\s*[-*]\s*', '', linea).strip()
        if not linea:
            continue
        m = re.match(r'@\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\|(.*)', linea)
        if m:
            k += 1
            globos.append(f'<span class="globo-img" style="left:{m[1]}%;top:{m[2]}%">{k}</span>')
            obs.append(f'<li><span class="globo">{k}</span>{markdown.markdown(m[3].strip())[3:-4]}</li>')
        else:
            obs.append(f'<li class="sin-globo">{markdown.markdown(linea)[3:-4]}</li>')
    lista = f'<ol class="obs">{"".join(obs)}</ol>' if obs else ''
    # El contenedor de los globos es inline-block: mide lo que la imagen y no
    # lo que la columna, así los % de los globos son de la imagen (WeasyPrint
    # no entiende width: fit-content).
    estilo = f' style="width:{ancho}"' if ancho else ''
    return (f'<div class="figobs"><figure class="fig"><div class="img-centro"><div class="img-globos"{estilo}>'
            f'<img src="{archivo.as_uri()}">{"".join(globos)}</div></div><figcaption>Figura {numero}. {html.escape(titulo)}</figcaption></figure>{lista}</div>')


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
        if nombre not in actual:
            # figura del motor que no es de un caso (p. ej. la radiografía de
            # un audiograma de H3): se numera como las imágenes, H3.N
            n_suelta = numeros['fig'].pop(0) if numeros['fig'] else 0
            return guardar(figura_con_globos(nombre, tipo, int(n or 1), cuerpo_fig.splitlines(),
                                             f'{cap}.{n_suelta}'))
        num = actual.get(nombre, 0)
        nfig[num] = nfig.get(num, 0) + 1
        return guardar(figura_con_globos(nombre, tipo, int(n or 1), cuerpo_fig.splitlines(),
                                         f'{cap}.{num}.{nfig[num]}'))

    def caja(m):
        tipo, titulo, dentro = m[1], (m[2] or '').strip(), m[3]
        # Un solo libro (decisión 2026-10-15): la guía del docente va
        # dentro de cada caso, en su recuadro verde, no en otra edición.
        ancho = tipo.endswith('-ancho')
        tipo = tipo.replace('-ancho', '')
        tipo = {'mana': 'truco'}.get(tipo, tipo)      # nombre anterior del recuadro
        titulo = titulo or CAJAS.get(tipo, '')
        cuerpo_caja = markdown.markdown(dentro, extensions=['tables'])
        return guardar(f'<aside class="caja caja-{tipo}{" ancho" if ancho else ""}">'
                       f'<p class="caja-titulo">{html.escape(titulo)}</p>{cuerpo_caja}</aside>')

    # En orden de aparición: la ficha numera el caso y sus figuras toman ese número
    patron = re.compile(r'\{\{caso\s+([a-z0-9_]+)\}\}|\{\{resultados\s+([a-z0-9_]+)\}\}'
                        r'|^:::figura\s+([a-z0-9_]+)\s+([a-z]+)(?:\s+(\d+))?\s*\n(.*?)^:::\s*$', re.M | re.S)

    def img(ruta, titulo, cuerpo_img):
        cuerpo_img = re.sub(r'<!--.*?-->', '', cuerpo_img, flags=re.S)   # notas internas (p. ej. el pedido del dibujo)
        nfig['img'] = numeros['img'].pop(0) if numeros['img'] else nfig.get('img', 0) + 1
        # ':::imagen ruta ancho=60% Título': el tamaño va antes del título
        m = re.match(r'ancho=(\d+(?:\.\d+)?(?:%|mm))\s*(.*)', titulo or '')
        ancho, titulo = (m[1], m[2]) if m else (None, titulo)
        return guardar(imagen_con_globos(ruta, titulo or '', cuerpo_img.splitlines(), f'{cap}.{nfig["img"]}', ancho))

    texto_img = re.compile(r'^:::imagen\s+(\S+)(?:[ \t]+(.*?))?\s*\n(.*?)^:::\s*$', re.M | re.S)
    # Imágenes y figuras del motor que no son de un caso comparten la serie
    # "Figura H3.N" y se procesan en pasadas distintas: el número sale del
    # orden en que aparecen en el texto, no del orden de proceso.
    casos_md = set(re.findall(r'\{\{caso\s+([a-z0-9_]+)\}\}', md_texto))
    serie = [('img' if m[1] else 'fig') for m in re.finditer(
        r'^:::(imagen)\s|^:::figura\s+([a-z0-9_]+)\s', md_texto, re.M)
        if m[1] or m[2] not in casos_md]
    numeros = {k: [i for i, t in enumerate(serie, 1) if t == k] for k in ('img', 'fig')}
    md_texto = texto_img.sub(lambda m: img(m[1], m[2], m[3]), md_texto)

    def uno(m):
        if m[1]:
            return caso(m[1])
        if m[2]:
            return res(m[2])
        return fig(m[3], m[4], m[5], m[6])

    texto = patron.sub(uno, md_texto)
    texto = re.sub(r'^:::([a-z-]+)(?:[ \t]+(.*?))?\n(.*?)^:::\s*$', caja, texto, flags=re.M | re.S)
    cuerpo = markdown.markdown(texto, extensions=['tables'])
    # Técnica, Fisiología, Patología y Razonamiento a dos columnas. Lo que va
    # a todo el ancho (fichas de caso, figuras relatadas, recuadros -ancho)
    # CORTA las columnas en vez de usar column-span: WeasyPrint perdía todo lo
    # que seguía cuando un column-span caía justo en un salto de página.
    def es_ancho(h):
        return (h.startswith(('<section class="caso"', '<div class="figobs"'))
                or re.match(r'<aside class="caja [^"]*\bancho\b', h) is not None)

    def dos_columnas(seccion):
        salida, columna = [], []
        for trozo in re.split(r'(<p>@@BLOQUE\d+@@</p>)', seccion):
            m = re.fullmatch(r'<p>(@@BLOQUE\d+@@)</p>', trozo)
            if m and es_ancho(marcas[m[1]]):
                if ''.join(columna).strip():
                    salida.append(f'<div class="dos-col">{"".join(columna)}</div>')
                columna = []
                salida.append(trozo)
            else:
                columna.append(trozo)
        if ''.join(columna).strip():
            salida.append(f'<div class="dos-col">{"".join(columna)}</div>')
        return ''.join(salida)

    partes = re.split(r'(<h2>.*?</h2>)', cuerpo)
    for i in range(1, len(partes) - 1, 2):
        titulo = re.sub(r'<.*?>', '', partes[i]).strip()
        if titulo in SECCIONES_DOS_COLUMNAS:
            partes[i + 1] = dos_columnas(partes[i + 1])
        elif titulo == 'Referencias':
            # a dos columnas y en letra más chica que el texto: ocupaban
            # páginas enteras
            partes[i + 1] = f'<div class="referencias">{partes[i + 1]}</div>'
    cuerpo = ''.join(partes)
    for clave, h in marcas.items():
        cuerpo = cuerpo.replace(f'<p>{clave}</p>', h)
    # Ilustraciones (dibujos tipo BioRender): ![descripción](ilustraciones/x.png).
    # Si el archivo todavía no existe sale un recuadro con la descripción,
    # para que se vea dónde va y qué tiene que mostrar.
    nilu = [0]

    def ilustracion(m):
        alt, src = html.unescape(m[1]), m[2]
        nilu[0] += 1
        ruta = LIBRO / src
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
    # Tablas numeradas ("Tabla H3.2"), para poder nombrarlas. Un párrafo
    # "Tabla: título" justo antes de la tabla se vuelve su título. Las de los
    # preliminares (abreviaturas) no se numeran.
    if cap != '0':
        ntab = [0]

        def tabla(m):
            ntab[0] += 1
            titulo = (m[1] or '').strip()
            pie = f'<span class="tabla-n">Tabla {cap}.{ntab[0]}</span>' + (f' {titulo}' if titulo else '')
            return f'<table><caption>{pie}</caption>'
        cuerpo = re.sub(r'(?:<p>Tabla:\s*(.*?)</p>\s*)?<table>', tabla, cuerpo, flags=re.S)

    # Apertura del capítulo: bloque con el número y el título (estilo de libro de texto)
    m = re.search(r'<h1>\s*(?:[A-Z]?\d+\.\s*)?(.*?)</h1>', cuerpo, re.S)
    if m and cap == '0':                       # preliminares: Prólogo, Cómo usar...
        cuerpo = cuerpo.replace(m[0], f'<h1 class="prelim">{m[1]}</h1>', 1)
        return f'<section class="preliminar">{cuerpo}</section>'
    if m:
        tipo = {'H': 'Herramienta', 'B': 'Bases'}.get(cap[:1], 'Capítulo')
        # data-marca: el marcador del PDF lleva el número ("H2. Acumetría")
        marca = html.escape(f"{cap}. {re.sub(r'<.*?>', '', m[1]).strip()}", quote=True)
        apertura = (f'<header class="apertura" id="cap-{cap}"><div class="ap-num"><span class="ap-tipo">{tipo}</span>'
                    f'<span class="ap-n">{cap}</span></div><h1 class="capitulo" data-marca="{marca}">{m[1]}</h1></header>')
        cuerpo = cuerpo[:m.start()] + apertura + cuerpo[m.end():]
    return cuerpo


def css():
    return f"""
@font-face {{ font-family: Fraunces; src: url('{(FUENTES / 'fraunces-latin.woff2').as_uri()}'); }}
@font-face {{ font-family: 'Plus Jakarta Sans'; src: url('{(FUENTES / 'plus-jakarta-sans-latin.woff2').as_uri()}'); }}
@font-face {{ font-family: 'Plus Jakarta Sans'; src: url('{(FUENTES / 'plus-jakarta-sans-latin-ext.woff2').as_uri()}'); }}
@page {{ size: {FORMATO['tamano']}; margin: {FORMATO['arriba']} {FORMATO['exterior']} {FORMATO['abajo']} {FORMATO['interior']};
        @bottom-right {{ content: counter(page); font: 8pt 'Plus Jakarta Sans'; color: #8f7a83; }}
        @bottom-left {{ content: "{TITULO}"; font: 8pt 'Plus Jakarta Sans'; color: #8f7a83; }} }}
@page :left {{ margin-left: {FORMATO['exterior']}; margin-right: {FORMATO['interior']};
        @bottom-left {{ content: counter(page); font: 8pt 'Plus Jakarta Sans'; color: #8f7a83; }}
        @bottom-right {{ content: "{TITULO}"; font: 8pt 'Plus Jakarta Sans'; color: #8f7a83; }} }}
@page :right {{ @top-right {{ content: string(capitulo); font: 7.5pt 'Plus Jakarta Sans'; color: #8f7a83; }} }}
@page :left {{ @top-left {{ content: string(capitulo); font: 7.5pt 'Plus Jakarta Sans'; color: #8f7a83; }} }}
@page portada {{ margin: 0; background: #24101a; @top-left {{ content: none; }} @top-right {{ content: none; }}
                @bottom-left {{ content: none; }} @bottom-right {{ content: none; }} }}
@page inicial {{ @top-left {{ content: none; }} @top-right {{ content: none; }}
                @bottom-left {{ content: none; }} @bottom-right {{ content: none; }} }}
@page frontal {{ @top-left {{ content: none; }} @top-right {{ content: none; }} @bottom-left {{ content: none; }}
                @bottom-right {{ content: counter(page, lower-roman); font: 8pt 'Plus Jakarta Sans'; color: #8f7a83; }} }}
@page frontal:left {{ @bottom-right {{ content: none; }}
                @bottom-left {{ content: counter(page, lower-roman); font: 8pt 'Plus Jakarta Sans'; color: #8f7a83; }} }}
@page :blank {{ @top-left {{ content: none; }} @top-right {{ content: none; }}
               @bottom-left {{ content: none; }} @bottom-right {{ content: none; }} }}
@page parte {{ margin: 0; background: #8e2a4a; @top-left {{ content: none; }} @top-right {{ content: none; }}
              @bottom-left {{ content: none; }} @bottom-right {{ content: none; }} }}
html {{ font: 9.8pt/1.55 'Plus Jakarta Sans', sans-serif; color: #2a1a20; }}
body {{ margin: 0; }}
.portada {{ page: portada; position: relative; height: 297mm; color: #F8F1F3; box-sizing: border-box; }}
.pt-banda-sup {{ position: absolute; top: 0; left: 0; right: 0; height: 14mm; background: #8e2a4a; color: #fff;
                 font: 700 10pt/14mm 'Plus Jakarta Sans'; letter-spacing: 3pt; text-transform: uppercase; padding-left: 22mm; }}
.pt-centro {{ position: absolute; top: 58mm; left: 22mm; right: 22mm; border-left: 3pt solid #E7A7BA; padding-left: 8mm; }}
.portada h1 {{ font: 700 38pt/1.08 Fraunces, serif; color: #F8F1F3; margin: 0 0 7mm; }}
.portada .bajada {{ font: 15pt/1.3 'Plus Jakarta Sans'; color: #E7A7BA; margin: 0; }}
.portada .trazos {{ position: absolute; left: 0; right: 0; top: 150mm; width: 210mm; height: 78mm; }}
.portada .autores {{ position: absolute; left: 22mm; right: 22mm; bottom: 44mm; margin: 0; padding-top: 5mm;
                     border-top: .8pt solid #5a2a3c; font: 600 10.5pt/1.6 'Plus Jakarta Sans'; letter-spacing: .4pt;
                     color: #F8F1F3; }}
.pt-logos, .cp-logos {{ position: absolute; left: 22mm; right: 22mm; bottom: 16mm; display: flex; align-items: center; gap: 10mm; }}
.pt-logos .logo, .cp-logos .logo {{ height: 13mm; }}
.pt-logos .logo.tm, .cp-logos .logo.tm {{ height: 17mm; }}
/* preliminares: números romanos, sin cabecera; el cuerpo arranca en 1 */
/* portadilla, portada interior y créditos van sin número; el resto de las preliminares, en romanos */
.portadilla, .interior, .creditos {{ page: inicial; }}
.indice, .preliminar {{ page: frontal; }}
/* El cuerpo es un grupo de páginas que parte en 1. Con counter-reset en el
   elemento WeasyPrint daba 1 en todo el índice (target-counter). */
.cuerpo {{ page: cuerpo; }}
@page cuerpo:nth(1 of cuerpo) {{ counter-reset: page 1; }}
.portadilla, .interior, .indice, .preliminar {{ break-before: right; }}
.creditos {{ break-before: left; }}
.interior {{ text-align: center; padding-top: 28mm; height: 255mm; box-sizing: border-box; position: relative; }}
.in-titulo {{ font: 700 28pt/1.12 Fraunces, serif; color: #24101a; margin: 0 10mm 4mm; }}
.in-bajada {{ font: 13pt 'Plus Jakarta Sans'; color: #8e2a4a; margin: 0 0 22mm; }}
.in-autores {{ font: 600 12pt/1.9 'Plus Jakarta Sans'; color: #2a1a20; margin: 0 0 14mm; }}
.in-edicion {{ font: 600 10pt 'Plus Jakarta Sans'; letter-spacing: 1.5pt; text-transform: uppercase; color: #8e2a4a; }}
.in-sello {{ position: absolute; left: 0; right: 0; bottom: 6mm; }}
.in-sello .logo {{ height: 15mm; margin: 0 6mm; vertical-align: middle; }}
.in-sello .logo.tm {{ height: 22mm; }}
.in-sello p {{ font: 9pt/1.5 'Plus Jakarta Sans'; color: #6f5a63; margin: 4mm 0 0; }}
h1.prelim {{ font: 700 24pt Fraunces, serif; color: #24101a; margin: 0 0 6mm; padding-bottom: 3mm; border-bottom: 2pt solid #8e2a4a; }}
.autor {{ margin: 0 0 4mm; }}
.autor-n {{ font: 700 12pt Fraunces, serif; color: #24101a; margin: 0 0 1mm; }}
.contraportada {{ page: portada; break-before: left; position: relative; height: 297mm; color: #F8F1F3; }}
.cp-titulo {{ position: absolute; top: 40mm; left: 25mm; right: 25mm; margin: 0; font: 700 22pt/1.15 Fraunces, serif; }}
.cp-texto {{ position: absolute; top: 80mm; left: 25mm; right: 25mm; margin: 0; font: 11pt/1.6 'Plus Jakarta Sans'; color: #E9D6DD; }}
.cp-autores {{ position: absolute; left: 25mm; right: 25mm; bottom: 50mm; margin: 0; font: 600 10pt/1.6 'Plus Jakarta Sans'; }}
.cp-licencia {{ position: absolute; right: 25mm; bottom: 20mm; margin: 0; font: 8pt 'Plus Jakarta Sans'; color: #A68F98; }}
.portadilla {{ padding-top: 80mm; text-align: center; }}
.pd-titulo {{ font: 700 24pt/1.15 Fraunces, serif; color: #24101a; margin: 0 20mm 4mm; }}
.pd-bajada {{ font: 12pt 'Plus Jakarta Sans'; color: #8e2a4a; }}
.creditos {{ padding-top: 150mm; font-size: 8.4pt; line-height: 1.5; color: #4a3a40; }}
.creditos p {{ margin: 0 0 3mm; }}

.titulo-indice {{ font: 700 26pt Fraunces, serif; color: #24101a; margin: 0 0 6mm; padding-bottom: 3mm; border-bottom: 2pt solid #8e2a4a; }}
.toc-parte {{ font: 700 8pt 'Plus Jakarta Sans'; letter-spacing: 1.2pt; text-transform: uppercase; color: #8e2a4a;
              margin: 5mm 0 1.5mm; break-after: avoid; }}
a.toc {{ display: block; color: #2a1a20; text-decoration: none; font-size: 10pt; margin: 0 0 1.4mm; }}
/* El número lo escribe el armador en data-pag (dos pasadas): target-counter
   de WeasyPrint daba 1 en todo con el cuerpo como grupo de páginas. */
a.toc::after {{ content: leader('.') attr(data-pag); color: #8f7a83; }}
.toc-n {{ display: inline-block; width: 11mm; font-weight: 700; color: #8e2a4a; }}
.parte {{ page: parte; break-before: right; height: 297mm; position: relative; color: #fff; }}
.pt-num {{ position: absolute; top: 95mm; left: 25mm; margin: 0; font: 700 13pt 'Plus Jakarta Sans'; letter-spacing: 3pt;
           text-transform: uppercase; color: #F5C9D6; }}
.pt-titulo {{ position: absolute; top: 108mm; left: 25mm; right: 25mm; margin: 0; font: 700 34pt/1.1 Fraunces, serif; color: #fff; }}
.apertura {{ break-before: right; display: flex; align-items: flex-end; gap: 6mm; margin: 0 0 7mm; padding-bottom: 4mm;
             border-bottom: 2pt solid #8e2a4a; }}
.ap-num {{ flex: none; width: 28mm; height: 28mm; background: #24101a; color: #fff; border-radius: 0 0 4mm 0;
           display: flex; flex-direction: column; justify-content: center; align-items: center; }}
.ap-tipo {{ font: 700 6.6pt 'Plus Jakarta Sans'; letter-spacing: 1.2pt; text-transform: uppercase; color: #E7A7BA; }}
.ap-n {{ font: 700 28pt/1 Fraunces, serif; margin-top: 1mm; }}
.apertura h1.capitulo {{ string-set: capitulo content(); break-before: auto; border: 0; padding: 0; margin: 0;
                         font: 700 25pt/1.1 Fraunces, serif; color: #24101a; }}
h1.capitulo {{ break-before: page; font: 700 26pt/1.1 Fraunces, serif; color: #24101a; margin: 0 0 6mm;
              padding-bottom: 3mm; border-bottom: 2pt solid #8e2a4a; }}
h2 {{ font: 600 15pt/1.2 Fraunces, serif; color: #24101a; margin: 8mm 0 2.5mm; break-after: avoid; }}
/* Índice del PDF (marcadores): parte > capítulo > sección. Los h3/h4 no
   entran: con ellos el panel era una mazamorra. */
.pt-titulo {{ bookmark-level: 1; bookmark-label: attr(data-marca); }}
h1.capitulo {{ bookmark-level: 2; bookmark-label: attr(data-marca); }}
h2 {{ bookmark-level: 3; }}
.preliminar h2 {{ bookmark-level: 2; }}
h3, h4, h5, h6 {{ bookmark-level: none; }}
h3 {{ font: 600 12pt/1.25 Fraunces, serif; color: #641c34; margin: 5mm 0 1.5mm; break-after: avoid; }}
h4 {{ font: 700 8.5pt 'Plus Jakarta Sans'; letter-spacing: .8pt; text-transform: uppercase; color: #7a2341;
      margin: 4mm 0 1mm; break-after: avoid; }}
p {{ margin: 0 0 2.4mm; orphans: 3; widows: 3; }}
li {{ orphans: 2; widows: 2; }}
h2, h3, h4, .rotulo-chico, .caja-titulo {{ break-after: avoid; }}
/* la ficha del caso no se parte y arrastra consigo la pregunta que la sigue. No
   abre página: si no cabe, pasa entera a la siguiente (con break-before: page
   cada caso dejaba media hoja en blanco y los capítulos llegaban a 24 págs.) */
.caso {{ break-after: avoid; }}
/* la ficha puede partirse en la historia clínica (entera dejaba media hoja en
   blanco); la cabecera y la anamnesis van juntas */
.caso-cab, .anamnesis {{ break-inside: avoid; }}
.historia li {{ break-inside: avoid; }}
.caso + .caja-pregunta, .caso + p {{ break-before: avoid; }}
/* un título de sección no queda solo al pie de la página */
h2 + p, h3 + p, h4 + p, h2 + ul, h3 + ul, h2 + ol, h3 + ol {{ break-before: avoid; }}
.caja {{ break-inside: avoid; }}
/* figura con globos: la figura no se parte, pero la lista de globos puede
   seguir en la página siguiente (entera saltaba y dejaba el hueco) */
.figobs {{ break-inside: auto; }}
.figobs .fig {{ break-after: avoid; }}
table {{ break-inside: auto; }}
tr {{ break-inside: avoid; }}
thead {{ display: table-header-group; }}
/* una tabla larga de los preliminares (abreviaturas) se parte entre filas:
   entera saltaba de página y dejaba el título solo */
.preliminar table {{ break-inside: auto; }}
.preliminar tr {{ break-inside: avoid; }}
.preliminar thead {{ display: table-header-group; }}
ol, ul {{ margin: 0 0 2.5mm; padding-left: 5mm; }}
li {{ margin-bottom: .8mm; }}
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
.referencias {{ column-count: 2; column-gap: 6mm; font-size: 7.6pt; line-height: 1.38; color: #3a2a30; }}
.referencias h3 {{ font-size: 9pt; margin: 2.5mm 0 1mm; }}
.referencias ol {{ padding-left: 4.5mm; margin-bottom: 1.5mm; }}
.referencias li {{ margin-bottom: .5mm; overflow-wrap: anywhere; }}
.dos-col h3 {{ break-after: avoid; }}
.dos-col .ancho, .dos-col table.ancho {{ column-span: all; }}
/* fichas y figuras relatadas van siempre a todo el ancho, aunque caigan en una sección a dos columnas */
.dos-col .caso, .dos-col .figobs, .dos-col .caja-pregunta.ancho {{ column-span: all; }}
.caja {{ break-inside: avoid; border-radius: 2mm; padding: 2.6mm 3.4mm 1.4mm; margin: 2mm 0 4mm; font-size: 8.9pt; line-height: 1.45; }}
.caja p, .caja li {{ margin-bottom: 1.2mm; }}
.caja ul, .caja ol {{ padding-left: 4.5mm; }}
.caja-titulo {{ font: 700 7.6pt 'Plus Jakarta Sans'; letter-spacing: 1pt; text-transform: uppercase; margin: 0 0 1.5mm !important; }}
/* Tablas con grilla: sin líneas no se leían las filas ni las columnas. */
table {{ width: 100%; border-collapse: collapse; font-size: 8.6pt; line-height: 1.4; margin: 1mm 0 3mm;
         border: .7pt solid #b9a3ad; }}
th, td {{ padding: 1mm 1.6mm; border: .5pt solid #cdbcc4; text-align: left; vertical-align: top; }}
th {{ background: #f1e4e9; color: #24101a; font-weight: 700; }}
tbody tr:nth-child(even) td {{ background: #faf6f8; }}
/* símbolos y palabras del oído en el texto: <span class="od">○</span> */
span.od {{ color: #c62f3a; font-weight: 700; }}
span.oi {{ color: #2c5cb0; font-weight: 700; }}
span.cl {{ color: #2e8540; font-weight: 700; }}
table caption {{ caption-side: top; text-align: left; font-size: 8pt; color: #5c4a52; padding: 0 0 1mm; }}
.tabla-n {{ font-weight: 700; color: #8e2a4a; letter-spacing: .3pt; }}
.caja table {{ font-size: 8pt; }}
.caja td, .caja th {{ padding: .9mm 1.4mm; }}
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
.caja-docente {{ background: #eaf6ef; border: 1pt solid #2e7d4f; }}
.caja-docente .caja-titulo {{ color: #2e7d4f; }}
.caja-truco {{ background: #f0f7f2; border: 1pt solid #2e8540; border-radius: 2mm; }}
.caja-truco .caja-titulo {{ color: #2e8540; }}
.caja-truco .caja-titulo::before {{ content: '✦ '; }}
.caja-comentario {{ background: #f3f3f1; border-left: 2.4pt solid #8a8a90; font-style: italic; }}
.caja-comentario .caja-titulo {{ color: #55555b; font-style: normal; }}
.figobs {{ margin: 3mm 0 5mm; }}
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
.img-centro {{ text-align: center; }}
.img-globos {{ position: relative; display: inline-block; max-width: 100%; text-align: left; }}
.img-globos img {{ display: block; width: 100%; max-height: 120mm; border-radius: 1.5mm; }}
.img-globos:not([style]) img {{ width: auto; max-width: 100%; }}
.globo-img {{ position: absolute; transform: translate(-50%, -50%); width: 5.4mm; height: 5.4mm; border-radius: 50%;
              background: #24101a; color: #fff; border: .5mm solid #fff; font: 700 7.6pt/5.4mm 'Plus Jakarta Sans';
              text-align: center; box-shadow: 0 0 0 .3mm rgba(0,0,0,.15); }}
.fig {{ margin: 2mm 0 5mm; break-inside: avoid; }}
.fig svg.grafico {{ display: block; max-width: 100%; height: auto; margin: 0 auto; }}
figcaption {{ font-size: 7.8pt; color: #7d6670; margin-top: 1.2mm; text-align: center; }}
strong {{ color: #24101a; }}
"""


def partes_del_indice():
    """{clave de capítulo: (parte, título de la parte)} leído de indice.md."""
    out, parte = {}, None
    for linea in (LIBRO / 'indice.md').read_text(encoding='utf-8').splitlines():
        m = re.match(r'^## (.+)$', linea)
        if m:
            titulo = m[1].strip()
            pm = re.match(r'Parte ([IVX]+) — (.+)', titulo)
            parte = (f'Parte {pm[1]}', pm[2]) if pm else (titulo, '')
            continue
        m = re.match(r'^### ([HB]?\d+)\. ', linea)
        if m and parte:
            out[m[1]] = parte
    return out


def trazos_portada():
    """Franja de trazos de PEAT para la portada, dibujados con la misma forma que el motor."""
    import math
    w, h, filas = 600, 220, 7
    caminos = []
    for k in range(filas):
        base = 30 + k * 27
        amp = 14 * (1 - k / (filas + 2))
        lat = 5.6 + k * 0.35
        pts = []
        for i in range(301):
            ms = i / 25
            y = sum(a * math.exp(-((ms - l) / 0.28) ** 2) for a, l in ((0.5, 1.6 + k * .08), (0.7, 3.8 + k * .2), (1.0, lat)))
            y -= 0.5 * math.exp(-((ms - lat - 1.1) / 0.5) ** 2)
            y += 0.06 * math.sin(ms * 7 + k)
            pts.append(f'{ms / 12 * w:.1f},{base - y * amp:.1f}')
        op = 0.85 - k * 0.09
        caminos.append(f'<path d="M{" L".join(pts)}" fill="none" stroke="#E7A7BA" stroke-width="1.6" stroke-opacity="{op:.2f}"/>')
    return (f'<svg class="trazos" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
            + ''.join(caminos) + '</svg>')


def logo(nombre, clase=''):
    return f'<img class="logo {clase}" src="{(LOGOS / nombre).as_uri()}">'


def paginas_iniciales(capitulos):
    """Portada, portadilla, portada interior, créditos, autores, prólogo,
    presentación, índice, cómo usar y abreviaturas. Cada una empieza en
    página derecha; las hojas blancas de por medio las pone el paginado."""
    anio = __import__('datetime').date.today().year
    portada = (f'<section class="portada"><div class="pt-banda-sup">TecMedHub · Universidad Austral de Chile</div>'
               f'<div class="pt-centro"><h1>{TITULO}</h1><p class="bajada">{BAJADA}</p></div>'
               f'{trazos_portada()}'
               + (f'<p class="autores">{" · ".join(AUTORES)}</p>' if AUTORES else '') +
               f'<div class="pt-logos">{logo("uach-pm-blanco.png")}{logo("tecmedhub-blanco.png", "tm")}</div></section>')
    portadilla = f'<section class="portadilla"><p class="pd-titulo">{TITULO}</p></section>'
    interior = (f'<section class="interior"><p class="in-titulo">{TITULO}</p><p class="in-bajada">{BAJADA}</p>'
                + (f'<p class="in-autores">{"<br>".join(AUTORES)}</p>' if AUTORES else '<p class="in-autores"></p>') +
                f'<p class="in-edicion">{EDICION}</p>'
                f'<div class="in-sello">{logo("uach-pm.png")}{logo("tecmedhub.png", "tm")}'
                f'<p>{" · ".join(SELLO)}<br>{CIUDAD}, {anio}</p></div></section>')
    creditos = (f'<section class="creditos"><p><strong>{TITULO}</strong><br>{BAJADA}</p>'
                f'<p>{EDICION}, {anio}</p>'
                + (f'<p>Autores: {", ".join(AUTORES)}</p>' if AUTORES else '') +
                f'<p>Edita: {", ".join(SELLO)}. {CIUDAD}, Chile.</p>'
                f'<p>ISBN: en trámite</p>'
                f'<p>Esta obra se distribuye con licencia <strong>Creative Commons Atribución-NoComercial-'
                f'CompartirIgual 4.0 Internacional ({LICENCIA})</strong>. Puedes copiarla, distribuirla y adaptarla '
                f'sin fines comerciales, citando a los autores y compartiendo las obras derivadas con la misma licencia.</p>'
                f'<p>Los pacientes de los casos son ficticios. Sus exámenes fueron generados con simuladores de apoyo '
                f'(LabSim y, en las secciones que los usan, trainHIT y labyrinthus3d). '
                f'Las otoscopías provienen de bancos de imágenes de acceso libre, con su autoría y licencia en el pie '
                f'de cada figura.</p>'
                f'<p>La audiología avanza: las normas, valores de referencia y criterios de este libro se revisaron '
                f'con la bibliografía citada en cada capítulo, pero quien atiende a un paciente debe contrastarlos '
                f'con la normativa vigente y el protocolo de su lugar de trabajo.</p>'
                f'<p>Diseño y diagramación: TecMedHub, con herramientas propias.</p></section>')
    autores = '' if not AUTORES else ('<section class="preliminar"><h1 class="prelim">Autores</h1>'
               + ''.join(f'<div class="autor"><p class="autor-n">{a}</p>'
                         f'<div class="pendiente"><span>Falta texto</span> nombre completo, título y afiliación</div></div>'
                         for a in AUTORES) + '</section>')
    prelim = {f.stem: capitulo(f.read_text(encoding='utf-8')) for f in sorted(PRELIMINARES.glob('*.md'))}
    antes = ''.join(v for k, v in prelim.items() if k[:2] in ('01', '02'))
    despues = ''.join(v for k, v in prelim.items() if k[:2] not in ('01', '02'))
    filas, parte_actual = [], None
    for cap, titulo, parte in capitulos:
        if parte and parte != parte_actual:
            filas.append(f'<p class="toc-parte">{parte[0]}{" · " + parte[1] if parte[1] else ""}</p>')
            parte_actual = parte
        filas.append(f'<a class="toc" href="#cap-{cap}" data-pag="@@PAG-{cap}@@"><span class="toc-n">{cap}</span>{titulo}</a>')
    indice = f'<section class="indice"><h1 class="titulo-indice">Índice</h1>{"".join(filas)}</section>'
    return portada + portadilla + interior + creditos + autores + antes + indice + despues


def contraportada():
    return (f'<section class="contraportada"><p class="cp-titulo">{TITULO}</p>'
            f'<p class="cp-texto">Un libro para aprender a evaluar y rehabilitar en otorrinolaringología como se '
            f'aprende en el box: con pacientes. Cada técnica se explica paso a paso y cada caso se razona desde la '
            f'anamnesis hasta el diagnóstico, con los exámenes relatados sobre sus gráficos. Los simuladores de '
            f'apoyo generan los pacientes y sus resultados, así que muchos casos se pueden atender en el '
            f'laboratorio.</p>'
            + (f'<p class="cp-autores">{" · ".join(AUTORES)}</p>' if AUTORES else '') +
            f'<div class="cp-logos">{logo("uach-pm-blanco.png")}{logo("tecmedhub-blanco.png", "tm")}</div>'
            f'<p class="cp-licencia">{LICENCIA}</p></section>')


def separador(parte):
    # data-marca: el separador es el primer nivel del índice del PDF y los
    # capítulos cuelgan de él
    if not parte[1]:          # Bases, Caja de herramientas: el nombre va grande
        marca = html.escape(parte[0], quote=True)
        return f'<section class="parte"><p class="pt-titulo" data-marca="{marca}">{parte[0]}</p></section>'
    marca = html.escape(f'{parte[0]} · {parte[1]}', quote=True)
    return (f'<section class="parte"><p class="pt-num">{parte[0]}</p>'
            f'<p class="pt-titulo" data-marca="{marca}">{parte[1]}</p></section>')


def escribir_con_indice(doc, destino):
    """Libro completo en dos pasadas: la primera ubica la página de cada
    capítulo (anclas cap-*), la segunda escribe esos números en el índice.
    Los números del índice no cambian el largo de nada, así que la segunda
    pasada pagina igual que la primera."""
    import logging
    from weasyprint import HTML
    logging.getLogger('weasyprint').setLevel(logging.ERROR)
    # '000' ocupa lo que un número real: el índice pagina igual en las dos pasadas
    primera = HTML(string=re.sub(r'@@PAG-[^@]+@@', '000', doc), base_url=str(LIBRO) + '/').render()
    pagina_de, inicio = {}, None
    for i, pag in enumerate(primera.pages):
        for ancla in pag.anchors:
            if ancla == 'inicio-cuerpo' and inicio is None:
                inicio = i
            if ancla.startswith('cap-') and ancla not in pagina_de:
                pagina_de[ancla] = i
    inicio = inicio or 0
    doc = re.sub(r'@@PAG-([A-Z]?\d+)@@',
                 lambda m: str(pagina_de[f'cap-{m[1]}'] - inicio + 1) if f'cap-{m[1]}' in pagina_de else '',
                 doc)
    HTML(string=doc, base_url=str(LIBRO) + '/').write_pdf(str(destino))


def main():
    global FORMATO
    args = sys.argv[1:]
    completo_despues = '--sin-completo' not in args
    if not completo_despues:
        args.remove('--sin-completo')
    if '--formato' in args:
        i = args.index('--formato')
        FORMATO = FORMATOS[args[i + 1]]
        del args[i:i + 2]
    una_pieza = '--de-una-pieza' in args
    if una_pieza:
        args.remove('--de-una-pieza')
    pedido = args
    if not pedido and not una_pieza:
        # Libro completo: por capítulos con caché (armado_incremental.py).
        # --de-una-pieza compone las ~500 páginas juntas, en dos pasadas.
        import armado_incremental
        armado_incremental.armar()
        return

    def clave(x):
        # 'H04' -> 'H4', '011' -> '11'
        return re.sub(r'^([A-Za-z]?)0*', r'\1', str(x)).upper()

    # orden del libro: Bases (B1...), Caja de herramientas (H1...), capítulos clínicos
    archivos = sorted(CAPITULOS.glob('*.md'), key=lambda a: ({'B': 0, 'H': 1}.get(a.name[:1].upper(), 2), a.name))
    if pedido:
        archivos = [a for a in archivos if clave(a.name.split('-')[0]) in {clave(p) for p in pedido}]
    if not archivos:
        sys.exit('No hay capítulos que armar en capitulos/')
    if pedido:
        # un capítulo suelto: sin portada, índice ni separadores
        cuerpo = ''.join(capitulo(a.read_text(encoding='utf-8')) for a in archivos)
    else:
        partes = partes_del_indice()
        capitulos, cuerpo_caps, parte_actual = [], [], None
        for a in archivos:
            md = a.read_text(encoding='utf-8')
            m = re.match(r'#\s+([A-Z]?\d+)\.\s*(.+)', md)
            cap, titulo = (m[1], m[2].strip()) if m else ('', a.stem)
            parte = partes.get(cap)
            capitulos.append((cap, titulo, parte))
            if parte and parte != parte_actual:
                cuerpo_caps.append(separador(parte))
                parte_actual = parte
            cuerpo_caps.append(capitulo(md))
        cuerpo = (paginas_iniciales(capitulos) + '<div class="cuerpo" id="inicio-cuerpo">' + ''.join(cuerpo_caps) + '</div>'
                  + contraportada())
    doc = f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{TITULO}</title><style>{css()}</style></head><body>{cuerpo}</body></html>'
    if pedido:
        SALIDA.mkdir(exist_ok=True)
        destino = SALIDA / f'capitulo-{"-".join(pedido)}.pdf'
    else:
        destino = LIBRO / 'libro.pdf'
    weasy = shutil.which('weasyprint') or str(pathlib.Path.home() / '.local' / 'bin' / 'weasyprint')
    with tempfile.NamedTemporaryFile('w', suffix='.html', encoding='utf-8', delete=False) as f:
        f.write(doc)
    # Se escribe aparte y se reemplaza de una vez: quien tenga libro.pdf
    # abierto (o dos armados a la vez) nunca ve un PDF a medio escribir.
    temporal = destino.with_name(f'.{destino.stem}.{os.getpid()}.pdf')
    try:
        if pedido:
            subprocess.run([weasy, '-u', str(LIBRO) + '/', f.name, str(temporal)], check=True)
        else:
            escribir_con_indice(doc, temporal)
        os.replace(temporal, destino)
    finally:
        pathlib.Path(f.name).unlink()
        temporal.unlink(missing_ok=True)
    print(destino)
    if pedido and completo_despues:
        # El libro completo se rearma después de cada capítulo: libro.pdf es
        # el compilado de referencia y tiene que estar siempre al día.
        formato = sys.argv[sys.argv.index('--formato'):sys.argv.index('--formato') + 2] if '--formato' in sys.argv else []
        subprocess.run([sys.executable, __file__, *formato], check=True)


if __name__ == '__main__':
    main()
