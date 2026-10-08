"""Panel de informe EOA (hallazgos + conclusión + aviso de guardado).

Mismo patrón que AbrReport/VempReport: el alumno escribe la descripción y
la conclusión, y el PDF lo arma el backend (report_pdf.php) con las
capturas de los 4 tabs. Se guarda solo mientras se atiende, como todos
los módulos de examen (ver core/report_autosave.py): hasta 2026-10-08 había
un botón "Guardar informe" propio de EOA.
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.estado_informe import EstadoInforme


class OaeReport(QWidget):
    """Tab 'Informe' del módulo EOA."""

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
        # adjuntar (si olvidó capturar un oído, acá se
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

        self.estado = EstadoInforme()
        outer.addWidget(self.estado)

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

    def clear_texts(self):
        self.text_edit_1.clear()
        self.text_edit_2.clear()
        self.estado.limpiar()
