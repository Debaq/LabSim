#!/bin/bash
# Publica un release GitHub para la build PyInstaller (Linux, onedir).
# Usa un prefijo de tag distinto ('pyinstaller-v') al de los releases del
# rewrite Tauri (v3.x) para no mezclarse en el mismo listado de tags.
#
# Uso: ./scripts/release_pyinstaller.sh
# Antes de tocar nada verifica que se pueda publicar: rama main, sin cambios
# sin commitear y sin quedar atras de origin/main. El instalador de Windows
# lo compila un runner desde el SHA, asi que lo que no este commiteado y
# pusheado no entra en el .exe aunque si este en el .tar.gz de Linux, y las
# dos cosas se suben a la misma release. ALLOW_DIRTY=1 saltea el chequeo
# (build de prueba).
# Pregunta si subir __VERSION__ (src/main.py). Si se mantiene, tagea con
# sufijo '-r<commit corto>' (build de prueba) para que el updater la
# detecte como nueva sin tener que subir versión cada vez, y no la vuelva
# a ofrecer una vez aplicada (ver _local_build_id en core/updater.py).
# Arma dist/LabSim via build.sh, escribe dist/LabSim/BUILD_VERSION, tarea
# -> LabSim-linux-x86_64.tar.gz (paquete full) y lo sube al release
# (creandolo si hace falta).
#
# En paralelo dispara el workflow build-windows.yml (GitHub Actions) sobre
# el MISMO commit, espera a que termine y adjunta a la release el instalador
# Inno que produce -- LabSim-windows-x86_64-setup.exe. En Windows el updater
# no usa la cadena de diffs: baja ese instalador y lo corre en silencio, asi
# que solo la release mas nueva necesita tenerlo. SKIP_WINDOWS=1 lo saltea
# (release solo Linux, mas rapida para probar).
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
    elif [ "$status" -eq 2 ]; then
        # Convención propia (ver delete_asset_if_present): "no había nada
        # que hacer", no una falla real -- no lo mezclamos con FALLÓ.
        printf "\r%s omitido: ya no existe (%ss)          \n" "$msg" "$((SECONDS - start))"
    else
        printf "\r%s FALLÓ (%ss)          \n" "$msg" "$((SECONDS - start))"
    fi
    return "$status"
}

# gh release delete-asset devuelve error si el asset ya no está en la
# release -- pasa seguido acá porque el script es idempotente y una
# corrida anterior ya lo pudo haber podado. Sin esto, cada corrida
# vuelve a intentar contra TODAS las releases viejas y reporta "FALLÓ"
# para las que ya están podadas, que no es una falla real.
delete_asset_if_present() {
    local tag="$1" asset="$2"
    local out
    if out=$(gh release delete-asset "$tag" "$asset" --yes 2>&1); then
        return 0
    fi
    if echo "$out" | grep -qi "not found"; then
        return 2
    fi
    echo "$out" >&2
    return 1
}

# El .exe de Windows no sale de esta máquina: el workflow hace checkout del
# SHA en un runner limpio. Todo lo que no esté commiteado y pusheado NO entra
# en esa build, así que un árbol sucio produce en silencio un instalador
# distinto del .tar.gz de Linux que se sube a la misma release. Por eso se
# corta acá y no más adelante: antes de tocar src/main.py y antes de buildear.
verificar_arbol_publicable() {
    BRANCH=$(git rev-parse --abbrev-ref HEAD)

    if [ "$BRANCH" != "main" ]; then
        echo "Estás en '${BRANCH}', no en main. Los releases salen de main." >&2
        echo "  (ALLOW_DIRTY=1 lo saltea, para un build de prueba)" >&2
        return 1
    fi

    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "Hay cambios sin commitear -- no entrarían en el build de Windows:" >&2
        git status --short --untracked-files=no >&2
        return 1
    fi

    # Los archivos nuevos sin agregar sí son un aviso y no un corte: casi
    # siempre son dist/, notas o pruebas que no van al release.
    local nuevos
    nuevos=$(git ls-files --others --exclude-standard)
    if [ -n "$nuevos" ]; then
        echo "Aviso: archivos nuevos sin agregar (no van al build):"
        echo "$nuevos" | sed 's/^/  /'
    fi

    run_with_spinner "Consultando origin/main..." git fetch origin main

    local atras
    atras=$(git rev-list --count HEAD..origin/main)
    if [ "$atras" -gt 0 ]; then
        echo "origin/main tiene ${atras} commit(s) que no están acá: haz git pull antes de publicar." >&2
        return 1
    fi

    local adelante
    adelante=$(git rev-list --count origin/main..HEAD)
    if [ "$adelante" -gt 0 ]; then
        echo "main está ${adelante} commit(s) adelante de origin -- se pushean antes de buildear."
    fi
    return 0
}

if [ "${ALLOW_DIRTY:-0}" = "1" ]; then
    echo "ALLOW_DIRTY=1 -- build de prueba: el instalador de Windows puede no coincidir con este código"
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
elif ! verificar_arbol_publicable; then
    exit 1
fi

CURRENT_VERSION=$(grep -oP "__VERSION__ = 'v\K[^']+" src/main.py)
if [ -z "$CURRENT_VERSION" ]; then
    echo "No pude leer __VERSION__ desde src/main.py" >&2
    exit 1
fi

