from pathlib import Path
import copy
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
from core import equipo
from core import report_autosave
from core.report_autosave import ReportAutosave, subir_pendientes
from core.secretaria import Secretaria, siguiente_paciente
from core.kiosko import es_kiosko, atender_apagado
from core.preferencias import preferencias
from core import mouse_zurdo, configuracion, hilos, registro, respaldo_informes
from core.module_placeholder import ModulePlaceholder
from core.updater import local_build_id
from core.helpers import (CasesOffline, CreatePatient, Preferences, Shedule, Storage,
                          es_docente, entry_estado_por,
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

__VERSION__ = 'v0.9.9'
# Build real (con sufijo -r<commit> si aplica) para mostrar en el título --
# __VERSION__ solo no alcanza porque no sube en cada build de prueba.
DISPLAY_VERSION = f"v{local_build_id(__VERSION__.lstrip('v'))}"
# Viaja con el login: el backend muestra qué versión hay en cada equipo.
equipo.version = DISPLAY_VERSION.lstrip('v')
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

# Cola local de logs de acciones (ver lib/backend/log_queue.py). Es solo un
# insert sqlite local, nunca toca la red -- se sube al backend en batches
# vía LogUploaderThread (ver MainWindow._data_login).
LOCAL_LOG_QUEUE = get_log_queue()
# Logger sin log_queue: stdout (prints de debug regados por todo el código)
# ya no se sube al backend -- era 87% del volumen y puro ruido interno
# ("cambio el sender", "True", [agenda_filter]...). Las acciones reales del
# alumno (audio_stim_button, z_dial_change, etc.) se suben aparte, con
# nombre propio, vía log_queue.push() explícito en Audiometer.py y Z.py.
# El registro va a la carpeta de datos (sobrevive a las actualizaciones) y
# se rota al arrancar; ver core/registro.py. Se manda desde Configuración.
LOG_FILE = registro.archivo()
registro.rotar(LOG_FILE)
sys.stdout = Logger(LOG_FILE, max_bytes=registro.MAX_BYTES, rotar=registro.rotar)
# stderr al mismo archivo. Los errores de PySide ("Error calling Python
# override of QWidget::eventFilter(): ...") y los traceback de cualquier
# excepcion NO pasan por stdout: sin esto, lo unico que quedaba del
# problema era lo que el alumno alcanzara a copiar de la consola, y la
# causa real es justo la ultima linea, la que la consola recorta.
sys.stderr = Logger(LOG_FILE, stream=sys.__stderr__, max_bytes=registro.MAX_BYTES,
                    rotar=registro.rotar)
# Un cuelgue duro (stack overflow de la cadena de layout de pyqtgraph, por
# ejemplo) no deja traceback de Python: faulthandler escribe el stack en
# el mismo log antes de que el proceso se vaya.
faulthandler.enable(file=open(LOG_FILE, 'a', buffering=1))
print(registro.encabezado())
# Si la vez anterior no terminó bien, al abrir se ofrece mandar el registro
# (ver core/soporte.ofrecer_envio_por_cierre).
CIERRE_PREVIO = registro.marcar_inicio(LOG_FILE)
if CIERRE_PREVIO:
    print(f"la vez anterior (abierta {CIERRE_PREVIO}) no terminó bien")


def _log_excepcion(tipo, valor, tb):
    """Toda excepcion no atrapada al log, no solo a una consola que se cierra."""
    traceback.print_exception(tipo, valor, tb)


sys.excepthook = _log_excepcion

# Después del registro y del excepthook: si algo falla acá queda en el log.
BACKEND_URL = Preferences.get("BACKEND_URL")
_layout = fetch_layout(BACKEND_URL)
if _layout:
    APPS = _layout["APP"]
    # Una respuesta sin sectores no puede impedir que la app abra.
    SECTORS = _layout.get("SECTORS") or {}
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
# Copia intacta para comparar cuando vuelve la red: APPS/BOXS se modifican
# en memoria con un docente logueado (_apply_admin_overrides_if_any), y
# comparar contra eso daba "la configuración cambió" sin haber cambiado.
_LAYOUT_ARRANQUE = copy.deepcopy(_layout) if _layout else None


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
        # Respaldos de informes ya subidos y viejos (ver core/respaldo_informes.py).
        respaldo_informes.podar()
        # Kiosko: cada media hora se mira si salió una versión nueva (ver
        # core/actualizacion_kiosko.py y _on_update_disponible).
        self._chequeo_update = None
        if es_kiosko() and getattr(sys, 'frozen', False):
            from core.actualizacion_kiosko import ChequeoPeriodico
            self._chequeo_update = ChequeoPeriodico(__VERSION__, BACKEND_URL, parent=self)
            self._chequeo_update.hay_update.connect(self._on_update_disponible)

    def _on_update_disponible(self):
        """Kiosko: hay versión nueva. Sin sesión iniciada se aplica ya; con
        un alumno atendiendo (o entrando), al cerrar sesión (ver logout)."""
        if self._sesion_activa():
            self._update_pendiente = True
        else:
            self._actualizar_ahora()

    def _sesion_activa(self):
        """Hay alguien adentro o entrando: el login corre en otro hilo y
        mientras tanto data_login sigue vacío."""
        if self.data_login:
            return True
        login = (self.subw or {}).get("LOGIN")
        return login is not None and getattr(login.obj, "_login_thread", None) is not None

    def _actualizar_ahora(self):
        """Tapa la ventana y actualiza. No vuelve si se instala (la app se
        reinicia); si falla, reintenta hasta lograrlo. Vuelve si ya no hay
        nada nuevo, si el equipo se está apagando o si alguien inició sesión
        en el medio: el reinicio cierra sin guardar, así que con una sesión
        abierta se cancela hasta en el último paso y queda para el logout."""
        if self._actualizando or self._apagando:
            return
        if self._sesion_activa():
            self._update_pendiente = True
            return
        from core.actualizacion_kiosko import actualizar_o_bloquear
        self._actualizando = True
        self._update_pendiente = False
        try:
            actualizar_o_bloquear(__VERSION__, BACKEND_URL,
                                  abortar=lambda: self._apagando or self._sesion_activa())
        finally:
            self._actualizando = False
            if self._sesion_activa():
                self._update_pendiente = True

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
        self._layout_retry = LayoutRetryThread(
            BACKEND_URL, al_recuperar=self._on_layout_recovered, dueno=self)
        self._layout_retry.start()

    def _on_layout_recovered(self, data):
        """El backend volvió. Si el layout fresco es igual al que ya está
        cargado (el caso normal: el layout casi nunca cambia) alcanza con
        sacar el aviso. Si cambió, o si arrancamos sin layout, hay que
        reiniciar -- la toolbar se arma una sola vez en __init__."""
        self._layout_retry = None
        self._set_offline_title(False)
        arranque = _LAYOUT_ARRANQUE or {}
        igual = (
            LAYOUT_AVAILABLE
            and data.get("APP") == arranque.get("APP")
            and data.get("BOXS") == arranque.get("BOXS")
            and (data.get("SECTORS") or {}) == (arranque.get("SECTORS") or {})
        )
        if igual:
            print("[layout] conexión restablecida, cache al día")
            return
        if self._sesion_activa():
            # Con una sesión abierta no se reinicia: execv cortaba la
            # atención sin subir nada. Se aplica al cerrar sesión.
            print("[layout] cambió la configuración; se reinicia al cerrar sesión")
            self._reinicio_pendiente = True
            return
        if es_kiosko():
            # Sin nadie adentro no hay nada que perder, y no es una
            # pregunta para el alumno que se sienta después.
            print("[layout] cambió la configuración; se reinicia (kiosko sin sesión)")
            self._restart_app()
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
        registro.marcar_salida()
        if getattr(sys, "frozen", False):
            os.execv(sys.executable, [sys.executable] + sys.argv[1:])
        else:
            os.execv(sys.executable, [sys.executable] + sys.argv)

    def _stop_layout_retry(self):
        if self._layout_retry is not None:
            self._layout_retry.stop()
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
        # Apagar el equipo no es una caída, aunque el plazo corte la salida.
        registro.marcar_salida()
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
        # Karime: avisos de la secretaria durante la atención (ver
        # core/secretaria.py), se programan junto con el cronómetro.
        self.secretaria = Secretaria(self.mdi_area)

    def create_variables(self):
        """Crea las variables necesarias para el funcionamiento del programa"""
        self.data_login = None
        # El equipo se está apagando (ver cerrar_por_apagado).
        self._apagando = False
        # Kiosko: versión nueva esperando a que se cierre la sesión, y
        # actualización en curso (ver _on_update_disponible).
        self._update_pendiente = False
        self._actualizando = False
        # Llegó un layout distinto con la sesión abierta (ver
        # _on_layout_recovered): se reinicia al cerrar sesión.
        self._reinicio_pendiente = False
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
        self._subida_pendientes = None
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
            cliente = self._logged_in_client()
            LOCAL_LOG_QUEUE.set_usuario((cliente.user or {}).get("id") if cliente else None)
            LOCAL_LOG_QUEUE.push("session_login", {
                "user": data.get("user"),
                "name": data.get("name"),
                "permission": data.get("permission"),
            })
            try:
                self.refresh_data()
            except Exception as exc:  # noqa: BLE001
                if not isinstance(exc, requests.RequestException):
                    # Una respuesta con forma inesperada o un error local:
                    # mismo rollback, la sesión no puede quedar a medias
                    # (sin módulos, sin sync, sin subir acciones).
                    traceback.print_exc()
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
                self._close_sub_windows()
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
            self._subir_pendientes_en_fondo()

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
            # Espera 2 s; si sigue en una subida termina sola (hilo de
            # Python, ver core/hilos.Ciclo).
            self.log_uploader.stop()
            self.log_uploader = None

    def _start_sync_thread(self):
        """Poll periódico al backend (ver sync_thread.py): si el admin edita
        la agenda desde otra terminal, esta refresca sola en el próximo ciclo."""
        client = self._logged_in_client()
        if client is None:
            return
        self.sync_thread = SyncThread(client, al_sincronizar=self._on_backend_sync, dueno=self)
        self.sync_thread.start()

    def _subir_pendientes_en_fondo(self):
        """Informes que quedaron en este equipo sin subir, de cualquier
        atención del usuario (ver report_autosave.subir_pendientes). Al
        iniciar sesión y con cada sync, que es cuando hay red."""
        if self._subida_pendientes is not None:
            return
        # Con cada sync: sin QThread, ver hilos.en_fondo.
        self._subida_pendientes = hilos.en_fondo(
            subir_pendientes, None, excluir=lambda: self.data_current_key,
            listo=self._fin_subida_pendientes, fallo=self._fallo_subida_pendientes,
            nombre="pendientes")

    def _fin_subida_pendientes(self, _resultado=None):
        self._subida_pendientes = None

    def _fallo_subida_pendientes(self, exc):
        print(f"autosave: no se pudieron subir los pendientes: {exc}")
        self._subida_pendientes = None

    def _on_backend_sync(self, delta):
        # Cada ciclo de sync (60 s, o al tiro con sync_ahora): la agenda se
        # arma con el delta en memoria; ya no se baja entera cada vez
        # (ver helpers.aplicar_delta).
        agenda_win = self.subw.get("AGENDA") if self.subw else None
        if agenda_win is not None:
            agenda_win.obj.aplicar_delta(delta)
        if "inbox_no_leidos" in delta:
            inbox.actualizar_badge(self, no_leidos=delta["inbox_no_leidos"])
        else:   # backend anterior: la bandeja entera, fuera de la ventana
            hilos.en_fondo(inbox.inbox_list, dueno=self, nombre="bandeja",
                           listo=lambda items: inbox.actualizar_badge(self, items))
        app_config_store.update_from_sync(delta.get("config"))
        self._subir_pendientes_en_fondo()

    def sync_ahora(self) -> bool:
        """Que el sync pregunte ya (tras atender, cerrar, una inasistencia).
        False si no hay sync corriendo (quien llama baja la agenda entera)."""
        if self.sync_thread is None:
            return False
        self.sync_thread.ahora()
        return True

    def _subir_logs_ahora(self):
        """Evento importante: las acciones juntadas en la cola suben ya."""
        if self.log_uploader is not None:
            self.log_uploader.ahora()

    def _stop_sync_thread(self):
        if self.sync_thread is not None:
            self.sync_thread.stop()   # ver _stop_log_uploader
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
        LOCAL_LOG_QUEUE.set_usuario(None)
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
        elif self._reinicio_pendiente:
            self._reinicio_pendiente = False
            QTimer.singleShot(0, self._restart_app)

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
        self.secretaria.detener()

    def _reset_cronometro(self):
        """Limpia el cronómetro (logout)"""
        self.cronometro_timer.stop()
        self.secretaria.detener()
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
                # Lo que la ventana tenga pidiendo al servidor (agenda,
                # chat, otoscopia) corre con hilos.en_fondo: termina solo y
                # su resultado ya no le llega a nadie.
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

        try:
            shedule = Shedule()
        except requests.RequestException as exc:
            return self._atender_sin_conexion(exc)
        agenda = shedule.data.setdefault("agenda_1", {})
        entry = agenda.get(key)
        if entry is None:
            return

        case_id = entry.case_id or None
        if not case_id:
            return
        try:
            cases = CasesOffline().get_cases()
        except requests.RequestException as exc:
            return self._atender_sin_conexion(exc)
        if case_id not in cases:
            return  # el caso fue borrado/no sincronizó -- no dejamos marcar "atendiendo" un caso inexistente

        if not es_prueba:
            marcar_entry_atendiendo(entry, self.data_login["user"])
            try:
                shedule.set(shedule.data)
            except requests.RequestException as exc:
                return self._atender_sin_conexion(exc)

        self.data_current = cases[case_id]
        self.data_current_key = key

        if not es_prueba and self.subw and "AGENDA" in self.subw:
            # En segundo plano: con la red cortada justo acá, el refresh
            # sincrónico lanzaba y la atención quedaba abierta en el
            # servidor sin módulos cargados ni autoguardado.
            self.subw["AGENDA"].obj.actualizar()
            self._subir_logs_ahora()

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
        # Con la agenda que ya se bajó acá: Shedule() es un pull completo
        # al backend y no se puede repetir en el hilo de la UI cuando salta
        # cada aviso. Mientras dure esta atención no se puede abrir otra
        # (ver _otra_atencion_abierta), así que el siguiente no cambia.
        self.secretaria.iniciar(siguiente_paciente(agenda, key, self.data_login["user"]))

    def _atender_sin_conexion(self, detalle):
        """Abrir una atención necesita al servidor (el caso, marcar
        'atendiendo'). Una vez abierta se sigue trabajando sin red."""
        print(f"atender: sin conexión: {detalle}")
        dlg = QMessageBox(QMessageBox.Icon.Warning, "Sin conexión con el servidor",
                          "No se pudo abrir la atención porque no hay conexión con el "
                          "servidor. Inténtalo de nuevo en un momento.",
                          QMessageBox.StandardButton.Ok, self)
        style_dialog(dlg)
        dlg.exec()

    def cerrar_atencion(self, key, nota):
        """Cierra la atención (estado 'atendido') guardando la nota de atención del estudiante"""
        if es_docente(self.data_login["permission"]):
            return  # admin/docente usan cerrar_atencion_prueba() o cerrar_atencion_base()
        return self._cerrar_atencion_real(key, nota)

    def cerrar_atencion_base(self, key, nota):
        """Contraparte de atender_paciente_base(): cierra de verdad (estado
        'atendido', chat guardado) la atención base del docente."""
        if not es_docente(self.data_login["permission"]):
            return  # esta variante es solo para admin/docente
        return self._cerrar_atencion_real(key, nota)

    def _cerrar_atencion_real(self, key, nota):
        """Lógica común a cerrar_atencion() (alumno) y cerrar_atencion_base()
        (docente en modo "guardar base").

        Devuelve False si no se pudo cerrar (sin conexión): la atención
        sigue abierta, los exámenes quedan respaldados en el equipo y la
        evolución escrita no se borra, para reintentar."""
        try:
            shedule = Shedule()
        except requests.RequestException as exc:
            return self._cierre_sin_conexion(exc)
        agenda = shedule.data.setdefault("agenda_1", {})
        entry = agenda.get(key)
        if entry is None:
            # La cita ya no está (la borró el docente): no hay qué cerrar, y
            # la evolución escrita no se puede tirar como si se hubiera
            # guardado.
            self._aviso("No se pudo cerrar la atención",
                        "Esta cita ya no está en la agenda (puede que el docente la "
                        "haya borrado). Lo que escribiste quedó guardado en este equipo; "
                        "avísale a tu docente.")
            return False
        if entry_estado_por(entry, self.data_login["user"]) == "atendido":
            # Un intento anterior sí llegó al servidor aunque la respuesta
            # no volvió a tiempo: ya está cerrada.
            return self._cierre_ya_hecho(key)

        actual = self.data_current_key == key
        fallidos = []
        if actual:
            # Los informes de los módulos "de examen" suben ANTES de marcar
            # 'atendido': shedule.set() empuja ese estado al backend en el
            # acto, y desde ahí report_upload.php rechaza con 409 (el
            # informe queda fijo). Con el orden al revés no se guardaba
            # ninguno. Además tiene que ser antes de _hydrate_modules(),
            # que les saca appointment_id/data_login.
            fallidos = self._subir_informes()
        # Lo que quedó en el equipo sin subir de otra vuelta (la app se
        # cerró sin red y se cierra sin haberla retomado).
        try:
            pendientes_ok, error = subir_pendientes(int(key))
        except (TypeError, ValueError):
            pendientes_ok, error = True, ""
        if fallidos or not pendientes_ok:
            # Cerrar ahora dejaba esos exámenes fuera para siempre (el
            # servidor no acepta informes de una atención cerrada).
            return self._cierre_sin_conexion(
                ", ".join(fallidos) or error, reanudar=actual)

        marcar_entry_atendido(entry, self.data_login["user"], nota)
        try:
            shedule.set(shedule.data)
        except requests.RequestException as exc:
            if self._quedo_cerrada(key):
                # El servidor la cerró y lo que se cortó fue la respuesta.
                return self._cierre_ya_hecho(key, avisar=False)
            return self._cierre_sin_conexion(exc, reanudar=actual)
        return self._cierre_ya_hecho(key, avisar=False)

    def _quedo_cerrada(self, key):
        """Después de un error al cerrar: ¿el servidor la cerró igual?"""
        try:
            entry = Shedule().data.get("agenda_1", {}).get(key)
        except requests.RequestException:
            return False
        return entry is not None and entry_estado_por(entry, self.data_login["user"]) == "atendido"

    def _cierre_ya_hecho(self, key, avisar=True):
        """La atención quedó cerrada en el servidor: se descarga de los
        módulos (lo que tenían ya subió antes de cerrar)."""
        self.report_autosave.detener()
        self._stop_cronometro()
        if self.data_current_key == key:
            self.data_current_key = None
            self.data_current = None
            self.paciente_actual = None
            self._hydrate_modules()
        if self.subw and "AGENDA" in self.subw:
            self.subw["AGENDA"].obj.actualizar()
        self._subir_logs_ahora()
        self.statusbar.clearMessage()
        if avisar:
            self._aviso("Atención cerrada",
                        "Esta atención ya había quedado cerrada en el servidor en un "
                        "intento anterior (la respuesta no alcanzó a llegar).",
                        QMessageBox.Icon.Information)
        return True

    def _aviso(self, titulo, texto, icono=QMessageBox.Icon.Warning):
        dlg = QMessageBox(icono, titulo, texto, QMessageBox.StandardButton.Ok, self)
        style_dialog(dlg)
        dlg.exec()

    def _cierre_sin_conexion(self, detalle, reanudar=False):
        """No se pudo cerrar la atención. Sigue abierta y el autoguardado
        vuelve a correr (se había detenido para la subida final)."""
        print(f"cerrar atención: no se pudo: {detalle}")
        if reanudar:
            self.report_autosave.reanudar()
        texto = str(detalle)
        if "401" in texto or "Unauthorized" in texto or "sesión" in texto.lower():
            motivo = ("Tu sesión con el servidor venció. Cierra sesión y vuelve a "
                      "ingresar: lo hecho está guardado en este equipo y se sube solo.")
        elif isinstance(detalle, (requests.ConnectionError, requests.Timeout)) \
                or "Connection" in texto or "timed out" in texto.lower():
            motivo = ("No hay conexión con el servidor. Cuando vuelva, guarda la "
                      "evolución de nuevo.")
        else:
            motivo = ("El servidor no aceptó el cierre. Inténtalo de nuevo y, si se "
                      "repite, avísale a tu docente o usa Configuración → Reportar un "
                      f"problema.\n\nDetalle: {texto[:200]}")
        self._aviso("No se pudo cerrar la atención",
                    "Tus exámenes quedaron guardados en este equipo y la atención sigue "
                    "abierta (lo que escribiste en la evolución no se borró).\n\n" + motivo)
        return False

    def _hydrate_modules(self):
        """Carga self.data_current en los módulos ya construidos, o los
        deshidrata (data_current=None) para que dejen de loguear acciones
        bajo el caso/paciente ya cerrado."""
        for attr in ("subw_a", "subw_z", "subw_w", "subw_ac", "subw_ot", "subw_abr",
                     "subw_aabr", "subw_eoas", "subw_vemp"):
            frame = getattr(self, attr, None)
            if frame is None:
                continue
            try:
                frame.obj.la_super(self.data_current, self.data_current_key)
            except Exception:  # noqa: BLE001
                # Un dato raro del caso en un módulo no puede dejar sin caso
                # (ni sin autoguardado) a los que vienen después.
                print(f"{attr}: no se pudo cargar el caso:")
                traceback.print_exc()

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
        pisaría esta. Devuelve los módulos que no pudieron subir (lo suyo
        quedó respaldado en el equipo, ver core/respaldo_informes.py)."""
        self.report_autosave.detener()
        report_autosave.ultimos_errores.clear()
        fallidos = []
        for modulo in self._modulos_examen():
            try:
                ok = modulo.submit_report()
            except Exception as exc:
                print(f"{type(modulo).__name__}: no se pudo subir el informe: {exc}")
                ok = False
            if ok is False:
                fallidos.append(type(modulo).__name__)
        if fallidos and report_autosave.ultimos_errores:
            # El motivo real (lo que respondió el servidor), no el módulo.
            return [f"{tipo}: {err[:150]}" for tipo, err in report_autosave.ultimos_errores.items()]
        return fallidos

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
        evolucion = (self.subw or {}).get("EVOLUCION")
        if evolucion is not None:
            # Lo último que escribió, antes de que se borre la ventana.
            evolucion.obj.guardar_borrador()
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

    def abrir_evolucion(self, nombre_paciente, on_guardar, appointment_id=None):
        """Abre (o trae al frente) la subventana MDI de evolución, reapuntada
        al paciente/callback indicado (ver Agenda._cerrar_atencion y
        Agenda._cerrar_atencion_prueba). Con `appointment_id` (atención
        real) lo escrito queda como borrador en el equipo."""
        borrador = None
        if appointment_id is not None:
            usuario = respaldo_informes.usuario_de(self._logged_in_client())
            if usuario:
                borrador = (usuario, appointment_id)
        self.subw["EVOLUCION"].obj.set_contexto(nombre_paciente, on_guardar, borrador)
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
        if self._apagando:
            # El equipo se apaga y da pocos segundos (core/kiosko.py): todo
            # al disco y nada a la red, que con la red colgada no
            # alcanzaba. Lo pendiente sube en el próximo inicio de sesión.
            evolucion = (self.subw or {}).get("EVOLUCION")
            if evolucion is not None:
                evolucion.obj.guardar_borrador()
            self.report_autosave.respaldar(con_imagenes=True)
        else:
            self._guardar_informes_al_salir()
            if self.log_uploader is not None:
                # Igual que en logout(): sin esto, acciones recién logueadas
                # quedan en la cola local hasta el próximo login si se
                # cierra con la X.
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
            try:
                _check_and_apply_update()
            except Exception:  # noqa: BLE001
                # Una respuesta rara de GitHub o del backend no puede
                # impedir que la app abra: se sigue con esta versión.
                print("actualización: no se pudo comprobar, se sigue con esta versión")
                traceback.print_exc()

    window = MainWindow()
    Preferences.get_style(window)
    if es_kiosko():
        window.showFullScreen()
    else:
        window.show()
    despertador = atender_apagado(window.cerrar_por_apagado)
    QTimer.singleShot(0, _precargar_modulos)
    if CIERRE_PREVIO:
        from core import soporte
        QTimer.singleShot(1500, lambda: soporte.ofrecer_envio_por_cierre(window, CIERRE_PREVIO))
    exit_code = context.app.exec()
    registro.marcar_salida()
    if hilos.quedan_vivos():
        # Un hilo que sigue en una petición de red se destruiría al
        # terminar el intérprete y Qt abortaría el proceso ("LabSim dejó de
        # funcionar" en Windows). Lo del alumno ya se subió o quedó en el
        # equipo en closeEvent: se sale sin esperar.
        print("salida: quedan hilos de red en curso, se sale sin esperarlos")
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(exit_code)
    sys.exit(exit_code)
