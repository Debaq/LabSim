# -*- coding: utf-8 -*-
"""
Auto-update de la build PyInstaller (onedir) contra GitHub Releases.

Dos estrategias segun plataforma:
- Linux: swap in-place de los archivos del dist (paquetes tar.gz, con
  cadena de diffs; todo lo que sigue de este docstring).
- Windows: todo pasa por instaladores Inno (installer/labsim.iss), nunca
  por un swap manual -- los DLL de _internal/ estan tomados por el proceso
  que corre y el instalador es el que sabe esperarlo, reemplazarlos y
  deshacer si algo falla. Igual que en Linux hay cadena: cada release trae
  un instalador delta (LabSim-windows-x86_64-update-setup.exe, solo lo que
  cambio respecto a la anterior) y se corren en fila, uno por release; si
  falta un eslabon se corre el instalador completo de la mas nueva que lo
  tenga. Los lanza aplicar.cmd (ver _script_windows), que si uno falla
  vuelve a abrir el LabSim que habia.

En las dos plataformas, antes de cerrarse para actualizar se deja una marca
(PENDIENTE) con la version esperada: al abrir de nuevo, revisar_update_anterior()
dice si llego o no, con el log del instalador/script, en vez de seguir como
si nada con la version vieja.

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
import time
from pathlib import Path
from http.client import HTTPException
from urllib.error import HTTPError, URLError
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
# Instalador delta: solo los archivos que cambiaron respecto a la release
# inmediatamente anterior (build-windows.yml, contra su manifest-windows.json).
# Se niega a correr si lo instalado no es esa release (ver labsim.iss).
WIN_UPDATE_ASSET_NAME = "LabSim-windows-x86_64-update-setup.exe"
IS_WINDOWS = sys.platform.startswith("win")
# Mutex con nombre que crea la app abierta y que el instalador espera a que
# se suelte antes de copiar (InitializeSetup en installer/labsim.iss). Mismo
# texto en los dos lados.
MUTEX_NAME = "LabSimAppMutex"
_mutex = None
# Carpetas de descarga en el temporal del sistema (tempfile.mkdtemp). En
# Windows no se pueden borrar al lanzar el instalador -- corre desde ahi --,
# asi que las barre limpiar_temporales() en un arranque posterior.
TMP_PREFIX = "labsim_update_"
# "Me cerre para actualizar a X": la deja apply_update_and_restart y la lee
# revisar_update_anterior() al abrir de nuevo. Con la data del usuario: el
# instalador y los paquetes no la tocan.
PENDIENTE = "resources/local_cache/update_pendiente.json"
# Un instalador sigue corriendo un rato despues de que la app se cerro: si el
# alumno abre LabSim a mano en ese lapso, la version aun no cambio y no es
# una falla. Pasado este tiempo sin la marca FALLO, si lo es.
PENDIENTE_GRACIA_S = 15 * 60
DESCARGA_INTENTOS = 4
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


def _fetch_releases_backend(backend_url: str) -> list:
    """La lista que guarda el backend (api/app_releases.php), con la misma
    forma que la de la API. Levanta si no responde o si no tiene una lista
    reciente (503)."""
    url = backend_url.rstrip("/") + "/api/app_releases.php"
    with urlopen(Request(url), timeout=REQUEST_TIMEOUT) as resp:
        data = json.load(resp)
    releases = data.get("releases") if isinstance(data, dict) else None
    if not isinstance(releases, list):
        raise ValueError("el backend no devolvio una lista de releases")
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
    except (URLError, OSError, ValueError, TimeoutError, HTTPException, ElementTree.ParseError):
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
    except (URLError, OSError, ValueError, TimeoutError, HTTPException):
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


def check_for_update(current_version: str, estricto: bool = False,
                     backend_url: str | None = None):
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

    De donde sale la lista, en orden: el backend (backend_url; consulta a
    GitHub una vez cada 10 min por todos los clientes, ver AppReleases.php),
    y si no responde, GitHub directo: primero el feed Atom (sin limite de
    consultas) por si dice que la local es la ultima, y si no, la API."""
    releases = None
    if backend_url:
        try:
            releases = _fetch_releases_backend(backend_url)
        except (URLError, OSError, ValueError, TimeoutError, HTTPException):
            releases = None
    if releases is None:
        if _al_dia_segun_feed(local_build_id(current_version).lstrip("v")):
            return None
        try:
            releases = _fetch_releases()
        except (URLError, OSError, ValueError, TimeoutError, HTTPException) as exc:
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
        return _con_verificacion(_check_install_integrity(candidates, candidates[local_index]), candidates)

    if IS_WINDOWS:
        return _con_verificacion(_update_windows(newer, chain_ok), candidates)

    latest = newer[-1]
    latest_tag = latest["tag_name"]
    latest_build_id = latest_tag[len(TAG_PREFIX):]

    hops = _cadena(newer, UPDATE_ASSET_NAME) if chain_ok else None
    if hops is not None and len(hops) <= MAX_CHAIN_HOPS:
        return _con_verificacion({
            "tag": latest_tag,
            "build_id": latest_build_id,
            "mode": "chain",
            "hops": hops,
            "notes": _extract_notes(latest),
        }, candidates)

    full_url = _asset_url(latest, FULL_ASSET_NAME)
    if full_url is None:
        return None
    return _con_verificacion({
        "tag": latest_tag,
        "build_id": latest_build_id,
        "mode": "full",
        "url": full_url,
        "notes": _extract_notes(latest),
    }, candidates)


