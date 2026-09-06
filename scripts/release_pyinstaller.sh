#!/bin/bash
# Publica un release GitHub para la build PyInstaller (Linux, onedir).
# Usa un prefijo de tag distinto ('pyinstaller-v') al de los releases del
# rewrite Tauri (v3.x) para no mezclarse en el mismo listado de tags.
#
# Uso: ./scripts/release_pyinstaller.sh
# Pregunta si subir __VERSION__ (src/main.py). Si se mantiene, tagea con
# sufijo '-r<commit corto>' (build de prueba) para que el updater la
# detecte como nueva sin tener que subir versión cada vez, y no la vuelva
# a ofrecer una vez aplicada (ver _local_build_id en core/updater.py).
# Arma dist/LabSim via build.sh, escribe dist/LabSim/BUILD_VERSION, tarea
# -> LabSim-linux-x86_64.tar.gz (paquete full) y lo sube al release
# (creandolo si hace falta).
#
# Ademas arma un paquete de update (diff) contra el manifest de la release
# anterior (scripts/update_diff.py) -- LabSim-linux-x86_64-update.tar.gz,
# solo con los archivos que cambiaron. El updater instalado encadena estos
# paquetes update (uno por release) para llegar a la última versión sin
# bajar los ~100MB completos cada vez; si a la cadena le falta un eslabón
# (release vieja sin paquete update, o demasiados saltos) cae solo al full.
# Por eso las releases viejas ya NO se borran completas: se les poda el
# asset full (pesado, superado) pero se mantiene el tag y el update asset,
# que es lo que necesita la cadena. Ver docstring de core/updater.py.
set -e
cd "$(dirname "$0")/.."

# Corre un comando mudo (gh/git contra la red) mostrando un spinner con
# segundos transcurridos -- sin esto, un paso lento (ej. subir el asset)
# no imprime nada y parece colgado.
run_with_spinner() {
    local msg="$1"; shift
    "$@" &
    local pid=$!
    local spin='|/-\'
    local i=0
    local start=$SECONDS
    while kill -0 "$pid" 2>/dev/null; do
        printf "\r%s %s (%ss)" "$msg" "${spin:i++%4:1}" "$((SECONDS - start))"
        sleep 0.2
    done
    wait "$pid"
    local status=$?
    if [ "$status" -eq 0 ]; then
        printf "\r%s listo (%ss)          \n" "$msg" "$((SECONDS - start))"
    else
        printf "\r%s FALLÓ (%ss)          \n" "$msg" "$((SECONDS - start))"
    fi
    return "$status"
}

CURRENT_VERSION=$(grep -oP "__VERSION__ = 'v\K[^']+" src/main.py)
if [ -z "$CURRENT_VERSION" ]; then
    echo "No pude leer __VERSION__ desde src/main.py" >&2
    exit 1
fi

read -rp "Versión actual: v${CURRENT_VERSION}. Nueva versión (Enter para mantener): " NEW_VERSION

