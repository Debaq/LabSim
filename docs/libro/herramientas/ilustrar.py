#!/usr/bin/env python3
"""Dibuja las ilustraciones del libro con Gemini, en estilo BioRender.

    GEMINI_API_KEY=... python3 docs/libro/herramientas/ilustrar.py              las que falten
    GEMINI_API_KEY=... python3 docs/libro/herramientas/ilustrar.py h01-otoscopio   solo esa (la rehace)
    python3 docs/libro/herramientas/ilustrar.py --listar                         qué falta, sin dibujar

Busca en capitulos/*.md las imágenes de ilustraciones/ que todavía no existen:
`![descripción](ilustraciones/x.png)` y `:::imagen ilustraciones/x.png Título`
(en este caso la descripción es la línea `<!-- dibujo: ... -->` que va
debajo del encabezado del bloque). La descripción dice QUÉ mostrar; el
estilo lo pone este script. Los dibujos van SIN TEXTO: los rótulos los pone
el libro con globos numerados, así no hay letras inventadas por la IA.

La key se lee de GEMINI_API_KEY o de ~/.kaggle/gemini_key (junto al token de
Kaggle; también ~/.config/labsim/gemini_key); nunca va
al repo. Cada dibujo queda registrado en ilustraciones/REGISTRO.md (modelo,
fecha y descripción): toda ilustración generada se revisa antes de publicar,
la IA se equivoca en anatomía.
"""
import base64
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.request

AQUI = pathlib.Path(__file__).resolve().parent        # docs/libro/herramientas
LIBRO = AQUI.parent
ILUSTRACIONES = LIBRO / 'ilustraciones'
REGISTRO = ILUSTRACIONES / 'REGISTRO.md'
MODELO = 'gemini-3.1-flash-image'

ESTILO = (
    'Scientific medical illustration for a university audiology textbook, in the clean flat vector style '
    'of BioRender: soft pastel colors, smooth subtle gradients, thin dark outlines, pure white background, '
    'anatomically and technically accurate, uncluttered composition with generous margins. '
    'ABSOLUTELY NO TEXT: no letters, no words, no labels, no numbers, no captions, no arrows with text. '
    'Subject (described in Spanish): '
)


def clave():
    k = os.environ.get('GEMINI_API_KEY')
    # Junto al token de Kaggle (~/.kaggle/access_token); la ruta vieja sigue valiendo.
    for f in (pathlib.Path.home() / '.kaggle' / 'gemini_key',
              pathlib.Path.home() / '.config' / 'labsim' / 'gemini_key'):
        if k:
            break
        k = f.read_text().strip() if f.exists() else None
    if not k:
        sys.exit('Falta la key: GEMINI_API_KEY=... o ~/.kaggle/gemini_key')
    return k


def pedidos():
    """{nombre: descripción} de todas las ilustraciones nombradas en los capítulos."""
    out = {}
    for md in sorted((LIBRO / 'capitulos').glob('*.md')):
        texto = md.read_text(encoding='utf-8')
        for desc, ruta in re.findall(r'!\[([^\]]+)\]\((ilustraciones/[^)]+)\)', texto):
            out[pathlib.Path(ruta).stem] = desc
        for ruta, cuerpo in re.findall(r'^:::imagen\s+(ilustraciones/\S+)[^\n]*\n(.*?)^:::', texto, re.M | re.S):
            dib = re.search(r'<!--\s*dibujo:\s*(.*?)-->', cuerpo, re.S)
            if dib:
                out[pathlib.Path(ruta).stem] = ' '.join(dib[1].split())
    return out


def sin_rotulos(descripcion):
    """Saca de la descripción los pedidos de rotular: los rótulos los pone el libro."""
    d = re.sub(r'\b[Rr]otular\b[^.]*\.?', '', descripcion)
    d = re.sub(r'\b[Rr]otulad[oa]s?\b', '', d)
    d = re.sub(r'"[^"]*"', '', d)                      # textos entre comillas
    return ' '.join(d.split())


def dibujar(nombre, descripcion, k, aspecto='4:3'):
    texto = (ESTILO + sin_rotulos(descripcion)
             + ' REMEMBER: the image must contain zero written characters of any kind; leave clean space where '
               'labels would go, they will be added later by the book.')
    cuerpo = {'contents': [{'parts': [{'text': texto}]}],
              'generationConfig': {'responseModalities': ['IMAGE'], 'imageConfig': {'aspectRatio': aspecto}}}
    req = urllib.request.Request(
        f'https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent',
        data=json.dumps(cuerpo).encode(), headers={'x-goog-api-key': k, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    for p in d['candidates'][0]['content']['parts']:
        if 'inlineData' in p:
            destino = ILUSTRACIONES / f'{nombre}.png'
            destino.write_bytes(base64.b64decode(p['inlineData']['data']))
            return destino
    raise RuntimeError(f'{nombre}: Gemini no devolvió imagen')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    todos = pedidos()
    ILUSTRACIONES.mkdir(exist_ok=True)
    if args:
        faltan = {n: todos[n] for n in args if n in todos}
        desconocidos = [n for n in args if n not in todos]
        if desconocidos:
            sys.exit('No están en ningún capítulo: ' + ', '.join(desconocidos))
    else:
        faltan = {n: d for n, d in todos.items() if not (ILUSTRACIONES / f'{n}.png').exists()}
    if '--listar' in sys.argv:
        for n, d in faltan.items():
            print(f'{n}: {d[:110]}')
        return
    k = clave()
    if not REGISTRO.exists():
        REGISTRO.write_text('# Ilustraciones generadas\n\nCada dibujo: modelo, fecha y lo que se pidió. '
                            'Se revisan antes de publicar.\n\n', encoding='utf-8')
    for n, d in faltan.items():
        f = dibujar(n, d, k)
        with REGISTRO.open('a', encoding='utf-8') as r:
            r.write(f'- **{f.name}** · {MODELO} · {datetime.date.today()} · {d}\n')
        print('  ', f.name)


if __name__ == '__main__':
    main()
