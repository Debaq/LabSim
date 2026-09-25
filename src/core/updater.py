# -*- coding: utf-8 -*-
"""
Auto-update de la build PyInstaller (onedir) contra GitHub Releases.

Dos estrategias segun plataforma:
- Linux: swap in-place de los archivos del dist (paquetes tar.gz, con
  cadena de diffs; todo lo que sigue de este docstring).
- Windows: baja el instalador Inno de la release mas nueva QUE TENGA
  instalador y lo corre en silencio. No hay diffs ni swap manual -- los DLL
  de _internal/ estan tomados por el proceso que corre y solo el instalador
  (Restart Manager) puede reemplazarlos. Ver installer/labsim.iss.

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
import hashlib
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
from xml.etree import ElementTree

REPO = "Debaq/LabSim"
TAG_PREFIX = "pyinstaller-v"
FULL_ASSET_NAME = "LabSim-linux-x86_64.tar.gz"
UPDATE_ASSET_NAME = "LabSim-linux-x86_64-update.tar.gz"
# Windows no usa la cadena de paquetes update: baja el instalador Inno y lo
# corre en silencio (ver check_for_update). Por eso el script de release solo
# mantiene este asset en las ultimas releases; el cliente busca hacia atras si
# a la mas nueva le falta (build de Windows caida, o SKIP_WINDOWS=1).
SETUP_ASSET_NAME = "LabSim-windows-x86_64-setup.exe"
IS_WINDOWS = sys.platform.startswith("win")
# per_page=100: la API devuelve 30 por defecto y las releases viejas se
# mantienen a proposito (son la cadena de updates). Pasadas las 30, una
# maquina atrasada no encontraba la suya en la lista y bajaba el full.
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases?per_page=100"
REQUEST_TIMEOUT = 5
# Mas saltos que esto y sale mas a cuenta bajar el full directo -- cada hop
# es una descarga + extraccion aparte, y encima "muchos hops" suele pasar
# quien no actualiza hace mucho, donde el full probablemente sea mas chico
# que la suma de todos los deltas intermedios igual.
MAX_CHAIN_HOPS = 8
MANIFEST_ASSET_NAME = "manifest.json"
# Marca "esta instalacion ya se verifico contra su release". Vive con la data
# del usuario (local_cache/) porque no es parte del build y no debe viajar en
# ningun paquete: si viajara, una instalacion rota heredaria el visto bueno.
VERIFY_MARKER = "resources/local_cache/.install_verified"
# Feed Atom de releases: es una pagina web, no la API, asi que no tiene el
# limite de 60 consultas por hora POR IP de la API sin autenticar (el
# laboratorio entero sale por la misma IP, y el kiosko pregunta al abrir y
# cada media hora). Trae solo las 10 mas nuevas y sin assets: sirve para
# saber si hay algo nuevo; la API se consulta solo cuando lo hay.
RELEASES_FEED = f"https://github.com/{REPO}/releases.atom"


class UpdateCheckError(Exception):
    """No se pudo saber si hay version nueva (red, GitHub, respuesta rara).
    Solo la levanta check_for_update(estricto=True): el kiosko no abre sin
    saberlo."""


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
        releases = json.load(resp)
    if not isinstance(releases, list):
        # con el limite agotado GitHub contesta un dict con "message"
        raise ValueError("GitHub no devolvio una lista de releases")
    return releases


def _ultimo_build_feed():
    """build_id de la release 'pyinstaller-v*' mas nueva segun el feed Atom,
    o None si el feed no trae ninguna (las 10 ultimas son del rewrite Tauri).
    Levanta si no se pudo leer."""
    with urlopen(Request(RELEASES_FEED), timeout=REQUEST_TIMEOUT) as resp:
        raiz = ElementTree.fromstring(resp.read())
    ns = "{http://www.w3.org/2005/Atom}"
    for entry in raiz.iter(ns + "entry"):
        tag = (entry.findtext(ns + "id") or "").rsplit("/", 1)[-1]
        if tag.startswith(TAG_PREFIX):
            return tag[len(TAG_PREFIX):]
    return None


def _al_dia_segun_feed(local_id: str) -> bool:
    """Atajo sin la API: la release mas nueva es la local y la instalacion ya
    se verifico contra ella (si no, hay que ir a la API a verificarla)."""
    try:
        ultimo = _ultimo_build_feed()
    except (URLError, OSError, ValueError, TimeoutError, ElementTree.ParseError):
        return False
    if ultimo is None or ultimo != local_id:
        return False
    try:
        marca = (_dist_dir() / VERIFY_MARKER).read_text(encoding="utf-8").strip()
    except OSError:
        return False
    return marca == local_id


def _asset_url(release: dict, name: str):
    return next(
        (a.get("browser_download_url") for a in release.get("assets", []) if a.get("name") == name),
        None,
    )



def _dist_dir() -> Path:
    return Path(sys.executable).resolve().parent


def _build_id_of(release: dict) -> str:
    return release["tag_name"][len(TAG_PREFIX):]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _install_matches_release(release: dict, dist_dir: Path):
    """True/False si el ejecutable local coincide con el de `release`.
    None si no se puede comprobar (release sin manifest, sin red, sin
    permisos): ante la duda no se molesta al usuario."""
    url = _asset_url(release, MANIFEST_ASSET_NAME)
    if url is None:
        return None
    try:
        with urlopen(Request(url), timeout=REQUEST_TIMEOUT * 3) as resp:
            manifest = json.load(resp)
    except (URLError, OSError, ValueError, TimeoutError):
        return None
    expected = (manifest.get("files") or {}).get("LabSim")
    exe = dist_dir / "LabSim"
    if not expected or not exe.is_file():
        return None
    try:
        return _sha256(exe) == expected
    except OSError:
        return None


def _check_install_integrity(candidates: list, local_release: dict):
    """El caso de un swap que copio a medias: BUILD_VERSION quedo en la
    version nueva pero el ejecutable es el viejo (ver _UPDATER_SCRIPT --
    hasta 2026-09-10 la version se escribia aunque los cp fallaran). Ahi el
    cliente corre codigo viejo Y el updater lo da por al dia, asi que no
    vuelve a ofrecer nada: queda clavado para siempre.

    Se comprueba una sola vez por build_id (marca en local_cache) y solo
    cuando no hay nada mas nuevo que ofrecer. Si el ejecutable no coincide
    con el de su release, se devuelve una reinstalacion completa."""
    dist_dir = _dist_dir()
    local_id = _build_id_of(local_release)
    marker = dist_dir / VERIFY_MARKER
    try:
        if marker.read_text(encoding="utf-8").strip() == local_id:
            return None
    except OSError:
        pass

    ok = _install_matches_release(local_release, dist_dir)
    if ok is None:
        return None
    if ok:
        try:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(local_id, encoding="utf-8")
        except OSError:
            pass
        return None

    asset = SETUP_ASSET_NAME if IS_WINDOWS else FULL_ASSET_NAME
    mode = "setup" if IS_WINDOWS else "full"
    for r in reversed(candidates):
        url = _asset_url(r, asset)
        if url is None:
            continue
        return {
            "tag": r["tag_name"],
            "build_id": _build_id_of(r),
            "mode": mode,
            "url": url,
            "repair": True,
            "notes": _extract_notes(r),
        }
    return None


def check_for_update(current_version: str, estricto: bool = False):
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
    - {"tag": ..., "build_id": ..., "mode": "setup", "url": ...} en Windows,
      siempre: el instalador de la release más nueva que tenga uno. Puede no
      ser la última: el .exe lo compila un runner aparte y puede faltar.

    Devuelve None si no hay nada nuevo, o si falla la red (nunca revienta:
    no queremos bloquear el arranque por un lab sin internet). Con
    estricto=True la falla de red levanta UpdateCheckError en vez de pasar
    por "no hay nada": el kiosko no abre sin saber si esta al dia.

    Primero se mira el feed Atom (sin limite de consultas): si dice que la
    local es la ultima, no se toca la API. Si el feed falla o hay algo
    nuevo, se sigue por la API como siempre."""
    if _al_dia_segun_feed(local_build_id(current_version).lstrip("v")):
        return None
    try:
        releases = _fetch_releases()
    except (URLError, OSError, ValueError, TimeoutError) as exc:
        if estricto:
            raise UpdateCheckError(str(exc)) from exc
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

    # Lo que corre localmente es, casi siempre, una release publicada: la
    # ubicamos por build_id en la lista ya ordenada por fecha. Todo lo que
    # viene DESPUES en esa lista es lo nuevo. Comparar por versión no
    # alcanza: las builds de prueba comparten versión (0.9.8-r<commit>) y
    # el sufijo de commit no tiene orden, así que "sufijo distinto" daba
    # por nuevas también a las releases anteriores -- y como las más viejas
    # no tienen paquete update, la cadena se rompía siempre y caía al full.
    local_index = next(
        (i for i, r in enumerate(candidates) if _build_id_of(r) == local_id), None
    )

    if local_index is not None:
        newer = candidates[local_index + 1:]
        chain_ok = True
    else:
        # Build que no corresponde a ninguna release (corrida en dev, o
        # release borrada): no sabemos en qué punto de la cadena estamos,
        # así que los diffs no son aplicables -- solo full.
        chain_ok = False
        newer = [r for r in candidates if _split_build_id(_build_id_of(r))[0] > local_v]
        if not newer:
            last_v, last_suffix = _split_build_id(_build_id_of(candidates[-1]))
            if last_v == local_v and last_suffix is not None and last_suffix != local_suffix:
                newer = [candidates[-1]]

    if not newer:
        # Nada nuevo que ofrecer: es el momento de comprobar que lo que
        # dice BUILD_VERSION sea de verdad lo que esta instalado.
        if local_index is None:
            return None
        return _check_install_integrity(candidates, candidates[local_index])

    latest = newer[-1]
    latest_tag = latest["tag_name"]
    latest_build_id = latest_tag[len(TAG_PREFIX):]

    if IS_WINDOWS:
        # El swap in-place que hace la cadena/full de Linux no es posible en
        # Windows: los DLL de _internal/ estan tomados por el proceso que
        # corre. El instalador resuelve las dos cosas -- cierra la instancia
        # via Restart Manager y reemplaza los archivos -- asi que en Windows
        # el update ES el setup completo, sin diffs.
        #
        # Se busca hacia atras la release mas nueva que TENGA instalador: el
        # .exe lo compila un runner aparte (build-windows.yml) y puede faltar
        # -- el workflow fallo, o la release se publico con SKIP_WINDOWS=1.
        # Mirando solo la ultima, esas releases dejaban a Windows sin
        # actualizacion y sin aviso, cuando la anterior si servia para
        # ponerlos al dia.
        for r in reversed(newer):
            setup_url = _asset_url(r, SETUP_ASSET_NAME)
            if setup_url is None:
                continue
            return {
                "tag": r["tag_name"],
                "build_id": r["tag_name"][len(TAG_PREFIX):],
                "mode": "setup",
                "url": setup_url,
                "notes": _extract_notes(r),
            }
        return None

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