def _cadena(releases: list, asset: str):
    """[(tag, url), ...] del paquete `asset` de cada release, en orden, o
    None si a alguna le falta: un eslabon roto invalida la cadena entera
    (cada paquete es un diff contra la release inmediatamente anterior)."""
    hops = []
    for r in releases:
        url = _asset_url(r, asset)
        if url is None:
            return None
        hops.append((r["tag_name"], url))
    return hops


def _update_windows(newer: list, chain_ok: bool):
    """El update de Windows: siempre instaladores Inno (ver docstring).

    El destino es la release mas nueva que TENGA instalador completo: el .exe
    lo compila un runner aparte (build-windows.yml) y puede faltar -- el
    workflow fallo, o la release se publico con SKIP_WINDOWS=1. Mirando solo
    la ultima, esas releases dejaban a Windows sin actualizacion y sin aviso,
    cuando la anterior si servia para ponerlos al dia.

    Hasta ese destino se va por la cadena de instaladores delta si esta
    entera (unos MB cada uno contra los ~55 del completo); si no, el
    completo. Las dos formas devuelven "instalador": True, que es lo que
    apply_update_and_restart mira para no correr el script de bash."""
    for idx in range(len(newer) - 1, -1, -1):
        r = newer[idx]
        setup_url = _asset_url(r, SETUP_ASSET_NAME)
        if setup_url is None:
            continue
        info = {
            "tag": r["tag_name"],
            "build_id": _build_id_of(r),
            "notes": _extract_notes(r),
            "instalador": True,
        }
        hops = _cadena(newer[:idx + 1], WIN_UPDATE_ASSET_NAME) if chain_ok else None
        if hops is not None and len(hops) <= MAX_CHAIN_HOPS:
            info.update(mode="chain", hops=hops)
        else:
            info.update(mode="setup", url=setup_url)
        return info
    return None


def _con_verificacion(info, releases: list):
    """Le agrega a `info` el tamaño y sha256 que GitHub informa de cada
    asset (campos size y digest de la API; el backend los reenvia), para que
    _download descarte un archivo cortado o corrupto en vez de dejarselo al
    tar o al instalador. Lo que no venga, no se verifica."""
    if info is None:
        return None
    verificar = {}
    for r in releases:
        for a in r.get("assets", []):
            url = a.get("browser_download_url")
            if not url:
                continue
            meta = {}
            size = a.get("size")
            if isinstance(size, int) and size > 0:
                meta["size"] = size
            digest = a.get("digest")
            if isinstance(digest, str) and digest.startswith("sha256:"):
                meta["sha256"] = digest[len("sha256:"):].lower()
            if meta:
                verificar[url] = meta
    info["verificar"] = verificar
    return info


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


