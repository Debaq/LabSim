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


def _fetch_releases() -> list:
    req = Request(RELEASES_API, headers={"Accept": "application/vnd.github+json"})
    with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.load(resp)


def check_for_update(current_version: str):
    """Busca el release 'pyinstaller-v*' más reciente. Si es más nuevo que
    current_version y trae el asset esperado, devuelve (tag, download_url).
    Si no hay nada nuevo, o falla la red, devuelve None (nunca revienta:
    no queremos bloquear el arranque por un lab sin internet)."""
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
    remote_version = tag[len(TAG_PREFIX):]
    if _parse_version(remote_version) <= _parse_version(current_version.lstrip("v")):
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
