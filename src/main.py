from pathlib import Path
import faulthandler
import os
import sys
import traceback
import requests
from PySide6.QtCore import QEvent, Qt, QSize, QTimer, Signal, Slot
from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QMessageBox, QProgressDialog

from agenda import Agenda
from agenda.ChatPaciente import ChatPacienteWidget
from audiometria import Acumetria, Otoscopia
from audiometria.DebugMkg import DebugMkgDialog
from auth import login as Ui_login
from core.base import context
from core.h_win import FrameSubMdi, MdiArea
from core import inbox
from core import mis_pacientes
from core import app_config_store
from core.report_autosave import ReportAutosave
from core.kiosko import es_kiosko, atender_apagado
from core.preferencias import preferencias
from core import mouse_zurdo, configuracion
from core.module_placeholder import ModulePlaceholder
from core.updater import local_build_id
from core.helpers import (CasesOffline, CreatePatient, Preferences, Shedule, Storage,
                          es_docente,
                          marcar_entry_atendiendo, marcar_entry_atendido,
                          reset_backend_session)
from core.ui_helpers import MoveWindow, ToolBar, show_hide, toggle_max_min, titlebar_icon, style_dialog, is_full_window, raise_window
from audiometria.UI.Ui_command_voice_A import Ui_Form as commandVoiceA
from core.UI.Ui_Main import Ui_MainWindow
from core.Logger import Logger
from backend.client import BackendClient
from backend.log_queue import LogUploaderThread, get_log_queue
from backend.sync_thread import SyncThread
from core import app_layout
from core.app_layout import LayoutRetryThread, fetch_layout

# Definir la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'resources' / 'config' / 'config.json'
LOG_FILE = BASE_DIR / 'log_file.txt'

__VERSION__ = 'vv0.9.9'
# Build real (con sufijo -r<commit> si aplica) para mostrar en el título --
# __VERSION__ solo no alcanza porque no sube en cada build de prueba.
DISPLAY_VERSION = f"v{local_build_id(__VERSION__.lstrip('v'))}"
Preferences = Preferences()
STYLES = Preferences.get("styles")
LANGUAJE = Preferences.get("lang")

# Layout (módulos/boxes/sectores) viene del backend. Antes vivía en
# resources/json/apps.json; ahora se pide por GET /api/layout.php al
# arrancar, y cada respuesta buena queda cacheada en
# resources/local_cache/layout.json (ver core/app_layout.py). Sin red se
# abre con esa copia: la app queda operativa igual, en modo offline, y un
# thread reintenta en background para volver a "online" sin reiniciar.
#
# Fallback mínimo (solo instalación nueva que nunca llegó a conectarse):
# dejar LOGIN en APPS para que el z-order de la ventana de login siga
# resuelto. Si no hubiera LOGIN, _close_sub_windows crashea con KeyError.
_LAYOUT_FALLBACK_APPS = {
    "LOGIN": [True, "Ingreso", 0, [True, True], [410, 140], "pre"],
}
BACKEND_URL = Preferences.get("BACKEND_URL")
_layout = fetch_layout(BACKEND_URL)
if _layout:
    APPS = _layout["APP"]
    SECTORS = _layout["SECTORS"]
    BOXS = _layout["BOXS"]
    LAYOUT_AVAILABLE = True
else:
    APPS = _LAYOUT_FALLBACK_APPS
    SECTORS = {}
    BOXS = {}
    LAYOUT_AVAILABLE = False
# 'network' (backend respondió), 'cache' (copia local, modo offline) o
# None (no hay layout de ninguna parte).
LAYOUT_SOURCE = app_layout.last_source

# Cola local de logs de acciones (ver lib/backend/log_queue.py). Es solo un
# insert sqlite local, nunca toca la red -- se sube al backend en batches
# vía LogUploaderThread (ver MainWindow._data_login).
LOCAL_LOG_QUEUE = get_log_queue()
# Logger sin log_queue: stdout (prints de debug regados por todo el código)
# ya no se sube al backend -- era 87% del volumen y puro ruido interno
# ("cambio el sender", "True", [agenda_filter]...). Las acciones reales del
# alumno (audio_stim_button, z_dial_change, etc.) se suben aparte, con
# nombre propio, vía log_queue.push() explícito en Audiometer.py y Z.py.
sys.stdout = Logger(LOG_FILE)
# stderr al mismo archivo. Los errores de PySide ("Error calling Python
# override of QWidget::eventFilter(): ...") y los traceback de cualquier
# excepcion NO pasan por stdout: sin esto, lo unico que quedaba del
# problema era lo que el alumno alcanzara a copiar de la consola, y la
# causa real es justo la ultima linea, la que la consola recorta.
sys.stderr = Logger(LOG_FILE, stream=sys.__stderr__)
# Un cuelgue duro (stack overflow de la cadena de layout de pyqtgraph, por
# ejemplo) no deja traceback de Python: faulthandler escribe el stack en
# el mismo log antes de que el proceso se vaya.
faulthandler.enable(file=open(LOG_FILE, 'a', buffering=1))


def _log_excepcion(tipo, valor, tb):
    """Toda excepcion no atrapada al log, no solo a una consola que se cierra."""
    traceback.print_exception(tipo, valor, tb)


sys.excepthook = _log_excepcion


class ComandVoiceA(QWidget, commandVoiceA):
    btn_checked = Signal(str)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.buttonGroup.buttonClicked.connect(self.state)

    def state(self):
        btn = self.buttonGroup.checkedButton()
        text = btn.text().replace(" ", "_").replace("?", "").replace("¿", "").lower()
        self.btn_checked.emit(text)


