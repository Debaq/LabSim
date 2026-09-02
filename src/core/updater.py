# -*- coding: utf-8 -*-
"""
Auto-update de la build PyInstaller (onedir, Linux) contra GitHub Releases.

Los releases de este repo se comparten con el rewrite Tauri (tags v3.x,
assets .deb/.rpm/.AppImage/.exe/.msi). Para no mezclarse con esos, esta
build usa su propio prefijo de tag: 'pyinstaller-v<version>', con un único
asset 'LabSim-linux-x86_64.tar.gz' que es el tar de la carpeta dist/LabSim.

Solo se reemplaza el código (LabSim + _internal/ + run.sh). resources/ no
se toca nunca: ahí vive la data local del usuario en modo offline
(cases/cases.json, json/schedule.json, local_cache/logs.db, preferencias
editadas en runtime -- ver core/helpers.py y backend/log_queue.py).
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


def _local_build_id(fallback_version: str) -> str:
    """Lee BUILD_VERSION al lado del ejecutable (lo escribe el script de
    release). Si no existe -- build vieja, previa a esta feature, o corrida
    en dev -- cae a __VERSION__."""
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

    remote = next(
        (r for r in releases if r.get("tag_name", "").startswith(TAG_PREFIX)),
        None,
    )
    if remote is None:
        return None

    tag = remote["tag_name"]
    remote_build_id = tag[len(TAG_PREFIX):]
    local_build_id = _local_build_id(current_version)

    remote_v, remote_suffix = _split_build_id(remote_build_id)
    local_v, local_suffix = _split_build_id(local_build_id)

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
# reemplaza codigo (bin + _internal + run.sh) y relanza. resources/ no
# se toca: ahi vive la data local del usuario.
set -e
PID="$1"
DIST_DIR="$2"
NEW_DIST="$3"

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

rm -rf "$(dirname "$NEW_DIST")"

cd "$DIST_DIR"
nohup ./run.sh >/dev/null 2>&1 &
"""


def apply_update_and_restart(download_url: str) -> None:
    """Descarga el asset, lo extrae, lanza el script que hace el swap una
    vez que este proceso muera, y termina el proceso actual. No vuelve:
    llama a os._exit al final."""
    dist_dir = Path(sys.executable).resolve().parent

    tmp_dir = Path(tempfile.mkdtemp(prefix="labsim_update_"))
    archive_path = tmp_dir / ASSET_NAME
    req = Request(download_url)
    with urlopen(req, timeout=60) as resp, open(archive_path, "wb") as f:
        shutil.copyfileobj(resp, f)

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

    subprocess.Popen(
        [str(script_path), str(os.getpid()), str(dist_dir), str(new_dist)],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    os._exit(0)