def _download(url: str, dest: Path, on_chunk, esperado: dict | None = None) -> None:
    """Baja `url` a `dest` aguantando la red del laboratorio: hasta
    DESCARGA_INTENTOS intentos, y cada reintento sigue desde donde se corto
    (Range) en vez de empezar de cero. Si `esperado` trae size/sha256 (ver
    _con_verificacion), el archivo se compara antes de darlo por bueno: uno
    cortado o corrupto se descarta y se baja de nuevo. Lo que se baja va a
    <dest>.part y recien al final pasa a llamarse `dest`."""
    esperado = esperado or {}
    parcial = dest.with_name(dest.name + ".part")
    error = None
    for intento in range(DESCARGA_INTENTOS):
        if intento:
            time.sleep(min(2 ** intento, 10))
        try:
            _bajar_desde(url, parcial, on_chunk)
        except (URLError, OSError, TimeoutError, HTTPException) as exc:
            error = exc
            continue
        problema = _problema_descarga(parcial, esperado)
        if problema is None:
            os.replace(parcial, dest)
            return
        error = ValueError(f"descarga de {dest.name} no coincide con la publicada: {problema}")
        parcial.unlink(missing_ok=True)
    raise error


def _bajar_desde(url: str, parcial: Path, on_chunk) -> None:
    ya = parcial.stat().st_size if parcial.exists() else 0
    headers = {"Range": f"bytes={ya}-"} if ya else {}
    try:
        resp = urlopen(Request(url, headers=headers), timeout=60)
    except HTTPError as exc:
        if exc.code == 416 and ya:
            # 416 a un Range que empieza en el final: ya estaba completo.
            return
        raise
    with resp:
        if ya and resp.status != 206:
            # El servidor no reanuda: manda el archivo entero desde el byte 0.
            ya = 0
        largo = int(resp.headers.get("Content-Length") or 0)
        total = ya + largo if largo else 0
        bajado = ya
        with open(parcial, "ab" if ya else "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                bajado += len(chunk)
                on_chunk(bajado, total)
    if largo and bajado - ya < largo:
        raise OSError(f"conexion cortada: {bajado} de {total} bytes")


def _problema_descarga(path: Path, esperado: dict):
    size = esperado.get("size")
    if size and path.stat().st_size != size:
        return f"{path.stat().st_size} bytes en vez de {size}"
    sha = esperado.get("sha256")
    if sha and _sha256(path) != sha:
        return "sha256 distinto"
    return None


def _entorno_limpio() -> dict:
    """Entorno para lo que se lanza al actualizar. El bootloader de
    PyInstaller deja variables _PYI_* (y _MEI* en builds viejas) que hereda
    todo hijo: el LabSim nuevo que relanza el instalador las recibiria del
    viejo y podria creerse un subproceso suyo. PYINSTALLER_RESET_ENVIRONMENT
    es la forma documentada de que arranque como una app independiente."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("_PYI_", "_MEI"))}
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return env


def _script_windows(n: int) -> str:
    """aplicar.cmd: corre paso1.exe..pasoN.exe (instaladores Inno, en la
    misma carpeta) en fila, cada uno con su log, y solo el ultimo relanza
    LabSim (/LAUNCH=1, ver installer/labsim.iss). Si uno sale con error
    corta ahi, deja la marca FALLO y abre el LabSim que habia (%1) -- antes
    el alumno se quedaba sin programa y sin saber por que.

    Rutas solo relativas a %~dp0 (la carpeta del script) y el ejecutable por
    argumento: cmd lee el .cmd en la pagina de codigos OEM, y una ruta con
    tildes escrita adentro (C:\\Users\\José\\...) se romperia. Los
    argumentos y %~dp0 no pasan por esa conversion."""
    lineas = [
        "@echo off",
        "rem Generado por core/updater.py -- ver _script_windows.",
        "setlocal",
    ]
    for i in range(1, n + 1):
        relanzar = " /LAUNCH=1" if i == n else ""
        lineas += [
            f'echo paso {i} de {n} >> "%~dp0aplicar.log"',
            f'start "" /wait "%~dp0paso{i}.exe" /SILENT /SUPPRESSMSGBOXES /NORESTART '
            f'/CLOSEAPPLICATIONS{relanzar} /LOG="%~dp0paso{i}.log"',
            "if errorlevel 1 goto fallo",
        ]
    lineas += [
        'echo OK >> "%~dp0aplicar.log"',
        "exit /b 0",
        ":fallo",
        'echo FALLO %errorlevel% >> "%~dp0aplicar.log"',
        'echo %errorlevel% > "%~dp0FALLO"',
        'start "" "%~1"',
        "exit /b 1",
    ]
    return "\r\n".join(lineas) + "\r\n"


def preparar_windows(carpeta: Path, setups: list) -> Path:
    """Deja en `carpeta` los instaladores como paso1.exe.. y aplicar.cmd.
    `setups` son rutas ya descargadas (en `carpeta` o no). Lo usa tambien
    scripts/probar_update_windows.py en CI, para probar exactamente esto."""
    for i, src in enumerate(setups, start=1):
        dest = carpeta / f"paso{i}.exe"
        if Path(src) != dest:
            shutil.copyfile(src, dest)
    script = carpeta / "aplicar.cmd"
    script.write_bytes(_script_windows(len(setups)).encode("ascii"))
    return script


def lanzar_windows(script: Path, exe: Path) -> subprocess.Popen:
    """Corre aplicar.cmd sin ventana de consola, en su propio grupo, para
    que sobreviva a este proceso, que se cierra acto seguido. /s y las
    comillas dobles de afuera son la forma en que cmd /c respeta las
    comillas de una ruta con espacios."""
    if IS_WINDOWS:
        # El bootloader fija el directorio de DLL de _internal/ para este
        # proceso; que no lo vea el instalador.
        try:
            import ctypes
            ctypes.windll.kernel32.SetDllDirectoryW(None)
        except Exception:  # noqa: BLE001
            pass
    comspec = os.environ.get("COMSPEC") or "cmd.exe"
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    return subprocess.Popen(
        f'"{comspec}" /d /s /c ""{script}" "{exe}""',
        creationflags=flags,
        close_fds=True,
        env=_entorno_limpio(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _marcar_pendiente(update_info: dict, carpeta: Path) -> None:
    ruta = _dist_dir() / PENDIENTE
    datos = {
        "esperado": update_info["build_id"],
        "desde": local_build_id(""),
        "carpeta": str(carpeta),
        "cuando": time.time(),
        "instalador": bool(update_info.get("instalador") or update_info["mode"] == "setup"),
    }
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(datos), encoding="utf-8")
    except OSError:
        pass


def _cola(path: Path, lineas: int) -> str:
    try:
        texto = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return "\n".join(texto.splitlines()[-lineas:])


def revisar_update_anterior(current_version: str):
    """¿Llego la actualizacion que se aplico al cerrar la vez anterior?

    None: no habia ninguna pendiente, o llego bien (se borran la marca y la
    carpeta de descarga). {"en_curso": True}: el instalador probablemente
    sigue trabajando (ver PENDIENTE_GRACIA_S) -- no conviene ofrecer otra
    actualizacion encima. Si fallo: {"esperado", "actual", "log"}, con la
    cola de los logs del instalador o del script, y la marca se borra (se
    avisa una vez; la proxima busqueda de updates la vuelve a ofrecer)."""
    ruta = _dist_dir() / PENDIENTE
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(datos, dict):
        datos = {}
    actual = local_build_id(current_version).lstrip("v")
    esperado = str(datos.get("esperado") or "")
    carpeta = Path(datos["carpeta"]) if datos.get("carpeta") else None

    if actual == esperado:
        ruta.unlink(missing_ok=True)
        if carpeta is not None:
            shutil.rmtree(carpeta, ignore_errors=True)
        return None

    joven = time.time() - float(datos.get("cuando") or 0) < PENDIENTE_GRACIA_S
    fallo_marcado = carpeta is not None and (carpeta / "FALLO").exists()
    if datos.get("instalador") and joven and not fallo_marcado:
        return {"en_curso": True}

    partes = []
    if carpeta is not None:
        aplicar = _cola(carpeta / "aplicar.log", 20)
        if aplicar:
            partes.append(aplicar)
        for log in sorted(carpeta.glob("paso*.log")):
            partes.append(f"--- {log.name}\n{_cola(log, 40)}")
    linux = _cola(_dist_dir() / "resources/local_cache/update.log", 30)
    if linux and not datos.get("instalador"):
        partes.append(linux)
    ruta.unlink(missing_ok=True)
    return {"esperado": esperado, "actual": actual, "log": "\n".join(partes)}


def limpiar_temporales(edad_min_s: int = 3600) -> None:
    """Borra las carpetas de descarga de actualizaciones viejas en el
    temporal del sistema (~55 MB cada una en Windows, donde no se pueden
    borrar al lanzar el instalador). Se salta las recientes -- un instalador
    puede seguir corriendo desde ahi -- y la de una actualizacion pendiente,
    que guarda los logs para revisar_update_anterior()."""
    protegida = None
    try:
        datos = json.loads((_dist_dir() / PENDIENTE).read_text(encoding="utf-8"))
        protegida = Path(datos["carpeta"]).resolve()
    except (OSError, ValueError, KeyError, TypeError):
        pass
    ahora = time.time()
    for carpeta in Path(tempfile.gettempdir()).glob(TMP_PREFIX + "*"):
        try:
            if not carpeta.is_dir() or carpeta.resolve() == protegida:
                continue
            if ahora - carpeta.stat().st_mtime < edad_min_s:
                continue
        except OSError:
            continue
        shutil.rmtree(carpeta, ignore_errors=True)


def tomar_mutex_instancia() -> bool:
    """Windows: crea el mutex MUTEX_NAME, que el instalador espera a que se
    suelte antes de copiar (sin el, Inno solo tiene el Restart Manager, que
    no siempre logra cerrar una instancia colgada). Devuelve True si otra
    instancia de LabSim ya lo tenia: con dos abiertas, actualizar desde una
    dejaria los DLL tomados por la otra. En Linux no hace nada."""
    global _mutex
    if not IS_WINDOWS:
        return False
    try:
        import ctypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateMutexW.restype = ctypes.c_void_p
        k32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        _mutex = k32.CreateMutexW(None, False, MUTEX_NAME)
        return ctypes.get_last_error() == 183  # ERROR_ALREADY_EXISTS
    except Exception:  # noqa: BLE001
        return False


def _salida_limpia():
    """Reiniciar para actualizar no es una caída (ver registro.marcar_inicio)."""
    try:
        from core import registro
        registro.marcar_salida()
    except Exception:  # noqa: BLE001
        pass


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
    tmp_dir = Path(tempfile.mkdtemp(prefix=TMP_PREFIX))
    verificar = update_info.get("verificar") or {}
    steps = []

    if update_info.get("instalador") or update_info["mode"] == "setup":
        # Windows: los instaladores hacen todo el trabajo; aplicar.cmd los
        # corre en fila cuando este proceso ya se cerro. tmp_dir NO se borra:
        # los .exe corren desde ahi y guarda sus logs (limpiar_temporales).
        if update_info["mode"] == "setup":
            urls = [update_info["url"]]
        else:
            urls = [url for _tag, url in update_info["hops"]]
        n = len(urls)
        setups = []
        for i, url in enumerate(urls, start=1):
            setup_path = tmp_dir / f"paso{i}.exe"
            report("download", 0, 0, i, n)
            _download(url, setup_path, lambda cur, tot, i=i: report("download", cur, tot, i, n),
                      verificar.get(url))
            setups.append(setup_path)
        script = preparar_windows(tmp_dir, setups)

        report("restart", 0, 0, n, n)
        _marcar_pendiente(update_info, tmp_dir)
        _salida_limpia()
        lanzar_windows(script, Path(sys.executable).resolve())
        os._exit(0)

    if update_info["mode"] == "full":
        archive_path = tmp_dir / "full.tar.gz"
        report("download", 0, 0, 1, 1)
        _download(update_info["url"], archive_path, lambda cur, tot: report("download", cur, tot, 1, 1),
                  verificar.get(update_info["url"]))

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
            _download(update_url, archive_path, lambda cur, tot, i=i, n=n: report("download", cur, tot, i, n),
                      verificar.get(update_url))

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
    _marcar_pendiente(update_info, tmp_dir)
    _salida_limpia()
    subprocess.Popen(
        [str(script_path), str(os.getpid()), str(dist_dir), str(steps_file), update_info["build_id"]],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    os._exit(0)
