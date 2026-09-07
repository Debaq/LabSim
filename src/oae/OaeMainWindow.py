"""OaeMainWindow - ventana principal del módulo OAE clínico.

QMainWindow + QTabWidget con 3 tabs (TEOAE / DPOAE / SFOAE). Construida en
código (sin .ui) porque es un módulo nuevo y no necesitamos compartir
diseño con Qt Designer todavía. Mismo patrón que ABR (QMainWindow, módulos
internos como widgets embebidos) pero más liviano - sin dock widgets, sin
toolbar: lo único compartido entre tipos es el banner de normativos.

Sigue la convención de los módulos "de examen": implementa `la_super(data,
appointment_id)` para que MainWindow._hydrate_modules no falle al cerrar
la atención. OAE en v1 no usa datos del paciente (todo sintético), pero
la firma queda lista para v2 si queremos cargar casos.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from oae.widgets.teoae_panel import TeoaePanel
from oae.widgets.dpoae_panel import DpoaePanel
from oae.widgets.sfoae_panel import SfoaePanel


class OaeMainWindow(QMainWindow):
    """Emisor Otoacústico Clínico (EOAC) - ventana MDI."""

    def __init__(self, data_login=None) -> None:
        super().__init__()
        self.data_login = data_login
        self.setWindowTitle("Emisor Otoacústico")
        self.resize(1200, 800)
        self._build_ui()
        self._refresh_normative_banner()

    def _build_ui(self) -> None:
        """Construye central widget: banner normativos arriba + tabs."""
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        # Banner amarillo si no hay override del curso (decisión usuario:
        # permitir + advertir, no bloquear). Se muestra siempre que falte
        # AL MENOS uno de los 3 tipos de normativo por curso.
        self.banner = QFrame()
        self.banner.setObjectName("oae_normative_banner")
        self.banner.setStyleSheet(
            "QFrame#oae_normative_banner {"
            "  background-color: #fff3cd;"
            "  color: #856404;"
            "  border: 1px solid #ffeeba;"
            "  border-radius: 4px;"
            "  padding: 6px;"
            "}"
            "QLabel { color: #856404; background: transparent; border: none; }"
        )
        banner_layout = QHBoxLayout(self.banner)
        self.banner_label = QLabel("")
        self.banner_label.setWordWrap(True)
        banner_layout.addWidget(self.banner_label, stretch=1)
        self.banner.setVisible(False)
        outer.addWidget(self.banner)

        # Tabs por tipo
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.teoae_panel = TeoaePanel()
        self.dpoae_panel = DpoaePanel()
        self.sfoae_panel = SfoaePanel()
        self.tabs.addTab(self.teoae_panel, "TEOAE  (Transientes)")
        self.tabs.addTab(self.dpoae_panel, "DPOAE  (Producto de distorsión)")
        self.tabs.addTab(self.sfoae_panel, "SFOAE  (Espontáneas / Supresión)")
        outer.addWidget(self.tabs, stretch=1)

        self.setCentralWidget(central)

    def _refresh_normative_banner(self) -> None:
        """Muestra banner si AL MENOS uno de los 3 tipos no tiene override
        del curso en app_config_store. La app sigue funcionando con el
        default bundled en resources/oae/normative_data.json."""
        from core import app_config_store

        keys = ("normative_data.teoae", "normative_data.dpoae", "normative_data.sfoae")
        missing = [k.split(".")[-1].upper() for k in keys if app_config_store.get(k) is None]
        if missing:
            tipos = ", ".join(missing)
            self.banner_label.setText(
                f"⚠  Usando normativos por defecto (sin override del curso "
                f"para: {tipos}). Si esperás valores distintos, pedile al "
                f"docente que los configure desde el panel admin."
            )
            self.banner.setVisible(True)
        else:
            self.banner.setVisible(False)

    def la_super(self, data, appointment_id=None) -> None:
        """Interfaz estándar de hidratación de módulos (Audiometer, ABR, Z).

        Propaga la patología por oído (cases.data['EOAS']['OD'/'OI'],
        mismo patrón que ABR) a los 3 paneles. Sin atención abierta o sin
        EOA configurado para un oído, ese panel bloquea la captura -- ver
        oae_attenuation_db en generators/base.py y memoria
        no_synthetic_fallback_data (sin datos reales, no generar nada).
        """
        self.data_current = data
        self.appointment_id = appointment_id
        eoas = (data or {}).get("EOAS") or {}
        case_od = eoas.get("OD")
        case_oi = eoas.get("OI")
        for panel in (self.teoae_panel, self.dpoae_panel, self.sfoae_panel):
            panel.set_case(case_od, case_oi)
