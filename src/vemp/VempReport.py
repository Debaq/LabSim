"""
Panel de informe VEMP (hallazgos + conclusión).

Réplica simplificada de AbrReport sin el modo OSCE (VEMP no se usa en
estaciones OSCE todavía). El PDF lo arma el backend en report_pdf.php.
"""

from PySide6.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QLabel, QFormLayout
from datetime import datetime


class VempReport(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.case = ""
        self.evaluador = ""

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Fecha:'))
        self.lbl_date = QLabel(datetime.now().strftime('%d/%m/%Y'))
        layout.addWidget(self.lbl_date)

        form = QFormLayout()
        self.le_eva = QLabel('Evaluador: -')
        form.addRow('Evaluador:', self.le_eva)
        layout.addLayout(form)

        layout.addWidget(QLabel('Hallazgos:'))
        self.text_edit_1 = QTextEdit()
        self.text_edit_1.setPlaceholderText('Descripción de los hallazgos (latencias, amplitudes, asimetrías)...')
        layout.addWidget(self.text_edit_1)

        layout.addWidget(QLabel('Conclusión:'))
        self.text_edit_2 = QTextEdit()
        self.text_edit_2.setPlaceholderText('Interpretación clínica del examen...')
        layout.addWidget(self.text_edit_2)

    def set_le_eva(self, text):
        self.evaluador = text or ''
        self.le_eva.setText(f'Evaluador: {self.evaluador}')
