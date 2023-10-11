import sys
from fbs_runtime.application_context.PySide6 import ApplicationContext
from lib.ContextManager import AppContextManager
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QSpacerItem, 
                               QSizePolicy, QMdiArea, QLabel, QWidget, QMdiSubWindow)
from PySide6.QtCore import Qt
from lib.CustomWidgets import CustomMdiArea, CustomMdiSubWindow
import json
from lib.ModuleImport import importar_modulo, importar_ui

MARGIN_RL = 20
MARGIN_TB = 20

class AppContext(ApplicationContext):
    def run(self):
        window = MainWindow()
        
        window.show()
        return self.app.exec()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LabSim")
        self.showFullScreen()
        self.setCentralWidget(MainWidget(self))


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(MARGIN_TB, MARGIN_RL, MARGIN_TB, MARGIN_RL)

        # Widget y layout para horizontal layout 1
        h_widget1 = QWidget()
        h_layout1 = QHBoxLayout(h_widget1)
        self.modules = {}
        
        # Leer el archivo JSON y crear botones
        with open(appctxt.get_resource("json/config.json"), 'r') as file:
            data = json.load(file)
            for win, props in data["windows"].items():
                if props["active"]:
                    btn = QPushButton(props["name"])
                    btn.clicked.connect(self.btn_test)
                    btn.setObjectName(win)
                    h_layout1.addWidget(btn)
                    #importar modulos
                    module_ui = f"UI_{win}"
                    module_logic = f"Logic_{win}"
                    self.modules[win] = [importar_ui(module_ui), importar_modulo(module_logic)]
                    
        btn_stop = QPushButton("stop")
        btn_stop.clicked.connect(self.stop)
        h_layout1.addWidget(btn_stop)
        
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        soft_name = QLabel("LabSim")
        h_layout1.addItem(spacer)
        h_layout1.addWidget(soft_name)
        h_layout1.setContentsMargins(0, 0, 0, 0)
        h_widget1.setFixedHeight(30)
        
        # Widget y layout para horizontal layout 2
        h_widget2 = QWidget()
        h_layout2 = QHBoxLayout(h_widget2)
        logo = appctxt.get_resource("img/LogoBN_back.png")
        self.mdi_area = CustomMdiArea(logo=logo)
        h_layout2.addWidget(self.mdi_area)
        h_layout2.setContentsMargins(0, 0, 0, 0)

        # Widget y layout para horizontal layout 3
        h_widget3 = QWidget()
        h_layout3 = QHBoxLayout(h_widget3)
        self.label = QLabel("listo")
        h_layout3.addWidget(self.label)
        h_widget3.setFixedHeight(30)
        h_layout3.setContentsMargins(0, 0, 0, 0)

        # Añadir widgets al layout principal
        main_layout.addWidget(h_widget1)
        main_layout.addWidget(h_widget2, 1)
        main_layout.addWidget(h_widget3)

        self.setLayout(main_layout)

    def set_label_info(self, text):
        self.label.setText(text)

    def btn_test(self):
        self.add_subwindow()

    def add_subwindow(self):
        ui = self.modules[self.sender().objectName()][0]
        fn = self.modules[self.sender().objectName()][1]
        fn_ui = fn.Funccion(ui)
        #print(dir(ui))
        #self.player.play(noise_type="tone")  # Change to "white", "pink", or "nbn" as needed
        subwindow = CustomMdiSubWindow(fn_ui)
        subwindow.setWindowTitle(self.sender().objectName())
        #subwindow.resize(200, 100)
        self.mdi_area.addSubWindow(subwindow)
        subwindow.show()


if __name__ == '__main__':
    appctxt = AppContext()
    AppContextManager.set_context(appctxt)
    exit_code = appctxt.run()
    sys.exit(exit_code)
