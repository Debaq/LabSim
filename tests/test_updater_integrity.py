"""
La versión instalada tiene que ser la que dice ser (core/updater.py).

Una docente reportó que la logoaudiometría seguía fallando "después de
actualizar". El BUILD_VERSION decía rde8b2be pero el sha256 del ejecutable
era el de rca161de: el swap había copiado a medias y el script viejo
escribía la versión igual. Peor, como el updater compara contra
BUILD_VERSION, esa instalación ya nunca volvía a ver una actualización:
quedaba clavada corriendo código viejo con etiqueta nueva.

Ahora, cuando no hay nada más nuevo que ofrecer, se comprueba el sha256 del
ejecutable contra el manifest de su propia release (una sola vez por
build_id) y, si no coincide, se ofrece reinstalar el paquete completo.
"""

import hashlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core import updater

FULL = updater.FULL_ASSET_NAME
UPDATE = updater.UPDATE_ASSET_NAME
MANIFEST = updater.MANIFEST_ASSET_NAME
SETUP = updater.SETUP_ASSET_NAME


def release(build_id, assets, fecha):
    return {
        "tag_name": f"pyinstaller-v{build_id}",
        "created_at": fecha,
        "body": "",
        "assets": [
            {"name": n, "browser_download_url": f"https://x/{build_id}/{n}"} for n in assets
        ],
    }


class _FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def buscar(releases, exe_bytes, manifest_exe_sha, local="0.9.8", windows=False,
           marker=None, manifest_falla=False):
    """check_for_update() con un dist de mentira: `exe_bytes` es el LabSim
    instalado y `manifest_exe_sha` lo que el manifest de la release dice que
    debería ser. Devuelve (resultado, contenido_de_la_marca)."""
    with tempfile.TemporaryDirectory() as tmp:
        dist = Path(tmp)
        (dist / "LabSim").write_bytes(exe_bytes)
        if marker is not None:
            m = dist / updater.VERIFY_MARKER
            m.parent.mkdir(parents=True, exist_ok=True)
            m.write_text(marker, encoding="utf-8")

        def fake_urlopen(req, timeout=None):
            if manifest_falla:
                raise OSError("sin red")
            return _FakeResp(json.dumps({"files": {"LabSim": manifest_exe_sha}}).encode())

        original = (updater._fetch_releases, updater.IS_WINDOWS,
                    updater.local_build_id, updater._dist_dir, updater.urlopen,
                    updater._ultimo_build_feed)
        updater._fetch_releases = lambda: releases
        updater._ultimo_build_feed = lambda: None     # sin atajo: va a la API
        updater.IS_WINDOWS = windows
        updater.local_build_id = lambda _v: local
        updater._dist_dir = lambda: dist
        updater.urlopen = fake_urlopen
        try:
            r = updater.check_for_update("v0.9.8")
        finally:
            (updater._fetch_releases, updater.IS_WINDOWS, updater.local_build_id,
             updater._dist_dir, updater.urlopen, updater._ultimo_build_feed) = original
        marca = dist / updater.VERIFY_MARKER
        return r, (marca.read_text(encoding="utf-8") if marca.is_file() else None)


SANO = b"binario de la release"
SHA_SANO = hashlib.sha256(SANO).hexdigest()
VIEJO = b"binario viejo que quedo de un swap a medias"

UNA = [release("0.9.8", [FULL, UPDATE, MANIFEST], "2026-09-01T00:00:00Z")]


def test_instalacion_sana_no_molesta_y_deja_la_marca():
    r, marca = buscar(UNA, SANO, SHA_SANO)
    assert r is None
    assert marca == "0.9.8"


def test_ejecutable_que_no_es_el_de_su_release_ofrece_reinstalar():
    r, marca = buscar(UNA, VIEJO, SHA_SANO)
    assert r is not None, "una instalación a medias tiene que avisar"
    assert r["repair"] is True
    assert r["mode"] == "full"
    assert r["url"].endswith(FULL)
    assert marca is None, "no se marca como verificada una instalación rota"


def test_en_windows_la_reparacion_es_el_instalador():
    r, _ = buscar([release("0.9.8", [FULL, SETUP, MANIFEST], "2026-09-01T00:00:00Z")],
                  VIEJO, SHA_SANO, windows=True)
    assert r["mode"] == "setup"
    assert r["url"].endswith(SETUP)


def test_con_la_marca_puesta_no_se_vuelve_a_comprobar():
    """La comprobación es una sola vez por build_id: no se baja el manifest
    ni se hashea el ejecutable en cada arranque."""
    r, _ = buscar(UNA, VIEJO, SHA_SANO, marker="0.9.8", manifest_falla=True)
    assert r is None


def test_marca_de_otra_version_no_sirve():
    r, _ = buscar(UNA, VIEJO, SHA_SANO, marker="0.9.7")
    assert r is not None and r["repair"] is True


def test_sin_red_no_se_inventa_nada():
    """No se puede comprobar: se sigue como si estuviera todo bien, no se
    le tira un diálogo de reparación a quien está sin internet."""
    r, marca = buscar(UNA, VIEJO, SHA_SANO, manifest_falla=True)
    assert r is None
    assert marca is None


def test_si_hay_algo_mas_nuevo_eso_manda():
    """Con una release nueva disponible no se comprueba integridad: el
    update normal ya va a reemplazar el ejecutable igual."""
    releases = UNA + [release("0.9.9", [FULL, UPDATE, MANIFEST], "2026-09-02T00:00:00Z")]
    r, _ = buscar(releases, VIEJO, SHA_SANO)
    assert r["tag"] == "pyinstaller-v0.9.9"
    assert not r.get("repair")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
