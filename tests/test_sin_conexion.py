"""LabSim sin internet: no se cierra, no pierde lo hecho y deja reportarlo.

- Respaldo de informes en el equipo (core/respaldo_informes.py): lo que no
  llegó al servidor vuelve al retomar, y gana sobre lo del servidor.
- Hilos de red que sobreviven a su dueño (core/hilos.py): destruir un
  QThread corriendo abortaba el proceso entero.
- Registro rotado y su cola para el reporte (core/registro.py).
- Reportar un problema (core/soporte.py): nada sale sin aceptar.
"""

import gzip
import os
import sys
import tempfile
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["LABSIM_DATA_DIR"] = tempfile.mkdtemp(prefix="labsim_datos_")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import requests  # noqa: E402
import shiboken6  # noqa: E402
from PySide6.QtCore import QThread  # noqa: E402
from PySide6.QtWidgets import QWidget  # noqa: E402

from core.base import context  # noqa: E402  (crea la QApplication)
from core import hilos, registro, respaldo_informes as rp  # noqa: E402
from core import report_autosave as ra  # noqa: E402

APP = context.app


def _job(data, tipo="ABR", cita=42):
    return {"appointment_id": cita, "tipo": tipo, "data": data}


def _imagen(contenido=b"jpg"):
    carpeta = tempfile.mkdtemp()
    ruta = os.path.join(carpeta, "0.jpg")
    with open(ruta, "wb") as f:
        f.write(contenido)
    return {"0": ruta}


# -- respaldo -----------------------------------------------------------------

def test_lo_no_subido_vuelve_y_gana_al_servidor():
    job = _job({"curvas": {"R1": 80}})
    assert rp.guardar("u1", job, ra.huella(job), _imagen())
    servidor = [{"tipo": "ABR", "data": {"curvas": {"R1": 60}}}]
    mezcla = rp.mezclar("u1", 42, servidor, ["ABR", "ELECTROCOCLEO"])
    assert mezcla[0]["data"] == {"curvas": {"R1": 80}} and mezcla[0]["origen"] == "equipo"
    assert mezcla[1] == servidor[0]
    assert set(rp.imagenes("u1", 42, "ABR")) == {"0"}


def test_cada_alumno_ve_solo_lo_suyo():
    job = _job({"curvas": {"R1": 70}}, cita=43)
    rp.guardar("u1", job, ra.huella(job))
    assert rp.mezclar("u2", 43, []) == []


def test_lo_subido_deja_de_ganar():
    job = _job({"curvas": {"R1": 50}}, cita=44)
    rp.guardar("u1", job, ra.huella(job))
    rp.marcar("u1", 44, "ABR", ra.huella(job), "subido")
    assert rp.pendientes("u1", 44) == []


def test_un_respaldo_mas_nuevo_sigue_pendiente():
    viejo = _job({"curvas": {"R1": 50}}, cita=45)
    nuevo = _job({"curvas": {"R1": 55}}, cita=45)
    rp.guardar("u1", viejo, ra.huella(viejo))
    rp.guardar("u1", nuevo, ra.huella(nuevo))
    rp.marcar("u1", 45, "ABR", ra.huella(viejo), "subido")   # llegó tarde el viejo
    assert [r["data"] for r in rp.pendientes("u1", 45)] == [{"curvas": {"R1": 55}}]


def test_respaldar_con_imagenes_de_su_propia_carpeta():
    """Una prueba del ABR recuperada del equipo se vuelve a respaldar con
    las imágenes que ya estaban ahí: no se pueden borrar antes de copiarlas."""
    job = _job({"curvas": {"R1": 40}}, tipo="ELECTROCOCLEO", cita=46)
    rp.guardar("u1", job, ra.huella(job), _imagen(b"curva"))
    propias = rp.imagenes("u1", 46, "ELECTROCOCLEO")
    rp.guardar("u1", job, ra.huella(job), propias)
    ruta = rp.imagenes("u1", 46, "ELECTROCOCLEO")["0"]
    assert open(ruta, "rb").read() == b"curva"


def test_podar_no_toca_lo_pendiente():
    pend = _job({"x": 1}, cita=47)
    sub = _job({"x": 2}, tipo="VEMP", cita=47)
    rp.guardar("u1", pend, ra.huella(pend))
    rp.guardar("u1", sub, ra.huella(sub))
    rp.marcar("u1", 47, "VEMP", ra.huella(sub), "subido")
    rp.podar(dias=-1)   # todo es "viejo"
    assert [r["tipo"] for r in rp.pendientes("u1", 47)] == ["ABR"]
    assert rp.imagenes("u1", 47, "VEMP") == {}


class _Cliente:
    user = {"id": 9}

    def __init__(self, falla=None):
        self.falla = falla
        self.subidos = []

    def is_logged_in(self):
        return True

    def upload_report(self, cita, tipo, data, imagenes):
        if self.falla is not None:
            raise self.falla
        self.subidos.append((cita, tipo, data, sorted(imagenes)))


