# -*- coding: utf-8 -*-
"""
Auto-update de la build PyInstaller (onedir, Linux) contra GitHub Releases.

Los releases de este repo se comparten con el rewrite Tauri (tags v3.x,
assets .deb/.rpm/.AppImage/.exe/.msi). Para no mezclarse con esos, esta
build usa su propio prefijo de tag: 'pyinstaller-v<version>'.

Cada release trae hasta dos assets, generados por
scripts/release_pyinstaller.sh + scripts/update_diff.py:
- LabSim-linux-x86_64.tar.gz (full): tar completo de dist/LabSim. Siempre
  presente, es lo que baja un usuario nuevo para instalar de cero.
- LabSim-linux-x86_64-update.tar.gz (update): solo los archivos que
  cambiaron respecto a la release inmediatamente anterior, mas
  __removed__.txt con las rutas que se borraron. Puede faltar (release
  previa a esta feature, o la primera release nunca tiene "anterior").

check_for_update() arma la cadena de paquetes update entre la build local y
la más nueva (uno por release intermedia) para no bajar el full de nuevo
-- 100+MB -- en cada actualización. Si algún eslabón de esa cadena falta,
o son demasiados saltos (MAX_CHAIN_HOPS), cae a bajar el full de la más
nueva directamente: más pesado pero siempre correcto.

apply_update_and_restart() reemplaza el código (LabSim + _internal/ +
run.sh) y sincroniza resources/ con la versión nueva -- EXCEPTO la data
dinámica del usuario: resources/local_cache/ (logs.db, cola de acciones) y
resources/json/session.json (sesión logueada). Todo lo demás bajo
resources/ (el resto de json/, styles/, img/, font/, UI/, audio/) es
config/asset estático que se define en el repo y nunca se edita en
runtime (Preferences.set() ni siquiera está implementado, ver
core/helpers.py) -- si no se sincronizara, un usuario que se actualiza
in-place (sin reinstalar desde cero) se quedaría para siempre con el
json/X.json del día que instaló, aunque el código nuevo ya espere
entradas que ese archivo no tiene (síntoma: KeyError al abrir una
ventana nueva que
ese json viejo no conoce).
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
FULL_ASSET_NAME = "LabSim-linux-x86_64.tar.gz"
UPDATE_ASSET_NAME = "LabSim-linux-x86_64-update.tar.gz"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases"
REQUEST_TIMEOUT = 5
# Mas saltos que esto y sale mas a cuenta bajar el full directo -- cada hop
# es una descarga + extraccion aparte, y encima "muchos hops" suele pasar
# quien no actualiza hace mucho, donde el full probablemente sea mas chico
# que la suma de todos los deltas intermedios igual.
MAX_CHAIN_HOPS = 8


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


def _asset_url(release: dict, name: str):
    return next(
        (a.get("browser_download_url") for a in release.get("assets", []) if a.get("name") == name),
        None,
    )


def check_for_update(current_version: str):
    """Busca releases 'pyinstaller-v*' más nuevas que el build local.

    'Más nueva' = publicada después que la release que corresponde al
    build local, según el orden por fecha de publicación (el mismo con el
    que se calcularon los diffs). Si el build local no corresponde a
    ninguna release (dev, o release borrada) solo cuentan las versiones
    mayores, más la última si comparte versión con otro sufijo de commit
    (build de prueba re-publicada) -- y en ese caso solo se ofrece full,
    porque no se sabe desde qué punto de la cadena se está saltando.

    Si hay algo nuevo, devuelve un dict:
    - {"tag": ..., "build_id": ..., "mode": "chain", "hops": [(tag, update_url), ...]}
      hops en orden (el más viejo primero) cubre paso a paso desde la build
      local hasta la más nueva, cada uno un paquete update (diff) chico.
    - {"tag": ..., "build_id": ..., "mode": "full", "url": ...} si falta
      algún eslabón de la cadena (release vieja sin paquete update) o hay
      demasiados saltos (MAX_CHAIN_HOPS) -- baja el full de la más nueva.

    Devuelve None si no hay nada nuevo, o si falla la red (nunca revienta:
    no queremos bloquear el arranque por un lab sin internet)."""
    try:
        releases = _fetch_releases()
    except (URLError, OSError, ValueError, TimeoutError):
        return None

    candidates = [r for r in releases if r.get("tag_name", "").startswith(TAG_PREFIX)]
    if not candidates:
        return None
    # La API de GitHub no garantiza orden por fecha en /releases -- hay que
    # ordenar a mano. Este orden es también el orden real de publicación,
    # que es contra el que scripts/release_pyinstaller.sh calculó cada
    # paquete update (diff contra "la release inmediatamente anterior por
    # fecha"), así que hay que respetarlo al armar la cadena de hops.
    candidates.sort(key=lambda r: r.get("created_at") or "")

    local_id = local_build_id(current_version).lstrip("v")
    local_v, local_suffix = _split_build_id(local_id)

    def build_id_of(release):
        return release["tag_name"][len(TAG_PREFIX):]

    # Lo que corre localmente es, casi siempre, una release publicada: la
    # ubicamos por build_id en la lista ya ordenada por fecha. Todo lo que
    # viene DESPUES en esa lista es lo nuevo. Comparar por versión no
    # alcanza: las builds de prueba comparten versión (0.9.8-r<commit>) y
    # el sufijo de commit no tiene orden, así que "sufijo distinto" daba
    # por nuevas también a las releases anteriores -- y como las más viejas
    # no tienen paquete update, la cadena se rompía siempre y caía al full.
    local_index = next(
        (i for i, r in enumerate(candidates) if build_id_of(r) == local_id), None
    )

    if local_index is not None:
        newer = candidates[local_index + 1:]
        chain_ok = True
    else:
        # Build que no corresponde a ninguna release (corrida en dev, o
        # release borrada): no sabemos en qué punto de la cadena estamos,
        # así que los diffs no son aplicables -- solo full.
        chain_ok = False
        newer = [r for r in candidates if _split_build_id(build_id_of(r))[0] > local_v]
        if not newer:
            last_v, last_suffix = _split_build_id(build_id_of(candidates[-1]))
            if last_v == local_v and last_suffix is not None and last_suffix != local_suffix:
                newer = [candidates[-1]]

    if not newer:
        return None

    latest = newer[-1]
    latest_tag = latest["tag_name"]
    latest_build_id = latest_tag[len(TAG_PREFIX):]

    hops = [] if chain_ok else None
    if hops is not None:
        for r in newer:
            update_url = _asset_url(r, UPDATE_ASSET_NAME)
            if update_url is None:
                hops = None
                break
            hops.append((r["tag_name"], update_url))

    if hops is not None and len(hops) <= MAX_CHAIN_HOPS:
        return {
            "tag": latest_tag,
            "build_id": latest_build_id,
            "mode": "chain",
            "hops": hops,
            "notes": _extract_notes(latest),
        }

    full_url = _asset_url(latest, FULL_ASSET_NAME)
    if full_url is None:
        return None
    return {
        "tag": latest_tag,
        "build_id": latest_build_id,
        "mode": "full",
        "url": full_url,
        "notes": _extract_notes(latest),
    }


def _extract_notes(release: dict) -> str:
    """Devuelve el body del release de GitHub (markdown) capeado a 1500
    chars para que el QMessageBox que muestra "¿actualizar?" no se infle.
    Vacío si el release no trae notas o son solo whitespace."""
    body = (release.get("body") or "").strip()
    if len(body) > 1500:
        body = body[:1500] + "\n[…]"
    return body


_UPDATER_SCRIPT = """#!/bin/bash
# Generado por core/updater.py -- espera a que cierre el proceso viejo,
# aplica los pasos listados en STEPS_FILE en orden (uno por linea, TAB
# separado: "FULL <dir>" reemplaza codigo+resources entero, "UPDATE <dir>"
# aplica un paquete diff), escribe BUILD_VERSION y relanza.
set -e
PID="$1"
DIST_DIR="$2"
STEPS_FILE="$3"
FINAL_VERSION="$4"

