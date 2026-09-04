# -*- coding: utf-8 -*-
"""
Auto-update de la build PyInstaller (onedir, Linux) contra GitHub Releases.

Los releases de este repo se comparten con el rewrite Tauri (tags v3.x,
assets .deb/.rpm/.AppImage/.exe/.msi). Para no mezclarse con esos, esta
build usa su propio prefijo de tag: 'pyinstaller-v<version>', con un único
asset 'LabSim-linux-x86_64.tar.gz' que es el tar de la carpeta dist/LabSim.

Reemplaza el código (LabSim + _internal/ + run.sh) y también sincroniza
resources/ con la versión nueva -- EXCEPTO la data dinámica del usuario en
modo offline: resources/cases/ (cases.json, labsim.json), resources/local_cache/
(logs.db, cola de acciones), resources/json/session.json (sesión logueada)
y resources/json/schedule.json (caché de agenda). Todo lo demás bajo
resources/ (apps.json y el resto de json/, styles/, img/, font/, UI/,
audio/) es config/asset estático que se define en el repo y nunca se
edita en runtime (Preferences.set() ni siquiera está implementado, ver
core/helpers.py) -- si no se sincronizara, un usuario que se actualiza
in-place (sin reinstalar desde cero) se quedaría para siempre con el
apps.json del día que instaló, aunque el código nuevo ya espere entradas
que ese archivo no tiene (síntoma: KeyError al abrir una ventana nueva
que ese apps.json viejo no conoce).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

REPO = "Debaq/LabSim"
TAG_PREFIX = "pyinstaller-v"
ASSET_NAME = "LabSim-linux-x86_64.tar.gz"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases"
REQUEST_TIMEOUT = 5


def _parse_version(version: str) -> tuple:
    return tuple(int(n) for n in re.findall(r"\d+", version))


def _split_build_id(build_id: str):
    """'0.9.8' -> ((0,9,8), None). '0.9.8-r0ce52be' -> ((0,9,8), '0ce52be').
    El sufijo de commit sirve para distinguir builds de prueba que no
    suben la versión (ver scripts/release_pyinstaller.sh)."""
    base, _, suffix = build_id.lstrip("v").partition("-r")
    return _parse_version(base), (suffix or None)


def local_build_id(fallback_version: str) -> str:
    """Lee BUILD_VERSION al lado del ejecutable (lo escribe el script de
    release). Si no existe -- build vieja, previa a esta feature, o corrida
    en dev -- cae a __VERSION__. Sirve también para mostrar la versión
    real (con sufijo -r<commit>) en el título de la ventana."""
    build_file = Path(sys.executable).resolve().parent / "BUILD_VERSION"
    try:
        content = build_file.read_text(encoding="utf-8").strip()
        if content:
            return content
    except OSError:
        pass
    return fallback_version


def _fetch_releases() -> list:
    req = Request(RELEASES_API, headers={"Accept": "application/vnd.github+json"})
    with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.load(resp)


def check_for_update(current_version: str):
    """Busca el release 'pyinstaller-v*' más reciente. Si es más nuevo que
    el build local y trae el asset esperado, devuelve (tag, download_url).
    'Más nuevo' es: versión mayor, o misma versión con un sufijo de commit
    distinto al local (build de prueba re-publicada) -- así una build ya
    aplicada no se vuelve a ofrecer en cada arranque. Si no hay nada nuevo,
    o falla la red, devuelve None (nunca revienta: no queremos bloquear el
    arranque por un lab sin internet)."""
    try:
        releases = _fetch_releases()
    except (URLError, OSError, ValueError, TimeoutError):
        return None

    candidates = [r for r in releases if r.get("tag_name", "").startswith(TAG_PREFIX)]
    if not candidates:
        return None
    # La API de GitHub no garantiza orden por fecha en /releases -- hay que
    # ordenar a mano, si no a veces se toma una release vieja como "la
    # última" y una build vieja no detecta que hay una más nueva.
    remote = max(candidates, key=lambda r: r.get("created_at") or "")

    tag = remote["tag_name"]
    remote_build_id = tag[len(TAG_PREFIX):]
    local_id = local_build_id(current_version)

    remote_v, remote_suffix = _split_build_id(remote_build_id)
    local_v, local_suffix = _split_build_id(local_id)

    if remote_v < local_v:
        return None
    if remote_v == local_v and (remote_suffix is None or remote_suffix == local_suffix):
        return None

    asset = next(
        (a for a in remote.get("assets", []) if a.get("name") == ASSET_NAME),
        None,
    )
    if asset is None:
        return None

    return tag, asset["browser_download_url"]


_UPDATER_SCRIPT = """#!/bin/bash
# Generado por core/updater.py -- espera a que cierre el proceso viejo,
# reemplaza codigo (bin + _internal + run.sh), sincroniza resources/
# (salvo la data dinamica del usuario -- ver docstring del modulo) y
# relanza.
set -e
PID="$1"
DIST_DIR="$2"
NEW_DIST="$3"

shopt -s nullglob dotglob

waited=0
while kill -0 "$PID" 2>/dev/null; do
    sleep 0.3
    waited=$((waited + 1))
    if [ "$waited" -gt 200 ]; then
        break
    fi
done

