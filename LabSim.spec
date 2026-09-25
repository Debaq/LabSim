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
    # setuptools se saca despues del analisis (ver VENDORED_DROP).
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
import subprocess
import sys
from PyInstaller.depend.bindepend import get_imports

QT_DROP = [
    # tema GTK: arrastra GTK3, cairo, pango, harfbuzz y libxml2
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
    # segunda ICU (v78, ~38 MB): la pide la libsqlite3 del env conda, pero
    # PyInstaller empaqueta la de /usr/lib, que no usa ICU. Qt trae la suya
    # (v73). Si alguna lib que queda la necesitara, prune_qt corta el build.
    'libicu*.so.78*',
]


def _qt_drop(dest):
    dest = dest.replace(os.sep, '/')
    return any(fnmatch.fnmatch(dest, p) for p in QT_DROP)


def _needed(path):
    """Libs que ESTE binario pide (NEEDED), sin seguir la cadena.

    get_imports() en Linux es ldd: transitivo y resuelto contra el env de
    build. Ahi _sqlite3 -> libsqlite3 de conda -> ICU 78, pero la libsqlite3
    que se empaqueta es la de /usr/lib, que no usa ICU, y el chequeo de
    abajo cortaba el build por una ICU que nadie carga. Con lo directo de
    cada lib empaquetada el chequeo mira lo que de verdad hay en el dist."""
    if sys.platform.startswith('linux'):
        out = subprocess.run(['objdump', '-p', path], capture_output=True,
                             text=True).stdout
        return {line.split()[1] for line in out.splitlines()
                if line.strip().startswith('NEEDED')}
    return {n for n, _ in get_imports(path)}


def _base(path):
    return os.path.basename(path.replace(os.sep, '/')).lower()


def prune_qt(binaries, datas):
    """Saca lo de QT_DROP y las libs que quedan sin nadie que las use.

    Solo se poda lo que colgaba de un plugin sacado (su clausura de
    dependencias): una lib que Qt abre con dlopen (FFmpeg, OpenSSL) no tiene
    importador y no hay que tocarla. Al final se verifica que nada de lo que
    queda importe algo que se saco, y si pasa el build se corta."""
    real = {d: s for d, s, t in binaries if t != 'SYMLINK'}
    imports = {d: {_base(n) for n in _needed(s)} for d, s in real.items()}
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

# --- setuptools --------------------------------------------------------------
# urllib3 prueba `from backports import zstd` (opcional; en 3.14 usa
# compression.zstd) y el hook de PyInstaller para `backports` lo resuelve en
# el _vendor de setuptools: con eso entraba setuptools entero y un runtime
# hook que lo importa en cada arranque (~160 ms). La app no lo usa. No sirve
# ponerlo en excludes: el hook de backports hace un alias a setuptools y
# PyInstaller corta con "already imported as ExcludedModule".
VENDORED_DROP = ('setuptools', '_distutils_hack', 'pkg_resources',
                 'distutils', 'backports', 'jaraco', 'more_itertools')
a.pure = [e for e in a.pure if e[0].split('.')[0] not in VENDORED_DROP]
a.scripts = [e for e in a.scripts if e[0] != 'pyi_rth_setuptools']
a.datas = [e for e in a.datas
           if e[0].replace(os.sep, '/').split('/')[0] not in VENDORED_DROP]

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

# El libpython del env conda viene con info de debug (29 de sus 34 MB) y las
# extensiones de lib-dynload tambien: ~40 MB que no sirven en el equipo del
# alumno. Solo --strip-debug (quedan los simbolos de enlace) y solo en estos
# archivos: el strip=True de PyInstaller pasa por todas las libs, y las de
# numpy.libs (retocadas con patchelf por auditwheel) se pueden romper.
if sys.platform.startswith('linux') and shutil.which('strip'):
    import glob
    internal = os.path.join(dist_dir, '_internal')
    to_strip = [p for p in
                glob.glob(os.path.join(internal, 'libpython3*.so*')) +
                glob.glob(os.path.join(internal, 'python3*', 'lib-dynload',
                                       '*.so'))
                if not os.path.islink(p)]
    subprocess.run(['strip', '--strip-debug', *to_strip], check=True)
    print(f'strip: --strip-debug en {len(to_strip)} archivos')

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
