"""
Elección del instalador en Windows (core/updater.py).

En Windows el update ES el instalador Inno de una release, y ese .exe lo
compila un runner aparte (build-windows.yml): puede faltar en la release más
nueva porque el workflow falló o porque se publicó con SKIP_WINDOWS=1. Antes
se miraba solo la última y esas releases dejaban a Windows sin actualización
y sin aviso, aunque la anterior sí servía para ponerlos al día.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core import updater


def release(build_id, assets, fecha):
    return {
        "tag_name": f"pyinstaller-v{build_id}",
        "created_at": fecha,
        "body": "",
        "assets": [
            {"name": n, "browser_download_url": f"https://x/{build_id}/{n}"} for n in assets
        ],
    }


SETUP = updater.SETUP_ASSET_NAME
FULL = updater.FULL_ASSET_NAME
UPDATE = updater.UPDATE_ASSET_NAME


def buscar(releases, local="0.9.8", windows=True):
    """check_for_update() contra una lista de releases de mentira, como si
    corriera en Windows (o en Linux con windows=False)."""
    original = (updater._fetch_releases, updater.IS_WINDOWS, updater.local_build_id)
    updater._fetch_releases = lambda: releases
    updater.IS_WINDOWS = windows
    updater.local_build_id = lambda _v: local
    try:
        return updater.check_for_update("v0.9.8")
    finally:
        updater._fetch_releases, updater.IS_WINDOWS, updater.local_build_id = original


def test_toma_el_instalador_de_la_mas_nueva():
    r = buscar([
        release("0.9.8", [FULL, SETUP], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL, SETUP], "2026-09-02T00:00:00Z"),
    ])
    assert r["mode"] == "setup"
    assert r["tag"] == "pyinstaller-v0.9.9"


def test_si_a_la_mas_nueva_le_falta_el_exe_cae_a_la_anterior():
    """El build de Windows falló en la última: la 0.9.9 igual los pone al día."""
    r = buscar([
        release("0.9.8", [FULL, SETUP], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL, SETUP], "2026-09-02T00:00:00Z"),
        release("1.0.0", [FULL], "2026-09-03T00:00:00Z"),
    ])
    assert r["tag"] == "pyinstaller-v0.9.9"
    assert r["url"].endswith(SETUP)


def test_sin_ningun_instalador_nuevo_no_ofrece_nada():
    """Nada que instalar es distinto de instalar algo viejo: no se retrocede
    a una release anterior a la que ya corre."""
    assert buscar([
        release("0.9.8", [FULL, SETUP], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL], "2026-09-02T00:00:00Z"),
    ]) is None


def test_sin_releases_nuevas_no_ofrece_nada():
    assert buscar([
        release("0.9.8", [FULL, SETUP], "2026-09-01T00:00:00Z"),
    ]) is None


def test_en_linux_el_instalador_no_cuenta():
    """La release nueva no trae paquete update, así que Linux baja el full;
    que tenga o no .exe de Windows no cambia nada."""
    r = buscar([
        release("0.9.8", [FULL, UPDATE], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL], "2026-09-02T00:00:00Z"),
    ], windows=False)
    assert r["mode"] == "full"
    assert r["tag"] == "pyinstaller-v0.9.9"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
