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

Antes de cada subida el informe se escribe en el disco del equipo (ver
core/respaldo_informes.py): sin red la subida falla, pero si la app se
cierra lo hecho no se pierde. Al retomar, lo que quedó sin subir gana sobre
lo del servidor, y el próximo tick lo sube.

Contrato con los módulos: `report_job()` devuelve None (nada que subir) o
un dict {appointment_id, tipo, data, images}, donde `images` es un callable
que exporta los JPEG y devuelve {sufijo: ruta}. Un módulo que sube más de un
informe por atención (el ABR: un ABR y un ECochG) expone además
`report_jobs()`, con la lista entera. Las imágenes se exportan
solo si `data` cambió: exportar los gráficos cuesta y no hace falta cada 30
segundos si el alumno no tocó nada.
"""

import hashlib
import json
import os
import shutil
import tempfile

import requests

from PySide6.QtCore import QObject, QTimer

from core import hilos, respaldo_informes
from core.base import context
from core.helpers import Preferences


INTERVALO_MS = 30_000
# Respaldo en el disco de los datos (sin exportar gráficos), más seguido
# que la subida: un corte de luz pierde a lo sumo esto.
INTERVALO_DISCO_MS = 5_000


def _client():
    from backend.client import BackendClient
    return BackendClient(Preferences().get("BACKEND_URL"),
                         context.get_resource("json/session.json"))


def huella(job) -> str:
    """Identifica el contenido de un informe: si no cambió, no se resube."""
    crudo = json.dumps([job["appointment_id"], job["tipo"], job["data"]],
                       sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.blake2b(crudo.encode("utf-8"), digest_size=16).hexdigest()


def trabajos(modulo) -> list:
    """Los informes que un módulo tiene para subir (ver el contrato arriba)."""
    if hasattr(modulo, "report_jobs"):
        return list(modulo.report_jobs())
    job = modulo.report_job()
    return [] if job is None else [job]


def subir(job, client=None) -> None:
    """Sube un informe en el hilo que llama. Lanza si falla. Si llega, el
    respaldo del equipo con esa misma huella deja de estar pendiente."""
    client = client if client is not None else _client()
    if not client.is_logged_in():
        raise RuntimeError("no hay sesión con el servidor")
    usuario = respaldo_informes.usuario_de(client)
    # La versión del servidor sobre la que se armó: si allá hay otra (otro
    # equipo, o un retomar que no alcanzó a traer lo guardado), el
    # servidor aparta la que pisa en vez de perderla.
    registro = respaldo_informes.leer(usuario, job["appointment_id"], job["tipo"]) or {}
    try:
        respuesta = client.upload_report(int(job["appointment_id"]), job["tipo"], job["data"],
                                         job.get("images_listas") or {},
                                         version_base=registro.get("version") or 0)
    except requests.HTTPError as exc:
        if getattr(exc.response, "status_code", None) == 409:
            # Atención ya cerrada: el servidor no lo va a aceptar nunca.
            respaldo_informes.marcar(usuario, job["appointment_id"], job["tipo"],
                                     huella(job), "cerrada")
        raise
    version = (respuesta or {}).get("version") if isinstance(respuesta, dict) else None
    respaldo_informes.marcar(usuario, job["appointment_id"], job["tipo"],
                             huella(job), "subido", version=version)


class _Subida:
    """Una subida en curso del autoguardado (corre con hilos.en_fondo, sin
    QThread: ver los cierres del 2026-10-09 en core/hilos.py)."""

    def __init__(self, job, clave, huella_job, carpeta, modulo=None):
        self.job = job
        self.clave = clave
        self.huella = huella_job
        self.carpeta = carpeta
        self.modulo = modulo
        self.tarea = None


def _subir_resultado(job):
    """(ok, error) de subir(job); corre en el hilo de en_fondo."""
    try:
        subir(job)
    except Exception as exc:  # noqa: BLE001 -- best-effort, se reintenta
        return False, str(exc)
    return True, ""


def recuperar(appointment_id, tipos, client=None) -> list:
    """Lo guardado de una cita, el más nuevo primero: lo del servidor con lo
    del equipo delante (ver respaldo_informes.mezclar). Corre en el hilo
    que llama (red)."""
    servidor_ok = False
    informes = []
    try:
        client = client if client is not None else _client()
        if client.is_logged_in():
            informes = client.get_my_report(appointment_id, tipos)
            servidor_ok = True
    except Exception as exc:  # noqa: BLE001 -- sin red se atiende igual
        print(f"autosave: no se pudo recuperar lo guardado: {exc}")
    if client is None:
        client = _client()
    usuario = respaldo_informes.usuario_de(client)
    for informe in informes:
        respaldo_informes.anotar_del_servidor(usuario, appointment_id, informe)
    return respaldo_informes.mezclar(usuario, appointment_id, informes, tipos,
                                     servidor_ok=servidor_ok)


class _Reparto:
    """Le da a cada módulo lo recuperado (ver ReportAutosave.recuperar)."""

    def __init__(self, destinos, sigue_vigente):
        self.destinos = destinos
        self.sigue_vigente = sigue_vigente

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
        self._respaldadas = {}  # (appointment_id, tipo) -> (huella, quedó en el disco)
        self._hilos = {}        # (appointment_id, tipo) -> _Subida en curso
        self._en_disco = {}     # (appointment_id, tipo) -> huella de los datos en el disco
        self._timer = QTimer(self)
        self._timer.setInterval(INTERVALO_MS)
        self._timer.timeout.connect(self.guardar)
        self._timer_disco = QTimer(self)
        self._timer_disco.setInterval(INTERVALO_DISCO_MS)
        self._timer_disco.timeout.connect(self.respaldar)

    def iniciar(self):
        """Arranca con una atención nueva: se olvida lo subido antes."""
        self._huellas.clear()
        self._respaldadas.clear()
        self._en_disco.clear()
        for m in self._modulos():
            estado = getattr(m, "estado_informe", None)
            if estado is not None:
                estado.limpiar()
        self._timer.start()
        self._timer_disco.start()

    def detener(self):
        self._timer.stop()
        self._timer_disco.stop()
        self.esperar()

    def reanudar(self):
        """Vuelve a correr sin olvidar nada (la subida final falló y la
        atención sigue abierta)."""
        self._timer.start()
        self._timer_disco.start()

    def respaldar(self, con_imagenes=False):
        """Solo al disco, sin red: los datos de lo que cambió (y, con
        `con_imagenes`, también los gráficos). Rápido y nunca lanza: corre
        cada pocos segundos y antes de que el equipo se apague."""
        usuario = None
        for m in self._modulos():
            try:
                jobs = trabajos(m)
                for job in jobs:
                    if usuario is None:
                        usuario = respaldo_informes.usuario_de(_client())
                    clave = (job["appointment_id"], job["tipo"])
                    h = huella(job)
                    if con_imagenes:
                        if self._respaldadas.get(clave, (None,))[0] == h:
                            continue
                        exportar = job.get("images")
                        imagenes = exportar() if callable(exportar) else {}
                        self._respaldadas[clave] = (
                            h, respaldo_informes.guardar(usuario, job, h, imagenes or {}))
                        self._en_disco[clave] = h
                        continue
                    if self._en_disco.get(clave) == h or self._respaldadas.get(clave, (None,))[0] == h:
                        continue
                    if respaldo_informes.guardar(usuario, job, h):
                        self._en_disco[clave] = h
            except Exception as exc:  # noqa: BLE001 -- un módulo no frena a los demás
                print(f"autosave: no se pudo respaldar {type(m).__name__}: {exc}")

    def esperar(self):
        """Espera a que terminen las subidas en curso. Se llama antes de la
        subida final (cierre de atención): si una subida vieja terminara
        después, pisaría el informe final con uno anterior."""
        for subida in list(self._hilos.values()):
            if not subida.tarea.esperar(35_000):
                # Con la red lenta la subida puede pasar los 35 s (el
                # timeout de requests es por operación, no total). Sigue
                # sola; lo que estaba subiendo ya quedó en el respaldo local.
                print(f"autosave: la subida de {subida.clave[1]} sigue en curso, se suelta")
                del self._hilos[subida.clave]
                continue
            # El aviso de fin está en camino: se procesa ya, así la huella
            # queda al día antes de la subida final.
            self._terminada(subida, subida.tarea.resultado or (False, "sin terminar"))

    def guardar(self, modulo=None):
        """Respalda en el disco y sube en segundo plano lo que haya cambiado
        (uno o todos)."""
        usuario = None
        for m in ([modulo] if modulo is not None else self._modulos()):
            try:
                jobs = trabajos(m)
                for job in jobs:
                    if usuario is None:
                        usuario = respaldo_informes.usuario_de(_client())
                    self._subir_si_cambio(m, job, usuario)
            except Exception as exc:  # noqa: BLE001 -- un módulo no frena a los demás
                print(f"autosave: {type(m).__name__}: {exc}")

    def _subir_si_cambio(self, modulo, job, usuario):
        clave = (job["appointment_id"], job["tipo"])
        h = huella(job)
        if self._respaldadas.get(clave, (None,))[0] != h:
            # Primero al disco, aunque haya una subida en curso: si la red
            # está colgada esa subida puede tardar, y lo nuevo no puede
            # quedar solo en memoria mientras tanto.
            exportar = job.get("images")
            imagenes = exportar() if callable(exportar) else {}
            self._respaldadas[clave] = (
                h, respaldo_informes.guardar(usuario, job, h, imagenes or {}))
            self._en_disco[clave] = h
        if clave in self._hilos:
            return  # sigue subiendo la anterior; el próximo tick va
        if self._huellas.get(clave) == h:
            return
        carpeta = tempfile.mkdtemp(prefix="labsim_informe_")
        job["images_listas"] = self._copiar_imagenes(
            respaldo_informes.imagenes(usuario, job["appointment_id"], job["tipo"]), carpeta)
        subida = _Subida(job, clave, h, carpeta, modulo)
        self._hilos[clave] = subida
        subida.tarea = hilos.en_fondo(_subir_resultado, job, nombre="autosave",
                                      listo=lambda r, s=subida: self._terminada(s, r))

    def recuperar(self, appointment_id, destinos, sigue_vigente):
        """Retomar la atención: pide lo ya guardado de esa cita y se lo da a
        cada módulo (`destinos`: {tipo: módulo con restore_report}).

        `sigue_vigente(appointment_id)`: si el alumno ya cerró o cambió de
        atención cuando llega la respuesta, no se toca nada.
        """
        reparto = _Reparto(destinos, sigue_vigente)
        return hilos.en_fondo(recuperar, appointment_id, list(destinos), dueno=self,
                              nombre="recuperar", listo=lambda informes:
                              reparto.repartir(appointment_id, informes))

    def olvidar(self, appointment_id, tipo):
        """La subida final ya se hizo a mano: que el próximo tick no crea
        que hay algo nuevo."""
        self._huellas.pop((appointment_id, tipo), None)

    def marcar_subido(self, job):
        self._huellas[(job["appointment_id"], job["tipo"])] = huella(job)

    @staticmethod
    def _copiar_imagenes(origen, carpeta):
        """Copia las imágenes respaldadas ({sufijo: ruta}) a una carpeta
        propia de esta subida: el próximo respaldo las pisaría mientras
        este hilo las está mandando."""
        rutas = {}
        for sufijo, ruta in origen.items():
            destino = os.path.join(carpeta, f"{sufijo}.jpg")
            try:
                shutil.copyfile(ruta, destino)
            except OSError:
                continue
            rutas[sufijo] = destino
        return rutas

    def _terminada(self, subida, resultado):
        # Puede llegar dos veces: desde esperar() y por el aviso de en_fondo.
        # O de una subida que esperar() soltó por lenta.
        ok, err = resultado
        if self._hilos.get(subida.clave) is not subida:
            shutil.rmtree(subida.carpeta, ignore_errors=True)
            return
        del self._hilos[subida.clave]
        shutil.rmtree(subida.carpeta, ignore_errors=True)
        if ok:
            self._huellas[subida.clave] = subida.huella
        else:
            print(f"autosave: no se pudo subir {subida.clave[1]}: {err}")
        # El alumno ve en el módulo si quedó guardado (no hay botón).
        estado = getattr(subida.modulo, "estado_informe", None)
        if estado is not None:
            try:
                estado.guardado(subida.clave[1], ok, err,
                                en_equipo=self._respaldadas.get(subida.clave, (None, False))[1])
            except RuntimeError:   # el módulo ya no existe (cerró sesión)
                pass


def subir_pendientes(appointment_id=None, client=None, excluir=None) -> tuple[bool, str]:
    """Sube lo que quedó en el equipo sin subir: de esa cita (antes de
    cerrarla: si algo no sube, no se cierra) o, con None, de todas las del
    usuario (al iniciar sesión y con cada sync: un alumno que trabajó sin
    red en un equipo y siguió en otro). `excluir()`: la cita abierta ahora,
    que la sube el autoguardado. Una atención ya cerrada responde 409 y
    queda como 'cerrada', sin trabar a las demás."""
    client = client if client is not None else _client()
    usuario = respaldo_informes.usuario_de(client)
    primer_error = ""
    for registro in respaldo_informes.pendientes(usuario, appointment_id):
        if excluir is not None and str(excluir()) == str(registro.get("appointment_id")):
            continue
        job = {"appointment_id": registro["appointment_id"], "tipo": registro["tipo"],
               "data": registro["data"],
               "images_listas": respaldo_informes.imagenes(
                   usuario, registro["appointment_id"], registro["tipo"])}
        try:
            subir(job, client)
        except Exception as exc:  # noqa: BLE001
            if appointment_id is not None:
                return False, str(exc)
            print(f"autosave: pendiente de la cita {registro.get('appointment_id')} "
                  f"({registro.get('tipo')}) no subió: {exc}")
            primer_error = primer_error or str(exc)
    return not primer_error, primer_error


# Motivo de la última subida sincrónica fallida de cada tipo: el cierre de
# la atención lo muestra (sin esto el aviso solo decía el nombre del módulo).
ultimos_errores = {}


def subir_ahora(job, client=None) -> tuple[bool, str]:
    """Subida sincrónica de un job (cierre de atención, cierre de la app).
    Las imágenes se exportan acá mismo. `client`: el BackendClient del
    módulo que llama (None = uno nuevo).

    Si ese mismo contenido ya subió, no se repite: al cerrar sesión en un
    equipo donde la atención quedó atrás, resubir pisaba lo que el alumno
    siguió haciendo en otro."""
    try:
        cliente = client if client is not None else _client()
        usuario = respaldo_informes.usuario_de(cliente)
        previo = respaldo_informes.leer(usuario, job["appointment_id"], job["tipo"]) or {}
        if previo.get("estado") == "subido" and previo.get("huella") == huella(job):
            return True, ""
        exportar = job.get("images")
        job = dict(job)
        # Una imagen que no se pudo exportar no tira abajo el informe entero.
        job["images_listas"] = {k: v for k, v in (exportar() if callable(exportar) else {}).items()
                                if os.path.isfile(v)}
        # Al disco antes que a la red: si la subida falla, al retomar vuelve.
        respaldo_informes.guardar(usuario, job, huella(job), job["images_listas"])
        subir(job, cliente)
    except Exception as exc:  # noqa: BLE001
        ultimos_errores[job.get("tipo")] = str(exc)
        return False, str(exc)
    ultimos_errores.pop(job.get("tipo"), None)
    return True, ""
