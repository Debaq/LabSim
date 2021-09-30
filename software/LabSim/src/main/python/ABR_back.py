# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                          VER. 0.7.5                           #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################

import json
import sys
import time
import random

import requests
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import Qt, pyqtSignal

from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton

import pyqtgraph as pg
import numpy as np

import lib.bezier_prop as bz

from UI.Ui_ABR_control import Ui_ABRSim
from UI.Ui_ABR_config import Ui_ABR_config
from UI.Ui_ABR_lat_select import Ui_ABR_lat_select
from UI.Ui_ABR_ctrl_graph import Ui_ABR_control_curve
from UI.Ui_ABR_detail import Ui_ABR_detail
from lib.EEG import EEG
from lib.ABR_generator import ABR_creator

class ABR_control(QWidget, Ui_ABR_config):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)


class ABR_detail(QWidget, Ui_ABR_detail):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)


class ABR_lat_select(QWidget, Ui_ABR_lat_select):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.data = {'lat_A':0, 'lat_B':0,'amp_AB':0, 'lat_AB':0,
                    'I':0,'Ip':0,'II':0,'IIp':0,
                    'III':0,'IIIp':0,'IV':0,'IVp':0,
                    'V':0,'Vp':0, 'I_III' : 0, 
                    'III_V' : 0, 'I_V' : 0}
        self.update_data()

    def update_data(self, key=None, value=None):

        if key is not None and value is not None:
            self.data[key] = value
            if self.data['I'] != 0 and self.data['III'] != 0:
                self.data['I_III'] = self.data['III'] - self.data['I']
            if self.data['I'] != 0 and self.data['V'] != 0:
                self.data['I_V'] = self.data['V'] - self.data['I']
            if self.data['III'] != 0 and self.data['V'] != 0:
                self.data['III_V'] = self.data['V'] - self.data['III']

        self.lbl_1.setText('A:{:.1f}ms B:{:.1f}ms'.format(self.data['lat_A'], self.data['lat_B']))
        self.lbl_2.setText('A-B:{:.2f}μV'.format(self.data['amp_AB']))
        self.lbl_3.setText('A<>B:{:.2f}ms'.format(self.data['lat_AB']))
        self.lbl_4.setText("I:{:.1f}ms I':{:.1f}ms".format(self.data['I'],self.data['Ip']))
        self.lbl_5.setText("II:{:.1f}ms II':{:.1f}ms".format(self.data['II'],self.data['IIp']))
        self.lbl_6.setText("III:{:.1f}ms III':{:.1f}ms".format(self.data['III'],self.data['IIIp']))
        self.lbl_7.setText("IV:{:.1f}ms IV':{:.1f}ms".format(self.data['IV'],self.data['IVp']))
        self.lbl_8.setText("V:{:.1f}ms V':{:.1f}ms".format(self.data['V'],self.data['Vp']))
        self.lbl_9.setText("I-III:{:.1f}ms".format(self.data['I_III']))
        self.lbl_10.setText("III-V:{:.1f}ms".format(self.data['III_V']))
        self.lbl_11.setText("I-V:{:.1f}ms".format(self.data['I_V']))


class ABR_ctrl_curve(QWidget, Ui_ABR_control_curve):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)


