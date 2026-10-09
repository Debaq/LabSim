#!/usr/bin/env python3
"""Arma el PDF de un manual de LabSim desde su markdown.

    python3 docs/manual/hacer_pdf.py estudiante   ->  manual-estudiante.pdf
    python3 docs/manual/hacer_pdf.py docente      ->  manual-docente.pdf

Mismo diagramador que el manual de PosAR, con los colores de LabSim.

Necesita los paquetes de Python `markdown`, `pillow` y `weasyprint` (pip install markdown pillow weasyprint).
Reglas de diagramación: cada sección numerada empieza en hoja nueva (la primera de cada
parte va con el título de la parte); una imagen sola en su párrafo va a todo el ancho y
varias seguidas, en fila; las imágenes verticales (celular, secciones del panel) van más bajas.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import pathlib
import markdown
import datetime
from PIL import Image

dir_ = pathlib.Path(__file__).resolve().parent
fuentes = dir_ / 'fuentes'
MANUALES = {
    'estudiante': {'kicker': 'Manual del estudiante', 'bajada': 'Simulador de evaluación auditiva y vestibular',
                   'pie': 'LabSim · manual del estudiante', 'portada': 'img/portada-estudiante.svg'},
    'docente': {'kicker': 'Manual del docente', 'bajada': 'Simulador de evaluación auditiva y vestibular',
                'pie': 'LabSim · manual del docente', 'portada': 'img/portada-docente.svg'},
}
cual = sys.argv[1] if len(sys.argv) > 1 else 'estudiante'
if cual not in MANUALES:
    sys.exit('Uso: hacer_pdf.py estudiante|docente')
M = MANUALES[cual]
# La versión de la app, de donde la define la app misma: el manual dice
# para qué versión se escribió y se actualiza solo al cambiarla.
_main = (dir_.parents[1] / 'src' / 'main.py').read_text(encoding='utf-8')
VERSION = re.search(r"__VERSION__\s*=\s*'v?([^']+)'", _main)[1]
# Y el commit, con el mismo formato que el título de la app (v0.9.9-r<sha>,
# ver scripts/release_pyinstaller.sh): dice exactamente qué código describe
# el manual. Sin git (copia suelta), solo la versión.
try:
    _sha = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=dir_, check=True,
                          capture_output=True, text=True).stdout.strip()
    VERSION = f'v{VERSION}-r{_sha}' if _sha else f'v{VERSION}'
except (OSError, subprocess.CalledProcessError):
    VERSION = f'v{VERSION}'
md = (dir_ / f'manual-{cual}.md').read_text(encoding='utf-8')

cuerpo = markdown.markdown(md, extensions=['tables', 'fenced_code'])

IMG = re.compile(r'<img alt="([^"]*)" src="([^"]*)" ?/?>')
def figura(alt, src):
    return f'<figure><img src="{src}"><figcaption>{alt}</figcaption></figure>'
def parrafo(m):
    imgs = IMG.findall(m[0])
    if len(imgs) == 1:
        alt, src = imgs[0]
        ancho, alto = Image.open(dir_ / src).size
        # capturas altas: las del panel y la administración, con texto, van más grandes que las del celular
        clase = '' if alto <= ancho else ' class="alta"' if src.startswith(('img/admin-', 'img/sec-')) else ' class="sola-movil"'
        return f'<figure{clase}><img src="{src}"><figcaption>{alt}</figcaption></figure>'
    return '<div class="fila">' + ''.join(figura(a, s) for a, s in imgs) + '</div>'
# un párrafo hecho sólo de imágenes: una sola va a todo el ancho; varias, en fila
cuerpo = re.sub(r'<p>(?:\s*<img [^>]+>\s*)+</p>', parrafo, cuerpo)
# todos los h1 salvo el título son partes (la guía rápida y las partes I a IV)
primero = cuerpo.index('</h1>')
cuerpo = cuerpo[:primero] + cuerpo[primero:].replace('<h1>', '<h1 class="parte">')

# portada y segunda hoja: lo que está antes de la parte I
corte = cuerpo.index('<h1 class="parte">')
preambulo, resto = cuerpo[:corte], cuerpo[corte:]
titulo = re.search(r'<h1>(.*?)</h1>', preambulo, re.S)[1].split(' — ')[0]
autores = re.findall(r'<li>(.*?)</li>', re.search(r'<strong>Autores</strong></p>\s*<ul>(.*?)</ul>', preambulo, re.S)[1])
casa = re.search(r'<strong>Autores</strong></p>\s*<ul>.*?</ul>\s*<p>(.*?)</p>', preambulo, re.S)[1]
LOGOS = ['img/logos/icono_app.png', 'img/logos/uach-blanco.png', 'img/logos/tecmedhub-blanco.png']   # en blanco, para el fondo oscuro
MESES = 'enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split()
hoy = datetime.date.today()
portada = f'''<section class="portada">
  <p class="kicker">{M['kicker']}</p>
  <h1 class="tapa">{titulo}</h1>
  <p class="bajada">{M['bajada']}</p>
  <p class="version">LabSim {VERSION}</p>
  <img class="ilustracion" src="{M['portada']}">
  <div class="pie-tapa">
    <div class="logos">{"".join(f'<img src="{x}">' for x in LOGOS)}</div>
    <p class="autores">{"<br>".join(" · ".join(f'<span>{x}</span>' for x in autores[i:i + 2]) for i in range(0, len(autores), 2))}</p>
    <p class="casa">{casa}</p>
    <p class="fecha">{MESES[hoy.month - 1].capitalize()} de {hoy.year}</p>
  </div>
</section>'''
segunda = ('<section class="segunda"><p class="rotulo-hoja">Sobre este manual</p>'
           + re.sub(r'<h1>.*?</h1>', '', preambulo, count=1, flags=re.S) + '</section>')
cuerpo = portada + segunda + resto
cuerpo = cuerpo.replace('<td>☐</td>', '<td class="casilla">☐</td>')
# los emojis de color no salen en el PDF: los estados van como puntos de color y el resto se quita
for emoji, color in (('🟢', '#2e9e4f'), ('🟡', '#e0a800'), ('🔴', '#d33a2c'), ('⚪', '#b8b2a8')):
    cuerpo = cuerpo.replace(emoji, f'<span style="color: {color}">●</span>')
for emoji in ('📸 ', '⏳ ', '📷 ', '⚙ ', '💡 '):
    cuerpo = cuerpo.replace(emoji, '')
# las tablas largas (la guía rápida, los problemas frecuentes) se pueden partir entre hojas
cuerpo = re.sub(r'<table>((?:(?!</table>).)*?)</table>', lambda m: ('<table class="larga">' if m[1].count('<tr>') > 9 else '<table>') + m[1] + '</table>', cuerpo, flags=re.S)
# cada sección numerada empieza en hoja nueva, salvo la primera de cada parte, que va con el título de la parte
cuerpo = re.sub(r'(<h1 class="parte">.*?)<h2>', lambda m: m[1] + '<h2 class="primera">', cuerpo, flags=re.S)

# un título no queda al pie de una hoja con su imagen en la siguiente: el título (con los
# subtítulos que le sigan pegados), lo que haya
# antes de su primera imagen (hasta tres bloques) y la imagen van juntos en un bloque
def juntar(m):
    titulo, despues = m[1], m[2]
    ini = despues.find('<figure')
    if ini < 0:
        return m[0]
    if despues[:ini].endswith('<div class="fila">'):
        ini -= len('<div class="fila">')
        fin = despues.index('</div>', ini) + len('</div>')
    else:
        fin = despues.index('</figure>', ini) + len('</figure>')
    if len(re.findall(r'^<(?:p|ul|ol|table|blockquote|pre)\b', despues[:ini], re.M)) > 3:
        return m[0]
    return f'<div class="junto">{titulo}{despues[:fin]}</div>{despues[fin:]}'
cuerpo = re.sub(r'((?:<h[234][^>]*>.*?</h[234]>\s*)+)(.*?)(?=<h[1234][ >]|$)', juntar, cuerpo, flags=re.S)
# un párrafo que presenta un bloque de código o una tabla («…:») va en la misma hoja que el bloque
cuerpo = re.sub(r'(<p>(?:(?!</p>).){0,400}:</p>\s*)(<pre>.*?</pre>|<table>.*?</table>)',
                r'<div class="junto">\1\2</div>', cuerpo, flags=re.S)

css = f"""
@font-face {{ font-family: Fraunces; src: url('file://{fuentes}/fraunces-latin.woff2'); }}
@font-face {{ font-family: Jakarta; src: url('file://{fuentes}/plus-jakarta-sans-latin.woff2'); }}
@font-face {{ font-family: Jakarta; src: url('file://{fuentes}/plus-jakarta-sans-latin-ext.woff2'); }}
@page {{ size: A4; margin: 15mm 14mm 16mm 14mm;
        @bottom-right {{ content: counter(page); font: 8pt Jakarta; color: #8f7a83; }}
        @bottom-left {{ content: "{M['pie']}"; font: 8pt Jakarta; color: #8f7a83; }} }}
@page portada {{ margin: 0; background: #24101a; @bottom-left {{ content: none; }} @bottom-right {{ content: none; }} }}
@page :first {{ @bottom-left {{ content: none; }} }}
.portada {{ page: portada; position: relative; height: 297mm; color: #F8F1F3; text-align: center; }}
.portada .kicker {{ position: absolute; top: 30mm; left: 0; right: 0; margin: 0; font: 700 9pt Jakarta; letter-spacing: 2.5pt;
                   text-transform: uppercase; color: #E7A7BA; }}
.portada h1.tapa {{ position: absolute; top: 38mm; left: 20mm; right: 20mm; margin: 0; font: 700 40pt/1.08 Fraunces, serif; color: #F8F1F3; }}
.portada .bajada {{ position: absolute; top: 56mm; left: 0; right: 0; margin: 0; font: 13pt Jakarta; color: #DCC8CF; }}
.portada .version {{ position: absolute; top: 64mm; left: 0; right: 0; margin: 0; font: 600 10pt Jakarta;
                    letter-spacing: .3pt; color: #E7A7BA; }}
.portada .ilustracion {{ position: absolute; top: 78mm; left: 37mm; width: 136mm; }}
.portada .pie-tapa {{ position: absolute; bottom: 18mm; left: 20mm; right: 20mm; border-top: .8pt solid #4a2232; padding-top: 6mm; }}
.portada .logos {{ display: flex; justify-content: center; align-items: center; gap: 14mm; margin: 0 0 5mm; }}
.portada .logos img {{ height: 19mm; }}
.portada .logos img:first-child {{ height: 20mm; }}
.portada .logos img:last-child {{ height: 24mm; }}
.portada .pie-tapa p {{ margin: 0 0 1.6mm; }}
.portada .autores {{ font: 600 10.5pt/1.6 Jakarta; color: #F8F1F3; }}
.portada .autores span {{ white-space: nowrap; }}
.portada .casa {{ font: 9pt Jakarta; color: #DCC8CF; }}
.portada .fecha {{ font: 8.5pt Jakarta; color: #A68F98; }}
.segunda {{ break-before: page; }}
.segunda .rotulo-hoja {{ font: 600 19pt/1.2 Fraunces, serif; color: #24101a; margin: 0 0 2mm; padding-bottom: 2mm; border-bottom: 1.2pt solid #8e2a4a; }}
.segunda .rotulo-hoja + p {{ font: 11pt/1.5 Jakarta; color: #7a2341; margin: 3mm 0 7mm; }}
.segunda p > strong:only-child {{ display: block; font: 700 8pt Jakarta; letter-spacing: 1.2pt; text-transform: uppercase; color: #7a2341; margin-top: 6mm; }}
.segunda blockquote {{ margin-top: 8mm; }}
.segunda ul {{ list-style: none; padding: 0; margin: 0 0 1mm; }}
.segunda li {{ margin: 0 0 .6mm; }}
html {{ font: 9.6pt/1.5 Jakarta, sans-serif; color: #2a1a20; }}
h1 {{ font: 700 26pt/1.1 Fraunces, serif; color: #24101a; margin: 18mm 0 3mm; }}
h1 + p {{ margin-top: 0; color: #7a2341; font-size: 11pt; }}
h1.parte {{ break-before: page; font-size: 21pt; margin: 0 0 4mm; padding: 0 0 2mm; border-bottom: 2pt solid #8e2a4a; }}
h2 {{ font: 600 15pt/1.2 Fraunces, serif; color: #24101a; margin: 7mm 0 2mm; padding-bottom: 1mm;
      border-bottom: 1.2pt solid #8e2a4a; break-after: avoid; break-before: page; }}
h2.primera {{ break-before: auto; }}
.junto {{ break-inside: avoid; }}
h1.parte + p, h1.parte + p + p {{ break-after: avoid; }}
h3 {{ font: 600 12pt/1.25 Fraunces, serif; color: #641c34; margin: 5mm 0 1.5mm; break-after: avoid; }}
h4 {{ font: 600 10.5pt/1.25 Fraunces, serif; color: #641c34; margin: 4mm 0 1mm; break-after: avoid; }}
h2 + p, h3 + p, h4 + p, h2 + p + p, h3 + p + p, h4 + p + p, h2 + blockquote, h3 + blockquote, h4 + blockquote {{ break-after: avoid; }}
p {{ margin: 0 0 2.2mm; }}
ul, ol {{ margin: 0 0 2.5mm; padding-left: 5mm; }}
li {{ margin-bottom: .8mm; }}
li > ul {{ margin: .8mm 0 0; }}
hr {{ border: 0; margin: 2mm 0; }}
code {{ font: 8.4pt monospace; background: #f4e9ed; padding: .2mm 1mm; border-radius: 1mm; }}
pre {{ background: #f4e9ed; padding: 2.5mm 3.5mm; border-radius: 2mm; break-inside: avoid; }}
pre code {{ background: none; padding: 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 1.5mm 0 3.5mm; font-size: 8.6pt; break-inside: avoid; }}
th {{ text-align: left; background: #2a1a20; color: #f8eef1; font-weight: 600; padding: 1.4mm 2mm; }}
td {{ padding: 1.2mm 2mm; border-bottom: .5pt solid #e6d3da; vertical-align: top; }}
tr:nth-child(even) td {{ background: #fbf4f6; }}
blockquote {{ margin: 2mm 0 3mm; padding: 2.2mm 3.5mm; background: #f8e8ee; border-left: 1.4pt solid #8e2a4a;
              border-radius: 0 1.5mm 1.5mm 0; break-inside: avoid; }}
blockquote p {{ margin: 0; }}
figure {{ margin: 2.5mm 0 4mm; break-inside: avoid; }}
figure img {{ max-width: 100%; max-height: 112mm; border-radius: 1.6mm; display: block; margin: 0 auto; }}
figure.sola-movil img {{ max-height: 95mm; }}
figure.alta img {{ max-height: 150mm; }}
table.larga {{ break-inside: auto; }}
table.larga tr {{ break-inside: avoid; }}
figcaption {{ font-size: 7.8pt; color: #7d6670; margin-top: 1.2mm; font-style: italic; text-align: center; }}
.fila {{ display: flex; justify-content: center; gap: 5mm; margin: 2.5mm 0 4mm; break-inside: avoid; }}
.fila figure {{ flex: 1 1 0; margin: 0; }}
.fila figure img {{ max-width: 100%; max-height: 105mm; border: .4pt solid #d8c3cb; }}
strong {{ color: #24101a; }}
/* guía rápida: pasos en tarjetas, de a dos (media hoja) o a todo el ancho */
.paso {{ box-sizing: border-box; margin: 0 0 4mm; padding: 3mm 3.5mm 2.5mm;
        border: .8pt solid #e6d3da; border-radius: 3mm; background: #fff; break-inside: avoid; }}
.par {{ display: table; table-layout: fixed; width: 100%; margin: 0 0 4mm; break-inside: avoid; }}
.par > .paso {{ display: table-cell; vertical-align: top; margin: 0; }}
.par > .hueco {{ display: table-cell; width: 4mm; }}
.paso.clave {{ border: 1.6pt solid #a8325a; background: #fdf6f8; }}
.paso-cab {{ display: flex; align-items: center; gap: 3mm; margin-bottom: 2.5mm; }}
.num {{ display: flex; flex: none; width: 10mm; height: 10mm; border-radius: 50%; background: #24101a; color: #fff;
        font: 700 15pt/1 Fraunces, serif; align-items: center; justify-content: center; }}
.clave .num {{ background: #a8325a; }}
.titulo {{ font: 600 13pt/1.15 Fraunces, serif; color: #24101a; }}
.paso img {{ display: block; max-width: 100%; margin: 0 auto 2mm; border-radius: 1.5mm; }}
.paso img.dibujo {{ max-height: 52mm; border-radius: 0; }}
.paso.ancho > img.dibujo {{ max-height: 80mm; }}
.paso > img:not(.dibujo) {{ width: 100%; height: auto; max-height: 95mm; object-fit: contain; }}
.paso img.mini {{ max-height: 42mm; }}
.paso p {{ margin: 0 0 1.5mm; }}
.paso figure {{ margin: 0; }}
.paso figcaption {{ font-style: normal; font-size: 8.4pt; color: #3a2630; margin: 1mm 0 2mm; }}
.fila-img {{ display: table; table-layout: fixed; width: 100%; margin: 0 0 1.5mm; }}
.fila-img > * {{ display: table-cell; vertical-align: top; padding: 0 1.5mm; }}
.fila-img > figure.angosta {{ width: 28%; }}
.fila-img img {{ width: 100%; height: auto; max-height: 70mm; object-fit: contain; }}
.paso:not(.ancho) .fila-img img.dibujo {{ max-height: 32mm; }}
.opciones {{ display: table; table-layout: fixed; width: 100%; }}
.opciones > div {{ display: table-cell; width: 50%; vertical-align: top; }}
.opciones > div:first-child {{ padding-right: 5mm; }}
.opcion {{ font: 700 10.5pt Jakarta; color: #a8325a; margin-bottom: 1mm !important; }}
.aviso {{ display: flex; gap: 4mm; align-items: center; background: #f6dde5; border-radius: 2mm; padding: 2.5mm 3.5mm; margin-top: 2mm; }}
.aviso p {{ margin: 0; }}
.aviso img.huincha {{ width: 62mm; flex: none; margin: 0; max-height: none; }}
.paso table {{ font-size: 8.8pt; margin: 1mm 0 2mm; }}

td.casilla {{ width: 5mm; font-size: 11pt; color: #8e2a4a; text-align: center; }}
"""

html = f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>LabSim — {M["kicker"].lower()}</title><style>{css}</style></head><body>{cuerpo}</body></html>'
weasy = shutil.which('weasyprint') or str(pathlib.Path.home() / '.local' / 'bin' / 'weasyprint')
with tempfile.NamedTemporaryFile('w', suffix='.html', encoding='utf-8', delete=False) as f:
    f.write(html)
try:
    subprocess.run([weasy, '-u', str(dir_) + '/', f.name, str(dir_ / f'manual-{cual}.pdf')], check=True)
finally:
    pathlib.Path(f.name).unlink()
print(dir_ / f'manual-{cual}.pdf')