if [ -n "$NEW_VERSION" ] && [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
    sed -i "s/__VERSION__ = 'v${CURRENT_VERSION}'/__VERSION__ = 'v${NEW_VERSION}'/" src/main.py
    git add src/main.py
    git commit -m "Sube versión a v${NEW_VERSION}"
    VERSION="$NEW_VERSION"
    BUILD_ID="$VERSION"
else
    VERSION="$CURRENT_VERSION"
    SHORT_SHA=$(git rev-parse --short HEAD)
    BUILD_ID="${VERSION}-r${SHORT_SHA}"
fi

TAG="pyinstaller-v${BUILD_ID}"
ASSET_NAME="LabSim-linux-x86_64.tar.gz"
MANIFEST_NAME="manifest.json"
UPDATE_ASSET_NAME="LabSim-linux-x86_64-update.tar.gz"

echo "Build: ${BUILD_ID} -> tag ${TAG}"

./build.sh

echo "$BUILD_ID" > dist/LabSim/BUILD_VERSION

TAR_PATH="dist/${ASSET_NAME}"
rm -f "$TAR_PATH"
run_with_spinner "Armando ${ASSET_NAME}..." tar -C dist -czf "$TAR_PATH" LabSim
echo "Armado ${TAR_PATH} ($(du -h "$TAR_PATH" | cut -f1))"

python3 scripts/update_diff.py manifest dist/LabSim "dist/${MANIFEST_NAME}"

# Release pyinstaller-v* mas reciente antes de esta (por fecha real de
# publicacion, igual criterio que usa el updater en el cliente) -- es la
# base contra la que se calcula el diff.
PREV_TAG=$(gh release list --json tagName,createdAt \
    -q "[.[] | select(.tagName | startswith(\"pyinstaller-v\")) | select(.tagName != \"${TAG}\")] | sort_by(.createdAt) | last | .tagName // empty")

UPDATE_TAR=""
if [ -n "$PREV_TAG" ]; then
    OLD_MANIFEST="dist/prev_manifest.json"
    rm -f "$OLD_MANIFEST"
    if gh release download "$PREV_TAG" -p "$MANIFEST_NAME" -O "$OLD_MANIFEST" >/dev/null 2>&1; then
        rm -rf dist/update_pkg
        if python3 scripts/update_diff.py diff dist/LabSim "$OLD_MANIFEST" dist/update_pkg; then
            UPDATE_TAR="dist/${UPDATE_ASSET_NAME}"
            run_with_spinner "Armando ${UPDATE_ASSET_NAME}..." tar -C dist/update_pkg -czf "$UPDATE_TAR" .
            echo "Armado ${UPDATE_TAR} ($(du -h "$UPDATE_TAR" | cut -f1))"
        fi
    else
        echo "Release anterior ${PREV_TAG} no tiene ${MANIFEST_NAME} (previa a esta feature) -- se sube solo el paquete full"
    fi
else
    echo "No hay release pyinstaller-v anterior -- primera build con este sistema, se sube solo el paquete full"
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "Tag ${TAG} ya existe localmente"
else
    git tag "$TAG"
    run_with_spinner "Pusheando tag ${TAG}..." git push origin "$TAG"
fi

ASSETS=("$TAR_PATH" "dist/${MANIFEST_NAME}")
[ -n "$UPDATE_TAR" ] && ASSETS+=("$UPDATE_TAR")

if gh release view "$TAG" >/dev/null 2>&1; then
    run_with_spinner "Subiendo assets al release..." gh release upload "$TAG" "${ASSETS[@]}" --clobber
else
    run_with_spinner "Creando release ${TAG} y subiendo assets..." gh release create "$TAG" "${ASSETS[@]}" \
        --title "LabSim ${TAG} (build PyInstaller)" \
        --notes "Build PyInstaller (Linux) de LabSim, build ${BUILD_ID}."
fi

# Ya no se borran releases pyinstaller-v* viejas completas: el tag y el
# paquete update de cada una son el eslabón que la cadena de updates del
# cliente necesita para llegar hasta acá desde cualquier versión anterior.
# Solo se poda el asset full (pesado, superado por el de esta release).
OLD_TAGS=$(gh release list --json tagName -q ".[] | select(.tagName | startswith(\"pyinstaller-v\")) | select(.tagName != \"${TAG}\") | .tagName")
if [ -n "$OLD_TAGS" ]; then
    echo "Podando asset full de releases pyinstaller-v* viejas (se mantiene el tag y el paquete update):"
    while IFS= read -r old_tag; do
        run_with_spinner "  Borrando ${ASSET_NAME} de ${old_tag}..." gh release delete-asset "$old_tag" "$ASSET_NAME" --yes || true
    done <<< "$OLD_TAGS"
fi

echo "Listo: https://github.com/Debaq/LabSim/releases/tag/${TAG}"