class Graph(QWidget):
    data_info = pyqtSignal(dict)
    lat_info = pyqtSignal(dict)
    def __init__(self):
        QWidget.__init__(self)
        color_backgorund = pg.mkColor(255, 255, 255, 255)
        self.color_pen = pg.mkColor(0, 0, 0, 255)
        pg.setConfigOption('background', color_backgorund)
        pg.setConfigOption('foreground', self.color_pen)
        self.pw1 = pg.PlotWidget(name='Plot1', background='default')
        self.pw1.setRange(yRange=(-2, 2), xRange=(0, 12), disableAutoRange=True)
        self.pw1.showGrid(x=True, y=True)
        self.pw1.setMouseEnabled(x=False, y=False)
        self.pw1.setMenuEnabled(False)
        #ax = self.pw1.getAxis('bottom')
        ay = self.pw1.getAxis('left')
        ay.setStyle(showValues=False)
        self.inifineA_B()
        #self.x = 0
        #self.y = 0
        self.marks = {'I': None, 'II':None, 'III':None, 'IV':None, 'V':None,
                      'Ip': None, 'IIp':None, 'IIIp':None, 'IVp':None, 'Vp':None}
        self.change_mark = False


    def find_nearest(self, array_in, value, array_out):
        array = np.asarray(array_in)
        idx = (np.abs(array - value)).argmin()
        return array_out[idx]

    def inifineA_B(self, pos_A = 0, pos_B = 0):
        #Variables internas
        pen1 = pg.mkPen('b', width=.5, style=Qt.DashLine)         
        opst = {'position':0.9, 'color': (255,255,255), 'fill': (0,0,0,255), 'movable': True}
        #Lineas infinitas
        self.inf_A = pg.InfiniteLine(pos=pos_A, movable=True, angle=90, pen=pen1, label ="A", labelOpts=opst)
        self.inf_B = pg.InfiniteLine(pos=pos_B, movable=True, angle=90, pen=pen1, label ="B", labelOpts=opst)
        #Posición en X de las lineas infinitas
        self.inf_A.sigPositionChanged.connect(self.get_amplitude)
        self.inf_B.sigPositionChanged.connect(self.get_amplitude)
        #Se agregan lineas infinitas a la grafica
        self.pw1.addItem(self.inf_A)
        self.pw1.addItem(self.inf_B)

    def update_graph(self):
        #Se actualiza el grafico
        #Variables internas
        pos_A = self.inf_A.getXPos()
        pos_B = self.inf_B.getXPos()
        #Plot con limpieza
        self.pw1.plot(self.newData, clear=True)
        #actualizar los componentes del gráfico
        self.inifineA_B(pos_A, pos_B)
        #self.update_marks()
       

    def update_data(self, data):
        #se actualiza el data del grafico
        x = data[0]
        y = data[1]
        self.newData = x,y
        

    def create_marks(self, mark, value):
            #lat_A = self.inf_A.getXPos()
            amp_A = self.find_nearest(self.x, value, self.y)
            if mark[-1] == "p":
                mod = mark[:-1]
                curve_mark = "|{}'".format(mod)
            else:
                curve_mark = "|{}".format(mark)
            text = pg.TextItem(text = curve_mark, anchor=(0.34,0.5), color=(0,0,0,255))
            #text.setPos(lat_A, amp_A)
            text.setPos(value, amp_A)
            self.pw1.addItem(text)
            self.lat_info.emit(self.marks)


    def change_keys(self, key=None, value=None):
        if key is not None and value is not None:
            self.change_mark = True
            self.marks[key] =  value
            self.update_graph()

    def update_marks(self):
        keys = self.marks.keys()
        for i in keys:
            if self.marks[i] is not None:

                self.create_marks(mark=i, value=self.marks[i])



    def move_graph(self, str_ud):
        if str_ud == "up":
            self.y = self.y + .1
        if str_ud == "down":
            self.y = self.y - .1
        self.update_graph()
    
    def get_amplitude(self):
        lat_A = self.inf_A.getXPos()
        lat_B = self.inf_B.getXPos()
        amp_A = self.find_nearest(self.x, lat_A, self.y)
        amp_B = self.find_nearest(self.x, lat_B, self.y)
        order_amp = np.sort(np.array([amp_A,amp_B]))
        order_lat = np.sort(np.array([lat_A,lat_B]))
        
        dif_amp = order_amp[1] - order_amp[0]
        dif_lat = order_lat[1] - order_lat[0]
        
        response = {"lat_A": lat_A, "lat_B": lat_B, "amp_AB": dif_amp, "lat_AB": dif_lat}
        self.data_info.emit(response)



