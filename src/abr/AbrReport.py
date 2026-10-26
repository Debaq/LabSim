from datetime import datetime

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from abr.UI.AbrReport_ui import Ui_AbrReport

tr = QCoreApplication.translate

class AbrReport(QWidget, Ui_AbrReport):
    def __init__(self) -> None:
        QWidget.__init__(self)
        self.setupUi(self)
        self.lbl_date.setText(self.date_current())
        self.case = ""
        self.type_use = "exam"
        self.armar()

    def armar(self):
        """Tres columnas a todo el alto: las curvas para tener a la vista, la
        descripción y la conclusión. Antes iban apiladas bajo un título
        grande (fijo, no cambiaba con la prueba) y los cuadros de texto se
        achicaban hasta no poder escribir."""
        self.tabWidget.tabBar().setVisible(False)
        for etiqueta in (self.label, self.label_2):
            etiqueta.hide()
        raiz = self.verticalLayout
        while raiz.count():
            raiz.takeAt(0)
        raiz.setSpacing(10)
        raiz.setContentsMargins(12, 10, 12, 10)

        cabecera = QHBoxLayout()
        self.le_eva.setMaximumWidth(280)
        cabecera.addWidget(self.le_eva)
        cabecera.addStretch(1)
        # Si quedó guardado o no (ver AbrMainWindow: EstadoInforme).
        self.layout_estado = QVBoxLayout()
        cabecera.addLayout(self.layout_estado)
        cabecera.addSpacing(16)
        cabecera.addWidget(self.lbl_date)
        raiz.addLayout(cabecera)

        columnas = QHBoxLayout()
        columnas.setSpacing(14)
        self.layout_resumen = QVBoxLayout()
        self.layout_resumen.setContentsMargins(0, 0, 0, 0)
        self.col_resumen = QWidget()
        self.col_resumen.setFixedWidth(400)
        col = QVBoxLayout(self.col_resumen)
        col.setContentsMargins(0, 0, 0, 0)
        col.addWidget(self._seccion(tr("AbrReport", "CURVAS")))
        col.addLayout(self.layout_resumen, 1)
        columnas.addWidget(self.col_resumen)

        for etiqueta, texto, caja in ((self.label_3, "DESCRIPCIÓN", self.text_edit_1),
                                      (self.label_4, "CONCLUSIÓN", self.text_edit_2)):
            etiqueta.setText(tr("AbrReport", texto))
            etiqueta.setProperty("role", "seccion")
            columna = QVBoxLayout()
            columna.addWidget(etiqueta)
            columna.addWidget(caja, 1)
            columnas.addLayout(columna, 1)
        raiz.addLayout(columnas, 1)

    @staticmethod
    def _seccion(texto):
        etiqueta = QLabel(texto)
        etiqueta.setProperty("role", "seccion")
        return etiqueta

    def date_current(self):
        current_date = datetime.now().strftime("%d/%m/%Y")
        return current_date

    def set_le_eva(self, text):
        self.le_eva.setDisabled(True)
        self.le_eva.setText(text)
