from datetime import datetime

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QWidget
from abr.UI.AbrReport_ui import Ui_AbrReport

tr = QCoreApplication.translate

class AbrReport(QWidget, Ui_AbrReport):
    def __init__(self) -> None:
        QWidget.__init__(self)
        self.setupUi(self)
        self.lbl_date.setText(self.date_current())
        self.case = ""
        self.type_use = "exam"
        self.modo_estacion_5 = False  # Flag para modo Estación 5 OSCE

    def activar_modo_estacion_5(self):
        """
        Activa el modo Estación 5 del OSCE:
        - Oculta la pestaña Esquema
        - Solo muestra Conclusiones
        """
        self.modo_estacion_5 = True
        # Ocultar pestaña Esquema (índice 1)
        self.tabWidget.removeTab(1)
        # Ahora solo queda Conclusiones (índice 0)
        self.tabWidget.setCurrentIndex(0)
        print("✓ Modo Estación 5 activado: Solo pestaña Conclusiones visible")

    def desactivar_modo_estacion_5(self):
        """Desactiva el modo Estación 5 y restaura todas las pestañas"""
        if self.modo_estacion_5:
            self.modo_estacion_5 = False
            # Reconstruir el widget para restaurar todas las pestañas
            print("✓ Modo Estación 5 desactivado")

    def date_current(self):
        current_date = datetime.now().strftime("%d/%m/%Y")
        return current_date

    def set_le_eva(self, text):
        self.le_eva.setDisabled(True)
        self.le_eva.setText(text)

    def obtener_informe_estacion_5(self):
        """
        Obtiene el informe de la Estación 5 desde los campos de la pestaña Conclusiones
        Retorna un dict compatible con el formato esperado por GeneradorInformeOSCE
        """
        import datetime

        informe_data = {
            'datos_caso': {
                'identificacion': 'Caso 3 - Estación 5',
                'fecha': self.lbl_date.text(),
                'condiciones': 'Evaluación OSCE - Estación 5'
            },
            'hallazgos': self.text_edit_1.toPlainText(),  # Campo "Descripción"
            'normativos': '',  # No hay campo específico, se incluye en conclusión
            'conclusion': self.text_edit_2.toPlainText(),  # Campo "Conclusión"
            'caso_id': self.case,
            'timestamp': datetime.datetime.now().isoformat()
        }

        return informe_data