class MainWindow(QWidget, Ui_ABRSim):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.control = ABR_control()
        self.detail = ABR_detail()
        self.eeg = EEG()
        self.detail.layout_eeg.addWidget(self.eeg.pw)

        self.lat_select_R = ABR_lat_select()
        self.lat_select_L = ABR_lat_select()
        self.ctrl_curve_R = ABR_ctrl_curve()
        self.ctrl_curve_L = ABR_ctrl_curve()

        self.grph_R = Graph()
        self.grph_L = Graph()

        #LAYOUTS
        self.layout_left.addWidget(self.control)
        self.layout_left.addWidget(self.detail)
        self.layout_left.addWidget(self.eeg)


        self.layourt_ctrl_R.addWidget(self.lat_select_R)
        self.layourt_ctrl_L.addWidget(self.lat_select_L)
        self.layout_ctrl_curve_R.addWidget(self.ctrl_curve_R)
        self.layout_ctrl_curve_L.addWidget(self.ctrl_curve_L)

        self.ctrl_curve_R.btn_up.clicked.connect(lambda:self.grph_R.move_graph("up"))
        self.ctrl_curve_R.btn_down.clicked.connect(lambda:self.grph_R.move_graph("down"))
        
        self.layout_graph_R.addWidget(self.grph_R.pw1)
        self.layout_graph_L.addWidget(self.grph_L.pw1)
        self.store = dict()
        self.data = ABR_creator()
       
       

        self.grph_R.data_info.connect(self.update_data)
        self.grph_L.data_info.connect(self.update_data)
        self.grph_L.lat_info.connect(self.update_data)
        self.grph_R.lat_info.connect(self.update_data)

        self.lat_select_R.btn_wave_I.clicked.connect(lambda:self.update_markers("I"))
        self.lat_select_R.btn_wave_II.clicked.connect(lambda:self.update_markers("II"))
        self.lat_select_R.btn_wave_III.clicked.connect(lambda:self.update_markers("III"))
        self.lat_select_R.btn_wave_IV.clicked.connect(lambda:self.update_markers("IV"))
        self.lat_select_R.btn_wave_V.clicked.connect(lambda:self.update_markers("V"))

        self.lat_select_R.btn_wave_Ip.clicked.connect(lambda:self.update_markers("Ip"))
        self.lat_select_R.btn_wave_IIp.clicked.connect(lambda:self.update_markers("IIp"))
        self.lat_select_R.btn_wave_IIIp.clicked.connect(lambda:self.update_markers("IIIp"))
        self.lat_select_R.btn_wave_IVp.clicked.connect(lambda:self.update_markers("IVp"))
        self.lat_select_R.btn_wave_Vp.clicked.connect(lambda:self.update_markers("Vp"))
        self.detail.btn_start.clicked.connect(self.capture)
        self.control


    def capture(self):
        intencity = self.control.sb_int.value()
        side = self.control.cb_side.currentText()
        if side == 'OD':
            side = 0
            letter = 'R'
        else: 
            side = 1
            letter = 'L'
        
        name = "{}_{}:0".format(intencity, letter)

        if name in self.store:
            name = self.numberName(name, letter, intencity)
   
        view = True
        repro = random.randint(80,99)
        self.store[name] = [[[],[]],[[],[]],side, intencity, repro, view]
        self.data.set_intencity(intencity)
        x, y = self.data.get()
        self.store[name][0][0] = x
        self.store[name][0][1] = y
        self.disabledInCapture()
        self.updateFlagsCurves()
        self.updateGraph(name)


        
        
        
        
    def updateGraph(self, curve):
        data = self.store[curve]
        x = data[0][0]
        y = data[0][1]
        side = data[2]
        if side == 0:
            self.grph_R.update_data([x,y])
            self.grph_R.update_graph()
        else:
            self.grph_L.update_data([x,y])
            self.grph_L.update_graph()
        
        self.disabledInCapture(False)
            


    def updateFlagsCurves(self):
        for i in reversed(range( self.ctrl_curve_R.layout_curves.count())): 
             self.ctrl_curve_R.layout_curves.itemAt(i).widget().deleteLater()
        for i in reversed(range( self.ctrl_curve_L.layout_curves.count())): 
            self.ctrl_curve_L.layout_curves.itemAt(i).widget().deleteLater()
        btns_left = list()
        btns_Right = list()
        for k in self.store:
            y, x = k.split('_')
            l,num = x.split(':')
            name = "{} {}{}".format(y, l, num) 
            id = k
            btn = [name,id]
            if l == 'L':
                btns_left.append(btn)
            else:
                btns_Right.append(btn)
            
            styleR = ("""
            QWidget {
                color: rgb(0, 0, 0);
                background-color: rgb(255, 0, 0);
            }
            """)
            styleL = ("""
            QWidget {
                color: rgb(0, 0, 0);
                background-color: rgb(0, 0, 255);
            }
            """)            
        
        for i in range(len(btns_left)):
            btn = QPushButton('{}'.format(btns_left[i][0]))
            btn.setObjectName(btns_left[i][1])
            btn.setStyleSheet(styleL)
            #btn.setCheckable(True)
            self.ctrl_curve_L.layout_curves.addWidget(btn)
        for i in range(len(btns_Right)):
            btn = QPushButton('{}'.format(btns_Right[i][0]))
            btn.setObjectName(btns_Right[i][1])
            btn.setStyleSheet(styleR)

            #btn.setCheckable(True)
            self.ctrl_curve_R.layout_curves.addWidget(btn)




    def numberName(self, name, ltr, tin):
        n = list()
        for i in self.store:
            _,x = i.split('_')
            l,num = x.split(':')
            if l == ltr:
                n.append(int(num))
        n.sort()
        resultN = n[-1]+1
        name = "{}_{}:{}".format(tin,ltr,resultN)
        return name


    def disabledInCapture(self, dis = True):
        self.detail.btn_start.setDisabled(dis)
        self.control.sb_int.setDisabled(dis)
        self.control.cb_side.setDisabled(dis)

    def update_data(self, data):
        keys = data.keys()
        for i in keys:
            self.lat_select_R.update_data(key=i, value=data[i])
        if 'lat_A' in data or 'lat_B' in data:
            self.AB = [[data['lat_A'], data['lat_B']], [data,data]]
        
    def update_markers(self, k ):
        mark = self.grph_R.marks
        data = self.AB[0][0]
        self.grph_R.change_keys(key=k, value=data)



