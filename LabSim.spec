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
    # scipy ya no es dependencia (core/dsp.py), pero si esta instalado en el
    # entorno pyqtgraph lo arrastra: solo lo usa en affineSlice con
    # interpolacion de orden > 1, que la app no llama. Son ~70 MB.
    excludes=['scipy'],
    noarchive=False,
    optimize=0,
)

# --- Recorte de Qt -----------------------------------------------------------
# El hook de PySide6 mete todos los plugins de Qt y cada uno arrastra sus libs.
# Estos no los usa la app (todo es Widgets, estilo Fusion forzado, sin PDF ni
# teclado virtual) y sacarlos baja el build ~75 MB en Linux. Ver
# docs/decisiones.md, "Build más liviano".
#
# NO sacar: QtQuick/Qml (los importa libffmpegmediaplugin, el audio),
# QtMultimedia/FFmpeg, QtNetwork, QtOpenGL/QtSvg/QtTest (pyqtgraph), ni el
# plugin wayland (la distro del kiosko puede no tener XWayland).
import fnmatch
import os
from PyInstaller.depend.bindepend import get_imports

QT_DROP = [
    # tema GTK: arrastra GTK3, cairo, pango, harfbuzz y libxml2. La segunda
    # ICU (v78) que venia con libxml2 se queda: la usa _sqlite3
    '*plugins/platformthemes/*qgtk3.*',
    '*plugins/platforminputcontexts/*qtvirtualkeyboardplugin.*',
    '*plugins/imageformats/*qpdf.*',
    '*plugins/imageformats/*qtiff.*',
    '*plugins/imageformats/*qwebp.*',
    '*plugins/imageformats/*qicns.*',
    '*plugins/imageformats/*qtga.*',
    '*plugins/imageformats/*qwbmp.*',
    '*plugins/platforms/*qeglfs.*',
    '*plugins/platforms/*qlinuxfb.*',
    '*plugins/platforms/*qminimalegl.*',
    '*plugins/platforms/*qminimal.*',
    '*plugins/platforms/*qvnc.*',
    '*plugins/platforms/*qvkkhrdisplay.*',
    '*plugins/platforms/*qoffscreen.*',
    '*plugins/egldeviceintegrations/*',
    # la app no instala ningun QTranslator: los .qm no se leen nunca
    'PySide6/*translations/*',
]


def _qt_drop(dest):
    dest = dest.replace(os.sep, '/')
    return any(fnmatch.fnmatch(dest, p) for p in QT_DROP)


def _base(path):
    return os.path.basename(path.replace(os.sep, '/')).lower()


def prune_qt(binaries, datas):
    """Saca lo de QT_DROP y las libs que quedan sin nadie que las use.

    Solo se poda lo que colgaba de un plugin sacado (su clausura de
    dependencias): una lib que Qt abre con dlopen (FFmpeg, OpenSSL) no tiene
    importador y no hay que tocarla. Al final se verifica que nada de lo que
    queda importe algo que se saco, y si pasa el build se corta."""
    real = {d: s for d, s, t in binaries if t != 'SYMLINK'}
    imports = {d: {_base(n) for n, _ in get_imports(s)} for d, s in real.items()}
    by_base = {}
    for d in real:
        by_base.setdefault(_base(d), set()).add(d)

    removed = {d for d in real if _qt_drop(d)}

    candidates, stack = set(), list(removed)
    while stack:
        for name in imports[stack.pop()]:
            for d in by_base.get(name, ()):
                if d not in candidates and d not in removed:
                    candidates.add(d)
                    stack.append(d)

    changed = True
    while changed:
        changed = False
        used = set()
        for d in real:
            if d not in removed:
                used |= imports[d]
        for d in candidates - removed:
            if _base(d) not in used:
                removed.add(d)
                changed = True

    gone = {_base(d) for d in removed}
    alive = {_base(d) for d in real if d not in removed}
    for d in real:
        if d in removed:
            continue
        missing = (imports[d] & gone) - alive
        if missing:
            raise SystemExit(f'prune_qt: {d} necesita {sorted(missing)}, '
                             'que se saco. Revisar QT_DROP.')

    kept_bin = [e for e in binaries
                if e[0] not in removed and not (
                    e[2] == 'SYMLINK' and _base(e[0]) in gone - alive)]
    kept_dat = [e for e in datas if not _qt_drop(e[0])]
    print(f'prune_qt: fuera {len(binaries) - len(kept_bin)} binarios y '
          f'{len(datas) - len(kept_dat)} datos de Qt')
    return kept_bin, kept_dat


a.binaries, a.datas = prune_qt(a.binaries, a.datas)

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

# COLLECT deja en la raiz de _internal un symlink a cada lib de PySide6/Qt/lib,
# incluso a las que prune_qt saco: quedan colgando.
for root, _, files in os.walk(dist_dir):
    for name in files:
        path = os.path.join(root, name)
        if os.path.islink(path) and not os.path.exists(path):
            os.remove(path)

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
