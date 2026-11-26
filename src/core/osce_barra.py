"""Barra de la estación OSCE (core/osce.py): número del alumno, confirmación
de su nombre, cuenta regresiva de su tiempo y "Entregar"; y la ventanita
flotante de los casos (VentanaCasos).

No sabe nada del ABR: main le pasa cuatro funciones.
- abrir(tarea, hecho): carga el caso de esa tarea y prepara su equipo (ABR o
  VEMP); con hecho (lo que el alumno dejó al salir de ese caso) lo devuelve
  tal cual (osce_restaurar).
- entrega(): lo que se sube del caso abierto (AbrMainWindow.osce_entrega).
- cerrar(): deja el equipo vacío para el caso o el alumno siguiente.
- bloquear(bool): congela el equipo mientras el alumno lee las indicaciones.

Entrar es en dos pasos: escribe su número, ve su nombre y toca "Sí, soy yo";
ahí parte SU tiempo (Osce::iniciarReloj en el servidor), así cada alumno
tiene siempre la duración completa aunque las estaciones queden desfasadas.

Una estación puede tener varios casos (cada uno con su examen, su peso y el
paciente que le toca al alumno). Al abrir un caso por primera vez la
ventanita muestra sus indicaciones; al aceptarlas se libera el equipo. El
alumno va y viene entre los casos con la ventanita mientras le dure el
tiempo: lo hecho en cada caso queda guardado y vuelve al regresar. La
entrega lleva lo de todos los casos que abrió.

El reloj se pide al servidor cada pocos segundos y entre medio corre solo.
Al llegar a cero entrega sola y el equipo se cierra. Si la entrega no sale,
queda guardada en el equipo (osce.guardar_pendiente) y se reintenta sola;
el alumno sigue a la próxima estación igual.
"""
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextBrowser, QVBoxLayout,
                               QWidget)

from core import hilos, osce

CADA_RELOJ_MS = 5000
CADA_PENDIENTES_MS = 15000
AVISO_FIN_MS = 6000


