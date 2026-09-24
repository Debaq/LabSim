"""Guardado automático de los informes de examen durante la atención.

Antes el informe de cada módulo (ABR, AABR, EOA, VEMP, Otoscopia) se subía
UNA vez, al cerrar la atención. Todo lo anterior vivía solo en memoria: si
la app se cerraba, se caía o el alumno atendía a otro paciente sin cerrar,
las curvas se perdían y el docente no tenía nada que revisar.

Ahora, mientras la atención está abierta, cada módulo se sube solo:
- cada INTERVALO_MS, si cambió algo desde la última subida;
- al esconder la ventana del módulo;
- al cerrar la app o la sesión (esto sincrónico, ver MainWindow).

El backend lo permite: mientras la atención siga 'atendiendo' el informe es
un upsert libre (ver report_upload.php).

Contrato con los módulos: `report_job()` devuelve None (nada que subir) o
un dict {appointment_id, tipo, data, images}, donde `images` es un callable
que exporta los JPEG y devuelve {sufijo: ruta}. Las imágenes se exportan
solo si `data` cambió: exportar los gráficos cuesta y no hace falta cada 30
segundos si el alumno no tocó nada.
"""

import hashlib
import json
import os
import shutil
import tempfile

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot

from core.base import context
from core.helpers import Preferences


INTERVALO_MS = 30_000


def _client():
    from backend.client import BackendClient
    return BackendClient(Preferences().get("BACKEND_URL"),
                         context.get_resource("json/session.json"))


