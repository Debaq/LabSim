"""Actualización obligatoria en el kiosko (LABSIM_KIOSKO=1, ver core/kiosko.py).

En el laboratorio una versión vieja es una versión rota: la actualización es
lo que funciona. Por eso en el kiosko:

- Al abrir, LabSim no se muestra hasta confirmar que está al día. Si hay
  versión nueva se instala; si no se puede consultar o la instalación falla,
  queda la pantalla de "Actualizando LabSim" reintentando sola. Sin internet
  la app tampoco serviría (el login necesita el backend), así que no se
  pierde nada.
- Con la app abierta se revisa cada CHEQUEO_MIN minutos. Si aparece algo y
  no hay sesión iniciada, se actualiza en ese momento; si hay un alumno
  atendiendo, al cerrar sesión (nunca a mitad de una atención). Si la red se
  cae con la app abierta, se sigue trabajando: ya tiene lo que necesita.

Fuera del kiosko nada de esto corre: se pregunta como siempre
(main._check_and_apply_update).
"""

import threading
import traceback

from PySide6.QtCore import QEventLoop, QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from core.base import context
from core.updater import UpdateCheckError, apply_update_and_restart, check_for_update


CHEQUEO_MIN = 30
# Espera entre reintentos: arranca corta (un corte de red breve al prender
# el equipo) y se estira para no martillar GitHub con todo el laboratorio.
ESPERAS_S = (10, 20, 40, 60, 120)


class PantallaActualizacion(QWidget):
    """Tapa todo mientras se busca/instala la versión nueva."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Actualizando LabSim")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet(
            "QWidget { background: #f4f6f8; color: #1f2933; }"
            "QLabel#titulo { font-size: 26px; font-weight: 600; }"
            "QLabel#detalle { font-size: 16px; color: #52606d; }")
        layout = QVBoxLayout(self)
        layout.addStretch(1)
        self.titulo = QLabel("Actualizando LabSim", objectName="titulo")
        self.detalle = QLabel("", objectName="detalle")
        self.detalle.setWordWrap(True)
        self.barra = QProgressBar()
        self.barra.setFixedWidth(420)
        self.barra.setTextVisible(False)
        for w in (self.titulo, self.detalle, self.barra):
            layout.addWidget(w, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

    def estado(self, titulo, detalle="", actual=0, total=0):
        self.titulo.setText(titulo)
        self.detalle.setText(detalle)
        # total 0: barra "ocupado" sin porcentaje
        self.barra.setRange(0, total)
        self.barra.setValue(actual)
        context.app.processEvents()

    def progreso(self, stage, current, total, hop, hops):
        """on_progress de apply_update_and_restart."""
        paso = f" ({hop}/{hops})" if hops > 1 else ""
        if stage == "download":
            mb = f"{current / 1048576:.1f}"
            if total:
                mb += f" / {total / 1048576:.1f}"
            self.estado("Descargando actualización" + paso, f"{mb} MB",
                        current, total)
        elif stage == "extract":
            self.estado("Instalando actualización" + paso)
        elif stage == "restart":
            self.estado("Reiniciando LabSim...")


def _esperar_ms(ms):
    """Deja correr Qt `ms` milisegundos sin bloquear la pantalla."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _en_hilo(fn, *args, **kwargs):
    """Corre `fn` en otro hilo y espera con Qt vivo (la consulta a GitHub
    puede tardar hasta el timeout y la pantalla no debe congelarse)."""
    resultado = {}

    def correr():
        try:
            resultado["ok"] = fn(*args, **kwargs)
        except BaseException as exc:  # se relanza en el hilo de Qt
            resultado["error"] = exc

    hilo = threading.Thread(target=correr, daemon=True)
    hilo.start()
    while hilo.is_alive():
        _esperar_ms(50)
    if "error" in resultado:
        raise resultado["error"]
    return resultado.get("ok")


def actualizar_o_bloquear(version, abortar=lambda: False):
    """No vuelve hasta que LabSim está al día.

    Si hay versión nueva la instala y reinicia (apply_update_and_restart no
    vuelve). Si no se puede consultar o la instalación falla, reintenta con
    la pantalla puesta. Vuelve solo cuando GitHub confirma que no hay nada
    nuevo, o si `abortar()` da True (el equipo se está apagando)."""
    pantalla = PantallaActualizacion()
    pantalla.showFullScreen()
    pantalla.raise_()
    pantalla.activateWindow()
    intento = 0
    try:
        while not abortar():
            pantalla.estado("Buscando actualizaciones...")
            try:
                update = _en_hilo(check_for_update, version, estricto=True)
            except UpdateCheckError as exc:
                motivo = ("No se pudo consultar si hay una versión nueva "
                          f"({exc}). Revisa la conexión a internet.")
            else:
                if update is None:
                    return
                try:
                    # No vuelve si sale bien: el proceso termina y el script
                    # del swap abre la versión nueva.
                    apply_update_and_restart(update, on_progress=pantalla.progreso)
                    motivo = "El paquete de actualización vino con una estructura inesperada."
                except Exception as exc:
                    traceback.print_exc()
                    motivo = f"No se pudo instalar la actualización ({exc})."

            espera = ESPERAS_S[min(intento, len(ESPERAS_S) - 1)]
            intento += 1
            for resto in range(espera, 0, -1):
                if abortar():
                    return
                pantalla.estado("LabSim no está actualizado",
                                f"{motivo}\nSe vuelve a intentar en {resto} s.")
                _esperar_ms(1000)
    finally:
        pantalla.close()


class ChequeoPeriodico(QObject):
    """Revisa cada CHEQUEO_MIN minutos, en otro hilo, si hay versión nueva.

    Solo avisa (`hay_update`); decidir cuándo aplicarla es de MainWindow,
    que sabe si hay un alumno atendiendo. Una falla de red se ignora: con
    la app abierta se sigue trabajando."""

    hay_update = Signal()

    def __init__(self, version, parent=None):
        super().__init__(parent)
        self._version = version
        self._timer = QTimer(self)
        self._timer.setInterval(CHEQUEO_MIN * 60 * 1000)
        self._timer.timeout.connect(self._chequear)
        self._timer.start()

    def _chequear(self):
        threading.Thread(target=self._consultar, daemon=True).start()

    def _consultar(self):
        try:
            update = check_for_update(self._version)
        except Exception:
            return
        if update is not None:
            # emitida desde otro hilo: Qt la entrega en el de la ventana
            self.hay_update.emit()