def test_subir_ahora_sin_red_queda_en_el_equipo():
    job = dict(_job({"curvas": {"R1": 30}}, cita=50), images=lambda: _imagen())
    ok, _ = ra.subir_ahora(job, _Cliente(requests.ConnectionError("sin red")))
    assert not ok
    assert [r["data"] for r in rp.pendientes("9", 50)] == [{"curvas": {"R1": 30}}]
    # Vuelve la red: al cerrar la atención se sube lo que quedó.
    cliente = _Cliente()
    ok, _ = ra.subir_pendientes(50, cliente)
    assert ok and cliente.subidos == [(50, "ABR", {"curvas": {"R1": 30}}, ["0"])]
    assert rp.pendientes("9", 50) == []


def test_atencion_cerrada_no_queda_pendiente_para_siempre():
    job = _job({"curvas": {"R1": 20}}, cita=51)
    respuesta = requests.Response()
    respuesta.status_code = 409
    ok, _ = ra.subir_ahora(job, _Cliente(requests.HTTPError("cerrada", response=respuesta)))
    assert not ok and rp.pendientes("9", 51) == []


# -- hilos ----------------------------------------------------------------------

class _Lento(QThread):
    def run(self):
        time.sleep(0.4)


def test_borrar_al_dueno_de_un_hilo_corriendo_no_aborta():
    dueno = QWidget()
    hilo = _Lento(dueno)
    hilo.start()
    hilos.soltar_hijos(dueno)
    # Sin soltar_hijos esto aborta el proceso entero: "QThread: Destroyed
    # while thread is still running".
    shiboken6.delete(dueno)
    del dueno
    assert hilo in hilos._sueltos
    hilo.wait(3000)
    APP.processEvents()
    assert hilo not in hilos._sueltos


def test_soltar_un_hilo_terminado_no_hace_nada():
    hilo = _Lento()
    hilo.start()
    hilo.wait(3000)
    hilos.soltar(hilo)
    assert hilo not in hilos._sueltos


# -- registro ---------------------------------------------------------------------

def test_registro_rota_al_pasar_el_tope():
    carpeta = tempfile.mkdtemp()
    from pathlib import Path
    ruta = Path(carpeta) / "labsim.log"
    ruta.write_bytes(b"x" * 100)
    registro.rotar(ruta, max_bytes=50, copias=2)
    assert not ruta.exists() and (Path(carpeta) / "labsim.1.log").read_bytes() == b"x" * 100
    ruta.write_bytes(b"y" * 100)
    registro.rotar(ruta, max_bytes=50, copias=2)
    assert (Path(carpeta) / "labsim.2.log").read_bytes() == b"x" * 100


def test_la_cola_trae_lo_ultimo():
    original = registro.archivo
    carpeta = tempfile.mkdtemp()
    from pathlib import Path
    ruta = Path(carpeta) / "labsim.log"
    (Path(carpeta) / "labsim.1.log").write_bytes(b"antes\n")
    ruta.write_bytes(b"0123456789")
    registro.archivo = lambda: ruta
    try:
        assert registro.cola(4) == b"6789"
        assert registro.cola(100) == b"antes\n0123456789"
    finally:
        registro.archivo = original


# -- reportar un problema ------------------------------------------------------------

def test_no_se_envia_sin_aceptar():
    from core.soporte import PaginaSoporte
    pagina = PaginaSoporte()
    assert not pagina.btn_enviar.isEnabled()
    pagina._enviar()
    assert pagina._envio is None
    pagina.chk_acepto.setChecked(True)
    assert pagina.btn_enviar.isEnabled()


def test_el_reporte_lleva_el_registro_comprimido():
    from backend import client as cliente_mod
    from core import soporte
    enviados = []

    class Falso:
        def __init__(self, *a):
            pass

        def is_logged_in(self):
            return True

        def send_ticket(self, descripcion, equipo_info, detalle, log_gz):
            enviados.append((descripcion, gzip.decompress(log_gz) if log_gz else b""))
            return {"id": 12}

    original = cliente_mod.BackendClient
    original_cola = registro.cola
    cliente_mod.BackendClient = Falso
    registro.cola = lambda *a: b"linea del registro\n"
    try:
        pagina = soporte.PaginaSoporte()
        pagina.txt_descripcion.setPlainText("se cerró sin internet")
        pagina.chk_acepto.setChecked(True)
        pagina._enviar()
        for _ in range(100):
            APP.processEvents()
            if pagina._envio is None:
                break
            time.sleep(0.02)
        assert enviados == [("se cerró sin internet", b"linea del registro\n")], enviados
        assert "#12" in pagina.lbl_estado.text()
        assert not pagina.chk_acepto.isChecked()   # el siguiente se vuelve a aceptar
    finally:
        cliente_mod.BackendClient = original
        registro.cola = original_cola


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {nombre}")
            except AssertionError as exc:
                fallas += 1
                print(f"FAIL {nombre}: {exc!r}")
    sys.exit(1 if fallas else 0)
