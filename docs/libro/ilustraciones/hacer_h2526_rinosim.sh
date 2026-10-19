#!/usr/bin/env bash
# Figuras de H25 y H26 hechas con RinoSim (curvas y pantallas de resultado, sin interfaz).
# Reproduce exactamente lo que hay en docs/libro/ilustraciones/h25-rs-* y h26-rs-*.
#   RINOSIM=/ruta/a/rinosim bash docs/libro/ilustraciones/hacer_h2526_rinosim.sh
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

# ---- H25 ----
fig h25-normal      --cuadro normal --minuto 37 --sin-vc
fig h25-broms       --cuadro mixta --sin-vc --broms
fig h25-vasomotora  --cuadro cornetes --lado D
fig h25-mixta       --cuadro mixta --lado D
fig h25-mecanica    --cuadro desviacion_derecha --lado D
fig h25-colapso     --cuadro colapso_valvular --forzada --sin-vc
fig h25-irregular   --cuadro normal --sin-vc --errores irregular
# ---- H26 ----
fig h26-normal      --cuadro normal --sin-vc --lado D
fig h26-mucosa      --cuadro cornetes --lado D
fig h26-estructura  --cuadro desviacion_derecha --lado D
fig h26-mixta       --cuadro mixta --lado D
fig h26-limite      --paciente "$RINOSIM/ejemplos/valvula-cerrada.json" --lado D
fig h26-fuga        --cuadro normal --sin-vc --lado D --errores fuga

# Los numeros.json quedan junto a las figuras por si hace falta releerlos.
if [ -n "${NUMEROS:-}" ]; then mkdir -p "$NUMEROS"; for d in "$TMP"/h2*; do cp "$d/numeros.json" "$NUMEROS/$(basename "$d").json"; done; fi

# Figuras sueltas
cp "$TMP/h25-broms/rm-curva.svg"      "$ILUS/h25-rs-broms.svg"
cp "$TMP/h25-colapso/rm-curva.svg"    "$ILUS/h25-rs-colapso.svg"
cp "$TMP/h25-irregular/rm-curva.svg"  "$ILUS/h25-rs-irregular.svg"
cp "$TMP/h26-normal/ra-curva.svg"     "$ILUS/h26-rs-curva.svg"
cp "$TMP/h26-mixta/ra-curva.svg"      "$ILUS/h26-rs-mixta.svg"
cp "$TMP/h26-limite/ra-curva.svg"     "$ILUS/h26-rs-limite.svg"
cp "$TMP/h26-fuga/ra-curva.svg"       "$ILUS/h26-rs-fuga.svg"

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

paneles('h25-rs-curvas.svg', [('h25-normal/rm-curva.svg', 'A'), ('h25-normal/rm-resistencia.svg', 'B')])
paneles('h25-rs-vasoconstrictor.svg', [('h25-vasomotora/rm-resistencia.svg', 'A'),
                                       ('h25-mixta/rm-resistencia.svg', 'B'),
                                       ('h25-mecanica/rm-resistencia.svg', 'C')])
paneles('h26-rs-vasoconstrictor.svg', [('h26-mucosa/ra-curva.svg', 'A'), ('h26-estructura/ra-curva.svg', 'B')])
PY

# ---- Pantallas de resultado (curva + tabla), sin la interfaz del programa ----
# Se copia RinoSim a la carpeta temporal y a la copia se le agrega CSS que esconde
# barra, botones, casillas, avisos, notas y referencias: queda solo la curva y la tabla.
# El repo de RinoSim no se toca.
if [ "${CAPTURAS:-1}" = 1 ]; then
  cp -r "$RINOSIM" "$TMP/rs" && rm -rf "$TMP/rs/.git"
  cat >> "$TMP/rs/css/estilo.css" <<'CSS'
body.captura .equipo-titulo, body.captura .herramientas, body.captura .mensaje,
body.captura .avisos, body.captura .referencias, body.captura .tabla .pie { display: none !important; }
CSS
  (python3 -m http.server "$PUERTO" --bind 127.0.0.1 -d "$TMP/rs" >/dev/null 2>&1) &
  SERV=$!
  sleep 1
  cap() { # cap <salida.png> <alto de ventana> <url>
    chromium --headless=new --no-sandbox --disable-gpu --window-size=1400,"$2" \
      --virtual-time-budget=8000 --screenshot="$TMP/c.png" "$3" >/dev/null 2>&1
    magick "$TMP/c.png" -trim +repage -bordercolor white -border 10 "$1"
  }
  cap "$ILUS/h25-rs-equipo.png" 2000 "http://localhost:$PUERTO/?vista=rm&cuadro=mixta&medir=1&vc=1&captura=1"
  cap "$ILUS/h26-rs-equipo.png" 1700 "http://localhost:$PUERTO/?vista=ra&cuadro=cornetes&medir=1&vc=1&captura=1"
fi
echo "listo"
