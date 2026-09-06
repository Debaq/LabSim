#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera el manifest de hashes de dist/LabSim y arma el paquete de update
(diff) contra el manifest de la release anterior. Usado solo desde
scripts/release_pyinstaller.sh -- no se importa desde la app ni desde
core/updater.py.

BUILD_VERSION y la data dinamica del usuario (resources/local_cache/,
resources/json/session.json) quedan afuera del manifest a proposito:
BUILD_VERSION cambia en cada build por definicion (metería ese archivo en
todos los updates aunque nada mas cambie) y lo escribe aparte el script
generado por core/updater.py; la data dinamica nunca es parte del build.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

EXCLUDE_PREFIXES = ("resources/local_cache/", "resources/json/session.json")
EXCLUDE_NAMES = {"BUILD_VERSION"}


def _included(rel: str) -> bool:
    if rel in EXCLUDE_NAMES:
        return False
    return not rel.startswith(EXCLUDE_PREFIXES)


def build_manifest(dist_dir: Path) -> dict:
    files = {}
    for p in sorted(dist_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(dist_dir).as_posix()
        if not _included(rel):
            continue
        files[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {"files": files}


def cmd_manifest(dist_dir: str, out_path: str) -> None:
    manifest = build_manifest(Path(dist_dir))
    Path(out_path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"manifest: {len(manifest['files'])} archivos")


def cmd_diff(dist_dir: str, old_manifest_path: str, update_dir_out: str) -> None:
    """Arma update_dir_out con los archivos nuevos/cambiados respecto al
    manifest viejo, mas __removed__.txt con las rutas que ya no existen.
    Sale con status 2 si no habia manifest previo (release anterior sin
    esta feature, o primera build) -- el caller decide si igual publica un
    paquete update (no tendria sentido: seria igual al full)."""
    dist_dir_p = Path(dist_dir)
    new_files = build_manifest(dist_dir_p)["files"]

    old_path = Path(old_manifest_path)
    old_files = {}
    had_previous = old_path.is_file()
    if had_previous:
        old_files = json.loads(old_path.read_text(encoding="utf-8")).get("files", {})

    update_dir = Path(update_dir_out)
    if update_dir.exists():
        shutil.rmtree(update_dir)
    update_dir.mkdir(parents=True)

    changed = [rel for rel, h in new_files.items() if old_files.get(rel) != h]
    for rel in changed:
        dest = update_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dist_dir_p / rel, dest)

    removed = [rel for rel in old_files if rel not in new_files]
    # newline final obligatorio: el updater lee esto con "while read" en
    # bash, que se salta la ultima linea si el archivo no termina en \n.
    removed_text = "".join(f"{rel}\n" for rel in removed)
    (update_dir / "__removed__.txt").write_text(removed_text, encoding="utf-8")

    print(f"diff: {len(changed)} cambiados/nuevos, {len(removed)} eliminados")
    sys.exit(0 if had_previous else 2)


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "manifest":
        cmd_manifest(sys.argv[2], sys.argv[3])
    elif action == "diff":
        cmd_diff(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(f"accion desconocida: {action}", file=sys.stderr)
        sys.exit(1)
