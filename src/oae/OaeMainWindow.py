"""OaeMainWindow - ventana principal del módulo OAE clínico.

QMainWindow + QTabWidget con 4 tabs (TEOAE / DPOAE / SOAE / SFOAE). Construida en
código (sin .ui) porque es un módulo nuevo y no necesitamos compartir
diseño con Qt Designer todavía. Mismo patrón que ABR (QMainWindow, módulos
internos como widgets embebidos) pero más liviano - sin dock widgets, sin
toolbar.

Sigue la convención de los módulos "de examen": implementa `la_super(data,
appointment_id)` para que MainWindow._hydrate_modules no falle al cerrar
la atención.
"""
import os

import requests
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.base import context
from core.helpers import Preferences
from backend.client import BackendClient
from oae.OaeReport import OaeReport
from oae.widgets.teoae_panel import TeoaePanel
from oae.widgets.dpoae_panel import DpoaePanel
from oae.widgets.soae_panel import SoaePanel
from oae.widgets.sfoae_panel import SfoaePanel

# Nombre de la prueba -> atributo del panel. El orden es el del informe.
PRUEBAS = (
    ("teoae", "teoae_panel", "TEOAE"),
    ("dpoae", "dpoae_panel", "DPOAE"),
    ("soae", "soae_panel", "SOAE"),
    ("sfoae", "sfoae_panel", "SFOAE"),
)