def huella(job) -> str:
    """Identifica el contenido de un informe: si no cambió, no se resube."""
    crudo = json.dumps([job["appointment_id"], job["tipo"], job["data"]],
                       sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.blake2b(crudo.encode("utf-8"), digest_size=16).hexdigest()


def subir(job, client=None) -> None:
    """Sube un informe en el hilo que llama. Lanza si falla."""
    client = client if client is not None else _client()
    if not client.is_logged_in():
        raise RuntimeError("no hay sesión con el servidor")
    client.upload_report(int(job["appointment_id"]), job["tipo"], job["data"],
                         job.get("images_listas") or {})


class _Subida(QThread):
    # (hilo, ok, error). Se conecta a un método de ReportAutosave, que vive
    # en el hilo principal: así el aviso llega encolado allá. Con una lambda
    # corría en ESTE hilo, que terminaba borrándose a sí mismo.
    terminada = Signal(object, bool, str)

    def __init__(self, job, clave, huella_job, carpeta, parent=None):
        super().__init__(parent)
        self.job = job
        self.clave = clave
        self.huella = huella_job
        self.carpeta = carpeta

    def run(self):
        try:
            subir(self.job)
        except Exception as exc:  # noqa: BLE001 -- best-effort, se reintenta
            self.resultado = (False, str(exc))
        else:
            self.resultado = (True, "")
        self.terminada.emit(self, *self.resultado)


class _Recuperacion(QThread):
    """Trae lo ya guardado de una cita (my_report.php) fuera del hilo de UI."""
    lista = Signal(object, object)   # appointment_id, [informes]

    def __init__(self, appointment_id, tipos, parent=None):
        super().__init__(parent)
        self.appointment_id = appointment_id
        self.tipos = tipos

    def run(self):
        try:
            client = _client()
            informes = client.get_my_report(self.appointment_id, self.tipos) \
                if client.is_logged_in() else []
        except Exception as exc:  # noqa: BLE001 -- sin red se atiende igual
            print(f"autosave: no se pudo recuperar lo guardado: {exc}")
            informes = []
        self.lista.emit(self.appointment_id, informes)


class _Reparto(QObject):
    """Le da a cada módulo lo recuperado (ver ReportAutosave.recuperar)."""

    def __init__(self, destinos, sigue_vigente, parent=None):
        super().__init__(parent)
        self.destinos = destinos
        self.sigue_vigente = sigue_vigente

    @Slot(object, object)
    def repartir(self, cita, informes):
        if not self.sigue_vigente(cita):
            return
        vistos = set()
        for informe in informes:   # el más nuevo primero
            tipo = informe.get("tipo")
            modulo = self.destinos.get(tipo)
            data = informe.get("data")
            if modulo is None or tipo in vistos or not isinstance(data, dict):
                continue
            vistos.add(tipo)
            try:
                modulo.restore_report(data)
            except Exception as exc:  # noqa: BLE001 -- uno no frena a los demás
                print(f"autosave: no se pudo recuperar {tipo}: {exc}")


class ReportAutosave(QObject):
    """Sube los informes de los módulos de examen mientras dura la atención.

    `modulos`: callable que devuelve los widgets de examen vigentes (los
    que tienen report_job). Es un callable porque MainWindow los recrea al
    loguearse.
    """

    def __init__(self, modulos, parent=None):
        super().__init__(parent)
        self._modulos = modulos
        self._huellas = {}      # (appointment_id, tipo) -> huella subida
        self._hilos = {}        # (appointment_id, tipo) -> _Subida en curso
        self._timer = QTimer(self)
        self._timer.setInterval(INTERVALO_MS)
        self._timer.timeout.connect(self.guardar)

    def iniciar(self):
        """Arranca con una atención nueva: se olvida lo subido antes."""
        self._huellas.clear()
        self._timer.start()

    def detener(self):
        self._timer.stop()
        self.esperar()

    def esperar(self):
        """Espera a que terminen las subidas en curso. Se llama antes de la
        subida final (cierre de atención): si una subida vieja terminara
        después, pisaría el informe final con uno anterior."""
        for hilo in list(self._hilos.values()):
            hilo.wait(35_000)
            # El aviso de fin quedó encolado: se procesa ya, así la huella
            # queda al día antes de la subida final.
            self._terminada(hilo, *getattr(hilo, "resultado", (False, "sin terminar")))

    def guardar(self, modulo=None):
        """Sube en segundo plano lo que haya cambiado (uno o todos)."""
        for m in ([modulo] if modulo is not None else self._modulos()):
            try:
                job = m.report_job()
            except Exception as exc:  # noqa: BLE001 -- un módulo no frena a los demás
                print(f"autosave: {type(m).__name__}: {exc}")
                continue
            if job is None:
                continue
            clave = (job["appointment_id"], job["tipo"])
            if clave in self._hilos:
                continue  # sigue subiendo la anterior; el próximo tick va
            h = huella(job)
            if self._huellas.get(clave) == h:
                continue
            carpeta = tempfile.mkdtemp(prefix="labsim_informe_")
            job["images_listas"] = self._copiar_imagenes(job, carpeta)
            hilo = _Subida(job, clave, h, carpeta, self)
            self._hilos[clave] = hilo
            hilo.terminada.connect(self._terminada)
            hilo.start()

    def recuperar(self, appointment_id, destinos, sigue_vigente):
        """Retomar la atención: pide lo ya guardado de esa cita y se lo da a
        cada módulo (`destinos`: {tipo: módulo con restore_report}).

        `sigue_vigente(appointment_id)`: si el alumno ya cerró o cambió de
        atención cuando llega la respuesta, no se toca nada.
        """
        reparto = _Reparto(destinos, sigue_vigente, self)
        hilo = _Recuperacion(appointment_id, list(destinos), self)
        # A un método de un QObject del hilo principal: el aviso llega
        # encolado allá, no en el hilo de la consulta.
        hilo.lista.connect(reparto.repartir)
        hilo.finished.connect(hilo.deleteLater)
        hilo.finished.connect(reparto.deleteLater)
        hilo.start()
        return hilo

    def olvidar(self, appointment_id, tipo):
        """La subida final ya se hizo a mano: que el próximo tick no crea
        que hay algo nuevo."""
        self._huellas.pop((appointment_id, tipo), None)

    def marcar_subido(self, job):
        self._huellas[(job["appointment_id"], job["tipo"])] = huella(job)

    @staticmethod
    def _copiar_imagenes(job, carpeta):
        """Copia las imágenes a una carpeta propia de esta subida: los
        módulos exportan siempre al mismo archivo y la próxima exportación
        lo pisaría mientras este hilo lo está mandando."""
        rutas = {}
        exportar = job.get("images")
        if not callable(exportar):
            return rutas
        for sufijo, ruta in (exportar() or {}).items():
            destino = os.path.join(carpeta, f"{sufijo}.jpg")
            try:
                shutil.copyfile(ruta, destino)
            except OSError:
                continue
            rutas[sufijo] = destino
        return rutas

    def _terminada(self, hilo, ok, err):
        # Puede llegar dos veces: desde esperar() y por la señal encolada.
        if self._hilos.get(hilo.clave) is not hilo:
            return
        del self._hilos[hilo.clave]
        shutil.rmtree(hilo.carpeta, ignore_errors=True)
        hilo.deleteLater()
        if ok:
            self._huellas[hilo.clave] = hilo.huella
        else:
            print(f"autosave: no se pudo subir {hilo.clave[1]}: {err}")


def subir_ahora(job, client=None) -> tuple[bool, str]:
    """Subida sincrónica de un job (cierre de atención, cierre de la app).
    Las imágenes se exportan acá mismo. `client`: el BackendClient del
    módulo que llama (None = uno nuevo)."""
    exportar = job.get("images")
    job = dict(job)
    # Una imagen que no se pudo exportar no tira abajo el informe entero.
    job["images_listas"] = {k: v for k, v in (exportar() if callable(exportar) else {}).items()
                            if os.path.isfile(v)}
    try:
        subir(job, client)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    return True, ""
