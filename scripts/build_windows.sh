#!/bin/bash
# Dispara el build de Windows (GitHub Actions) para el commit actual, espera
# a que termine y baja el instalador a dist/win/ -- SIN publicar release ni
# tocar tags. Es el camino para probar el .exe suelto; la release completa la
# arma scripts/release_pyinstaller.sh, que hace esto mismo y ademas adjunta
# el instalador al release.
#
# Uso: ./scripts/build_windows.sh [sha]
#   sha: commit a compilar (default: HEAD). Tiene que estar en origin -- el
#        script pushea la rama actual antes de disparar.
set -e
cd "$(dirname "$0")/.."

WIN_WORKFLOW="build-windows.yml"
SETUP_ASSET_NAME="LabSim-windows-x86_64-setup.exe"
SHA="${1:-$(git rev-parse HEAD)}"
BRANCH=$(git rev-parse --abbrev-ref HEAD)

VERSION=$(grep -oP "__VERSION__ = 'v\K[^']+" src/main.py)
BUILD_ID="${VERSION}-r$(git rev-parse --short "$SHA")"

echo "Commit ${SHA} (rama ${BRANCH}) -> build_id ${BUILD_ID}"

echo "Pusheando ${BRANCH} a origin..."
git push origin "HEAD:${BRANCH}"

echo "Disparando ${WIN_WORKFLOW}..."
gh workflow run "$WIN_WORKFLOW" --ref "$BRANCH" -f sha="$SHA" -f build_id="$BUILD_ID"

# gh workflow run no devuelve el id del run: hay que buscarlo, y tarda unos
# segundos en aparecer en la API.
RUN_ID=""
for _ in $(seq 1 20); do
    RUN_ID=$(gh run list --workflow "$WIN_WORKFLOW" --event workflow_dispatch --limit 20 \
        --json databaseId,headSha,createdAt \
        -q "[.[] | select(.headSha == \"${SHA}\")] | sort_by(.createdAt) | last | .databaseId // empty" \
        2>/dev/null) || RUN_ID=""
    if [ -n "$RUN_ID" ]; then
        break
    fi
    sleep 3
done

if [ -z "$RUN_ID" ]; then
    echo "No pude ubicar el run. Revisalo en: https://github.com/Debaq/LabSim/actions" >&2
    exit 1
fi

echo "Run: https://github.com/Debaq/LabSim/actions/runs/${RUN_ID}"

if ! gh run watch "$RUN_ID" --exit-status --interval 15; then
    echo "El build FALLÓ. Log: gh run view ${RUN_ID} --log-failed" >&2
    exit 1
fi

rm -rf dist/win
gh run download "$RUN_ID" -n labsim-windows-setup -D dist/win
echo "Listo: dist/win/${SETUP_ASSET_NAME} ($(du -h "dist/win/${SETUP_ASSET_NAME}" | cut -f1))"
echo "Portable (zip), si lo querés: gh run download ${RUN_ID} -n labsim-windows-portable -D dist/win"
