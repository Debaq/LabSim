#!/usr/bin/env python3
"""Rostros de los pacientes del libro (la "carita" de la ficha de cada caso).

    python3 docs/libro/herramientas/rostros.py              # los que faltan
    python3 docs/libro/herramientas/rostros.py demo-41      # rehacer uno (o varios)
    python3 docs/libro/herramientas/rostros.py --listar     # quién tiene y quién no

Uno por PERSONA, no por caso: un paciente de práctica (demo:NN) aparece en
varios capítulos con distinto nombre de caso y tiene que ser la misma cara.
La clave es `demo-NN` para esos y el nombre del caso para los armados por
cuadro (ver clave_rostro() en hacer_libro.py).

Los pedidos están en rostros/pedidos.json: edad, sexo y lo que se vería en la
cara según el caso (una microtia, la boca abierta del que respira por la
boca, el cráneo del Paget, una parálisis facial...). Personas ficticias:
retratos sintéticos, nunca parecidos a alguien real. Cada imagen se revisa
antes de usarla; queda anotada en rostros/REGISTRO.md.
"""
import datetime
import json
import pathlib
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ilustrar import clave, MODELO  # noqa: E402

import base64  # noqa: E402

LIBRO = pathlib.Path(__file__).resolve().parent.parent
ROSTROS = LIBRO / 'rostros'
PEDIDOS = ROSTROS / 'pedidos.json'
REGISTRO = ROSTROS / 'REGISTRO.md'

ESTILO = (
    'Photorealistic synthetic portrait photograph of a FICTIONAL person (must not resemble any real or famous '
    'person), for the patient card of a clinical case in a university audiology textbook. Head and shoulders, '
    'facing the camera or slightly turned, natural soft window light, plain light warm-grey background, '
    'natural skin texture, realistic age, no makeup glamour, dignified and respectful. '
    'Absolutely no text, letters, logos or watermarks. Square framing with the face centred. Person: '
)


def retratar(nombre, descripcion, k):
    cuerpo = {'contents': [{'parts': [{'text': ESTILO + descripcion}]}],
              'generationConfig': {'responseModalities': ['IMAGE'], 'imageConfig': {'aspectRatio': '1:1'}}}
    req = urllib.request.Request(
        f'https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent',
        data=json.dumps(cuerpo).encode(), headers={'x-goog-api-key': k, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    for p in d['candidates'][0]['content']['parts']:
        if 'inlineData' in p:
            # 512 px en JPG: en la ficha va a 24 mm, y así el repo no carga
            # 650 KB por cara
            import io
            from PIL import Image
            img = Image.open(io.BytesIO(base64.b64decode(p['inlineData']['data']))).convert('RGB')
            destino = ROSTROS / f'{nombre}.jpg'
            img.resize((512, 512), Image.LANCZOS).save(destino, quality=88)
            return destino
    raise RuntimeError(f'{nombre}: Gemini no devolvió imagen')


def main():
    pedidos = json.loads(PEDIDOS.read_text(encoding='utf-8'))
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--listar' in sys.argv:
        for n in pedidos:
            print(('✓ ' if (ROSTROS / f'{n}.jpg').exists() else '· ') + n)
        return
    nombres = args or [n for n in pedidos if not (ROSTROS / f'{n}.jpg').exists()]
    k = clave()
    if not REGISTRO.exists():
        REGISTRO.write_text('# Rostros generados\n\nPersonas ficticias. Cada retrato: modelo, fecha y lo que se pidió.\n\n')
    for n in nombres:
        try:
            f = retratar(n, pedidos[n], k)
        except Exception as e:  # uno que falla no frena al resto
            print(f'✗ {n}: {e}')
            continue
        with REGISTRO.open('a', encoding='utf-8') as r:
            r.write(f'- **{f.name}** · {MODELO} · {datetime.date.today()} · {pedidos[n]}\n')
        print(f'✓ {f.relative_to(LIBRO)}')


if __name__ == '__main__':
    main()
