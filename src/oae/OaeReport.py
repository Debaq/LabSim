"""Panel de informe EOA (hallazgos + conclusión + guardar).

Mismo patrón que AbrReport/VempReport: el alumno escribe la descripción y
la conclusión, y el PDF lo arma el backend (report_pdf.php) con las
capturas de los 4 tabs. La diferencia con ABR/VEMP es el botón "Guardar
informe": acá el alumno guarda cuando quiere (y puede rehacerlo mientras la
atención siga abierta), no solo al cerrar la atención.
"""
from datetime import datetime

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class OaeReport(QWidget):
    """Tab 'Informe' del módulo EOA."""

    save_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.evaluador = ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)

        cab = QGroupBox("Informe de emisiones otoacústicas")
        form = QFormLayout(cab)
        self.lbl_eva = QLabel("-")
        form.addRow("Evaluador/a:", self.lbl_eva)
        self.lbl_date = QLabel(datetime.now().strftime("%d/%m/%Y"))
        form.addRow("Fecha:", self.lbl_date)
        # El módulo recibe el caso (data['EOAS']), no la ficha del paciente:
        # se identifica la atención, que es lo que ata el informe al perfil.
        self.lbl_atencion = QLabel("Sin atención abierta")
        form.addRow("Atención:", self.lbl_atencion)
        outer.addWidget(cab)

        # Resumen de lo capturado: el alumno tiene que ver QUÉ se va a
        # adjuntar antes de guardar (si olvidó capturar un oído, acá se
        # nota; en el PDF ya sería tarde).
        outer.addWidget(QLabel("Pruebas capturadas (se adjuntan al PDF):"))
        self.lbl_capturas = QLabel("--")
        self.lbl_capturas.setWordWrap(True)
        self.lbl_capturas.setStyleSheet("color: #444444;")
        outer.addWidget(self.lbl_capturas)

        outer.addWidget(QLabel("Descripción de los hallazgos:"))
        self.text_edit_1 = QTextEdit()
        self.text_edit_1.setPlaceholderText(
            "TEOAE / DPOAE por oído: bandas o frecuencias presentes y ausentes, "
            "SNR, reproducibilidad, piso de ruido, calidad del sello..."
        )
        outer.addWidget(self.text_edit_1, stretch=1)

        outer.addWidget(QLabel("Conclusión:"))
        self.text_edit_2 = QTextEdit()
        self.text_edit_2.setPlaceholderText(
            "Interpretación clínica: función coclear por oído, correlación con "
            "el resto de la evaluación y sugerencias."
        )
        outer.addWidget(self.text_edit_2, stretch=1)

        botones = QHBoxLayout()
        botones.addStretch(1)
        self.lbl_status = QLabel("")
        botones.addWidget(self.lbl_status)
        self.btn_save = QPushButton("Guardar informe")
        self.btn_save.clicked.connect(self.save_requested.emit)
        botones.addWidget(self.btn_save)
        outer.addLayout(botones)

    # ------------------------------------------------------------------
    def set_evaluador(self, text):
        self.evaluador = text or ""
        self.lbl_eva.setText(self.evaluador or "-")

    def set_atencion(self, appointment_id):
        self.lbl_atencion.setText(
            f"N° {appointment_id}" if appointment_id else "Sin atención abierta")

    def set_capturas(self, resumen):
        """`resumen`: lista de strings tipo 'TEOAE: OD, OI'."""
        self.lbl_capturas.setText(", ".join(resumen) if resumen
                                  else "Todavía no hay capturas.")

    def set_status(self, text, ok=True):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(
            "color: #27ae60;" if ok else "color: #c0392b;")

    def clear_texts(self):
        self.text_edit_1.clear()
        self.text_edit_2.clear()
        self.set_status("")
