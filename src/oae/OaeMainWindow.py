"""OaeMainWindow - ventana principal del módulo OAE clínico.

QMainWindow + QTabWidget con 3 tabs (TEOAE / DPOAE / SFOAE). Construida en
código (sin .ui) porque es un módulo nuevo y no necesitamos compartir
diseño con Qt Designer todavía. Mismo patrón que ABR (QMainWindow, módulos
internos como widgets embebidos) pero más liviano - sin dock widgets, sin
toolbar.

Sigue la convención de los módulos "de examen": implementa `la_super(data,
appointment_id)` para que MainWindow._hydrate_modules no falle al cerrar
la atención.
"""
from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget

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
        self.sfoae_panel = SfoaePanel()
        self.tabs.addTab(self.teoae_panel, "TEOAE  (Transientes)")
        self.tabs.addTab(self.dpoae_panel, "DPOAE  (Producto de distorsión)")
        self.tabs.addTab(self.sfoae_panel, "SFOAE  (Espontáneas / Supresión)")
        outer.addWidget(self.tabs, stretch=1)

        self.setCentralWidget(central)

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