class VentanaCasos(QWidget):
    """Ventanita flotante sobre el equipo: en qué caso va, sus indicaciones
    (con "Acepto" la primera vez) y los botones para ir y volver."""

    def __init__(self, barra, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.WindowTitleHint
                         | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setObjectName("osce_casos")
        self.setWindowTitle("Casos de la estación")
        self.barra = barra
        col = QVBoxLayout(self)
        col.setContentsMargins(10, 8, 10, 8)
        col.setSpacing(6)
        self.lbl_caso = QLabel("")
        self.lbl_caso.setWordWrap(True)
        fuente = QFont(self.lbl_caso.font())
        fuente.setPointSizeF(fuente.pointSizeF() * 1.15)
        fuente.setBold(True)
        self.lbl_caso.setFont(fuente)
        col.addWidget(self.lbl_caso)
        self.txt = QTextBrowser()
        self.txt.setOpenLinks(False)
        self.txt.setMinimumHeight(90)
        col.addWidget(self.txt, 1)
        self.btn_acepto = QPushButton("Acepto: empezar")
        self.btn_acepto.clicked.connect(self.barra.aceptar_indicaciones)
        col.addWidget(self.btn_acepto)
        fila = QHBoxLayout()
        self.btn_ant = QPushButton("← Caso anterior")
        self.btn_ant.clicked.connect(self.barra.caso_anterior)
        self.btn_ver = QPushButton("Indicaciones")
        self.btn_ver.setCheckable(True)
        self.btn_ver.toggled.connect(self._ver)
        self.btn_sig = QPushButton("Siguiente caso →")
        self.btn_sig.clicked.connect(self.barra.caso_siguiente)
        for b in (self.btn_ant, self.btn_ver, self.btn_sig):
            fila.addWidget(b)
        col.addLayout(fila)
        self.setMinimumWidth(340)
        self._ubicada = False

    def _ver(self, visible):
        self.txt.setVisible(visible)
        self.adjustSize()

    def mostrar(self, k, n, tarea, aceptado):
        peso = tarea.get("peso")
        peso = f" · {peso:g} %" if isinstance(peso, (int, float)) and n > 1 else ""
        self.lbl_caso.setText(f"Caso {k + 1} de {n}: {tarea.get('titulo', '')}{peso}")
        indicaciones = (tarea.get("indicaciones") or "").strip()
        self.txt.setPlainText(indicaciones or "Configura el equipo para este paciente. Lanza una curva para verificar y, "
                                              "cuando estés conforme, pasa al caso siguiente.")
        self.btn_acepto.setVisible(not aceptado)
        for b in (self.btn_ant, self.btn_sig):
            b.setVisible(aceptado and n > 1)
        self.btn_ant.setEnabled(k > 0)
        self.btn_sig.setEnabled(k < n - 1)
        self.btn_ver.setVisible(aceptado)
        self.btn_ver.blockSignals(True)
        self.btn_ver.setChecked(not aceptado)
        self.btn_ver.blockSignals(False)
        self.txt.setVisible(not aceptado)
        self.adjustSize()
        if not self._ubicada and self.parentWidget() is not None:
            # Arriba a la derecha de la ventana principal, bajo la barra.
            ventana = self.parentWidget().window()
            esquina = ventana.mapToGlobal(ventana.rect().topRight())
            self.move(esquina.x() - self.width() - 24, esquina.y() + 110)
            self._ubicada = True
        self.show()
        self.raise_()


class BarraOsce(QWidget):
    def __init__(self, abrir, entrega, cerrar, bloquear=None, parent=None):
        super().__init__(parent)
        self.setObjectName("barra_osce")
        self._abrir, self._entrega, self._cerrar = abrir, entrega, cerrar
        self._bloquear = bloquear or (lambda _si: None)
        self.alumno = None          # código del alumno trabajando
        self.ventana = None         # {inicio_s, fin_s} de su tiempo
        self.datos_reloj = None
        self._entregando = False
        self._confirmar = False
        self._por_confirmar = None  # número escrito, esperando "Sí, soy yo"
        self.tareas = []            # los casos del alumno (respuesta['tareas'])
        self.k = 0                  # el que tiene abierto
        self.hechas = {}            # k -> lo que dejó en ese caso
        self.aceptadas = set()      # casos cuyas indicaciones ya aceptó
        self._respuesta = None
        self.casos = None           # VentanaCasos (se crea con el primer alumno)

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
        # Segundo paso: "¿Eres ...?"
        self.lbl_nombre = QLabel("")
        normal = QFont(self.font())
        normal.setPointSizeF(normal.pointSizeF() * 1.3)
        self.lbl_nombre.setFont(normal)
        self.btn_soy = QPushButton("Sí, soy yo: empezar")
        self.btn_soy.clicked.connect(self.confirmar)
        self.btn_no_soy = QPushButton("No soy yo")
        self.btn_no_soy.clicked.connect(self.no_soy)
        self.lbl_alumno = QLabel("")
        self.lbl_alumno.setFont(fuente)
        for w in (self.lbl_codigo, self.campo, self.btn_entrar, self.lbl_nombre, self.btn_soy,
                  self.btn_no_soy, self.lbl_alumno):
            fila.addWidget(w)

        self.btn_casos = QPushButton("Casos")
        self.btn_casos.setToolTip("Muestra la ventanita de los casos de la estación")
        self.btn_casos.clicked.connect(self._mostrar_casos)
        fila.addWidget(self.btn_casos)

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

    def _mostrar_paso(self, paso):
        """espera: escribe su número; confirmar: ¿eres ...?; alumno: trabajando."""
        for w in (self.lbl_codigo, self.campo, self.btn_entrar):
            w.setVisible(paso == "espera")
        for w in (self.lbl_nombre, self.btn_soy, self.btn_no_soy):
            w.setVisible(paso == "confirmar")
        for w in (self.lbl_alumno, self.btn_entregar):
            w.setVisible(paso == "alumno")
        self.btn_casos.setVisible(paso == "alumno")

    def _modo_espera(self, mensaje=""):
        self.alumno = None
        self.ventana = None
        self._entregando = False
        self._confirmar = False
        self._por_confirmar = None
        self.tareas = []
        self.k = 0
        self.hechas = {}
        self.aceptadas = set()
        self._respuesta = None
        if self.casos is not None:
            self.casos.hide()
        self._mostrar_paso("espera")
        self.campo.setEnabled(True)
        self.btn_entrar.setEnabled(True)
        self.lbl_alumno.setText("")
        self.btn_entregar.setText("Entregar")
        self.lbl_cuenta.setStyleSheet("")
        self.lbl_estado.setText(mensaje)
        self.campo.clear()
        self.campo.setFocus()

    def _modo_alumno(self, codigo, ventana, numero=None):
        self.alumno = codigo
        self.ventana = ventana
        self._mostrar_paso("alumno")
        self.lbl_alumno.setText(f"N.º {numero}" if numero else codigo)
        self.btn_entregar.setEnabled(True)
        self.lbl_estado.setText("")

    # -- Entrar: número y nombre --------------------------------------------------

    def entrar(self):
        codigo = self.campo.text().strip()
        if not codigo or self.alumno is not None:
            return
        self.campo.setEnabled(False)
        self.btn_entrar.setEnabled(False)
        self.lbl_estado.setText("Revisando…")
        hilos.en_fondo(osce.entrar, codigo, listo=self._a_confirmar, fallo=self._no_entro,
                       dueno=self, nombre="osce_entrar")

    def _a_confirmar(self, respuesta):
        self._por_confirmar = respuesta.get("codigo") or self.campo.text().strip()
        self.lbl_nombre.setText(f"¿Eres <b>{respuesta.get('nombre', '')}</b>? (N.º {respuesta.get('numero', '')})")
        self.btn_soy.setEnabled(True)
        self.btn_no_soy.setEnabled(True)
        self._mostrar_paso("confirmar")
        self.lbl_estado.setText("Sigue tu tiempo." if respuesta.get("partio") else "Tu tiempo parte al confirmar.")

    def no_soy(self):
        self._modo_espera("Revisa el número de tu tarjeta.")

    def confirmar(self):
        if not self._por_confirmar or self.alumno is not None:
            return
        self.btn_soy.setEnabled(False)
        self.btn_no_soy.setEnabled(False)
        self.lbl_estado.setText("Abriendo…")
        hilos.en_fondo(osce.confirmar, self._por_confirmar, listo=self._entro, fallo=self._no_confirmo,
                       dueno=self, nombre="osce_confirmar")

    def _no_confirmo(self, exc):
        self._modo_espera(str(exc) if isinstance(exc, osce.ErrorOsce)
                          else "Sin conexión con el servidor. Intenta de nuevo.")

    def _entro(self, respuesta):
        # Una estación de antes (sin 'tareas') es un solo caso con todo arriba.
        tareas = respuesta.get("tareas") or [{k: respuesta.get(k) for k in
                                              ("tipo", "modulo", "prueba", "curvas", "caso")}]
        self._respuesta = respuesta
        self.tareas = tareas
        self.k = 0
        self.hechas = {}
        self.aceptadas = set()
        try:
            self._abrir_tarea(0)
        except Exception as exc:  # noqa: BLE001 -- que el alumno no quede pegado
            self._modo_espera(f"No se pudo abrir el equipo: {exc}")
            return
        self._modo_alumno(respuesta["codigo"], respuesta.get("ventana") or {}, respuesta.get("numero"))
        self._mostrar_casos()

    def _abrir_tarea(self, k):
        tarea = dict(self.tareas[k])
        tarea["codigo"] = self._respuesta["codigo"]
        tarea["numero"] = self._respuesta.get("numero")
        tarea.setdefault("tipo", self._respuesta.get("tipo"))
        self._abrir(tarea, self.hechas.get(k))
        # Mientras no acepte las indicaciones de este caso, el equipo no se toca.
        self._bloquear(k not in self.aceptadas)

    # -- Ventanita de casos ---------------------------------------------------------

    def _mostrar_casos(self):
        if self.alumno is None and not self.tareas:
            return
        if self.casos is None:
            self.casos = VentanaCasos(self, self.window())
        self.casos.mostrar(self.k, len(self.tareas), self.tareas[self.k], self.k in self.aceptadas)

    def aceptar_indicaciones(self):
        if self.alumno is None:
            return
        self.aceptadas.add(self.k)
        self._bloquear(False)
        self._mostrar_casos()

    def caso_anterior(self):
        self.ir_a(self.k - 1)

    def caso_siguiente(self):
        self.ir_a(self.k + 1)

    def ir_a(self, k):
        """Guarda lo hecho en el caso abierto y abre otro (o vuelve a uno ya
        visto, tal como lo dejó). Solo mientras le dure el tiempo."""
        if self.alumno is None or self._entregando or not 0 <= k < len(self.tareas) or k == self.k:
            return
        self._guardar_tarea_actual()
        self._cerrar()
        self.k = k
        try:
            self._abrir_tarea(k)
        except Exception as exc:  # noqa: BLE001
            self.lbl_estado.setText(f"No se pudo abrir el caso: {exc}")
        self._mostrar_casos()

    def _guardar_tarea_actual(self):
        try:
            self.hechas[self.k] = self._entrega()
        except Exception as exc:  # noqa: BLE001
            self.hechas[self.k] = {"error_app": str(exc)}

    def _entrega_total(self):
        """Lo de cada caso en orden (null en los que no alcanzó a abrir)."""
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

    def _cambio_queda(self):
        """Sin alumno, en el cambio: cuánto falta para que la estación reciba."""
        d = self.datos_reloj or {}
        reloj = d.get("reloj") or {}
        if reloj.get("fase") not in ("cambio", "entre_vueltas") or reloj.get("restante_s") is None:
            return None
        corre = d.get("estado") == "en_curso" and not d.get("pausado")
        pasado = time.monotonic() - d.get("_pedido", time.monotonic()) if corre else 0
        return max(0.0, float(reloj["restante_s"]) - pasado)

    def _cada_tic(self):
        if self.alumno is None:
            cambio = self._cambio_queda()
            if cambio is None:
                self.lbl_cuenta.setText("")
            else:
                s = int(cambio + 0.999)
                self.lbl_cuenta.setText(f"Cambio {s // 60}:{s % 60:02d}")
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
        if self.casos is not None:
            self.casos.hide()
        alumno = self.alumno
        self._guardar_tarea_actual()
        entrega = self._entrega_total()
        entrega["auto"] = bool(auto)
        try:
            osce.guardar_pendiente(alumno, entrega)
        except OSError as exc:
            print(f"osce: no se pudo guardar la entrega en el equipo: {exc}")
        # Se acabó: el equipo queda quieto hasta que se cierre.
        self._bloquear(True)
        self.lbl_estado.setText("Se acabó el tiempo. Entregando…" if auto else "Entregando…")
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
            self._bloquear(False)
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
        if self.casos is not None:
            self.casos.hide()