# Todo lo que sigue va a un log: este script corre desacoplado y con
# stdout/stderr a /dev/null (ver apply_update_and_restart), asi que una
# copia que falla era invisible -- y la version quedaba mintiendo.
LOG_DIR="$DIST_DIR/resources/local_cache"
mkdir -p "$LOG_DIR" 2>/dev/null || true
LOG="$LOG_DIR/update.log"
if ! touch "$LOG" 2>/dev/null; then
    LOG="${TMPDIR:-/tmp}/labsim-update.log"
fi
exec >>"$LOG" 2>&1
echo "=== $(date -Is) update -> $FINAL_VERSION (dist: $DIST_DIR)"
FAILED=0

copy_or_flag() {
    if ! cp -a "$1" "$2"; then
        echo "labsim-update: FALLO copiando $1 -> $2"
        FAILED=1
    fi
}

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
    copy_or_flag "$new_dist/_internal" "$DIST_DIR/_internal"
    copy_or_flag "$new_dist/LabSim" "$DIST_DIR/LabSim"
    copy_or_flag "$new_dist/run.sh" "$DIST_DIR/run.sh"
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
                    copy_or_flag "$jf" "$DIST_DIR/resources/json/$jname"
                done
            else
                rm -rf "$DIST_DIR/resources/$name"
                copy_or_flag "$item" "$DIST_DIR/resources/$name"
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
        copy_or_flag "$relfile" "$DIST_DIR/$rel"
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

