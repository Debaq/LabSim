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
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
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

_DEMO_TYPES = ("normal", "coclear", "transmission", "neural")


class OaeMainWindow(QMainWindow):
    """Emisor Otoacústico Clínico (EOAC) - ventana MDI."""

    def __init__(self, data_login=None) -> None:
        super().__init__()
        self.data_login = data_login
        self.data_current = None
        # Modo demo: solo para el docente/admin (permission 777, mismo
        # criterio que el resto de la app -- ver main.py). Un alumno sin
        # atención abierta debe seguir bloqueado, no ver datos inventados.
        self.is_admin = bool(data_login) and data_login.get("permission") == 777
        self.setWindowTitle("Emisor Otoacústico")
        self.resize(1200, 800)
        self._build_ui()
        self._refresh_case()

    def _build_ui(self) -> None:
        """Construye central widget: barra de modo demo (solo admin) + tabs por tipo de OEA."""
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        self.demo_bar = self._build_demo_bar() if self.is_admin else None
        if self.demo_bar is not None:
            outer.addWidget(self.demo_bar)

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

    def _build_demo_bar(self) -> QFrame:
        """Barra de modo demo -- solo existe para el docente/admin (ver
        self.is_admin), y dentro de eso SOLO se muestra sin paciente/
        atención conectada, para poder probar el módulo sin depender de
        un caso real. En cuanto hay atención abierta se oculta y se usa
        la patología real del caso (o None si no está configurada, que
        bloquea la captura -- ver memoria no_synthetic_fallback_data)."""
        frame = QFrame()
        frame.setObjectName("oae_demo_bar")
        frame.setStyleSheet(
            "QFrame#oae_demo_bar {"
            "  background-color: #e8f0fe;"
            "  border: 1px solid #aac7f7;"
            "  border-radius: 4px;"
            "  padding: 6px;"
            "}"
        )
        layout = QHBoxLayout(frame)
        layout.addWidget(QLabel("Modo demo (sin paciente conectado) -- patología simulada:"))
        self.demo_type = QComboBox()
        self.demo_type.addItems(_DEMO_TYPES)
        layout.addWidget(self.demo_type)
        layout.addWidget(QLabel("Umbral (dB):"))
        self.demo_umbral = QDoubleSpinBox()
        self.demo_umbral.setRange(0.0, 90.0)
        self.demo_umbral.setValue(20.0)
        self.demo_umbral.setSingleStep(5.0)
        layout.addWidget(self.demo_umbral)
        layout.addStretch(1)

        self.demo_type.currentTextChanged.connect(self._refresh_case)
        self.demo_umbral.valueChanged.connect(self._refresh_case)
        return frame

    def _refresh_case(self) -> None:
        """Decide qué patología por oído se manda a los 3 paneles: la real
        del caso si hay atención abierta, o (solo para admin) la del modo
        demo si no hay ninguna (self.data_current is None)."""
        use_demo = self.data_current is None and self.demo_bar is not None
        if self.demo_bar is not None:
            self.demo_bar.setVisible(use_demo)
        if self.data_current is not None:
            eoas = self.data_current.get("EOAS") or {}
            case_od = eoas.get("OD")
            case_oi = eoas.get("OI")
        elif use_demo:
            demo_case = {"type": self.demo_type.currentText(), "umbral": self.demo_umbral.value()}
            case_od = demo_case
            case_oi = demo_case
        else:
            case_od = None
            case_oi = None
        for panel in (self.teoae_panel, self.dpoae_panel, self.sfoae_panel):
            panel.set_case(case_od, case_oi)

    def la_super(self, data, appointment_id=None) -> None:
        """Interfaz estándar de hidratación de módulos (Audiometer, ABR, Z).

        Propaga la patología por oído (cases.data['EOAS']['OD'/'OI'],
        mismo patrón que ABR) a los 3 paneles. Sin atención abierta muestra
        la barra de modo demo (patología simulada, elegida a mano); con
        atención abierta pero sin EOA configurado para un oído, ese panel
        bloquea la captura -- ver oae_attenuation_db en generators/base.py.
        """
        self.data_current = data
        self.appointment_id = appointment_id
        self._refresh_case()
