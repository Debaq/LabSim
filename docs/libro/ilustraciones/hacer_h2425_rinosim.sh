#!/usr/bin/env bash
# Figuras y capturas de H24 y H25 hechas con RinoSim (software libre del autor).
# Reproduce exactamente lo que hay en docs/libro/ilustraciones/h24-rs-* y h25-rs-*.
#   RINOSIM=/ruta/a/rinosim bash docs/libro/ilustraciones/hacer_h2425_rinosim.sh
# No modifica RinoSim: las figuras salen a una carpeta temporal y de ahí se copian.
# Con CAPTURAS=0 se saltan las capturas de pantalla (no hace falta chromium).
set -euo pipefail
RINOSIM=${RINOSIM:-/home/nick/Escritorio/Proyectos/rinosim}
ILUS=$(cd "$(dirname "$0")" && pwd)
TMP=$(mktemp -d)
PUERTO=${PUERTO:-8897}
SERV=""
limpiar() { [ -n "$SERV" ] && kill "$SERV" 2>/dev/null || true; rm -rf "$TMP"; }
trap limpiar EXIT

fig() { # fig <carpeta> <opciones de figuras.mjs...>
  local n=$1; shift
  (cd "$RINOSIM" && node tools/figuras.mjs "$@" --salida "$TMP/$n" >/dev/null)
}

# ---- H24 ----
fig h24-normal      --cuadro normal --minuto 37 --sin-vc
fig h24-broms       --cuadro mixta --sin-vc --broms
fig h24-vasomotora  --cuadro cornetes --lado D
fig h24-mixta       --cuadro mixta --lado D
fig h24-mecanica    --cuadro desviacion_derecha --lado D
fig h24-colapso     --cuadro colapso_valvular --forzada --sin-vc
fig h24-irregular   --cuadro normal --sin-vc --errores irregular
# ---- H25 ----
fig h25-normal      --cuadro normal --sin-vc --lado D
fig h25-mucosa      --cuadro cornetes --lado D
fig h25-estructura  --cuadro desviacion_derecha --lado D
fig h25-mixta       --cuadro mixta --lado D
fig h25-limite      --paciente "$RINOSIM/ejemplos/valvula-cerrada.json" --lado D
fig h25-fuga        --cuadro normal --sin-vc --lado D --errores fuga

# Los numeros.json quedan junto a las figuras por si hace falta releerlos.
if [ -n "${NUMEROS:-}" ]; then mkdir -p "$NUMEROS"; for d in "$TMP"/h2*; do cp "$d/numeros.json" "$NUMEROS/$(basename "$d").json"; done; fi

# Figuras sueltas
cp "$TMP/h24-broms/rm-curva.svg"      "$ILUS/h24-rs-broms.svg"
cp "$TMP/h24-colapso/rm-curva.svg"    "$ILUS/h24-rs-colapso.svg"
cp "$TMP/h24-irregular/rm-curva.svg"  "$ILUS/h24-rs-irregular.svg"
cp "$TMP/h25-normal/ra-curva.svg"     "$ILUS/h25-rs-curva.svg"
cp "$TMP/h25-mixta/ra-curva.svg"      "$ILUS/h25-rs-mixta.svg"
cp "$TMP/h25-limite/ra-curva.svg"     "$ILUS/h25-rs-limite.svg"
cp "$TMP/h25-fuga/ra-curva.svg"       "$ILUS/h25-rs-fuga.svg"

# Figuras en paneles (A, B, C...) apiladas
python3 - "$TMP" "$ILUS" <<'PY'
import re, sys
tmp, ilus = sys.argv[1], sys.argv[2]

def paneles(destino, lista):
    """lista de (archivo, letra). Apila los SVG de RinoSim con su letra."""
    y, partes, w = 0, [], 722
    for arch, letra in lista:
        s = open(f'{tmp}/{arch}', encoding='utf-8').read()
        m = re.search(r'viewBox="0 0 (\d+) (\d+)"', s)
        ancho, alto = int(m[1]), int(m[2])
        s = re.sub(r'<title>.*?</title>', '', s)
        s = re.sub(r'<svg [^>]*>', f'<svg x="22" y="{y}" width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}">', s, count=1)
        partes.append(s)
        partes.append(f'<text x="3" y="{y + 16}" font-size="15" font-weight="700" fill="#44403c" '
                      f'font-family="\'Plus Jakarta Sans\', \'Segoe UI\', system-ui, sans-serif">{letra}</text>')
        y += alto + 8
    out = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {y - 8}" width="{w}" height="{y - 8}" role="img">'
           + ''.join(partes) + '</svg>')
    open(f'{ilus}/{destino}', 'w', encoding='utf-8').write(out)

paneles('h24-rs-curvas.svg', [('h24-normal/rm-curva.svg', 'A'), ('h24-normal/rm-resistencia.svg', 'B')])
paneles('h24-rs-vasoconstrictor.svg', [('h24-vasomotora/rm-resistencia.svg', 'A'),
                                       ('h24-mixta/rm-resistencia.svg', 'B'),
                                       ('h24-mecanica/rm-resistencia.svg', 'C')])
paneles('h25-rs-vasoconstrictor.svg', [('h25-mucosa/ra-curva.svg', 'A'), ('h25-estructura/ra-curva.svg', 'B')])
PY

# ---- Capturas de la aplicacion (chromium sin pantalla, servidor solo de lectura) ----
if [ "${CAPTURAS:-1}" = 1 ]; then
  (cd "$RINOSIM" && python3 -m http.server "$PUERTO" --bind 127.0.0.1 >/dev/null 2>&1) &
  SERV=$!
  sleep 1
  cap() { # cap <salida.png> <alto de ventana> <url> <recorte ancho x alto>
    chromium --headless=new --no-sandbox --disable-gpu --window-size=1400,"$2" \
      --virtual-time-budget=8000 --screenshot="$TMP/c.png" "$3" >/dev/null 2>&1
    magick "$TMP/c.png" -crop "$4+0+0" +repage "$1"
  }
  # alto de ventana y alto final (sin el gris de abajo)
  cap "$ILUS/h24-rs-equipo.png" 2000 "http://localhost:$PUERTO/?vista=rm&cuadro=mixta&medir=1&vc=1&captura=1" 1400x1550
  cap "$ILUS/h25-rs-equipo.png" 1580 "http://localhost:$PUERTO/?vista=ra&cuadro=cornetes&medir=1&vc=1&captura=1" 1385x1490
fi
echo "listo"
