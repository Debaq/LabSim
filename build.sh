#!/bin/bash
set -e
cd "$(dirname "$0")"

eval "$(micromamba shell hook --shell bash)"
micromamba activate labsim

python -m PyInstaller LabSim.spec --noconfirm
