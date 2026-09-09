"""
Panel de informe VEMP (hallazgos + conclusión).

Réplica simplificada de AbrReport sin el modo OSCE (VEMP no se usa en
estaciones OSCE todavía). El PDF lo arma el backend en report_pdf.php.

Arriba de los cuadros de texto va la razón de asimetría, que la calcula el
módulo con las amplitudes pico-pico marcadas por el alumno. Se muestra el
número y la cuenta, no una lectura: qué asimetría es patológica lo decide
quien informa.
"""

from datetime import datetime

from PySide6.QtWidgets import (QFormLayout, QLabel, QTextEdit, QVBoxLayout,
                               QWidget)


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

        self.lbl_asimetria = QLabel('Razón de asimetría: sin amplitudes marcadas')
        self.lbl_asimetria.setWordWrap(True)
        layout.addWidget(self.lbl_asimetria)

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

    def set_asimetria(self, subtipo, od=None, oi=None, ratio=None):
        """od/oi: amplitud pico-pico (µV) de cada oído; ratio: AR en %."""
        if ratio is None:
            self.lbl_asimetria.setText(
                f'Razón de asimetría ({subtipo}): faltan amplitudes pico-pico '
                'en uno de los dos oídos')
            return
        self.lbl_asimetria.setText(
            f'Razón de asimetría ({subtipo}): {ratio:.0f}%  '
            f'[|{od:.1f} - {oi:.1f}| / ({od:.1f} + {oi:.1f})]')