def ABR_Curve(nHL = 80, peak_I=1.6, peak_III=3.7, peak_v=5.6, amp_V = 0.8, VrelI = True):

    peak_I = 1.6
    peak_III = 3.7
    peak_V = 5.6
    amp_V = 0.8
    VrelI = True

    if VrelI:
        var = random.uniform(0,0.2)
        amp_I = amp_V / 3
        amp_I = amp_I + var
    else:
        var = random.uniform(0,0.2)
        amp_I = amp_V / 1.5
        amp_I = amp_I 
       

    curve_cm = (0.6, 0.15)
    curve_cmp = (0.7, -0.05)

    curve_I = (peak_I,amp_I/2)
    curve_Ip = (curve_I[0]+.5,-(amp_I/2))

    curve_II = (curve_I[0] + 1, curve_Ip[1]+0.1)
    curve_IIp = (curve_II[0]+.3,curve_II[1]-.02)

    curve_III = (peak_III,0.3)
    curve_IIIp = (curve_III[0]+.9,curve_III[1]-0.3)

    VrefIII = (random.uniform(-.4,.7)) + curve_III[1]
    curve_V = (peak_V,VrefIII)

    sn10refV = curve_V[1] - amp_V
    sn10 = (curve_V[0]+1,sn10refV)

    curve_IV = (peak_V-.5, curve_V[1]-.05)
    curve_IVp = (curve_IV[0]+.25, curve_IV[1]-.05)

    curve_VI = (sn10[0]+1.5, curve_V[1]-.3)
    curve_VIp = (curve_VI[0]+1.5, curve_VI[1]-.3)
    curve_VII = (curve_VIp[0]+1.5, curve_VIp[1]+.6)


    points = np.array([
            [0,0],

            [curve_cm[0]-.2, 0],
            [curve_cm[0], curve_cm[1]],
            [curve_cmp[0],curve_cmp[1]],

            [curve_I[0],curve_I[1]],
            [curve_Ip[0],curve_Ip[1]],

            [curve_II[0],curve_II[1]],
            [curve_IIp[0],curve_IIp[1]],
        
            [curve_III[0],curve_III[1]],
            [curve_IIIp[0],curve_IIIp[1]],
        
            [curve_IV[0], curve_IV[1]],
            [curve_IVp[0], curve_IVp[1]],
            
            [curve_V[0],curve_V[1]],
            [sn10[0],sn10[1]],

            [curve_VI[0],curve_VI[1]],
            [curve_VIp[0],curve_VIp[1]],
            [curve_VII[0],curve_VII[1]],
            [12,0]        
    ])
    Bezi = bz.Bezier()
    path = Bezi.evaluate_bezier(points, 20)

    # extract x & y coordinates of points
    x, y = points[:,0], points[:,1]
    px, py = path[:,0], path[:,1]

    y_noise = np.random.normal(0, .01, py.shape)
    y_new = py + y_noise

    return px, y_new

px, y_new = ABR_Curve()

if __name__ == '__main__':
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext
    window = MainWindow()
    window.show()
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)