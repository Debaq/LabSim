#!/usr/bin/env bash
# Figuras del capitulo 35 (nariz tapada) hechas con RinoSim (software libre del autor).
# Reproduce docs/libro/ilustraciones/cap35-rs-*.svg y los numeros de las tablas del capitulo.
#   RINOSIM=/ruta/a/rinosim bash docs/libro/ilustraciones/hacer_cap35_rinosim.sh
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

# Caso 1: desviacion septal derecha (estructural), reposo y con vasoconstrictor
fig desv      --cuadro desviacion_derecha
# Caso 2: colapso de la valvula, inspiracion forzada (y en reposo, para los numeros)
fig colapso   --cuadro colapso_valvular --forzada
fig colapso-r --cuadro colapso_valvular
# Caso 3: nariz sin obstruccion (el cuadro normal), solo reposo
fig normal    --cuadro normal --sin-vc

if [ -n "${NUMEROS:-}" ]; then mkdir -p "$NUMEROS"; for d in "$TMP"/*; do cp "$d/numeros.json" "$NUMEROS/$(basename "$d").json"; done; fi

cp "$TMP/desv/rm-curva.svg"    "$ILUS/cap35-rs-desv-rm.svg"
cp "$TMP/desv/ra-curva.svg"    "$ILUS/cap35-rs-desv-ra.svg"
cp "$TMP/colapso/rm-curva.svg" "$ILUS/cap35-rs-colapso-rm.svg"
cp "$TMP/colapso/ra-curva.svg" "$ILUS/cap35-rs-colapso-ra.svg"
cp "$TMP/normal/rm-curva.svg"  "$ILUS/cap35-rs-normal-rm.svg"
cp "$TMP/normal/ra-curva.svg"  "$ILUS/cap35-rs-normal-ra.svg"
echo "listo"

# ---- Cifras del texto que no estan en numeros.json: flujo a presiones altas (inspiracion forzada) ----
# Se leen con las funciones de RinoSim (solo lectura) y se redondean en el texto del capitulo.
RINOSIM="$RINOSIM" node --input-type=module - <<'JS'
const R = process.env.RINOSIM;
const { paciente } = await import(R + '/js/modelo.js');
const RM = await import(R + '/js/rinomanometria.js');
for (const cuadro of ['colapso_valvular', 'normal']) {
  const e = RM.examen(paciente(cuadro), { vc: false, minuto: 0 }, { forzada: true });
  for (const P of [300, 600, 800]) {
    const m = e.fosas.D.media;
    console.log(cuadro, 'FND', P, 'Pa  insp', Math.round(RM.leeEn(m.insp, P)), ' esp', Math.round(RM.leeEn(m.esp, P)), 'cm3/s');
  }
}
JS

# ---- Imagen real del capitulo (no sale de RinoSim): tomografia coronal con tabique desviado ----
# Simsim R, Alhumaizi A, Althubiti S. J Surg Case Rep 2026; doi:10.1093/jscr/rjag689 (PMC13452474),
# Fig. 1, licencia CC BY 4.0 verificada en la pagina del articulo. Sin modificaciones.
#   curl -sL -A "Mozilla/5.0" https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8ed8/13452474/c3adb841fd1d/rjag689f1.jpg \
#        -o docs/libro/ilustraciones/cap35-tc-tabique.jpg
