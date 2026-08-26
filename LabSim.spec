# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LabSim',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LabSim',
)

import os
import subprocess

dist_dir = os.path.join(DISTPATH, 'LabSim')

run_sh = os.path.join(dist_dir, 'run.sh')
with open(run_sh, 'w') as f:
    f.write('#!/bin/bash\ncd "$(dirname "$0")"\n./LabSim\n')
os.chmod(run_sh, 0o755)

# COLLECT bundles datas under _internal/, but base.py's context.get_resource()
# resolves 'resources/...' relative to cwd (dist_dir), so it must live
# top-level next to the exe, not inside _internal. rsync keeps rebuilds fast
# by only copying changed files.
subprocess.run(
    ['rsync', '-a', '--delete', os.path.join(SPECPATH, 'resources') + '/',
     os.path.join(dist_dir, 'resources') + '/'],
    check=True,
)
