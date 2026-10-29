"""Caras de los acompañantes (madre, padre...) de los pacientes menores del libro,
a partir de la cara del hijo, para que se parezcan.

    cd libro-orl && ~/.local/share/labsim/libro-venv/bin/python ../LabSim/scripts/libro/caras_acompanantes.py CARPETA

CARPETA tiene datos_libro.json e ids_libro.json (ver sql_practica.py). Deja
material/rostros/acompanantes/<caso>__<rol>.jpg y CARPETA/acompanantes.json para
subirlas con consola.py rostro <id> <archivo> --persona <id>. Revisarlas antes.
"""
import base64, io, json, pathlib, sys, urllib.request
from PIL import Image
LIBRO = pathlib.Path.home() / 'Escritorio/Proyectos/libro-orl'
sys.path.insert(0, str(LIBRO / 'herramientas'))
from ilustrar import clave, MODELO
from rostros import ESTILO
S = pathlib.Path(sys.argv[1])
SALIDA = LIBRO / 'material/rostros/acompanantes'; SALIDA.mkdir(exist_ok=True)
datos = json.load(open(S / 'datos_libro.json')); ids = json.load(open(S / 'ids_libro.json'))
ROLES = {'madre': 'mother', 'padre': 'father', 'abuelo': 'grandparent', 'cuidador': 'caregiver'}
hechos = []
for k, d in datos.items():
    if k not in ids or int(d.get('edad') or 0) >= 18:
        continue
    for p in d.get('Sala', {}).get('personas', []):
        if p.get('es_paciente') or p.get('rol') not in ROLES:
            continue
        destino = SALIDA / f"{k}__{p['rol']}.jpg"
        if destino.exists():
            hechos.append((k, p, destino)); continue
        hijo = LIBRO / 'material/rostros' / f'{k}.jpg'
        sexo = 'woman' if p.get('genero') == 1 else 'man'
        texto = (ESTILO + f"a Chilean {sexo}, {p.get('edad')} years old, the {ROLES[p['rol']]} of the child in the "
                 "reference photo: same family, coherent ethnicity and features, an ordinary person at a hospital "
                 "audiology appointment, everyday clothes"
                 + (f", looks {p['comportamiento']}" if p.get('comportamiento') else '') + '. '
                 "The reference photo is ONLY to keep the family resemblance: show the adult alone, not the child.")
        partes = [{'text': texto}, {'inlineData': {'mimeType': 'image/jpeg',
                                                   'data': base64.b64encode(hijo.read_bytes()).decode()}}]
        cuerpo = {'contents': [{'parts': partes}],
                  'generationConfig': {'responseModalities': ['IMAGE'], 'imageConfig': {'aspectRatio': '1:1'}}}
        # curl y no urllib: urllib se cuelga en este equipo (IPv6) y curl responde en segundos
        import subprocess
        try:
            r = subprocess.run(['curl', '-s', '--max-time', '120', '-H', f'x-goog-api-key: {clave()}',
                                '-H', 'Content-Type: application/json', '--data-binary', '@-',
                                f'https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent'],
                               input=json.dumps(cuerpo).encode(), capture_output=True, timeout=150)
            resp = json.loads(r.stdout)
            img = next(base64.b64decode(x['inlineData']['data']) for x in resp['candidates'][0]['content']['parts'] if 'inlineData' in x)
        except Exception as e:
            print('FALLA', k, e); continue
        Image.open(io.BytesIO(img)).convert('RGB').resize((512, 512), Image.LANCZOS).save(destino, quality=88)
        hechos.append((k, p, destino)); print('ok', k, p['rol'], p.get('edad'))
json.dump([{'clave': k, 'case_id': ids[k], 'persona': p['id'], 'rol': p['rol'], 'nombre': p.get('nombre'),
            'archivo': str(f)} for k, p, f in hechos], open(S / 'acompanantes.json', 'w'), ensure_ascii=False, indent=1)
print(len(hechos), 'acompañantes con cara')