# BUILD_VERSION es lo que la app muestra como version y lo que el updater
# compara contra las releases. Escribirla sin que la copia haya funcionado
# deja al cliente con codigo viejo y etiqueta nueva: el update no se
# reintenta nunca y el bug "ya actualizado" se vuelve indiagnosticable.
if [ "$FAILED" -eq 0 ]; then
    if echo "$FINAL_VERSION" > "$DIST_DIR/BUILD_VERSION"; then
        echo "labsim-update: OK -> $FINAL_VERSION"
    else
        echo "labsim-update: se aplico todo pero no pude escribir BUILD_VERSION"
    fi
else
    echo "labsim-update: update INCOMPLETO -- BUILD_VERSION queda en $(cat "$DIST_DIR/BUILD_VERSION" 2>/dev/null); se reintenta en el proximo arranque"
fi

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

    if update_info["mode"] == "setup":
        # Windows: el instalador hace todo el trabajo. Se lanza desacoplado
        # (DETACHED_PROCESS) porque acto seguido este proceso se muere, y con
        # /LAUNCH=1, que en installer/labsim.iss relanza LabSim al terminar.
        # tmp_dir NO se borra: el .exe que esta corriendo vive ahi.
        setup_path = tmp_dir / SETUP_ASSET_NAME
        report("download", 0, 0, 1, 1)
        _download(update_info["url"], setup_path, lambda cur, tot: report("download", cur, tot, 1, 1))

        report("restart", 0, 0, 1, 1)
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0
        )
        subprocess.Popen(
            [
                str(setup_path),
                "/SILENT",
                "/CLOSEAPPLICATIONS",
                "/NORESTART",
                "/LAUNCH=1",
            ],
            creationflags=flags,
            close_fds=True,
        )
        os._exit(0)

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
