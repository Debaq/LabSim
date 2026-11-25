"""Barra de la estación OSCE (core/osce.py): código del alumno, cuenta
regresiva de su tiempo y "Entregar".

No sabe nada del ABR: main le pasa tres funciones.
- abrir(tarea): carga el caso de esa tarea y prepara su equipo (ABR o VEMP).
- entrega(): lo que se sube de la tarea abierta (AbrMainWindow.osce_entrega).
- cerrar(): deja el equipo vacío para la tarea o el alumno siguiente.

Una estación puede tener varias tareas (cada una con su examen, su peso y
el paciente que le toca al alumno). Se hacen en orden: "Siguiente tarea"
guarda lo hecho y abre la próxima, sin volver. La entrega lleva lo de
todas las tareas a las que llegó.

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
        self._confirmar_sig = False
        self.tareas = []            # las tareas del alumno (respuesta['tareas'])
        self.k = 0                  # la que tiene abierta
        self.hechas = {}            # k -> lo que entregó de esa tarea
        self._respuesta = None

        fila = QHBoxLayout(self)
        fila.setContentsMargins(10, 4, 10, 4)
        fila.setSpacing(10)
        info = osce.estacion or {}
        self.lbl_estacion = QLabel(f"<b>{info.get('titulo', 'Estación')}</b> · {info.get('osce', '')}")
        self.lbl_estacion.setWordWrap(True)
        self.lbl_estacion.setMaximumWidth(300)
        fila.addWidget(self.lbl_estacion)
        fila.addStretch(1)

        self.lbl_codigo = QLabel("Tu número:")
        self.campo = QLineEdit()
        self.campo.setPlaceholderText("N.º")
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

        self.lbl_tarea = QLabel("")
        self.lbl_tarea.setWordWrap(True)
        self.lbl_tarea.setMaximumWidth(260)
        fila.addWidget(self.lbl_tarea)
        self.btn_siguiente = QPushButton("Siguiente tarea →")
        self.btn_siguiente.clicked.connect(self.pedir_siguiente)
        fila.addWidget(self.btn_siguiente)

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
        self._confirmar_sig = False
        self.tareas = []
        self.k = 0
        self.hechas = {}
        self._respuesta = None
        self.lbl_tarea.setText("")
        self.btn_siguiente.setVisible(False)
        self.btn_siguiente.setText("Siguiente tarea →")
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

    def _modo_alumno(self, codigo, ventana, numero=None):
        self.alumno = codigo
        self.ventana = ventana
        for w in (self.lbl_codigo, self.campo, self.btn_entrar):
            w.setVisible(False)
        self.lbl_alumno.setText(f"N.º {numero}" if numero else codigo)
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
        # Una estación de antes (sin 'tareas') es una sola tarea con todo arriba.
        tareas = respuesta.get("tareas") or [{k: respuesta.get(k) for k in
                                              ("tipo", "modulo", "prueba", "curvas", "caso")}]
        self._respuesta = respuesta
        self.tareas = tareas
        self.k = 0
        self.hechas = {}
        try:
            self._abrir_tarea(0)
        except Exception as exc:  # noqa: BLE001 -- que el alumno no quede pegado
            self._modo_espera(f"No se pudo abrir el equipo: {exc}")
            return
        self._modo_alumno(respuesta["codigo"], respuesta.get("ventana") or {}, respuesta.get("numero"))
        self._mostrar_tarea()

    def _abrir_tarea(self, k):
        tarea = dict(self.tareas[k])
        tarea["codigo"] = self._respuesta["codigo"]
        tarea["numero"] = self._respuesta.get("numero")
        tarea.setdefault("tipo", self._respuesta.get("tipo"))
        self._abrir(tarea)

    def _mostrar_tarea(self):
        n = len(self.tareas)
        t = self.tareas[self.k] if self.tareas else {}
        if n > 1:
            peso = t.get("peso")
            peso = f" ({peso:g} %)" if isinstance(peso, (int, float)) else ""
            self.lbl_tarea.setText(f"<b>Tarea {self.k + 1} de {n}</b> · {t.get('titulo', '')}{peso}")
        else:
            self.lbl_tarea.setText("")
        self.btn_siguiente.setVisible(self.k < n - 1)
        self.btn_siguiente.setEnabled(True)
        self.btn_siguiente.setText("Siguiente tarea →")
        self._confirmar_sig = False

    # -- Siguiente tarea -------------------------------------------------------

    def pedir_siguiente(self):
        """Dos toques, como Entregar: no se vuelve a la tarea anterior."""
        if self.alumno is None or self._entregando or self.k >= len(self.tareas) - 1:
            return
        if not self._confirmar_sig:
            self._confirmar_sig = True
            self.btn_siguiente.setText("¿Seguro? No se vuelve")
            QTimer.singleShot(4000, self, self._olvidar_siguiente)
            return
        self.siguiente()

    def _olvidar_siguiente(self):
        if self._confirmar_sig and self.alumno is not None:
            self._confirmar_sig = False
            self.btn_siguiente.setText("Siguiente tarea →")

    def _guardar_tarea_actual(self):
        try:
            self.hechas[self.k] = self._entrega()
        except Exception as exc:  # noqa: BLE001
            self.hechas[self.k] = {"error_app": str(exc)}

    def siguiente(self):
        if self.alumno is None or self.k >= len(self.tareas) - 1:
            return
        # Lo hecho queda en memoria hasta la entrega (no como pendiente: el
        # reintento automático lo entregaría antes de tiempo).
        self._guardar_tarea_actual()
        self._cerrar()
        self.k += 1
        try:
            self._abrir_tarea(self.k)
        except Exception as exc:  # noqa: BLE001
            self.lbl_estado.setText(f"No se pudo abrir la tarea: {exc}")
        self._mostrar_tarea()

    def _entrega_total(self):
        """Lo de cada tarea en orden (null en las que no alcanzó a abrir)."""
        return {"tareas": [self.hechas.get(i) for i in range(len(self.tareas))]}

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
        if 0 < queda <= 60 and not self._entregando:
            self.lbl_estado.setText("Queda menos de 1 minuto: al llegar a cero se entrega solo.")
        elif queda > 60 and self.lbl_estado.text().startswith("Queda menos"):
            self.lbl_estado.setText("")
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
        self.btn_siguiente.setEnabled(False)
        alumno = self.alumno
        self._guardar_tarea_actual()
        entrega = self._entrega_total()
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
            if (osce.estacion or {}).get("tipo") == "conclusion":
                # La IA corrige el informe en el servidor; acá no se espera.
                hilos.en_fondo(osce.corregir, alumno, dueno=self, nombre="osce_corregir")
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
