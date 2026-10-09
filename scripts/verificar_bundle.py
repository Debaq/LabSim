#!/usr/bin/env python3
"""Arranca el build de Linux unos segundos y lista qué librerías cargó desde
fuera del dist (/proc/<pid>/maps). Sale con 1 si alguna no está en la lista
de lo que puede venir del sistema del equipo (ver LabSim.spec,
SISTEMA_PERMITIDO, y docs/decisiones.md, "Build encapsulado").

    scripts/verificar_bundle.py [dist/LabSim] [--plataforma xcb|wayland] [--segundos 12]

Necesita una sesión gráfica (xcb corre sobre XWayland). Solo stdlib.
"""
import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

# Lo que sí puede venir del sistema: glibc y sus módulos nss, el despachador
# GL (glvnd: elige el driver del equipo, aunque la app no usa GL) y
# libpipewire, que QtCore sondea y tiene que calzar con el daemon y los
# plugins spa del equipo.
PERMITIDO = re.compile(
    r"^(ld-linux-x86-64\.so\.2|lib(c|m|dl|pthread|rt|util|resolv|anl|crypt)\.so"
    r"|libnss_.*\.so|libGL(X|dispatch|ESv2)?\.so|libEGL\.so|libOpenGL\.so"
    r"|libpipewire-0\.3\.so)")


def _foto(dist):
    """{ruta: (tamaño, mtime)} de todo el dist."""
    foto = {}
    for root, dirs, files in os.walk(dist):
        for nombre in dirs + files:
            ruta = os.path.join(root, nombre)
            try:
                st = os.lstat(ruta)
            except OSError:
                continue
            foto[ruta] = (st.st_size, st.st_mtime_ns)
    return foto


def _limpiar(dist, antes):
    """La app escribe en el dist al arrancar (resources/local_cache): lo
    nuevo se borra para que no termine en el paquete de la versión."""
    despues = _foto(dist)
    for ruta in sorted(set(despues) - set(antes), key=len, reverse=True):
        if os.path.isdir(ruta) and not os.path.islink(ruta):
            shutil.rmtree(ruta, ignore_errors=True)
        elif os.path.lexists(ruta):
            os.remove(ruta)
    cambiados = [r for r in antes if r in despues and despues[r] != antes[r]
                 and not os.path.isdir(r)]
    for ruta in cambiados:
        print(f"  ojo: la app modificó {os.path.relpath(ruta, dist)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dist", nargs="?", default="dist/LabSim")
    ap.add_argument("--plataforma", default="xcb")
    ap.add_argument("--segundos", type=float, default=12)
    args = ap.parse_args()

    dist = os.path.realpath(args.dist)
    env = dict(os.environ, QT_QPA_PLATFORM=args.plataforma,
               LABSIM_DATA_DIR=tempfile.mkdtemp(prefix="labsim_verificar_"))
    antes = _foto(dist)
    proc = subprocess.Popen([os.path.join(dist, "LabSim")], cwd=dist, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(args.segundos)
        if proc.poll() is not None:
            print(f"LabSim terminó solo (código {proc.returncode}) antes de medir")
            return 2
        with open(f"/proc/{proc.pid}/maps") as f:
            rutas = {line.split()[-1] for line in f
                     if re.search(r"\.so(\.\d|$)", line.split()[-1])}
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        _limpiar(dist, antes)

    de_afuera = sorted(r for r in rutas if not r.startswith(dist + "/"))
    malas = [r for r in de_afuera if not PERMITIDO.match(os.path.basename(r))]
    print(f"{len(rutas)} librerías cargadas, {len(de_afuera)} del sistema "
          f"({args.plataforma}):")
    for r in de_afuera:
        print(("  NO  " if r in malas else "  ok  ") + r)
    if malas:
        print("Hay librerías del sistema que deberían venir en el dist.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
