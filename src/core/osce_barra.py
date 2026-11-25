"""Barra de la estación OSCE (core/osce.py): código del alumno, cuenta
regresiva de su tiempo y "Entregar".

No sabe nada del ABR: main le pasa tres funciones.
- abrir(respuesta): carga el caso que mandó el servidor y prepara el equipo.
- entrega(): lo que se sube (AbrMainWindow.osce_entrega).
- cerrar(): deja el equipo vacío para el siguiente.

El reloj se pide al servidor cada pocos segundos y entre medio corre solo.
Al llegar a cero entrega sola. Si la entrega no sale, queda guardada en el
equipo (osce.guardar_pendiente) y se reintenta sola; el alumno sigue a la
próxima estación igual.
"""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from core import hilos, osce

CADA_RELOJ_MS = 5000
CADA_PENDIENTES_MS = 15000
AVISO_FIN_MS = 6000


class BarraOsce(QWidget):
    def __init__(self, abrir, entrega, cerrar, parent=None):
        super().__init__(parent)
        self.setObjectName("barra_osce")
        self._abrir, self._entrega, self._cerrar = abrir, entrega, cerrar
        self.alumno = None          # código del alumno trabajando
        self.ventana = None         # {inicio_s, fin_s} de su tiempo
        self.datos_reloj = None
        self._entregando = False
        self._confirmar = False

        fila = QHBoxLayout(self)
        fila.setContentsMargins(10, 4, 10, 4)
        fila.setSpacing(10)
        info = osce.estacion or {}
        self.lbl_estacion = QLabel(f"<b>{info.get('titulo', 'Estación')}</b> · {info.get('osce', '')}")
        self.lbl_estacion.setWordWrap(True)
        self.lbl_estacion.setMaximumWidth(300)
        fila.addWidget(self.lbl_estacion)
        fila.addStretch(1)

        self.lbl_codigo = QLabel("Tu código:")
        self.campo = QLineEdit()
        self.campo.setPlaceholderText("K7F-3QM")
        self.campo.setMaxLength(9)
        self.campo.setFixedWidth(130)
        self.campo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fuente = QFont(self.campo.font())
        fuente.setPointSizeF(fuente.pointSizeF() * 1.4)
        fuente.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        self.campo.setFont(fuente)
        self.campo.returnPressed.connect(self.entrar)
        self.btn_entrar = QPushButton("Entrar")
        self.btn_entrar.clicked.connect(self.entrar)
        self.lbl_alumno = QLabel("")
        self.lbl_alumno.setFont(fuente)
        for w in (self.lbl_codigo, self.campo, self.btn_entrar, self.lbl_alumno):
            fila.addWidget(w)

        self.lbl_cuenta = QLabel("")
        grande = QFont(self.font())
        grande.setPointSizeF(grande.pointSizeF() * 1.8)
        grande.setBold(True)
        self.lbl_cuenta.setFont(grande)
        self.lbl_cuenta.setMinimumWidth(90)
        self.lbl_cuenta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fila.addWidget(self.lbl_cuenta)

        self.btn_entregar = QPushButton("Entregar")
        self.btn_entregar.clicked.connect(self.pedir_entrega)
        fila.addWidget(self.btn_entregar)

        # Con los PC del laboratorio (hasta 1024 de ancho) el aviso se parte
        # en dos líneas en vez de cortarse.
        self.lbl_estado = QLabel("")
        self.lbl_estado.setWordWrap(True)
        self.lbl_estado.setMinimumWidth(200)
        self.lbl_estado.setMaximumWidth(330)
        fila.addWidget(self.lbl_estado)

        self._modo_espera()

        self._tic = QTimer(self)
        self._tic.setInterval(250)
        self._tic.timeout.connect(self._cada_tic)
        self._tic.start()
        self._t_reloj = QTimer(self)
        self._t_reloj.setInterval(CADA_RELOJ_MS)
        self._t_reloj.timeout.connect(self._pedir_reloj)
        self._t_reloj.start()
        self._t_pend = QTimer(self)
        self._t_pend.setInterval(CADA_PENDIENTES_MS)
        self._t_pend.timeout.connect(self._reintentar_pendientes)
        self._t_pend.start()
        self._pedir_reloj()
        self._reintentar_pendientes()

    # -- Estados -----------------------------------------------------------

    def _modo_espera(self, mensaje=""):
        self.alumno = None
        self.ventana = None
        self._entregando = False
        self._confirmar = False
        for w in (self.lbl_codigo, self.campo, self.btn_entrar):
            w.setVisible(True)
        self.campo.setEnabled(True)
        self.btn_entrar.setEnabled(True)
        self.lbl_alumno.setText("")
        self.btn_entregar.setVisible(False)
        self.btn_entregar.setText("Entregar")
        self.lbl_cuenta.setStyleSheet("")
        self.lbl_estado.setText(mensaje)
        self.campo.clear()
        self.campo.setFocus()

    def _modo_alumno(self, codigo, ventana):
        self.alumno = codigo
        self.ventana = ventana
        for w in (self.lbl_codigo, self.campo, self.btn_entrar):
            w.setVisible(False)
        self.lbl_alumno.setText(codigo)
        self.btn_entregar.setVisible(True)
        self.btn_entregar.setEnabled(True)
        self.lbl_estado.setText("")

    # -- Entrar --------------------------------------------------------------

    def entrar(self):
        codigo = self.campo.text().strip()
        if not codigo or self.alumno is not None:
            return
        self.campo.setEnabled(False)
        self.btn_entrar.setEnabled(False)
        self.lbl_estado.setText("Revisando…")
        hilos.en_fondo(osce.entrar, codigo, listo=self._entro, fallo=self._no_entro,
                       dueno=self, nombre="osce_entrar")

    def _entro(self, respuesta):
        try:
            self._abrir(respuesta)
        except Exception as exc:  # noqa: BLE001 -- que el alumno no quede pegado
            self._modo_espera(f"No se pudo abrir el equipo: {exc}")
            return
        self._modo_alumno(respuesta["codigo"], respuesta.get("ventana") or {})

    def _no_entro(self, exc):
        self.campo.setEnabled(True)
        self.btn_entrar.setEnabled(True)
        self.campo.selectAll()
        self.campo.setFocus()
        self.lbl_estado.setText(str(exc) if isinstance(exc, osce.ErrorOsce)
                                else "Sin conexión con el servidor. Intenta de nuevo.")

    # -- Reloj ---------------------------------------------------------------

    def _pedir_reloj(self):
        if not osce.activo:
            return
        hilos.en_fondo(osce.reloj, listo=self._llego_reloj, dueno=self, nombre="osce_reloj")

    def _llego_reloj(self, datos):
        self.datos_reloj = datos

    def _queda(self):
        t = osce.transcurrido(self.datos_reloj)
        if t is None or not self.ventana:
            return None
        return float(self.ventana.get("fin_s", 0)) - t

    def _cada_tic(self):
        if self.alumno is None:
            self.lbl_cuenta.setText("")
            return
        queda = self._queda()
        if queda is None:
            return
        s = max(0, int(queda + 0.999))
        self.lbl_cuenta.setText(f"{s // 60}:{s % 60:02d}")
        self.lbl_cuenta.setStyleSheet("color: #b91c1c;" if queda <= 60 else "")
        if queda <= 0 and not self._entregando:
            self.entregar(auto=True)

    # -- Entregar ------------------------------------------------------------

    def pedir_entrega(self):
        """Dos toques: el primero pregunta (sin diálogos que bloqueen el equipo)."""
        if self.alumno is None or self._entregando:
            return
        if not self._confirmar:
            self._confirmar = True
            self.btn_entregar.setText("¿Seguro? Toca de nuevo")
            QTimer.singleShot(4000, self, self._olvidar_confirmacion)
            return
        self.entregar()

    def _olvidar_confirmacion(self):
        if self._confirmar and not self._entregando:
            self._confirmar = False
            self.btn_entregar.setText("Entregar")

    def entregar(self, auto=False):
        if self.alumno is None or self._entregando:
            return
        self._entregando = True
        self.btn_entregar.setEnabled(False)
        alumno = self.alumno
        try:
            entrega = self._entrega()
        except Exception as exc:  # noqa: BLE001
            entrega = {"error_app": str(exc)}
        entrega["auto"] = bool(auto)
        try:
            osce.guardar_pendiente(alumno, entrega)
        except OSError as exc:
            print(f"osce: no se pudo guardar la entrega en el equipo: {exc}")
        self.lbl_estado.setText("Entregando…")
        hilos.en_fondo(osce.entregar, alumno, entrega, listo=lambda _r: self._entregada(alumno, True),
                       fallo=lambda exc: self._entregada(alumno, False, exc), dueno=self, nombre="osce_entregar")

    def _entregada(self, alumno, ok, exc=None):
        if ok or isinstance(exc, osce.ErrorOsce):
            osce.borrar_pendiente(alumno)
        if ok:
            mensaje = f"Entregado ✓ ({alumno}). Pasa a la siguiente estación."
        elif isinstance(exc, osce.ErrorOsce):
            mensaje = f"{alumno}: {exc}"
        else:
            mensaje = f"Sin conexión: la entrega de {alumno} quedó en el equipo y se enviará sola."
        try:
            self._cerrar()
        finally:
            self._modo_espera(mensaje)
        QTimer.singleShot(AVISO_FIN_MS, self, self._limpiar_aviso)

    def _limpiar_aviso(self):
        if self.alumno is None:
            self.lbl_estado.setText("")

    def _reintentar_pendientes(self):
        if not osce.activo or not osce.pendientes():
            return
        hilos.en_fondo(osce.enviar_pendientes, dueno=self, nombre="osce_pendientes")

    def detener(self):
        for t in (self._tic, self._t_reloj, self._t_pend):
            t.stop()
