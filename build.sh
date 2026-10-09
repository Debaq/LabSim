#!/bin/bash
set -e
cd "$(dirname "$0")"

eval "$(micromamba shell hook --shell bash)"
micromamba activate labsim

python -m PyInstaller LabSim.spec --noconfirm

# Que lo que carga la app venga del dist y no del sistema (ver
# docs/decisiones.md, "Build encapsulado"). Necesita sesión gráfica.
if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    python scripts/verificar_bundle.py dist/LabSim --plataforma xcb
else
    echo "verificar_bundle: sin sesión gráfica, no se verificó el build" >&2
fi
