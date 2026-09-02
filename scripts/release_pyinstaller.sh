#!/bin/bash
# Publica un release GitHub para la build PyInstaller (Linux, onedir).
# Usa un prefijo de tag distinto ('pyinstaller-v') al de los releases del
# rewrite Tauri (v3.x) para no mezclarse en el mismo listado de tags.
#
# Uso: ./scripts/release_pyinstaller.sh
# Toma la version de __VERSION__ en src/main.py, arma dist/LabSim.spec
# via build.sh, tarea dist/LabSim -> LabSim-linux-x86_64.tar.gz y lo sube
# al release (creandolo si no existe).
set -e
cd "$(dirname "$0")/.."

VERSION=$(grep -oP "__VERSION__ = 'v\K[^']+" src/main.py)
if [ -z "$VERSION" ]; then
    echo "No pude leer __VERSION__ desde src/main.py" >&2
    exit 1
fi
TAG="pyinstaller-v${VERSION}"
ASSET_NAME="LabSim-linux-x86_64.tar.gz"

echo "Version detectada: v${VERSION} -> tag ${TAG}"

./build.sh

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
        --notes "Build PyInstaller (Linux) de LabSim v${VERSION}."
fi

echo "Listo: https://github.com/Debaq/LabSim/releases/tag/${TAG}"
