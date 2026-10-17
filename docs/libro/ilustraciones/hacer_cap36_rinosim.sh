#!/usr/bin/env bash
# Figuras del capitulo 36 (rinitis y vasoconstrictor) hechas con RinoSim (software libre del autor).
# Reproduce docs/libro/ilustraciones/cap36-rs-*.svg y los numeros de las tablas del capitulo.
#   RINOSIM=/ruta/a/rinosim bash docs/libro/ilustraciones/hacer_cap36_rinosim.sh
# No modifica RinoSim: las figuras salen a una carpeta temporal y de ahi se copian.
# Con NUMEROS=/carpeta quedan ahi los numeros.json de cada paciente.
set -euo pipefail
RINOSIM=${RINOSIM:-/home/nick/Escritorio/Proyectos/rinosim}
ILUS=$(cd "$(dirname "$0")" && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fig() { # fig <carpeta> <opciones de figuras.mjs...>
  local n=$1; shift
  (cd "$RINOSIM" && node tools/figuras.mjs "$@" --salida "$TMP/$n" >/dev/null)
}

# Caso 1: rinitis alergica, cornetes con mucosa congestionada; minuto 5 del ciclo nasal (las fosas no quedan identicas)
fig alergica  --cuadro cornetes --minuto 5
# Caso 2: rinitis medicamentosa; mismo cuadro, variante individual (semilla 1) mas congestionada
fig medic     --cuadro cornetes --semilla 1
# Caso 3: desviacion derecha mas cornetes congestionados (mixta); minuto 10 del ciclo
fig mixta     --cuadro mixta --minuto 10
# Pólipos: el segundo minimo ya no es el cornete (solo la fosa derecha)
fig polipos   --cuadro polipos --lado D --minuto 0

if [ -n "${NUMEROS:-}" ]; then mkdir -p "$NUMEROS"; for d in "$TMP"/*/; do cp "$d/numeros.json" "$NUMEROS/$(basename "$d").json"; done; fi

cp "$TMP/alergica/rm-curva.svg" "$ILUS/cap36-rs-alergica-rm.svg"
cp "$TMP/alergica/ra-curva.svg" "$ILUS/cap36-rs-alergica-ra.svg"
cp "$TMP/medic/rm-curva.svg"    "$ILUS/cap36-rs-medic-rm.svg"
cp "$TMP/medic/ra-curva.svg"    "$ILUS/cap36-rs-medic-ra.svg"
cp "$TMP/mixta/rm-curva.svg"    "$ILUS/cap36-rs-mixta-rm.svg"
cp "$TMP/mixta/ra-curva.svg"    "$ILUS/cap36-rs-mixta-ra.svg"
cp "$TMP/polipos/ra-curva.svg"  "$ILUS/cap36-rs-polipos-ra.svg"

# ---- Ciclo nasal simulado: resistencia a 150 Pa de cada fosa cada 5 minutos, en una nariz normal y en otra con cornetes congestionados ----
# Se leen con las funciones de RinoSim (solo lectura) y se dibujan aqui.
RINOSIM="$RINOSIM" node --input-type=module - > "$TMP/ciclo.json" <<'JS'
const R = process.env.RINOSIM;
const { paciente } = await import(R + '/js/modelo.js');
const RM = await import(R + '/js/rinomanometria.js');
const sal = {};
for (const cuadro of ['normal', 'cornetes']) {
  sal[cuadro] = [];
  for (let m = 0; m <= 300; m += 5) {
    const e = RM.examen(paciente(cuadro), { vc: false, minuto: m }, {});
    sal[cuadro].push({ m, D: e.fosas.D.lecturas['150'].insp.R, I: e.fosas.I.lecturas['150'].insp.R, T: e.total['150'] });
  }
}
console.log(JSON.stringify(sal));
JS
if [ -n "${NUMEROS:-}" ]; then cp "$TMP/ciclo.json" "$NUMEROS/ciclo.json"; fi

python3 - "$TMP/ciclo.json" "$ILUS/cap36-rs-ciclo.svg" <<'PY'
import json, math, sys
datos = json.load(open(sys.argv[1]))
FUENTE = "'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif"
ROJO, AZUL, GRIS, REJ, EJE = '#c62f3a', '#2b5fa8', '#8a8a90', '#e7e5e0', '#cfccc5'
W, ANCHO_P, ALTO_P = 700, 620, 150
X0, Y0 = 62, 14
YMIN, YMAX = 0.1, 100.0
def px(m): return X0 + m / 300 * ANCHO_P
def py(r, top): return top + ALTO_P - (math.log10(max(r, YMIN)) - math.log10(YMIN)) / (math.log10(YMAX) - math.log10(YMIN)) * ALTO_P
def t(x, y, s, size=9.5, anchor='start', fill='#44403c', peso=400):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FUENTE}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" font-weight="{peso}">{s}</text>'
partes = []
alto_total = 0
for i, (clave, letra) in enumerate([('normal', 'A'), ('cornetes', 'B')]):
    top = Y0 + i * (ALTO_P + 62)
    for v in (0.1, 1, 10, 100):
        y = py(v, top)
        partes.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X0 + ANCHO_P}" y2="{y:.1f}" stroke="{REJ}" stroke-width="0.6"/>')
        partes.append(t(X0 - 6, y + 3.5, str(v).replace('.', ',').rstrip('0').rstrip(',') if v < 1 else str(int(v)), anchor='end', fill=GRIS))
    for m in range(0, 301, 50):
        partes.append(f'<line x1="{px(m):.1f}" y1="{top}" x2="{px(m):.1f}" y2="{top + ALTO_P}" stroke="{REJ}" stroke-width="0.6"/>')
        partes.append(t(px(m), top + ALTO_P + 14, str(m), anchor='middle', fill=GRIS))
    partes.append(f'<rect x="{X0}" y="{top}" width="{ANCHO_P}" height="{ALTO_P}" fill="none" stroke="{EJE}" stroke-width="1.2"/>')
    yr = py(0.4, top)
    partes.append(f'<line x1="{X0}" y1="{yr:.1f}" x2="{X0 + ANCHO_P}" y2="{yr:.1f}" stroke="{GRIS}" stroke-width="0.9" stroke-dasharray="4 3"/>')
    for serie, color, ancho in (('T', GRIS, 1.6), ('D', ROJO, 2.0), ('I', AZUL, 2.0)):
        pts = ' '.join(f'{px(r["m"]):.1f},{py(r[serie], top):.1f}' for r in datos[clave])
        partes.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{ancho}" stroke-linejoin="round"/>')
    partes.append(t(X0 + 6, top + 18, letra, size=15, peso=700))
    partes.append(t(X0 + ANCHO_P / 2, top + ALTO_P + 30, 'minuto del ciclo nasal', size=9.5, anchor='middle', fill=GRIS))
    partes.append(f'<text transform="rotate(-90 14 {top + ALTO_P / 2:.1f})" x="14" y="{top + ALTO_P / 2:.1f}" font-family="{FUENTE}" font-size="9.5" text-anchor="middle" fill="{GRIS}">R a 150 Pa (escala log)</text>')
    alto_total = top + ALTO_P + 40
# leyenda
ly = alto_total + 2
for j, (nombre, color) in enumerate((('fosa derecha', ROJO), ('fosa izquierda', AZUL), ('total (en paralelo)', GRIS), ('valor de trabajo, 0,4', GRIS))):
    x = X0 + j * 150
    dash = ' stroke-dasharray="4 3"' if j == 3 else ''
    partes.append(f'<line x1="{x}" y1="{ly}" x2="{x + 22}" y2="{ly}" stroke="{color}" stroke-width="{1.2 if j == 3 else 2.4}"{dash}/>')
    partes.append(t(x + 28, ly + 3.5, nombre, size=10))
alto_total = ly + 14
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {alto_total:.0f}" width="{W}" height="{alto_total:.0f}" role="img">'
       f'<title>Ciclo nasal simulado: resistencia de cada fosa según el minuto</title><rect width="{W}" height="{alto_total:.0f}" fill="#ffffff"/>'
       + ''.join(partes) + '</svg>')
open(sys.argv[2], 'w', encoding='utf-8').write(svg)
PY

# ---- Cifras del texto que no estan en numeros.json: extremos del ciclo ----
python3 - "$TMP/ciclo.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
for k, serie in d.items():
    for lado in 'DIT':
        v = [r[lado] for r in serie]
        print(k, lado, 'min', round(min(v), 3), 'max', round(max(v), 3))
PY

# ---- Imagen real del capitulo (no sale de RinoSim): endoscopia de rinitis alergica ----
# Liu B y cols. Front Immunol 2026; doi:10.3389/fimmu.2026.1828695 (PMC13160792), Fig. 4,
# licencia CC BY verificada en la pagina del articulo. Sin modificaciones.
#   curl -sL -A "Mozilla/5.0" https://cdn.ncbi.nlm.nih.gov/pmc/blobs/436a/13160792/3ef4bc2d3d4f/fimmu-17-1828695-g004.jpg \
#        -o docs/libro/ilustraciones/cap36-rinitis-endoscopia.jpg
echo "listo"
