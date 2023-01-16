import sys


from collections import namedtuple

import numpy as np
import pyqtgraph as pg
from PIL import Image
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QTransform, QPainterPath, QFont
from PySide6.QtWidgets import (QGraphicsEllipseItem, QMessageBox, QWidget,
                               QHBoxLayout, QLabel, QComboBox, QPushButton)

from base import context
from lib.helpers import Preferences
from UI.Ui_CVC import Ui_CVC
from UI.Ui_pref_cvc import Ui_pref_cvc
from UI.Ui_cvc_test import Ui_test

Preferences = Preferences()
pref_cvc = Preferences.get("CVC")

class UiTest(QWidget, Ui_test):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.graph = Graph_CVC()
        self.layout_graph.addWidget(self.graph.plot_widget)
        self.eye_image = EyeImage()
        self.layout_eye_2.addWidget(self.eye_image.plot_widget)
        
    def move_image(self, i):
        key = self.sender().text()
        vel =5
        if key == "up":
            self.eye_image.move_camera(vel,0)
        if key == "down":
            self.eye_image.move_camera(-vel,0)
        if key == "left":
            self.eye_image.move_camera(0,-vel)
        if key == "right":
            self.eye_image.move_camera(0,vel)

class Graph_CVC(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        color_backgournd = pg.mkColor(255, 255, 255, 255)
        self.color_pen = pg.mkColor(0, 0, 0, 255)
        pg.setConfigOption('background', color_backgournd)
        pg.setConfigOption('foreground', self.color_pen)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setMaximumSize(350,350)
        self.plot_widget.setXRange(-7, 7)
        self.plot_widget.setYRange(-7, 7)
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.setMouseEnabled(False, False)
        self.plot_widget.enableAutoRange(enable=True)
        self.plot_widget.getPlotItem().hideAxis('bottom')
        self.plot_widget.getPlotItem().hideAxis('left')
        self.threshold_memory = [False,False]
        self.side_current = 0
        self.pattern = pref_cvc["test_pattern"]
        self.tests = pref_cvc["biblio_test"]
        self.text_symbol = namedtuple("TextSymbol", "label symbol scale")
        self._draw_scheme()

    def dot(self, side, test=None):
        if test is None:
            test = "Central 30-2"
        
        test_actual = self.tests[test]
        data_y = []
        data_x = []
        for row, data in enumerate(test_actual):
            if side:
                data = list(reversed(data))
            for column, datum in enumerate(data):
                if datum:
                    data_x.append(self.pattern[row][column][0])
                    data_y.append(self.pattern[row][column][1])

        return data_x, data_y

    def createLabel(self, label):
        label = str(label)
        symbol = QPainterPath()
        #symbol.addText(0, 0, QFont("San Serif", 10), label)
        f = QFont()
        f.setPointSize(10)
        symbol.addText(0, 0, f, label)
        br = symbol.boundingRect()
        scale = min(1. / br.width(), 1. / br.height())
        tr = QTransform()
        tr.scale(scale, scale)
        #tr.rotate(angle)
        tr.translate(-br.x() - br.width()/2., -br.y() - br.height()/2.)
        return self.text_symbol(label, tr.map(symbol), 0.1 / scale)


    def _decibels(self, data):
        
        s2 = pg.ScatterPlotItem(size=1, pen=pg.mkPen('black'), pxMode=True)
        spots = []
        for datum in data:
            
            label = self.createLabel(datum[0])
            pos = (datum[1],datum[2])
            d_d ={'pos': pos, 'data': 1, 'brush':pg.hsvColor(0,0,1), 'symbol': label[1], 'size': label[2]*10}
            spots.append(d_d)
            
        s2.addPoints(spots)
        self.plot_widget.addItem(s2)


    def _threshold(self, db):
        thresh = pg.TextItem(text=f"Umbral Foveal:{db}db", color=(0,0,0), anchor=(-1,3.6))
        self.plot_widget.addItem(thresh)
    
    def activate_threshold(self, db):
        self.threshold_memory[self.side_current] = db
        self._draw_scheme(init=False)
    
    def _draw_circle(self,  arg0, fill = False):
        circle= QGraphicsEllipseItem(-arg0,-arg0,arg0  * 2, arg0 * 2)
        circle.setPen(pg.mkPen(0.2))
        if fill:
            circle.setBrush(pg.mkBrush(color=(255,255,255)))
        return circle

    def _draw_across(self,  arg0, arg1, arg2, arg3):
        across = pg.PlotCurveItem()
        across.setData(x=[arg0,arg1], y=[arg2,arg3])
        across.setPen(pg.mkPen(0.2))
        return across
    
        
    def _draw_scheme(self, init=True, test=None):
        across_x = self._draw_across(-6, 6, 0, 0)
        across_y = self._draw_across(0, 0, -6, 6)
        self.plot_widget.addItem(across_x)
        self.plot_widget.addItem(across_y)
        circle_center = self._draw_circle(0.5, True)
        circle_peri = self._draw_circle(7)
        self.plot_widget.addItem(circle_center)
        self.plot_widget.addItem(circle_peri)
        if init:
            dots = self._draw_dot(0, test)
            self.plot_widget.addItem(dots)
        
        if self.threshold_memory[self.side_current]:
            self._threshold(self.threshold_memory[self.side_current])
            self._decibels([[30,2,3],[28,0,1]])

    def read_case(self):
        pass

    def _draw_dot(self, side, test):
        dots_data =self.dot(side, test)
        dots = pg.ScatterPlotItem()
        dots.setData(x=dots_data[0], y=dots_data[1], size=3)
        dots.setPen(pg.mkPen(0.2))
        return dots

    def change_side(self, side, test):
        self.side_current = side
        self.plot_widget.getPlotItem().clear()
        dots = self._draw_dot(side, test)
        self.plot_widget.addItem(dots)
        self._draw_scheme(False, test)

class EyeImage(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        color_backgournd = pg.mkColor(255, 255, 255, 255)
        self.color_pen = pg.mkColor(0, 0, 0, 255)
        pg.setConfigOption('background', color_backgournd)
        pg.setConfigOption('foreground', self.color_pen)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setMaximumSize(200,200)
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.setMouseEnabled(False, False)
        self.plot_widget.enableAutoRange(enable=True)
        
        ####
        self.timer_animation = QTimer(self)
        self.timer_animation.timeout.connect(self._animation_image)
        self.timer_animation.start(25)
        self.position = [-180,-320]
        self.images = self._image_load()
        
        self.current_sit()
        self.plot_widget.getPlotItem().hideAxis('bottom')
        self.plot_widget.getPlotItem().hideAxis('left')
        self.plot_widget.setXRange(-100, 100)
        self.plot_widget.setYRange(-100, 100)
        
    def _animation_image(self):
        i = self.image_current[1][1]
        #print(self.image_current)
        if self.image_current[0] == 0:
            self.image_current[0] = self.image_current[1][0]
        next_image = self.image_current[0] + 1
        if next_image == i:
            next_image = self.image_current[1][0]
        self.image_current[0] = next_image
        self._update_image()
        
    def _image_load(self, patient=1):
        name_folder = f"img/cvc_pat_{patient}"
        name_file = f"{name_folder}/cvc_eye-2500_"
        extencion = ".jpg"
        images = (1, 518) #aca se cargan todas las imagenes
        data_image=[]
        for i in range(images[0], images[1]):
            #print(f"cvc_eye-2500_{i:05d}")
            i = i + 1
            image = Image.open(context.get_resource(f"{name_file}{i:05d}{extencion}"))
            data_image.append(image)
        return data_image
    
    def _update_image(self):
        transform_image = QTransform()
        transform_image.rotate(-90)
        transform_image.scale(1.5, 1.5)
        #transform_image.translate(-452, -112)
        X , Y = self.position
        transform_image.translate(X, Y)
        self.plot_widget.getPlotItem().clear()
        image_current = self.images[self.image_current[0]]
        img_np = np.array(image_current)
        #crop_image = img_np[100:250, 80:230]
        img = pg.ImageItem(image=img_np) # create example image
        img.setRect(1000, -1.5, 3, 3)
        img.setTransform(transform_image) # assign transform     
        self.plot_widget.addItem(img)
        self.across()
        
    def move_camera(self, x, y):
        x_mov = self.position[0] + x
        y_mov = self.position[1] + y
        #x_mov = min(x_mov, 70)
        #x_mov = max(x_mov, -70)
        #y_mov = min(y_mov, 230)
        #y_mov = max(y_mov, -230)
        self.position = [x_mov, y_mov]
        

    def across(self):
        across_x = self._extracted_from_across_2(-10, 10, 0, 0)
        across_y = self._extracted_from_across_2(0, 0, 10, -10)
        self.plot_widget.addItem(across_x)
        self.plot_widget.addItem(across_y)


    # TODO Rename this here and in `across`
    def _extracted_from_across_2(self, arg0, arg1, arg2, arg3):
        result = pg.PlotCurveItem()
        result.setData(x=[arg0, arg1], y=[arg2, arg3])
        result.setPen(pg.mkPen(0.2))
        result.setPen(pg.mkPen(color=(0,254,0)))
        return result
    
    def current_sit(self, sit=0)->None:
        situaciones = [ [0,[0,200]], [0,[100,101]], [0,[470,500]], [0,[280,350]]
            
        ]
        self.image_current = situaciones[sit] #[iterador, [range]]
        

class PrefCVC(QWidget, Ui_pref_cvc):
    sig = Signal(dict)
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("Configuración de parámetros de umbral")
        self.state = {'Estrategia de prueba': 'SITA-Standard', 
                      'Velocidad de Prueba': 'Normal', 
                      'Objetivo de fijación': 'Central', 
                      'Monitorización de fijación': 'Mirada/Mancha ciega', 
                      'Azul - amarillo': 'Apagado', 
                      'Umbral foveal': 'Apagado', 
                      'Tamaño del estímulo': 'I', 
                      'Color de estímulo': 'Blanco', 
                      'Fluctuación': 'Apagado'}
    
    def agrege(self,it):
        self.variables = it
        for i, v in it.items():
            l = QHBoxLayout()
            lbl = QLabel(i)
            box = QComboBox()
            box.activated.connect(self._set_pref)
            box.setObjectName(i)
            box.addItems(v)
            self._add_widget_layout(l, lbl, box)
        button_acept = QPushButton("Aceptar")
        button_cancel = QPushButton("Cancelar")
        button_cancel.clicked.connect(self.close)
        button_acept.clicked.connect(self.get_pref)
        btn_layout = QHBoxLayout()
        self._add_widget_layout(btn_layout, button_acept, button_cancel)

    def _add_widget_layout(self, layout, widget_1, widget_2):
        layout.addWidget(widget_1)
        layout.addWidget(widget_2)
        self.verticalLayout.addLayout(layout)
        
    def _set_pref(self, value):
        variable = self.sender().objectName()
        value = self.variables[variable][value]
        self.state[variable] = value
        
        
    def get_pref(self):
        self.sig.emit(self.state)
        self.close()
        
        


class CVC(QWidget, Ui_CVC):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.test = UiTest()
        self.horizontalLayout_3.addWidget(self.test)
        self.test.btn_change_eye.clicked.connect(lambda:self.change_eye(True))
        self.test.btn_play_pause.clicked.connect(self.starTest)
        self.test.btn_state.clicked.connect(self.state_test)
        self.test.btn_param.clicked.connect(self.pref_test)
        self.values_config = 0
        self.w = PrefCVC()
        self.w.agrege(pref_cvc["config_param_thres_cvc"])
        self.w.sig.connect(self.get_values_config)
        self.eyes = ["OD", "OI"]
        self.current_eye = 0
        self.start=False
        self.time = QTimer(self)
        self.time.timeout.connect(self.counter)
        self.btn_left.clicked.connect(self.test.move_image)
        self.btn_right.clicked.connect(self.test.move_image)
        self.btn_down.clicked.connect(self.test.move_image)
        self.btn_up.clicked.connect(self.test.move_image)
        #ojos_info[umbral, [decibeles 10x10], ubicación mancha ciega,errores[falsos negativos, falsos positivo, perdidas de fijación]]
        self.show()

        #self.image_eye()

    def get_values_config(self,x):
        self.values_config = x
        self.change_eye(False)
        

    def change_eye(self, change=True):
        if change:
            self.current_eye = 1 if self.current_eye == 0 else 0
        if self.values_config:
            test = self.values_config["formato de análisis"]
        else: test = None
        self.lbl_side_eye.setText(self.eyes[self.current_eye])
        self.test.graph.change_side(self.current_eye, test)
        self.test.btn_play_pause.setText("Iniciar")
        self.start=False


    def starTest(self):
        if self.start == False:
            self.start=True
            self.test.btn_play_pause.setText("Pausar")
            self._threshold_foveal()

        else:
            self.start=False
            self.test.btn_play_pause.setText("Continuar")
            
    def _threshold_foveal(self):
        msg_box = QMessageBox()
        msg_box.setText("se comenzara a medir el umbral")
        msg_box.setInformativeText("mire las luces de fijación inferiores")
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Ok)
        msg_box.exec()
        if msg_box.clickedButton() == msg_box.button(QMessageBox.Ok):
            self.time_thershold = 0
            self.time.start(1000)
            self.measuring = self.advice_win(info="Comenzando medición")
            self.test.eye_image.current_sit(1)
            self.measuring.show()
        else:
            self.test.btn_play_pause.setText("Iniciar")
            self.start=False


    def counter(self):
        self.time_thershold += 1
        self.measuring.setText("Midiendo umbral foveal")
        self.measuring.setInformativeText(f"Tiempo transcurrido 00:{self.time_thershold}")
        if self.time_thershold == 10:
            self.measuring.close()
            self.test.graph.activate_threshold(5)
            self.time.stop()
            
    def measure(self):
        pass

    def advice_win(self, title = None, info = None, btn = False):
        adv = QMessageBox()
        if title is not None:
            title = f"<b>{title}</b>"
            adv.setText(title)
        if info is not None:
            adv.setInformativeText(info)
        adv.setStandardButtons(QMessageBox.Ok)
        if btn is False:
            adv.button(QMessageBox.Ok).hide()
        return adv

    def state_test(self):
        if not self.values_config:
            win = self.advice_win("error", "no ha configurado aún", btn=True)
        else:
            text = ""
            for i in self.values_config:
                text = f"{text}<br>{i} : <b>{self.values_config[i]}</b>"
            win = self.advice_win(
                title= "Parametros de la prueba",
                info=text, btn=True)
        win.exec()

    def pref_test(self):
        self.w.show()
        


if __name__ == '__main__':
    window = CVC()
    exit_code = context.app.exec()
    sys.exit(exit_code)
    