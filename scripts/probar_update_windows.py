#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba de punta a punta del update de Windows, en el runner de
build-windows.yml, antes de subir nada a la release.

Instala la release anterior tal cual se publico (su instalador completo) y
la actualiza con lo recien compilado por el mismo camino que la app:
core.updater.preparar_windows + lanzar_windows (aplicar.cmd). Comprueba:

- delta: la instalacion queda igual, archivo por archivo, al
  manifest-windows.json nuevo; lo borrado en esta version ya no esta; y
  correrlo de nuevo sobre la version ya nueva se niega (base equivocada),
  deja FALLO y no toca nada.
- completo: lo mismo desde la anterior (salvo lo que sobra: el completo no
  borra), con un LabSim "abierto" (el mutex tomado): el instalador tiene que
  esperar a que se suelte en vez de copiar encima.

Que la app vuelva a abrirse al final solo se avisa, no se exige.

Si el delta no pasa se borra su .exe (el cliente cae al completo) y se
avisa; si el completo no pasa sale con 1 y el build falla.
"""
import argparse
import ctypes
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import winreg
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from core import updater  # noqa: E402

CLAVE = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\{9EBD5A50-4B31-4855-B38A-E8CFBA118B6F}_is1"
EXCLUIDOS = ("resources/local_cache/", "resources/json/session.json")


def carpeta_instalada() -> Path:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE) as k:
        return Path(winreg.QueryValueEx(k, "InstallLocation")[0])


def version_instalada() -> str:
    try:
        return (carpeta_instalada() / "BUILD_VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def matar_labsim():
    subprocess.run(["taskkill", "/F", "/IM", "LabSim.exe"], capture_output=True)


def labsim_corriendo() -> bool:
    salida = subprocess.run(["tasklist", "/FI", "IMAGENAME eq LabSim.exe"],
                            capture_output=True, text=True).stdout
    return "LabSim.exe" in salida


def instalar_anterior(setup: Path, esperado: str, logs: Path):
    matar_labsim()
    rc = subprocess.run([str(setup), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
                         f"/LOG={logs / 'anterior.log'}"]).returncode
    if rc != 0 or version_instalada() != esperado:
        raise SystemExit(f"no se pudo instalar la release anterior (rc={rc}, "
                         f"BUILD_VERSION={version_instalada()!r}, esperado {esperado!r})")
    print(f"instalada la anterior {esperado} en {carpeta_instalada()}")


def diferencias(manifest: dict, anterior: dict | None) -> list:
    base = carpeta_instalada()
    problemas = []
    for rel, h in manifest["files"].items():
        ruta = base / rel
        if not ruta.is_file():
            problemas.append(f"falta {rel}")
        elif hashlib.sha256(ruta.read_bytes()).hexdigest() != h:
            problemas.append(f"distinto {rel}")
    for rel in (anterior or {}).get("files", {}):
        if rel not in manifest["files"] and not rel.startswith(EXCLUIDOS) and (base / rel).exists():
            problemas.append(f"sobra {rel}")
    return problemas


def correr(setup: Path, logs: Path, nombre: str, mutex_s: float = 0):
    """aplicar.cmd con `setup` como unico paso, como lo lanza la app. Con
    mutex_s, sostiene el mutex de LabSim ese tiempo y devuelve tambien la
    version que habia instalada mientras tanto (el instalador no tiene que
    haber copiado nada aun)."""
    carpeta = Path(tempfile.mkdtemp(prefix=f"prueba_{nombre}_", dir=logs))
    exe = carpeta_instalada() / "LabSim.exe"
    durante = None
    handle = None
    if mutex_s:
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateMutexW.restype = ctypes.c_void_p
        k32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        k32.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = k32.CreateMutexW(None, False, updater.MUTEX_NAME)
    script = updater.preparar_windows(carpeta, [setup])
    proc = updater.lanzar_windows(script, exe)
    if handle:
        time.sleep(mutex_s * 0.75)
        durante = version_instalada()
        time.sleep(mutex_s * 0.25)
        k32.CloseHandle(handle)
    rc = proc.wait(timeout=1200)
    for log in sorted(carpeta.glob("*.log")):
        print(f"--- {nombre}/{log.name}")
        print("\n".join(log.read_text(encoding="utf-8-sig", errors="replace").splitlines()[-25:]))
    return rc, carpeta, durante


def avisar_si_no_relanzo(quien: str):
    """Solo aviso: que la app abra en el runner (sin usuario, sin red al
    backend) no depende del update, y un falso negativo aca no puede dejar
    a Windows sin version nueva."""
    for _ in range(30):
        if labsim_corriendo():
            return
        time.sleep(1)
    print(f"::warning::{quien} no volvio a abrir LabSim (o se cerro enseguida)")


def probar_delta(args, anterior_setup, manifest, anterior_manifest, logs) -> list:
    fallas = []
    instalar_anterior(anterior_setup, args.anterior_id, logs)
    rc, carpeta, _ = correr(args.delta, logs, "delta")
    if rc != 0 or (carpeta / "FALLO").exists():
        fallas.append(f"el delta salio con {rc}")
    if version_instalada() != args.build_id:
        fallas.append(f"tras el delta BUILD_VERSION={version_instalada()!r}")
    fallas += diferencias(manifest, anterior_manifest)[:20]
    avisar_si_no_relanzo("el delta")
    matar_labsim()

    # Mismo delta sobre la version ya nueva: tiene que negarse sin tocar nada
    # y volver a abrir el LabSim que habia.
    rc, carpeta, _ = correr(args.delta, logs, "delta_base_mala")
    if rc == 0 or not (carpeta / "FALLO").exists():
        fallas.append(f"el delta sobre otra base no se nego (rc={rc})")
    if version_instalada() != args.build_id or diferencias(manifest, None):
        fallas.append("el delta rechazado igual toco la instalacion")
    avisar_si_no_relanzo("tras el delta rechazado,")
    matar_labsim()
    return fallas


def probar_completo(args, anterior_setup, manifest, anterior_manifest, logs) -> list:
    fallas = []
    instalar_anterior(anterior_setup, args.anterior_id, logs)
    rc, carpeta, durante = correr(args.completo, logs, "completo", mutex_s=12)
    if durante != args.anterior_id:
        fallas.append(f"con LabSim abierto el instalador no espero (BUILD_VERSION={durante!r})")
    if rc != 0 or (carpeta / "FALLO").exists():
        fallas.append(f"el completo salio con {rc}")
    if version_instalada() != args.build_id:
        fallas.append(f"tras el completo BUILD_VERSION={version_instalada()!r}")
    # Sin `anterior`: el completo no sabe que borro esta version (solo el
    # delta trae esa lista), y lo que sobra de antes no estorba.
    fallas += diferencias(manifest, None)[:20]
    avisar_si_no_relanzo("el completo")
    matar_labsim()
    return fallas


def main():
    # La consola del runner es cp1252: un log del instalador con BOM o con un
    # carácter fuera de cp1252 tumbaba la prueba al imprimirlo (2026-10-30).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--anterior", required=True, help="tag de la release anterior")
    ap.add_argument("--build-id", required=True)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--completo", required=True, type=Path)
    ap.add_argument("--delta", type=Path)
    args = ap.parse_args()
    args.anterior_id = args.anterior[len(updater.TAG_PREFIX):]

    logs = Path(tempfile.mkdtemp(prefix="probar_update_"))
    bajadas = logs / "anterior"
    rc = subprocess.run(["gh", "release", "download", args.anterior, "-D", str(bajadas),
                         "-p", updater.SETUP_ASSET_NAME, "-p", "manifest-windows.json"]).returncode
    anterior_setup = bajadas / updater.SETUP_ASSET_NAME
    if rc != 0 and not anterior_setup.is_file():
        print(f"::warning::{args.anterior} no tiene instalador de Windows: no se puede probar el update")
        return 0
    anterior_manifest = None
    if (bajadas / "manifest-windows.json").is_file():
        anterior_manifest = json.loads((bajadas / "manifest-windows.json").read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    if args.delta and args.delta.is_file():
        fallas = probar_delta(args, anterior_setup, manifest, anterior_manifest, logs)
        if fallas:
            for f in fallas:
                print(f"delta: {f}")
            print("::warning::el instalador delta no paso la prueba: no se publica, "
                  "los clientes bajaran el completo")
            args.delta.unlink()
        else:
            print("delta: OK")

    fallas = probar_completo(args, anterior_setup, manifest, anterior_manifest, logs)
    for f in fallas:
        print(f"completo: {f}")
        print(f"::error::{f}")
    if not fallas:
        print("completo: OK")
    shutil.rmtree(bajadas, ignore_errors=True)
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
