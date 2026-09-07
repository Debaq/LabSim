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
from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from oae.widgets.teoae_panel import TeoaePanel
from oae.widgets.dpoae_panel import DpoaePanel
from oae.widgets.soae_panel import SoaePanel
from oae.widgets.sfoae_panel import SfoaePanel


class OaeMainWindow(QMainWindow):
    """Emisor Otoacústico Clínico (EOAC) - ventana MDI."""

    def __init__(self, data_login=None) -> None:
        super().__init__()
        self.data_login = data_login
        self.data_current = None
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
        self._refresh_case()
