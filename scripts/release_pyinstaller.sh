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
# -> LabSim-linux-x86_64.tar.gz y lo sube al release (creandolo si hace falta).
set -e
cd "$(dirname "$0")/.."

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

echo "Build: ${BUILD_ID} -> tag ${TAG}"

./build.sh

echo "$BUILD_ID" > dist/LabSim/BUILD_VERSION

TAR_PATH="dist/${ASSET_NAME}"
rm -f "$TAR_PATH"
tar -C dist -czf "$TAR_PATH" LabSim
echo "Armado ${TAR_PATH} ($(du -h "$TAR_PATH" | cut -f1))"

if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "Tag ${TAG} ya existe localmente"
else
    git tag "$TAG"
    git push origin "$TAG"
fi

if gh release view "$TAG" >/dev/null 2>&1; then
    gh release upload "$TAG" "$TAR_PATH" --clobber
else
    gh release create "$TAG" "$TAR_PATH" \
        --title "LabSim ${TAG} (build PyInstaller)" \
        --notes "Build PyInstaller (Linux) de LabSim, build ${BUILD_ID}."
fi

# Borra cualquier otro release pyinstaller-v* -- el updater viejo instalado
# en los clientes agarra "el primero que matchea el prefijo" sin ordenar
# por fecha (ver core/updater.py), así que si queda más de un candidato
# puede no detectar el más nuevo. Con uno solo, no hay ambigüedad posible.
OLD_TAGS=$(gh release list --json tagName -q ".[] | select(.tagName | startswith(\"pyinstaller-v\")) | select(.tagName != \"${TAG}\") | .tagName")
if [ -n "$OLD_TAGS" ]; then
    echo "Borrando releases pyinstaller-v* viejos:"
    while IFS= read -r old_tag; do
        echo "  - ${old_tag}"
        gh release delete "$old_tag" --yes --cleanup-tag
    done <<< "$OLD_TAGS"
fi

echo "Listo: https://github.com/Debaq/LabSim/releases/tag/${TAG}"