read -rp "Versión actual: v${CURRENT_VERSION}. Nueva versión (Enter para mantener): " NEW_VERSION
# La "v" la pone el script: escribir "v0.9.9" dejaba 'vv0.9.9' en main.py y
# el instalador de Windows fallaba (VersionInfoVersion solo acepta números).
NEW_VERSION="${NEW_VERSION#[vV]}"
if [ -n "$NEW_VERSION" ] && ! [[ "$NEW_VERSION" =~ ^[0-9]+(\.[0-9]+){1,3}$ ]]; then
    echo "Versión inválida: '${NEW_VERSION}' (formato 0.9.9)" >&2
    exit 1
fi

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

SETUP_ASSET_NAME="LabSim-windows-x86_64-setup.exe"
WIN_WORKFLOW="build-windows.yml"
SHA=$(git rev-parse HEAD)
WIN_RUN_ID=""

# Se pushea siempre, no solo cuando hay build de Windows: el updater encadena
# los paquetes de update de cada release, así que el commit del que salió cada
# una tiene que existir en origin para poder reconstruirla.
run_with_spinner "Pusheando ${BRANCH} a origin..." git push origin "HEAD:${BRANCH}"

# El build de Windows se dispara ACA, antes del build local: son ~3 min en
# el runner que corren en paralelo con PyInstaller local, y recien se espera
# el resultado al final, con la release ya creada.
if [ "${SKIP_WINDOWS:-0}" = "1" ]; then
    echo "SKIP_WINDOWS=1 -- no se dispara el build de Windows"
else
    # El workflow hace checkout del SHA exacto (para que el .exe salga del
    # mismo codigo que el .tar.gz) -- ya se pusheo arriba.
    run_with_spinner "Disparando build de Windows..." gh workflow run "$WIN_WORKFLOW" \
        --ref "$BRANCH" -f sha="$SHA" -f build_id="$BUILD_ID"

    # gh workflow run no devuelve el id del run: hay que buscarlo, y tarda
    # unos segundos en aparecer en la API. Si hubo dispatches previos sobre
    # el mismo commit (corrida repetida del script), el mas nuevo es el
    # nuestro.
    for _ in $(seq 1 20); do
        WIN_RUN_ID=$(gh run list --workflow "$WIN_WORKFLOW" --event workflow_dispatch --limit 20 \
            --json databaseId,headSha,createdAt \
            -q "[.[] | select(.headSha == \"${SHA}\")] | sort_by(.createdAt) | last | .databaseId // empty" \
            2>/dev/null) || WIN_RUN_ID=""
        # 'test && break' no sirve aca: con set -e, el test fallido en la
        # ultima linea del cuerpo del loop mata el script.
        if [ -n "$WIN_RUN_ID" ]; then
            break
        fi
        sleep 3
    done
    if [ -n "$WIN_RUN_ID" ]; then
        echo "Build de Windows corriendo: https://github.com/Debaq/LabSim/actions/runs/${WIN_RUN_ID}"
    else
        echo "No pude ubicar el run de Windows -- sigo con Linux, revisalo a mano" >&2
    fi
fi

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

WIN_OK=0
if [ -n "$WIN_RUN_ID" ]; then
    echo "Esperando el build de Windows (run ${WIN_RUN_ID})..."
    if gh run watch "$WIN_RUN_ID" --exit-status --interval 15; then
        rm -rf dist/win
        if run_with_spinner "Bajando ${SETUP_ASSET_NAME}..." \
                gh run download "$WIN_RUN_ID" -n labsim-windows-setup -D dist/win; then
            echo "Instalador: dist/win/${SETUP_ASSET_NAME} ($(du -h "dist/win/${SETUP_ASSET_NAME}" | cut -f1))"
            run_with_spinner "Subiendo ${SETUP_ASSET_NAME} al release..." \
                gh release upload "$TAG" "dist/win/${SETUP_ASSET_NAME}" --clobber
            WIN_OK=1
        fi
    else
        echo "El build de Windows FALLÓ -- la release queda solo con Linux." >&2
        echo "  Log: gh run view ${WIN_RUN_ID} --log-failed" >&2
        echo "  Reintento: gh workflow run ${WIN_WORKFLOW} --ref ${BRANCH} -f sha=${SHA} -f build_id=${BUILD_ID}" >&2
    fi
fi

# Ya no se borran releases pyinstaller-v* viejas completas: el tag y el
# paquete update de cada una son el eslabón que la cadena de updates del
# cliente necesita para llegar hasta acá desde cualquier versión anterior.
# Solo se poda el asset full (pesado, superado por el de esta release).
OLD_TAGS=$(gh release list --json tagName -q ".[] | select(.tagName | startswith(\"pyinstaller-v\")) | select(.tagName != \"${TAG}\") | .tagName")
if [ -n "$OLD_TAGS" ]; then
    echo "Podando asset full de releases pyinstaller-v* viejas (se mantiene el tag y el paquete update):"
    while IFS= read -r old_tag; do
        run_with_spinner "  Borrando ${ASSET_NAME} de ${old_tag}..." delete_asset_if_present "$old_tag" "$ASSET_NAME" || true
        # El instalador de Windows es siempre completo y el updater solo mira
        # la release mas nueva: los viejos no le sirven a nadie. Solo se podan
        # si el de esta release ya subio, para no dejar cero instaladores.
        if [ "$WIN_OK" = "1" ]; then
            run_with_spinner "  Borrando ${SETUP_ASSET_NAME} de ${old_tag}..." delete_asset_if_present "$old_tag" "$SETUP_ASSET_NAME" || true
        fi
    done <<< "$OLD_TAGS"
fi

echo "Listo: https://github.com/Debaq/LabSim/releases/tag/${TAG}"