shopt -s nullglob dotglob

waited=0
while kill -0 "$PID" 2>/dev/null; do
    sleep 0.3
    waited=$((waited + 1))
    if [ "$waited" -gt 200 ]; then
        break
    fi
done

# De aca en adelante no abortamos mas: si un item puntual falla no queremos
# perder el resto de los pasos ni dejar el relanzamiento sin ejecutar.
set +e

# resources/: se sincroniza con la version nueva salvo las carpetas/archivos
# 100% dinamicos del usuario (local_cache/, json/session.json) -- todo lo
# demas (el resto de json/, styles/, img/, font/, UI/, audio/)
# es config/asset estatico que debe quedar al dia con cada release, no solo
# en una instalacion nueva.
apply_full() {
    local new_dist="$1"
    rm -rf "$DIST_DIR/_internal"
    cp -a "$new_dist/_internal" "$DIST_DIR/_internal"
    cp -a "$new_dist/LabSim" "$DIST_DIR/LabSim"
    cp -a "$new_dist/run.sh" "$DIST_DIR/run.sh"
    chmod +x "$DIST_DIR/LabSim" "$DIST_DIR/run.sh"

    if [ -d "$new_dist/resources" ]; then
        mkdir -p "$DIST_DIR/resources"

        # 1) Borrar en destino lo que ya no existe en el release nuevo
        #    (huerfanos de una version anterior), salvo la data dinamica.
        for old_item in "$DIST_DIR/resources"/*; do
            name="$(basename "$old_item")"
            case "$name" in
                local_cache) continue ;;
            esac
            if [ ! -e "$new_dist/resources/$name" ]; then
                rm -rf "$old_item"
            fi
        done
        if [ -d "$DIST_DIR/resources/json" ]; then
            for old_jf in "$DIST_DIR/resources/json"/*; do
                jname="$(basename "$old_jf")"
                case "$jname" in
                    session.json) continue ;;
                esac
                if [ ! -e "$new_dist/resources/json/$jname" ]; then
                    rm -f "$old_jf"
                fi
            done
        fi

        # 2) Copiar todo lo nuevo.
        for item in "$new_dist/resources"/*; do
            name="$(basename "$item")"
            case "$name" in
                local_cache) continue ;;
            esac
            if [ "$name" = "json" ]; then
                mkdir -p "$DIST_DIR/resources/json"
                for jf in "$item"/*; do
                    jname="$(basename "$jf")"
                    case "$jname" in
                        session.json) continue ;;
                    esac
                    cp -a "$jf" "$DIST_DIR/resources/json/$jname" || echo "labsim-update: fallo copiando json/$jname" >&2
                done
            else
                rm -rf "$DIST_DIR/resources/$name"
                cp -a "$item" "$DIST_DIR/resources/$name" || echo "labsim-update: fallo copiando resources/$name" >&2
            fi
        done
    fi
}

# Paquete update (diff): trae solo los archivos nuevos/cambiados, con su
# ruta relativa a DIST_DIR tal cual, mas __removed__.txt con las rutas que
# se eliminaron en esa release. A diferencia de apply_full, no toca nada
# que no este listado -- no hay swap total de _internal/.
apply_update() {
    local upd_dir="$1"
    local removed_file="$upd_dir/__removed__.txt"

    while IFS= read -r -d '' relfile; do
        rel="${relfile#"$upd_dir"/}"
        case "$rel" in
            __removed__.txt) continue ;;
        esac
        mkdir -p "$DIST_DIR/$(dirname "$rel")"
        cp -a "$relfile" "$DIST_DIR/$rel" || echo "labsim-update: fallo copiando $rel" >&2
    done < <(find "$upd_dir" -type f -print0)

    chmod +x "$DIST_DIR/LabSim" 2>/dev/null
    chmod +x "$DIST_DIR/run.sh" 2>/dev/null

    if [ -f "$removed_file" ]; then
        while IFS= read -r rel; do
            [ -z "$rel" ] && continue
            case "$rel" in
                resources/local_cache*|resources/json/session.json) continue ;;
            esac
            rm -rf "$DIST_DIR/$rel"
        done < "$removed_file"
    fi
}

while IFS=$'\\t' read -r kind path; do
    case "$kind" in
        FULL) apply_full "$path" ;;
        UPDATE) apply_update "$path" ;;
    esac
done < "$STEPS_FILE"

echo "$FINAL_VERSION" > "$DIST_DIR/BUILD_VERSION"

rm -rf "$(dirname "$STEPS_FILE")"

cd "$DIST_DIR"
nohup ./run.sh >/dev/null 2>&1 &
"""


def _download(url: str, dest: Path, on_chunk) -> None:
    req = Request(url)
    with urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
        total = int(resp.headers.get("Content-Length") or 0)
        downloaded = 0
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            on_chunk(downloaded, total)


def apply_update_and_restart(update_info: dict, on_progress=None) -> None:
    """Descarga el/los paquete(s) de update_info (ver check_for_update),
    los extrae, lanza el script que hace el swap una vez que este proceso
    muera, y termina el proceso actual. No vuelve si tiene éxito: llama a
    os._exit al final.

    on_progress(stage, current, total, hop, hops), si se pasa, se llama
    durante cada etapa ('download', 'extract', 'restart') para que el
    caller (main.py) pueda mostrar una barra de progreso -- sin esto la
    descarga/extracción queda muda y la ventana parece congelada. hop/hops
    identifican qué paquete de la cadena se está bajando (1/1 en modo full)."""
    def report(stage, current=0, total=0, hop=1, hops=1):
        if on_progress:
            on_progress(stage, current, total, hop, hops)

    dist_dir = Path(sys.executable).resolve().parent
    tmp_dir = Path(tempfile.mkdtemp(prefix="labsim_update_"))
    steps = []

    if update_info["mode"] == "full":
        archive_path = tmp_dir / "full.tar.gz"
        report("download", 0, 0, 1, 1)
        _download(update_info["url"], archive_path, lambda cur, tot: report("download", cur, tot, 1, 1))

        report("extract", 0, 0, 1, 1)
        extract_dir = tmp_dir / "full_extracted"
        with tarfile.open(archive_path) as tf:
            tf.extractall(extract_dir)
        archive_path.unlink()

        new_dist = extract_dir / "LabSim"
        if not new_dist.is_dir():
            # asset con estructura inesperada: no arriesgamos el swap
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return
        steps.append(("FULL", new_dist))
    else:
        hops = update_info["hops"]
        n = len(hops)
        for i, (_tag, update_url) in enumerate(hops, start=1):
            archive_path = tmp_dir / f"update_{i}.tar.gz"
            report("download", 0, 0, i, n)
            _download(update_url, archive_path, lambda cur, tot, i=i, n=n: report("download", cur, tot, i, n))

            report("extract", 0, 0, i, n)
            extract_dir = tmp_dir / f"update_{i}_extracted"
            with tarfile.open(archive_path) as tf:
                tf.extractall(extract_dir)
            archive_path.unlink()
            steps.append(("UPDATE", extract_dir))

    steps_file = tmp_dir / "steps.tsv"
    # newline final obligatorio: el script bash lee esto con "while read",
    # que se salta la ultima linea si el archivo no termina en \n.
    steps_text = "".join(f"{kind}\t{path}\n" for kind, path in steps)
    steps_file.write_text(steps_text, encoding="utf-8")

    script_path = tmp_dir / "apply_update.sh"
    script_path.write_text(_UPDATER_SCRIPT, encoding="utf-8")
    script_path.chmod(0o755)

    report("restart", 0, 0, len(steps), len(steps))
    subprocess.Popen(
        [str(script_path), str(os.getpid()), str(dist_dir), str(steps_file), update_info["build_id"]],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    os._exit(0)