class OaeMainWindow(QMainWindow):
    """Emisor Otoacústico Clínico (EOAC) - ventana MDI."""

    def __init__(self, data_login=None) -> None:
        super().__init__()
        self.data_login = data_login or {}
        self.data_current = None
        self.appointment_id = None
        self.setWindowTitle("Emisor Otoacústico")
        self.resize(1200, 800)
        self._build_ui()
        self._refresh_case()

    def _build_ui(self) -> None:
        """Construye central widget: tabs por tipo de OEA."""
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.teoae_panel = TeoaePanel()
        self.dpoae_panel = DpoaePanel()
        self.soae_panel = SoaePanel()
        self.sfoae_panel = SfoaePanel()
        self.tabs.addTab(self.teoae_panel, "TEOAE  (Transientes)")
        self.tabs.addTab(self.dpoae_panel, "DPOAE  (Producto de distorsión)")
        # SOAE y SFOAE son pruebas distintas: espontáneas = sin estímulo;
        # SFOAE = con tono de estímulo y supresor. El tab de SFOAE decía
        # "Espontáneas", que es el error conceptual que más se arrastra.
        self.tabs.addTab(self.soae_panel, "SOAE  (Espontáneas)")
        self.tabs.addTab(self.sfoae_panel, "SFOAE  (Frecuencia de estímulo / Supresión)")

        # Tab de informe: es donde el alumno redacta y guarda -- sin esto el
        # módulo generaba capturas que no llegaban a ninguna parte.
        self.report = OaeReport()
        self.report.set_evaluador(self.data_login.get("name", ""))
        self.report.save_requested.connect(self._on_save_report)
        self.tabs.addTab(self.report, "Informe")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        outer.addWidget(self.tabs, stretch=1)

        self.setCentralWidget(central)

    def _refresh_case(self) -> None:
        """Manda a los paneles la patología por oído del caso abierto.

        Sin atención abierta no hay patología que simular: los paneles
        quedan bloqueados. Antes había una barra de "modo demo" (patología
        + umbral a mano, solo admin) que inventaba un caso plano -- un
        `type`/`umbral` sin perfil por frecuencia, sello, ruido ni
        variabilidad, así que todos los pacientes demo salían iguales y un
        "coclear" con umbral 20 daba exactamente lo mismo que un normal.
        Eso es justo lo que la memoria no_synthetic_fallback_data manda no
        hacer: sin datos reales del backend, el módulo se bloquea.
        """
        if self.data_current is not None:
            eoas = self.data_current.get("EOAS") or {}
            case_od = eoas.get("OD")
            case_oi = eoas.get("OI")
        else:
            case_od = None
            case_oi = None
        for panel in (self.teoae_panel, self.dpoae_panel, self.soae_panel,
                      self.sfoae_panel):
            panel.set_case(case_od, case_oi)

    def la_super(self, data, appointment_id=None) -> None:
        """Interfaz estándar de hidratación de módulos (Audiometer, ABR, Z).

        Propaga la patología por oído (cases.data['EOAS']['OD'/'OI'],
        mismo patrón que ABR) a los 4 paneles. Sin atención abierta -- o
        con atención abierta pero sin EOA configurado para ese oído -- el
        panel bloquea la captura, ver oae_attenuation_db en
        generators/base.py.
        """
        self.data_current = data
        self.appointment_id = appointment_id
        self.report.set_atencion(appointment_id if data is not None else None)
        self.report.set_evaluador(self.data_login.get("name", ""))
        # Atención cerrada o paciente nuevo: el informe anterior ya se subió
        # en submit_report(), así que nada de él (texto ni capturas) puede
        # arrastrarse al siguiente paciente.
        self.report.clear_texts()
        for _clave, attr, _label in PRUEBAS:
            getattr(self, attr).reset_all()
        self.report.set_capturas([])
        self._refresh_case()

    # ------------------------------------------------------------------
    # Informe
    # ------------------------------------------------------------------
    def _on_tab_changed(self, index):
        if self.tabs.widget(index) is self.report:
            self.report.set_capturas(self._capturas_texto())

    def _panels_summary(self):
        """{'teoae': {'OD': {...}}, ...} con solo las pruebas que tienen datos."""
        resumen = {}
        for clave, attr, _label in PRUEBAS:
            datos = getattr(self, attr).report_summary()
            if datos:
                resumen[clave] = datos
        return resumen

    def _capturas_texto(self):
        lineas = []
        for clave, attr, label in PRUEBAS:
            oidos = sorted(getattr(self, attr).report_summary().keys())
            if oidos:
                lineas.append(f"{label}: {', '.join(oidos)}")
        return lineas

    def _export_images(self):
        """Vuelca las capturas de cada panel a JPEG. {sufijo: ruta}."""
        temp_dir = context.get_resource("local_cache/oae/temp")
        os.makedirs(temp_dir, exist_ok=True)
        images = {}
        for clave, attr, _label in PRUEBAS:
            for ear, pixmap in getattr(self, attr).report_shots().items():
                suffix = f"{clave}_{ear.lower()}"
                path = os.path.join(temp_dir, f"upload_{suffix}.jpg")
                if pixmap.save(path, "JPG", 90):
                    images[suffix] = path
        return images

    def restore_report(self, data):
        """Retomar la atención: vuelven los resultados ya guardados de cada
        prueba y oído (ver core/report_autosave.py).

        Se recuperan los números, no los gráficos: las capturas ya están en
        el servidor y no se vuelven a subir. Lo que importa es que una
        captura nueva no reemplace el informe entero por uno con solo esa
        prueba. Un oído que se vuelva a medir pisa al recuperado.
        """
        pruebas = data.get('pruebas') or {}
        recuperado = False
        for clave, attr, _label in PRUEBAS:
            panel = getattr(self, attr)
            for oido, resumen in (pruebas.get(clave) or {}).items():
                if oido not in panel._report:
                    panel._report[oido] = resumen
                    recuperado = True
        if not self.report.text_edit_1.toPlainText().strip():
            self.report.text_edit_1.setPlainText(data.get('hallazgos') or '')
        if not self.report.text_edit_2.toPlainText().strip():
            self.report.text_edit_2.setPlainText(data.get('conclusion') or '')
        return recuperado

    def report_job(self):
        """El informe tal como se sube (ver core/report_autosave.py), o None
        si todavía no hay ninguna captura."""
        if not self.data_login:
            return None
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return None
        pruebas = self._panels_summary()
        if not pruebas:
            return None
        data = {
            "pruebas": pruebas,
            "hallazgos": self.report.text_edit_1.toPlainText(),
            "conclusion": self.report.text_edit_2.toPlainText(),
        }
        return {"appointment_id": appointment_id, "tipo": "EOA", "data": data,
                "images": self._export_images}

    def _on_save_report(self):
        """Botón 'Guardar informe': mismo camino que el cierre de atención,
        pero avisando en pantalla qué pasó (el alumno tiene que saber si su
        informe quedó guardado o no)."""
        ok, mensaje = self.submit_report()
        self.report.set_status(mensaje, ok)
        if ok:
            QMessageBox.information(self, "Informe EOA", mensaje)
        else:
            QMessageBox.warning(self, "Informe EOA", mensaje)

    def submit_report(self):
        """Sube el informe (resúmenes por prueba/oído + capturas + texto) al
        backend -- ver BackendClient.upload_report() / report_upload.php.

        Se llama desde el botón "Guardar informe" y también al cerrar la
        atención (main.py::_cerrar_atencion_real), antes de que
        _hydrate_modules() saque appointment_id. Devuelve (ok, mensaje) para
        que el botón pueda mostrar el motivo real del fallo; el cierre de
        atención ignora el resultado (best-effort, igual que ABR/VEMP: sin
        conexión no debe romper el cierre, que ya quedó guardado local).
        """
        if not self.data_login:
            return False, "No hay sesión de usuario."
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return False, "No hay una atención abierta a la que adjuntar el informe."

        pruebas = self._panels_summary()
        if not pruebas:
            return False, ("Todavía no hay ninguna captura: registra al menos "
                           "una prueba antes de guardar el informe.")

        data = {
            "pruebas": pruebas,
            "hallazgos": self.report.text_edit_1.toPlainText(),
            "conclusion": self.report.text_edit_2.toPlainText(),
        }
        try:
            images = self._export_images()
            client = BackendClient(
                Preferences().get("BACKEND_URL"),
                context.get_resource("json/session.json"),
            )
        except Exception as exc:  # noqa: BLE001 - no puede romper el cierre
            return False, f"No se pudo preparar el informe: {exc}"
        if not client.is_logged_in():
            return False, "No hay sesión con el servidor (vuelve a iniciar sesión)."
        try:
            client.upload_report(appointment_id, "EOA", data, images)
        except requests.HTTPError as exc:
            return False, f"El servidor rechazó el informe: {exc}"
        except requests.RequestException as exc:
            return False, f"Sin conexión con el servidor: {exc}"
        return True, "Informe guardado. Queda en 'Mis pacientes' de tu perfil."
