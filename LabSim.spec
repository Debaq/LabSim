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
    icon='icons/Icon.ico',
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
import shutil
import sys

dist_dir = os.path.join(DISTPATH, 'LabSim')

if sys.platform != 'win32':
    run_sh = os.path.join(dist_dir, 'run.sh')
    with open(run_sh, 'w') as f:
        f.write('#!/bin/bash\ncd "$(dirname "$0")"\n./LabSim\n')
    os.chmod(run_sh, 0o755)

# COLLECT bundles datas under _internal/, but base.py's context.get_resource()
# resolves 'resources/...' relative to cwd (dist_dir), so it must live
# top-level next to the exe, not inside _internal. shutil.copytree (not rsync,
# which isn't available on Windows runners) keeps this build portable.
# Los caches de audio (_generated, _panned) se rehacen solos en runtime dentro
# del dist, asi que no tiene sentido copiarlos y engordar el build.
resources_dst = os.path.join(dist_dir, 'resources')
if os.path.isdir(resources_dst):
    shutil.rmtree(resources_dst)
shutil.copytree(
    os.path.join(SPECPATH, 'resources'),
    resources_dst,
    ignore=shutil.ignore_patterns('_generated', '_panned'),
)