rm -rf "$DIST_DIR/_internal"
cp -a "$NEW_DIST/_internal" "$DIST_DIR/_internal"
cp -a "$NEW_DIST/LabSim" "$DIST_DIR/LabSim"
cp -a "$NEW_DIST/run.sh" "$DIST_DIR/run.sh"
[ -f "$NEW_DIST/BUILD_VERSION" ] && cp -a "$NEW_DIST/BUILD_VERSION" "$DIST_DIR/BUILD_VERSION"
chmod +x "$DIST_DIR/LabSim" "$DIST_DIR/run.sh"

# De aca en adelante no abortamos mas: el codigo ya quedo actualizado, y si
# algun item de resources/ falla no queremos perder el resto ni dejar el
# relanzamiento sin ejecutar (antes, con set -e activo, un solo cp -a que
# fallara cortaba el loop a mitad de camino y el resto de items nunca se
# copiaba -- "se salta archivos" silenciosamente).
set +e

# resources/: se sincroniza con la version nueva salvo las carpetas/archivos
# 100% dinamicos del usuario (cases/, local_cache/, json/session.json,
# json/schedule.json) -- todo lo demas (apps.json, el resto de json/,
# styles/, img/, font/, UI/, audio/) es config/asset estatico que debe
# quedar al dia con cada release, no solo en una instalacion nueva.
if [ -d "$NEW_DIST/resources" ]; then
    mkdir -p "$DIST_DIR/resources"

    # 1) Borrar en destino lo que ya no existe en el release nuevo (huerfanos
    #    de una version anterior), salvo la data dinamica del usuario. Antes
    #    esto no se hacia: un item borrado/renombrado en el release nunca se
    #    borraba de la instalacion, quedaba basura vieja para siempre.
    for old_item in "$DIST_DIR/resources"/*; do
        name="$(basename "$old_item")"
        case "$name" in
            cases|local_cache) continue ;;
        esac
        if [ ! -e "$NEW_DIST/resources/$name" ]; then
            rm -rf "$old_item"
        fi
    done
    if [ -d "$DIST_DIR/resources/json" ]; then
        for old_jf in "$DIST_DIR/resources/json"/*; do
            jname="$(basename "$old_jf")"
            case "$jname" in
                session.json|schedule.json) continue ;;
            esac
            if [ ! -e "$NEW_DIST/resources/json/$jname" ]; then
                rm -f "$old_jf"
            fi
        done
    fi

    # 2) Copiar todo lo nuevo. Antes json/ solo copiaba archivo por archivo
    #    sin borrar primero (ya cubierto arriba en el paso 1).
    for item in "$NEW_DIST/resources"/*; do
        name="$(basename "$item")"
        case "$name" in
            cases|local_cache) continue ;;
        esac
        if [ "$name" = "json" ]; then
            mkdir -p "$DIST_DIR/resources/json"
            for jf in "$item"/*; do
                jname="$(basename "$jf")"
                case "$jname" in
                    session.json|schedule.json) continue ;;
                esac
                cp -a "$jf" "$DIST_DIR/resources/json/$jname" || echo "labsim-update: fallo copiando json/$jname" >&2
            done
        else
            rm -rf "$DIST_DIR/resources/$name"
            cp -a "$item" "$DIST_DIR/resources/$name" || echo "labsim-update: fallo copiando resources/$name" >&2
        fi
    done
fi

rm -rf "$(dirname "$NEW_DIST")"

cd "$DIST_DIR"
nohup ./run.sh >/dev/null 2>&1 &
"""


def apply_update_and_restart(download_url: str, on_progress=None) -> None:
    """Descarga el asset, lo extrae, lanza el script que hace el swap una
    vez que este proceso muera, y termina el proceso actual. No vuelve:
    llama a os._exit al final.

    on_progress(stage, current, total), si se pasa, se llama durante cada
    etapa ('download', 'extract', 'restart') para que el caller (main.py)
    pueda mostrar una barra de progreso -- sin esto la descarga/extracción
    queda muda y la ventana parece congelada."""
    def report(stage, current=0, total=0):
        if on_progress:
            on_progress(stage, current, total)

    dist_dir = Path(sys.executable).resolve().parent

    tmp_dir = Path(tempfile.mkdtemp(prefix="labsim_update_"))
    archive_path = tmp_dir / ASSET_NAME
    req = Request(download_url)
    report("download", 0, 0)
    with urlopen(req, timeout=60) as resp, open(archive_path, "wb") as f:
        total = int(resp.headers.get("Content-Length") or 0)
        downloaded = 0
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            report("download", downloaded, total)

    report("extract", 0, 0)
    extract_dir = tmp_dir / "extracted"
    with tarfile.open(archive_path) as tf:
        tf.extractall(extract_dir)
    archive_path.unlink()

    new_dist = extract_dir / "LabSim"
    if not new_dist.is_dir():
        # asset con estructura inesperada: no arriesgamos el swap
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return

    script_path = tmp_dir / "apply_update.sh"
    script_path.write_text(_UPDATER_SCRIPT, encoding="utf-8")
    script_path.chmod(0o755)

    report("restart", 0, 0)
    subprocess.Popen(
        [str(script_path), str(os.getpid()), str(dist_dir), str(new_dist)],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    os._exit(0)