class MainWindow(QMainWindow, Ui_MainWindow, ToolBar):
    """Ventana Principal"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.cmb_case.setVisible(False)
        self.cmb_case.setEnabled(False)
        self.create_variables()
        # Mouse para zurdos: sigue a la preferencia del alumno logueado, solo
        # en modo laboratorio (ver core/mouse_zurdo.py).
        mouse_zurdo.conectar()
        self.set_mdi_area()
        self.create_sub_windows()
        layout = (self.horizontalLayout_5, self.layoutTest)

        ToolBar.__init__(self, self.sender, BOXS, APPS, layout, self.frame_sec, self.modules, self.mdi_area, self.size, self.subw)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle(f"LabSim {DISPLAY_VERSION}")
        self.lbl_title.setText(f"LabSim {DISPLAY_VERSION}")
        self.configure_btn()
        if not es_kiosko():
            # En el laboratorio la ventana no se mueve ni se restaura: va
            # a pantalla completa (ver _aplicar_kiosko).
            MoveWindow(self).set_movewindow()
        self._aplicar_kiosko()
        self._setup_layout_status()
        # Kiosko: cada media hora se mira si salió una versión nueva (ver
        # core/actualizacion_kiosko.py y _on_update_disponible).
        self._chequeo_update = None
        if es_kiosko() and getattr(sys, 'frozen', False):
            from core.actualizacion_kiosko import ChequeoPeriodico
            self._chequeo_update = ChequeoPeriodico(__VERSION__, BACKEND_URL, parent=self)
            self._chequeo_update.hay_update.connect(self._on_update_disponible)

    def _on_update_disponible(self):
        """Kiosko: hay versión nueva. Sin sesión iniciada se aplica ya; con
        un alumno atendiendo, al cerrar sesión (ver logout)."""
        if self.data_login:
            self._update_pendiente = True
        else:
            self._actualizar_ahora()

    def _actualizar_ahora(self):
        """Tapa la ventana y actualiza. No vuelve si se instala (la app se
        reinicia); si falla, reintenta hasta lograrlo. Vuelve solo si ya no
        hay nada nuevo o si el equipo se está apagando."""
        if self._actualizando or self._apagando:
            return
        from core.actualizacion_kiosko import actualizar_o_bloquear
        self._actualizando = True
        self._update_pendiente = False
        try:
            actualizar_o_bloquear(__VERSION__, BACKEND_URL,
                                  abortar=lambda: self._apagando)
        finally:
            self._actualizando = False

    def _setup_layout_status(self):
        """Avisa (o no) según de dónde salió el layout, y deja un reintento
        en background si no vino del backend.

        - 'network': todo normal, nada que decir.
        - 'cache': la app está operativa con la copia local; solo se marca
          "sin conexión" en el título. No se interrumpe con un modal: sin
          layout fresco no se pierde nada, el layout casi nunca cambia.
        - None: no hay layout ni cache (instalación nueva que nunca se
          conectó). Ahí sí el aviso duro, porque solo queda el login."""
        self._layout_retry = None
        if LAYOUT_SOURCE == "network":
            return

        detalle = ""
        err = app_layout.last_error
        if err is not None:
            detalle = f"\nDetalle: {err.phase} — {err.detail}"

        if LAYOUT_SOURCE == "cache":
            self._set_offline_title(True)
            print(f"[layout] backend sin respuesta, se usa la cache local.{detalle}")
        else:
            warning = QMessageBox(self)
            warning.setIcon(QMessageBox.Warning)
            warning.setWindowTitle("Sin conexión con el servidor")
            warning.setText(
                "No se pudo obtener la configuración de módulos desde el "
                "servidor y este equipo todavía no tiene una copia local "
                "(es la primera vez que se abre sin conexión).\n\n"
                "Queda solo la ventana de ingreso. La app sigue "
                "reintentando sola: cuando el servidor responda te avisa "
                "para reiniciar y quedar operativo." + detalle
            )
            warning.setStandardButtons(QMessageBox.Ok)
            style_dialog(warning)
            warning.exec()

        self._start_layout_retry()

    def _set_offline_title(self, offline):
        """Marca el modo offline en el título -- único indicador cuando la
        app está corriendo con el layout cacheado."""
        base = f"LabSim {DISPLAY_VERSION}"
        text = f"{base}  ·  sin conexión" if offline else base
        self.setWindowTitle(text)
        self.lbl_title.setText(text)

    def _start_layout_retry(self):
        if not BACKEND_URL:
            return
        self._layout_retry = LayoutRetryThread(BACKEND_URL, parent=self)
        self._layout_retry.recovered.connect(self._on_layout_recovered)
        self._layout_retry.start()

    def _on_layout_recovered(self, data):
        """El backend volvió. Si el layout fresco es igual al que ya está
        cargado (el caso normal: el layout casi nunca cambia) alcanza con
        sacar el aviso. Si cambió, o si arrancamos sin layout, hay que
        reiniciar -- la toolbar se arma una sola vez en __init__."""
        self._layout_retry = None
        self._set_offline_title(False)
        igual = (
            LAYOUT_AVAILABLE
            and data.get("APP") == APPS
            and data.get("BOXS") == BOXS
            and data.get("SECTORS") == SECTORS
        )
        if igual:
            print("[layout] conexión restablecida, cache al día")
            return
        ask = QMessageBox(self)
        ask.setIcon(QMessageBox.Information)
        ask.setWindowTitle("Conexión restablecida")
        ask.setText(
            "El servidor volvió a responder y la configuración de módulos "
            "cambió. Hay que reiniciar LabSim para aplicarla.\n\n"
            "¿Reiniciar ahora?"
        )
        ask.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        ask.setDefaultButton(QMessageBox.Yes)
        style_dialog(ask)
        if ask.exec() == QMessageBox.Yes:
            self._restart_app()

    def _restart_app(self):
        """Relanza el proceso. La cache local ya quedó escrita por el
        reintento, así que el arranque nuevo levanta con el layout fresco
        aunque la red se caiga de nuevo en el medio."""
        self.close()
        if getattr(sys, "frozen", False):
            os.execv(sys.executable, [sys.executable] + sys.argv[1:])
        else:
            os.execv(sys.executable, [sys.executable] + sys.argv)

    def _stop_layout_retry(self):
        if self._layout_retry is not None:
            self._layout_retry.stop()
            self._layout_retry.wait(2000)
            self._layout_retry = None

    def configure_btn(self):
        """Configura los botones de la ventana: iconos propios (dibujados
        en blanco) en vez de texto (_, O, X) para min/max/cerrar"""
        icon_size = QSize(14, 14)
        self.btn_min.setText("")
        self.btn_min.setIcon(titlebar_icon("min"))
        self.btn_min.setIconSize(icon_size)
        self.btn_salir.setText("")
        self.btn_salir.setIcon(titlebar_icon("close"))
        self.btn_salir.setIconSize(icon_size)
        self._update_max_icon()

        self.btn_salir.clicked.connect(self.close)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(self._toggle_max_min)
        self.btn_login.clicked.connect(self.toggle_login)

    # -----------------------------------------------------------------
    # Modo laboratorio (ver core/kiosko.py)
    # -----------------------------------------------------------------

    def _salida_permitida(self):
        """En el laboratorio solo sale un docente logueado: el alumno no
        puede cerrar la app. Fuera del laboratorio, siempre. Si el equipo
        se apaga, también: el sistema no espera a un docente."""
        if not es_kiosko() or self._apagando:
            return True
        return bool(self.data_login) and es_docente(self.data_login.get("permission"))

    def _aplicar_kiosko(self):
        """Pantalla completa y sin botones de ventana. El de cerrar vuelve
        a aparecer con un docente logueado, que es la salida del personal
        (si no, solo quedaría el administrador de tareas)."""
        if not es_kiosko():
            return
        self.btn_min.setVisible(False)
        self.btn_max.setVisible(False)
        self.btn_salir.setVisible(self._salida_permitida())

    def cerrar_por_apagado(self):
        """El equipo se apaga (SIGTERM, ver core/kiosko.atender_apagado):
        cierra como con la X -- sube informes y logs, para los hilos --
        aunque no haya un docente logueado."""
        if self._apagando:
            return
        self._apagando = True
        self.close()
        context.app.quit()

    def changeEvent(self, event):
        super().changeEvent(event)
        # Algo la sacó de pantalla completa (Win+Abajo, doble clic, el
        # sistema): vuelve sola.
        if (es_kiosko() and event.type() == QEvent.Type.WindowStateChange
                and self.isVisible() and not self.isFullScreen()):
            QTimer.singleShot(0, self.showFullScreen)

    def _update_max_icon(self):
        """Cambia el icono de btn_max entre maximizar/restaurar según el
        estado actual de la ventana"""
        kind = "restore" if self.isMaximized() else "max"
        self.btn_max.setText("")
        self.btn_max.setIcon(titlebar_icon(kind))
        self.btn_max.setIconSize(QSize(14, 14))

    def _toggle_max_min(self):
        toggle_max_min(self)
        self._update_max_icon()

    def set_mdi_area(self):
        """Crea el objeto mdi_area"""
        self.mdi_area = MdiArea()
        self.horizontalLayout.addWidget(self.mdi_area)

    def create_variables(self):
        """Crea las variables necesarias para el funcionamiento del programa"""
        self.data_login = None
        # El equipo se está apagando (ver cerrar_por_apagado).
        self._apagando = False
        # Kiosko: versión nueva esperando a que se cierre la sesión, y
        # actualización en curso (ver _on_update_disponible).
        self._update_pendiente = False
        self._actualizando = False
        self.data_current = None
        self.data_current_key = None
        self.paciente_actual = None
        self.debug_mkg_dialog = None
        self.subw = None
        self.sectors_lbl = SECTORS
        # El Storage se indexa por pos_z, que NO es un índice denso: el
        # layout tiene huecos (hoy falta el 12) y los pos_z pueden pasarse
        # de la cantidad de apps. Dimensionarlo con len(APPS) dejaba el
        # último módulo justo afuera -- abrirlo reventaba con IndexError en
        # Storage.is_full. Manda el pos_z más alto, no cuántas apps hay.
        self.modules = Storage(max((app[2] for app in APPS.values()), default=0) + 1)
        self.var_list_word = Storage(2)
        self.log_uploader = None
        self.sync_thread = None
        self.report_autosave = ReportAutosave(self._modulos_examen, self)
        self._layout_retry = None
        self._layout_sin_override = None
        self.cronometro_segundos = 0
        self.cronometro_timer = QTimer(self)
        self.cronometro_timer.setInterval(1000)
        self.cronometro_timer.timeout.connect(self._tick_cronometro)

    def create_sub_windows(self):
        """Crea las subventanas"""
        self.create_sw_login()

    def create_sw_login(self):
        """Crea la subventana login"""
        subw_login = FrameSubMdi(Ui_login.MainLogin())
        subw_login.obj.data_login_signal.connect(self._data_login)
        self.subw = {"LOGIN": subw_login}

    @Slot(dict)
    def _data_login(self, data):
        """Recibe el data de la subventana login"""
        user = data["user"]
        if not user:
            self.logout()
        else:
            reset_backend_session()
            show_hide(self.modules, 0)
            self.lbl_name.setText(f"{user}")
            self.btn_login.setText("Cerrar Sesión")
            self.data_login = data
            # Atajos y mouse del alumno: vienen con el login, así lo siguen
            # a cualquier equipo (ver core/preferencias.py).
            preferencias().cargar(data.get("prefs") or {})
            self._aplicar_kiosko()
            self._apply_admin_overrides_if_any()
            LOCAL_LOG_QUEUE.push("session_login", {
                "user": data.get("user"),
                "name": data.get("name"),
                "permission": data.get("permission"),
            })
            try:
                self.refresh_data()
            except requests.RequestException as exc:
                # Servidor caído/inestable justo después del login (ver
                # BackendClient: nunca se cuelga, propaga la excepción) --
                # sin este catch, el traceback subía sin manejar y Qt
                # dejaba la ventana principal en un estado roto. Avisamos
                # y devolvemos la ventana de login para reintentar, en vez
                # de crashear.
                QMessageBox.warning(
                    self,
                    "Sin conexión con el servidor",
                    "Se inició sesión, pero no se pudo cargar la información "
                    "desde el backend (agenda, casos, etc.). Verifica tu "
                    "conexión e intenta ingresar nuevamente."
                    f"\nDetalle: {exc}",
                )
                self.data_login = None
                self._limpiar_barras()
                self._restaurar_layout()
                self.lbl_name.setText("")
                self.btn_login.setText("Ingresar")
                login_subw = self.subw.get("LOGIN") if self.subw else None
                if login_subw is not None:
                    login_subw.obj._enable_widgets()
                return
            self.btns_actions()
            self._warn_if_no_modules()
            self._start_log_uploader()
            self._start_sync_thread()

    def _warn_if_no_modules(self):
        """Aviso explícito cuando el backend devuelve modules=[]: la sesión
        entra bien y las secciones (boxes) se dibujan igual, pero ningún
        equipo queda visible (ver SubWindow._module_visible) y la ventana
        parece cargada a medias sin decir por qué. Pasa cuando la cuenta no
        quedó asignada a ningún curso, o cuando ese curso todavía no tiene
        módulos habilitados en el panel admin."""
        if not self.data_login:
            return
        modules = self.data_login.get("modules")
        if modules is None or modules:
            return
        QMessageBox.warning(
            self,
            "Sin módulos habilitados",
            "Iniciaste sesión, pero tu cuenta no tiene ningún módulo "
            "habilitado: se ven las secciones, pero no los equipos.\n\n"
            "Revisa en el panel admin (Cursos) que tu usuario esté asignado "
            "al curso y que ese curso tenga módulos habilitados.",
        )

    def _apply_admin_overrides_if_any(self):
        """Admin (permission 777) ve toda la estructura sin filtrar:
        todos los boxes activos, todos los módulos como "pre" (no gris).
        El layout llega igual para todos desde /api/layout; este override
        es local porque la metadata estructural no debería filtrarse por
        rol -- un admin probando qué hay en cada box no tiene que esperar
        a que alguien le habilite Box_2 a mano en apps.json.
        Mutamos self.apps/self.boxs in-place: son los mismos dicts que
        ToolBar tiene referenciados (Python pasa dict por referencia), y
        btns_seccion/chargeBtnsArea corren DESPUÉS de este método, así que
        ven la versión overridden. No-admin: no-op (el filtro por curso
        sigue pasando por GATED_MODULE_CODES / data_login["modules"])."""
        if not self.data_login:
            return
        if self.data_login.get("permission") != 777:
            return
        # Se guarda lo que vino del layout para devolverlo al cerrar sesión
        # (ver _restaurar_layout): si no, el alumno que entra después del
        # admin hereda sus boxes y módulos habilitados.
        if self._layout_sin_override is None:
            self._layout_sin_override = (
                {k: box[0] for k, box in self.boxs.items()},
                {k: app[5] for k, app in self.apps.items() if len(app) > 5},
            )
        for box in self.boxs.values():
            box[0] = True
        for app in self.apps.values():
            # índice 5 = state ("pre" / "development"). Forzamos "pre"
            # para que chargeBtnsArea no haga btn.setDisabled(True).
            if len(app) > 5:
                app[5] = "pre"

    def _restaurar_layout(self):
        """Deshace _apply_admin_overrides_if_any (in-place, por lo mismo)."""
        if self._layout_sin_override is None:
            return
        boxs, apps = self._layout_sin_override
        for k, activo in boxs.items():
            self.boxs[k][0] = activo
        for k, state in apps.items():
            self.apps[k][5] = state
        self._layout_sin_override = None

    def _limpiar_barras(self):
        """Saca los botones de secciones, de equipos y de acciones: sin
        sesión la barra queda vacía como al abrir la app (btns_seccion y
        btns_actions los vuelven a armar en el próximo login)."""
        for layout in (*self.layouts, self.layoutAction):
            self._clear_layout(layout)
        for attr in ("btn_chat_paciente", "btn_cmd_voice", "btn_list_words",
                     "btn_cerrar_ventanas", "btn_configuracion",
                     "btn_debug_mkg", "btn_bandeja_oirs"):
            setattr(self, attr, None)

    def _logged_in_client(self):
        """Cliente del backend con la sesión que dejó el login, o None si ese
        login no llegó a dejar un token (usado por log_uploader y sync_thread)."""
        client = BackendClient(Preferences.get("BACKEND_URL"), context.get_resource('json/session.json'))
        return client if client.is_logged_in() else None

    def _start_log_uploader(self):
        """Sube en lotes los logs de acciones acumulados (ver log_queue.py).
        Solo aplica si el login realmente dejó un token."""
        client = self._logged_in_client()
        if client is None:
            return
        self.log_uploader = LogUploaderThread(LOCAL_LOG_QUEUE, client)
        self.log_uploader.start()

    def _stop_log_uploader(self):
        if self.log_uploader is not None:
            self.log_uploader.stop()
            self.log_uploader = None

    def _start_sync_thread(self):
        """Poll periódico al backend (ver sync_thread.py): si el admin edita
        la agenda desde otra terminal, esta refresca sola en el próximo ciclo."""
        client = self._logged_in_client()
        if client is None:
            return
        self.sync_thread = SyncThread(client)
        self.sync_thread.sync_ok.connect(self._on_backend_sync)
        self.sync_thread.start()

    def _on_backend_sync(self, _delta):
        # refresh_async: este callback corre en cada ciclo de polling (15s);
        # refresh() normal dispara una consulta de red nueva y BLOQUEANTE
        # (Shedule() -> get_full_state), que con el backend caído congelaba
        # toda la ventana hasta 10s por ciclo (timeout SSL).
        agenda_win = self.subw.get("AGENDA") if self.subw else None
        if agenda_win is not None:
            agenda_win.obj.refresh_async()
        inbox.actualizar_badge(self)
        app_config_store.update_from_sync(_delta.get("config"))

    def _stop_sync_thread(self):
        if self.sync_thread is not None:
            self.sync_thread.stop()
            self.sync_thread = None

    def toggle_login(self):
        """Cierra sesión de inmediato si hay una activa, si no abre la ventana de login"""
        if self.data_login:
            self.logout()
        else:
            self.activate_subwindow(self.size, "LOGIN", self.subw["LOGIN"])

    def logout(self):
        """Cierra la sesión actual"""
        self._guardar_informes_al_salir()
        LOCAL_LOG_QUEUE.push("session_logout", {
            "user": self.data_login.get("user") if self.data_login else None,
        })
        if self.log_uploader is not None:
            # Sube ahora mismo: si esperamos al ciclo normal, este evento
            # queda en la cola local hasta el próximo login (el hilo se
            # detiene abajo).
            self.log_uploader.flush_now()
        self._stop_log_uploader()
        self._stop_sync_thread()
        self._reset_cronometro()
        self._close_sub_windows()
        self._limpiar_barras()
        self._restaurar_layout()
        login_subw = self.subw.get("LOGIN") if self.subw else None
        if login_subw is not None:
            # El login se logueó via toggle_login (btn "Cerrar Sesión"), no
            # via el btn "Salir" propio de la ventana de login -- por eso
            # login.py:logout() (que limpia y reactiva los campos) nunca se
            # ejecuta acá. Sin esto, la próxima vez que se abre la ventana
            # de login los campos quedan deshabilitados con el usuario
            # anterior escrito.
            login_subw.obj._enable_widgets()
        self.lbl_name.setText("")
        self.btn_login.setText("Ingresar")
        if self.debug_mkg_dialog is not None:
            # el panel muestra los umbrales del caso: no puede sobrevivir al
            # cierre de sesión
            self.debug_mkg_dialog.close()
            self.debug_mkg_dialog = None
        self.data_login = None
        self.data_current = None
        self.data_current_key = None
        self.paciente_actual = None
        preferencias().limpiar()
        self._aplicar_kiosko()
        if self._update_pendiente:
            # Kiosko: salió una versión nueva durante la atención.
            QTimer.singleShot(0, self._actualizar_ahora)

    def _start_cronometro(self):
        """Arranca (o reinicia si ya venía corriendo) el cronómetro de
        atención al presionar "atender" -- se muestra al centro de la barra
        de botones de equipos/ventanas MDI."""
        self.cronometro_segundos = 0
        self.lbl_cronometro.setText("00:00:00")
        self.cronometro_timer.start()

    def _stop_cronometro(self):
        """Detiene el cronómetro (al evolucionar) dejando el tiempo final
        visible hasta el próximo "atender" o el logout"""
        self.cronometro_timer.stop()

    def _reset_cronometro(self):
        """Limpia el cronómetro (logout)"""
        self.cronometro_timer.stop()
        self.cronometro_segundos = 0
        self.lbl_cronometro.setText("")

    def _tick_cronometro(self):
        self.cronometro_segundos += 1
        minutos, segundos = divmod(self.cronometro_segundos, 60)
        horas, minutos = divmod(minutos, 60)
        self.lbl_cronometro.setText(f"{horas:02d}:{minutos:02d}:{segundos:02d}")

    def _close_sub_windows(self):
        """Cierra todas las subventanas abiertas (excepto LOGIN) y deshidrata sus datos"""
        login_pos_z = self.apps["LOGIN"][2]
        for pos_z in self.modules.length(True):
            if pos_z == login_pos_z:
                continue
            sub = self.modules.get(pos_z)
            if sub is not None:
                self.mdi_area.removeSubWindow(sub)
                sub.deleteLater()
                self.modules.set(pos_z, None)

        login_subw = self.subw.get("LOGIN") if self.subw else None
        self.subw = {"LOGIN": login_subw} if login_subw else None

        for attr in ("subw_a", "subw_w", "subw_z", "subw_ac", "subw_ot", "subw_abr",
                     "subw_aabr", "subw_eoas", "subw_vemp"):
            if hasattr(self, attr):
                delattr(self, attr)

    def atender_paciente(self, key):
        """
        Inicia o retoma la atención (estado 'atendiendo'), carga el caso e hidrata
        los módulos. Se llama tanto la primera vez como al retomar un paciente que
        ya estaba en atención (tras reabrir la app o al volver desde otro paciente).
        """
        if es_docente(self.data_login["permission"]):
            return  # admin/docente usan atender_paciente_prueba() o atender_paciente_base()
        self._atender_caso(key, es_prueba=False)

    def atender_paciente_base(self, key):
        """
        Admin/docente con "Guardar esta atención" marcado en la agenda (ver
        Agenda.chk_guardar_base): mismo ciclo real que atender_paciente() --
        SÍ marca "atendiendo" y SÍ guarda el chat con el paciente -- pero bajo
        la propia cuenta del docente, para crear una atención base con la que
        comparar después a los alumnos. A diferencia de
        atender_paciente_prueba(), esto deja rastro real en la base de datos.
        """
        if not es_docente(self.data_login["permission"]):
            return  # esta variante es solo para admin/docente
        self._atender_caso(key, es_prueba=False)

    def atender_paciente_prueba(self, key):
        """
        Admin: carga el caso `key` en los módulos (audiómetro, chat con el
        paciente, etc.) para probarlo. A diferencia de atender_paciente(), NO
        marca "atendiendo" ni escribe en attendances/agenda -- no deja rastro
        en la base de datos, es solo para verificar que un caso funciona.
        """
        self._atender_caso(key, es_prueba=True)

    def cerrar_atencion_prueba(self, nota):
        """Admin/profe: descarga el caso de prueba de los módulos, igual que
        cerrar_atencion(), pero sin marcar "atendido" ni escribir en
        attendances/agenda -- no deja rastro en la base de datos."""
        if not es_docente(self.data_login["permission"]):
            return  # solo admin/profe usan el ciclo de prueba
        self.report_autosave.detener()
        self.data_current_key = None
        self.data_current = None
        self.paciente_actual = None
        self._hydrate_modules()
        self.statusbar.showMessage(f"[PRUEBA] Atención cerrada (no se guarda): {nota[:80]}")
        self._stop_cronometro()

    def _atender_caso(self, key, *, es_prueba):
        """Lógica común a atender_paciente() y atender_paciente_prueba() --
        difieren solo en si se marca "atendiendo" en la agenda/backend y en
        el appointment_id que queda asociado al chat (ver docstrings de cada
        una)."""
        if self._otra_atencion_abierta(key):
            return

        shedule = Shedule()
        agenda = shedule.data.setdefault("agenda_1", {})
        entry = agenda.get(key)
        if entry is None:
            return

        case_id = entry.case_id or None
        if not case_id:
            return
        cases = CasesOffline().get_cases()
        if case_id not in cases:
            return  # el caso fue borrado/no sincronizó -- no dejamos marcar "atendiendo" un caso inexistente

        if not es_prueba:
            marcar_entry_atendiendo(entry, self.data_login["user"])
            shedule.set(shedule.data)

        self.data_current = cases[case_id]
        self.data_current_key = key

        if not es_prueba and self.subw and "AGENDA" in self.subw:
            self.subw["AGENDA"].obj.refresh()

        self._hydrate_modules()
        if self.data_current:
            self.changeStateBtnAreas(self.frameAction, self.data_current["box"])
        self.report_autosave.iniciar()
        if not es_prueba:
            self._recuperar_informes(key)

        rut = entry.rut
        nombre = f"{entry.nombre} {entry.apellido}".strip()
        procedimiento = entry.procedimiento
        try:
            edad, _, _ = CreatePatient().get_age_from_rut(int(rut))
        except (TypeError, ValueError):
            edad = 0

        if es_prueba:
            appointment_id = None  # "prueba" -- nunca se guarda el chat de esto
        else:
            try:
                appointment_id = int(key)
            except (TypeError, ValueError):
                appointment_id = None

        self.paciente_actual = {
            "case_id": case_id, "nombre": nombre or "el paciente",
            "edad": edad, "procedimiento": procedimiento, "appointment_id": appointment_id,
        }

        if es_prueba:
            self.statusbar.showMessage(f"[PRUEBA] Caso cargado: {nombre or case_id} (no se guarda atención)")
        else:
            self.statusbar.showMessage(f"Estás atendiendo a: RUT {rut} — Fecha de nacimiento {entry.fecha_nac}")

        self._start_cronometro()

    def cerrar_atencion(self, key, nota):
        """Cierra la atención (estado 'atendido') guardando la nota de atención del estudiante"""
        if es_docente(self.data_login["permission"]):
            return  # admin/docente usan cerrar_atencion_prueba() o cerrar_atencion_base()
        self._cerrar_atencion_real(key, nota)

    def cerrar_atencion_base(self, key, nota):
        """Contraparte de atender_paciente_base(): cierra de verdad (estado
        'atendido', chat guardado) la atención base del docente."""
        if not es_docente(self.data_login["permission"]):
            return  # esta variante es solo para admin/docente
        self._cerrar_atencion_real(key, nota)

    def _cerrar_atencion_real(self, key, nota):
        """Lógica común a cerrar_atencion() (alumno) y cerrar_atencion_base()
        (docente en modo "guardar base")."""
        shedule = Shedule()
        agenda = shedule.data.setdefault("agenda_1", {})
        entry = agenda.get(key)
        if entry is None:
            return

        if self.data_current_key == key:
            # Los informes de los módulos "de examen" suben ANTES de marcar
            # 'atendido': shedule.set() empuja ese estado al backend en el
            # acto, y desde ahí report_upload.php rechaza con 409 (el
            # informe queda fijo). Con el orden al revés no se guardaba
            # ninguno. Además tiene que ser antes de _hydrate_modules(),
            # que les saca appointment_id/data_login.
            self._subir_informes()

        marcar_entry_atendido(entry, self.data_login["user"], nota)
        shedule.set(shedule.data)
        self._stop_cronometro()

        if self.data_current_key == key:
            self.data_current_key = None
            self.data_current = None
            self.paciente_actual = None
            self._hydrate_modules()

        if self.subw and "AGENDA" in self.subw:
            self.subw["AGENDA"].obj.refresh()

        self.statusbar.clearMessage()

    def _hydrate_modules(self):
        """Carga self.data_current en los módulos ya construidos, o los
        deshidrata (data_current=None) para que dejen de loguear acciones
        bajo el caso/paciente ya cerrado."""
        for attr in ("subw_a", "subw_z", "subw_w", "subw_ac", "subw_ot", "subw_abr",
                     "subw_aabr", "subw_eoas", "subw_vemp"):
            try:
                getattr(self, attr).obj.la_super(self.data_current, self.data_current_key)
            except AttributeError:
                pass

    def load_sub_windows(self):
        """Carga las subventanas"""
        from abr.AabrMainWindow import AabrMainWindow
        from abr.AbrMainWindow import AbrMainWindow
        from audiometria import Audiometer, ListWords
        from impedanciometria import Z
        from oae.OaeMainWindow import OaeMainWindow
        from vemp.VempMainWindow import VempMainWindow

        self.subw_a = FrameSubMdi(Audiometer.Audiometer(self.data_current))
        self.subw_ac = FrameSubMdi(Acumetria.Acumetria(self.data_current))
        self.subw_ot = FrameSubMdi(Otoscopia.Otoscopia(self.data_current))
        self.subw_w = FrameSubMdi(ListWords.ListWords(self.data_current))
        self.subw_z = FrameSubMdi(Z.ZControl())
        self.subw_abr = FrameSubMdi(AbrMainWindow(data_login=self.data_login))
        self.subw_aabr = FrameSubMdi(AabrMainWindow(data_login=self.data_login))
        self.subw_eoas = FrameSubMdi(OaeMainWindow(data_login=self.data_login))
        self.subw_vemp = FrameSubMdi(VempMainWindow(data_login=self.data_login))

        self.subw.update({
            "A": self.subw_a,
            "AC": self.subw_ac,
            "OT": self.subw_ot,
            "ABR": self.subw_abr,
            "AABR": self.subw_aabr,
            "VEMP": self.subw_vemp,
            "EOAS": self.subw_eoas,
            "AGENDA": FrameSubMdi(Agenda.Agenda(self.data_login["permission"], self)),
            "CVOICE": FrameSubMdi(ComandVoiceA()),
            "CHAT": FrameSubMdi(ChatPacienteWidget(self.data_login.get("name"))),
            "FICHA": FrameSubMdi(Agenda.FichaClinicaWidget(), expand=True),
            "EVOLUCION": FrameSubMdi(Agenda.EvolucionWidget(), expand=True),
            "INBOX": FrameSubMdi(inbox.InboxWidget(self)),
            "MIS_PACIENTES": FrameSubMdi(mis_pacientes.MisPacientesWidget(self)),
            "W": self.subw_w,
            "Z": self.subw_z,
        })

        self._hydrate_modules()
        self.connect_signals()
        # Al esconder un módulo de examen se sube lo que tenga (ver
        # core/report_autosave.py).
        for attr in self._ATTRS_EXAMEN:
            frame = getattr(self, attr)
            frame.visibility_changed.connect(
                lambda visible, m=frame.obj: None if visible else self.report_autosave.guardar(m))

    def activate_listWords(self):
        if self.subw_a.obj.lbl_prueba.text() == "Logoaudiometría":
            self.activate_auto("W")

    def speechlist_mode(self, state):
        self.subw["W"].obj.update_state(state)

    def connect_signals(self):
        self.subw["A"].visibility_changed.connect(self._on_audiometro_visibility)
        self.subw["CVOICE"].obj.btn_checked.connect(self.subw["A"].obj.supra)
        self.subw["A"].obj.signal_speech.connect(self.speechlist_mode)
        self.subw["W"].obj.level_changed.connect(
            lambda level: self.subw["A"].obj._on_player_level(self.subw["W"].obj.channel, level))

    def refresh_data(self):
        self.load_sub_windows()
        self.btns_seccion()
        if self.data_current:
            self.changeStateBtnAreas(self.frameAction, self.data_current["box"])

    def btns_actions(self):
        for i in reversed(range(self.layoutAction.count())):
            widget = self.layoutAction.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        # los botones se recrean abajo: las refs viejas quedan apuntando a
        # widgets ya destruidos (_update_action_buttons las usa)
        self.btn_cmd_voice = None
        self.btn_list_words = None
        self.btn_debug_mkg = None
        if self._module_visible("CHAT"):
            self.btn_chat_paciente = QPushButton("Hablar con el paciente")
            self.btn_chat_paciente.setObjectName("btn_chat_paciente")
            self.btn_chat_paciente.clicked.connect(self.abrir_chat_paciente)
            self.layoutAction.addWidget(self.btn_chat_paciente)
        if self._module_visible("CVOICE"):
            self.btn_cmd_voice = QPushButton("Comandos de voz")
            self.btn_cmd_voice.setObjectName("btn_CVOICE")
            self.btn_cmd_voice.clicked.connect(self.activate_soft)
            self.layoutAction.addWidget(self.btn_cmd_voice)
        if self._module_visible("W"):
            self.btn_list_words = QPushButton("Listas de Palabras")
            self.btn_list_words.setObjectName("btn_W")
            self.btn_list_words.clicked.connect(self.activate_listWords)
            self.layoutAction.addWidget(self.btn_list_words)
        # Rescate: una subventana tapada o corrida se cierra desde acá sin
        # tener que encontrarle la ✕.
        self.btn_cerrar_ventanas = QPushButton("Cerrar ventanas")
        self.btn_cerrar_ventanas.setObjectName("btn_cerrar_ventanas")
        self.btn_cerrar_ventanas.clicked.connect(self.cerrar_ventanas)
        self.layoutAction.addWidget(self.btn_cerrar_ventanas)
        # Atajos de teclado y mouse para zurdos, guardados en el perfil.
        self.btn_configuracion = QPushButton("Configuración")
        self.btn_configuracion.setObjectName("btn_configuracion")
        self.btn_configuracion.clicked.connect(lambda: configuracion.abrir(self))
        self.layoutAction.addWidget(self.btn_configuracion)
        if es_docente((self.data_login or {}).get("permission")):
            # Panel de depuración: umbrales *_mkg cargados y rangos de
            # enmascaramiento en vivo. Solo admin/docente -- al alumno le
            # entregaría las respuestas del caso.
            self.btn_debug_mkg = QPushButton("Depurar enmascaramiento")
            self.btn_debug_mkg.setObjectName("btn_debug_mkg")
            self.btn_debug_mkg.clicked.connect(self.abrir_debug_mkg)
            self.layoutAction.addWidget(self.btn_debug_mkg)
        self._update_action_buttons()

    def cerrar_ventanas(self):
        """Oculta todas las subventanas normales, igual que su ✕ (el
        contenido se conserva). Los módulos a pantalla completa (ABR, VEMP,
        EOAS) quedan: ocupan todo el MDI, no se pueden perder, y cerrarlos a
        mitad de un examen sería un accidente."""
        login_pos_z = self.apps["LOGIN"][2]
        login = self.modules.get(login_pos_z)
        for sub in self.mdi_area.subWindowList():
            if sub is login or sub.isHidden() or is_full_window(sub):
                continue
            sub.hide()

    def abrir_debug_mkg(self):
        """Abre (o trae al frente) el panel de depuración de
        enmascaramiento. No modal: se deja abierto al lado del audiómetro
        para ver cómo cambian los rangos al mover las perillas."""
        if not es_docente((self.data_login or {}).get("permission")):
            return
        if getattr(self, "debug_mkg_dialog", None) is None:
            self.debug_mkg_dialog = DebugMkgDialog(self)
        self.debug_mkg_dialog.show()
        self.debug_mkg_dialog.raise_()
        self.debug_mkg_dialog.activateWindow()
        self.debug_mkg_dialog.refresh()

    def _on_audiometro_visibility(self, visible):
        """Al esconder el audiómetro se van con él sus accesorios: listas de
        palabras y comandos de voz operan sobre sus canales, solos no sirven."""
        self._update_action_buttons()
        if visible:
            return
        for name in ("W", "CVOICE"):
            if name in self.apps and name in self.subw:
                self.close_sub_window(name)

    def _update_action_buttons(self):
        """Comandos de voz y Listas de palabras son controles del audiómetro
        (dictan/reproducen por sus canales): sin el audiómetro abierto no
        tienen sentido, así que se muestran solo con él a la vista."""
        subw_a = self.subw.get("A") if self.subw else None
        con_audiometro = subw_a is not None and subw_a.isVisible()
        for btn in (getattr(self, "btn_cmd_voice", None),
                    getattr(self, "btn_list_words", None)):
            if btn is not None:
                btn.setVisible(con_audiometro)

    def abrir_chat_con(self, case_id, nombre, edad, procedimiento, appointment_id=None):
        """Abre (o trae al frente) la subventana MDI de chat con el paciente,
        reapuntada al caso indicado. appointment_id=None = no se guarda el
        chat (ver ChatPacienteWidget.set_paciente)."""
        self.subw["CHAT"].obj.set_paciente(case_id, nombre, edad, procedimiento, appointment_id)
        self.activate_auto("CHAT")

    # -----------------------------------------------------------------
    # Informes de examen (ver core/report_autosave.py)
    # -----------------------------------------------------------------

    _ATTRS_EXAMEN = ("subw_abr", "subw_aabr", "subw_vemp", "subw_eoas", "subw_ot")

    def _modulos_examen(self):
        return [getattr(self, a).obj for a in self._ATTRS_EXAMEN
                if getattr(self, a, None) is not None]

    def _subir_informes(self):
        """Subida final y sincrónica de todos los informes. Primero espera
        las subidas automáticas en curso: si una vieja terminara después,
        pisaría esta."""
        self.report_autosave.detener()
        for modulo in self._modulos_examen():
            try:
                modulo.submit_report()
            except Exception as exc:
                print(f"{type(modulo).__name__}: no se pudo subir el informe: {exc}")

    # El ABR recupera lo suyo solo (AbrMainWindow.restore_current), junto
    # con la lista de sesiones anteriores.
    _TIPO_POR_MODULO = {"subw_aabr": "AABR", "subw_vemp": "VEMP",
                        "subw_eoas": "EOA", "subw_ot": "OTOSCOPIA"}

    def _recuperar_informes(self, key):
        """Retomar una atención: vuelve lo que ya se había guardado solo."""
        try:
            appointment_id = int(key)
        except (TypeError, ValueError):
            return
        destinos = {tipo: getattr(self, attr).obj
                    for attr, tipo in self._TIPO_POR_MODULO.items()
                    if getattr(self, attr, None) is not None}
        self.report_autosave.recuperar(
            appointment_id, destinos,
            lambda cita: str(self.data_current_key) == str(cita))

    def _otra_atencion_abierta(self, key):
        """Atender a otro paciente con una atención real abierta vaciaba los
        módulos de examen sin subir nada: las curvas del anterior se
        perdían. Ahora se pide cerrar primero."""
        actual = self.data_current_key
        if actual is None or actual == key:
            return False
        if (self.paciente_actual or {}).get("appointment_id") is None:
            return False  # "prueba" del docente: no hay nada que perder
        nombre = (self.paciente_actual or {}).get("nombre") or "otro paciente"
        dlg = QMessageBox(QMessageBox.Icon.Warning, "Atención abierta",
                          f"Tienes a {nombre} en atención. Ciérrala primero "
                          "(Cerrar/Evolucionar en la agenda) para que sus exámenes "
                          "queden guardados.",
                          QMessageBox.StandardButton.Ok, self)
        style_dialog(dlg)
        dlg.exec()
        return True

    def _guardar_informes_al_salir(self):
        """Cerrar la app o la sesión con la atención abierta: los informes
        se suben igual (la atención sigue 'atendiendo' y se puede retomar)."""
        if self.data_current_key is None:
            return
        if (self.paciente_actual or {}).get("appointment_id") is None:
            return
        self._subir_informes()

    def abrir_abr_consulta(self, data, aviso):
        """"Mis pacientes" -> Ver en el ABR: abre el ABR de una atención ya
        cerrada, solo para mirarlo (ver AbrMainWindow.open_past)."""
        if not self._module_visible("ABR") or getattr(self, "subw_abr", None) is None:
            QMessageBox.information(self, "Ver en el ABR",
                                    "El módulo ABR no está habilitado en tu curso.")
            return
        if self.data_current_key is not None or not self.subw_abr.obj.open_past(data, aviso):
            QMessageBox.information(
                self, "Ver en el ABR",
                "Tienes una atención en curso. Ciérrala para mirar exámenes anteriores.")
            return
        # activate_auto alterna: con el ABR ya a la vista lo escondería.
        pos_z = self.apps["ABR"][2]
        sub = self.modules.get(pos_z) if self.modules.is_full(pos_z) else None
        if sub is not None and not sub.isHidden():
            raise_window(sub)
        else:
            self.activate_auto("ABR")

    def abrir_ficha_con(self, html, on_chat=None):
        """Abre (o trae al frente) la subventana MDI de ficha clínica,
        reapuntada al paciente indicado."""
        self.subw["FICHA"].obj.set_ficha(html, on_chat)
        self.activate_auto("FICHA")

    def abrir_evolucion(self, nombre_paciente, on_guardar):
        """Abre (o trae al frente) la subventana MDI de evolución, reapuntada
        al paciente/callback indicado (ver Agenda._cerrar_atencion y
        Agenda._cerrar_atencion_prueba)."""
        self.subw["EVOLUCION"].obj.set_contexto(nombre_paciente, on_guardar)
        self.activate_auto("EVOLUCION")

    def abrir_chat_paciente(self):
        """Abre el chat con el paciente simulado por LLM del caso que se está atendiendo."""
        if not self.paciente_actual:
            QMessageBox.information(self, "Hablar con el paciente", "No estás atendiendo un paciente.")
            return
        p = self.paciente_actual
        self.abrir_chat_con(p["case_id"], p["nombre"], p["edad"], p["procedimiento"], p.get("appointment_id"))

    def closeEvent(self, event):
        if not self._salida_permitida():
            # Laboratorio: ni la X (que no está) ni Alt+F4 cierran la app.
            event.ignore()
            return
        self._guardar_informes_al_salir()
        if self.log_uploader is not None:
            # Igual que en logout(): sin esto, acciones recién logueadas quedan
            # en la cola local hasta el próximo login si se cierra con la X.
            self.log_uploader.flush_now()
        self._stop_log_uploader()
        self._stop_sync_thread()
        self._stop_layout_retry()
        super().closeEvent(event)


def _auto_update_forzado():
    """LABSIM_AUTO_UPDATE=1: se actualiza sin preguntar, y si falla se abre
    la versión actual. El kiosko no pasa por acá: ahí la actualización es
    obligatoria (core/actualizacion_kiosko.py)."""
    return os.environ.get("LABSIM_AUTO_UPDATE", "").strip() == "1"


def _download_and_apply(update, silencioso=False):
    """Baja y aplica `update` (actualización o reparación) con barra de
    progreso. No vuelve si el swap sale bien: la app se reinicia sola.

    silencioso: si falla, se sigue con la versión actual sin cartel -- en
    un kiosko nadie lo cierra y la app quedaría trabada detrás."""
    from core.updater import apply_update_and_restart
    progress = QProgressDialog("Preparando actualización...", None, 0, 0)
    progress.setWindowTitle("Actualizando LabSim")
    progress.setWindowModality(Qt.WindowModal)
    progress.setCancelButton(None)
    progress.setMinimumDuration(0)
    progress.setAutoClose(False)
    progress.setAutoReset(False)
    progress.show()
    style_dialog(progress)
    context.app.processEvents()

    def on_progress(stage, current, total, hop, hops):
        paso = f" ({hop}/{hops})" if hops > 1 else ""
        if stage == "download":
            if total:
                progress.setRange(0, total)
                progress.setValue(current)
                cur_mb = current / (1024 * 1024)
                tot_mb = total / (1024 * 1024)
                progress.setLabelText(
                    f"Descargando actualización{paso}... {cur_mb:.1f} / {tot_mb:.1f} MB"
                )
            else:
                progress.setRange(0, 0)
                cur_mb = current / (1024 * 1024)
                progress.setLabelText(f"Descargando actualización{paso}... {cur_mb:.1f} MB")
        elif stage == "extract":
            progress.setRange(0, 0)
            progress.setLabelText(f"Instalando actualización{paso}...")
        elif stage == "restart":
            progress.setLabelText("Reiniciando LabSim...")
        context.app.processEvents()

    try:
        apply_update_and_restart(update, on_progress=on_progress)  # no vuelve si tiene éxito
    except Exception as exc:
        # Falla de red o archivo corrupto a mitad de la descarga/extracción:
        # no dejamos morir la app acá, se sigue con la versión actual instalada.
        progress.close()
        if silencioso:
            print(f"Actualización automática fallida, sigue la versión actual: {exc}")
            return
        warning = QMessageBox()
        warning.setIcon(QMessageBox.Warning)
        warning.setWindowTitle("Actualización fallida")
        warning.setText(
            f"No se pudo completar la actualización, se abre la versión actual.\n{exc}"
        )
        warning.setStandardButtons(QMessageBox.Ok)
        style_dialog(warning)
        warning.exec()
    else:
        # apply_update_and_restart solo vuelve si el asset tenía una
        # estructura inesperada (no lanzó, no hizo el swap) -- el
        # dialog quedaría abierto para siempre si no se cierra acá.
        progress.close()


def _precargar_modulos():
    """Importa los módulos de examen mientras se muestra el login.

    Son los que traen numpy y pyqtgraph (~0,45 s): se importan recién en
    load_sub_windows, después del login, para que la ventana aparezca antes.
    Se precargan acá, con la ventana ya a la vista y el alumno escribiendo
    usuario y clave, así el login no paga el import. Si algo falla, se
    ignora: load_sub_windows lo vuelve a importar y ahí sí se ve el error."""
    try:
        import abr.AabrMainWindow  # noqa: F401
        import abr.AbrMainWindow  # noqa: F401
        import audiometria.Audiometer  # noqa: F401
        import audiometria.ListWords  # noqa: F401
        import impedanciometria.Z  # noqa: F401
        import oae.OaeMainWindow  # noqa: F401
        import vemp.VempMainWindow  # noqa: F401
    except Exception:
        traceback.print_exc()


def _check_and_apply_update():
    """Busca una versión nueva en GitHub Releases y, si el usuario acepta,
    la descarga y aplica (reemplaza el build actual y reinicia -- no vuelve
    si tiene éxito). Solo se llama en build congelada (PyInstaller); en modo
    dev correr desde código fuente ya es la versión más nueva."""
    from core.updater import check_for_update
    update = check_for_update(__VERSION__, backend_url=BACKEND_URL)
    if update is None:
        return
    tag = update["tag"]
    notes = update.get("notes") or ""
    if _auto_update_forzado():
        _download_and_apply(update, silencioso=True)
        return
    if update.get("repair"):
        # El ejecutable instalado no coincide con el de la release que dice
        # tener: un swap que copió a medias (ver core/updater.py
        # _check_install_integrity). No es "hay algo nuevo", es "lo que
        # tenés no es lo que dice ser".
        prompt = QMessageBox()
        prompt.setIcon(QMessageBox.Warning)
        prompt.setWindowTitle("Instalación incompleta")
        prompt.setText(
            f"La instalación figura como {DISPLAY_VERSION} pero el programa "
            "instalado no es ese: una actualización anterior se copió a "
            "medias, así que estás corriendo una versión vieja.\n"
            "Se descargará el paquete completo y se reinstalará.\n"
            "¿Reparar ahora? La aplicación se cerrará y volverá a abrir sola."
        )
        prompt.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        prompt.setDefaultButton(QMessageBox.Yes)
        style_dialog(prompt)
        if prompt.exec() != QMessageBox.Yes:
            return
        _download_and_apply(update)
        return
    if update["mode"] == "chain":
        n = len(update["hops"])
        detalle = f"Se aplicará en {n} paso{'s' if n != 1 else ''} (paquetes livianos, solo lo que cambió)."
    elif update["mode"] == "setup":
        detalle = "Se descargará el instalador y se ejecutará sin preguntar nada más."
    else:
        detalle = "Se descargará el paquete completo."
    # Prompt estilizado: logo + stylesheet del tema + release notes del
    # GitHub release bajo "Show Details" (colapsable). Antes era un
    # QMessageBox.question plano sin contexto.
    prompt = QMessageBox()
    prompt.setIcon(QMessageBox.Question)
    prompt.setWindowTitle("Actualización disponible")
    prompt.setText(
        f"Hay una nueva versión disponible ({tag}).\n{detalle}\n"
        "¿Actualizar ahora? La aplicación se cerrará y volverá a abrir sola."
    )
    if notes:
        prompt.setDetailedText(notes)
    prompt.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    prompt.setDefaultButton(QMessageBox.Yes)
    style_dialog(prompt)
    resp = prompt.exec()
    if resp != QMessageBox.Yes:
        return

    _download_and_apply(update)


if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        if es_kiosko():
            # No se abre con una versión vieja: espera a estar al día.
            from core.actualizacion_kiosko import actualizar_o_bloquear
            actualizar_o_bloquear(__VERSION__, BACKEND_URL)
        else:
            _check_and_apply_update()

    window = MainWindow()
    Preferences.get_style(window)
    if es_kiosko():
        window.showFullScreen()
    else:
        window.show()
    despertador = atender_apagado(window.cerrar_por_apagado)
    QTimer.singleShot(0, _precargar_modulos)
    exit_code = context.app.exec()
    sys.exit(exit_code)
