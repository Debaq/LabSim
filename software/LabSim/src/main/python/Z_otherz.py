# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - Zmeter                       #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QShortcut, QWidget, QFileDialog
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QScreen
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from datetime import datetime


from UI.Ui_Z_control import Ui_Z_control
from UI.Ui_Z_screen_z import Ui_Z_zscreen
from UI.Ui_Z_screen_r import Ui_Z_rscreen
from UI.Ui_Z_screen_d import Ui_Z_dscreen

import numpy as np
import random
import pyqtgraph as pg
import bezier


class ZRscreen(QWidget, Ui_Z_rscreen):
    def __init__(self):
        # Inicialización de la ventana y propiedades
        QWidget.__init__(self)
        self.setupUi(self)
        color = pg.mkColor(85,170,255,255)
        pg.setConfigOption('background', color)
        pg.setConfigOption('foreground', 'w')
        pw1 = pg.PlotWidget(name='Plot1', background='default')
        pw1.setRange(yRange = (-150, 150), xRange = (0, 2), disableAutoRange=True)
        pw1.showGrid(x=True, y=True)
        pw1.setMouseEnabled(x=False, y=False)
        pw1.setMenuEnabled(False)
        ax = pw1.getAxis('bottom')
        ay = pw1.getAxis('left')
        pw1.setLabel(axis='bottom', text='S')
        pw1.setLabel(axis='left', text='μl')
        ticksx = [ 2]
        ticksy = [-150,0, 150]
        ax.setTicks([[(v, str(v)) for v in ticksx ]])
        ay.setTicks([[(v, str(v)) for v in ticksy ]])
        self.graph.addWidget(pw1)

class ZDscreen(QWidget, Ui_Z_dscreen):
    def __init__(self):
        # Inicialización de la ventana y propiedades
        QWidget.__init__(self)
        self.setupUi(self)
        color = pg.mkColor(85,170,255,255)
        pg.setConfigOption('background', color)
        pg.setConfigOption('foreground', 'w')
        pw1 = pg.PlotWidget(name='Plot1', background='default')
        pw1.setRange(yRange = (-225, 225), xRange = (0, 12), disableAutoRange=True)
        pw1.showGrid(x=True, y=True)
        pw1.setMouseEnabled(x=False, y=False)
        pw1.setMenuEnabled(False)
        ax = pw1.getAxis('bottom')
        ay = pw1.getAxis('left')
        pw1.setLabel(axis='bottom', text='S')
        pw1.setLabel(axis='left', text='μl')
        ticksx = [ 12]
        ticksy = [-225,0, 225]
        ax.setTicks([[(v, str(v)) for v in ticksx ]])
        ay.setTicks([[(v, str(v)) for v in ticksy ]])
        self.graph.addWidget(pw1)

class ZZscreen(QWidget, Ui_Z_zscreen):
    def __init__(self):
        # Inicialización de la ventana y propiedades
        QWidget.__init__(self)
        self.setupUi(self)
        self.create_graph()
    
    def create_graph(self, clear=False):
        if clear:
            self.pw1.clear()
            self.ploty.clear()
            self.ploty.setData()

        color = pg.mkColor(85,170,255,255)
        pg.setConfigOption('background', color)
        pg.setConfigOption('foreground', 'w')
        self.pw1 = pg.PlotWidget(name='Plot1', background='default')
        self.pw1.setXRange(-405,205)
        self.pw1.setYRange(0,1.8)
        self.pw1.setLabel('left', '', units ='ml')
        self.pw1.setLabel('bottom', '', units ='daPa')
        self.pw1.setMouseEnabled(x=False, y=False)
        self.pw1.setMenuEnabled(False)
        pen1 = pg.mkPen('w', width=1, style=Qt.DashLine)          ## Make a dashed yellow line 2px wide
        self.inf1 = pg.InfiniteLine(movable=False, angle=90, pen=pen1)
        self.pw1.addItem(self.inf1)
        self.ploty = self.pw1.plot()
        self.graph.addWidget(self.pw1)
    
    def update_graph(self, data):
        x = data[1]
        y = data[2]
        #print(len(x))
        idx_y = data[2].index(max(y))
        pos_max = data[1][idx_y]
        self.inf1.setPos([pos_max,2])
        #pen_color = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
        #pen_idx = random.randint(0,7)
        self.ploty.setData(x, y, pen='w')

    def move_mark(self, pos):
        pos_mark = self.inf1.value() + pos*2
        self.inf1.setPos([pos_mark,2])
    
    def set_side(self, side):
        self.lbl_side.setText(side)
        
    def get_side(self):
        return self.lbl_side.text()

class ZControl(QWidget, Ui_Z_control):
    def __init__(self,):
        QWidget.__init__(self)
        # Inicialización de la ventana y propiedades
        self.data_side = [Z_225_result(),  Z_225_result()]
        self.prevData = [[[None, None, None],[]],[[None,None,None],[]]]
        #self.laSuper(data)
        self.setupUi(self)
        self.Z = ZZscreen()
        self.R = ZRscreen()
        self.D = ZDscreen()
        self.date_time()
        self.Screen_Layout.addWidget(self.Z)
        self.btn_reflex.clicked.connect(lambda:self.change_screen("Reflex"))
        self.btn_226.clicked.connect(lambda:self.change_screen("Z-226"))
        self.btn_1000.clicked.connect(lambda:self.change_screen("Z-1000"))
        self.btn_1000.setDisabled(True)
        self.btn_toneDecay.clicked.connect(lambda:self.change_screen("tone-decay"))
        self.btn_stimulus.clicked.connect(self.timer_init)
        self.btn_1.clicked.connect(lambda:self.move(-1))
        self.btn_2.clicked.connect(lambda:self.move(1))
        self.btn_side.clicked.connect(self.side_change)
        self.btn_print.clicked.connect(self.print)
        self.side_lbl = ["OD","OI"]
        self.side = 1
        self.side_sonda = ""
        self.screen_list = ["Z-226","Reflex","tone-decay"]
        self.last_screen = 0
        self.time_ch0 = QTimer(self)
        self.time_ch0.timeout.connect(self.timer_print)
        self.time_ch1 = QTimer(self)
        self.time_ch1.timeout.connect(self.date_time)
        self.time_ch1.start(3000)
        self.memory = [-1, [],[]]
        self.side_change()

    def laSuper(self, data):
        print("se cambio paciente")
        self.DATAS = data
        state = data['sector']
        if state == 'Z_OI' or state == 'Z_OD':
            if state == 'Z_OD' :                  
                self.side_sonda = 0
                contra = 1
                side_text = 'Z_OD'
            else:
                self.side_sonda = 1
                contra = 0
                side_text = 'Z_OI'
            self.preCharger(self.side_sonda, data, side_text, contra)   
        else:
            self.side_sonda = 2
        
    def preCharger(self, side, data, text, contra):
        if self.prevData[side][0][0] == None:
            print("no hay nada")
            print(data[text])

            self.data_side[side].create_auto(data[text], vol = data['volume'][side])
            self.prevData[side][0][0] = self.data_side[side].compliance
            self.prevData[side][0][1] = self.data_side[side].presure
            self.prevData[side][0][2] = self.data_side[side].volume
            self.data_set = self.data_side[side].getDataSet()
            print(self.data_set)
        else:
            print("hay algo")
            c = self.prevData[side][0][0]
            p = self.prevData[side][0][1]
            vol = self.prevData[side][0][2]
            self.data_side[side].create_manual(c=c, p=p, vol=vol)
            self.data_set = self.data_side[side].getDataSet()
        #if self.prevData[contre][0][0] != None:
        #    self.data_side[contra].zeros()

    def print(self):
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow( self.Z.winId() )
        now = datetime.now()
        current_time = now.strftime("%d-%m-%y_%H_%M_%S")        
        file = str(QFileDialog.getExistingDirectory(self, "Seleccionar destino"))
        name = file + '/'+ current_time + '.jpg'
        screenshot.save(name, 'jpg')
    
    def date_time(self):
        now = datetime.now()
        current_time = now.strftime("%d/%m/%y %H:%M:%S")
        self.Z.lbl_timeDate.setText(current_time)
        
    def side_change(self):
        side_text = self.Z.get_side()
        if side_text == 'OD':
            side = 1            
        else:
            side = 0
        self.Z.set_side(self.side_lbl[side])
        self.refresh(side)
        #self.change_screen(self.screen_list[self.last_screen])

    def refresh(self, side):
        print(side)
        if side == 1:
            contra = 0
        else:
            contra = 1
        
        if self.side_sonda != side:
            self.data_set = self.data_side[side].zeros()
        else:
            self.data_set = self.data_side[self.side].getDataSet()


    def move(self, pos):
        self.Z.move_mark(pos)

    def change_screen(self, screen_name):
        self.resetLayout(self.Screen_Layout)
        if screen_name == "Z-226":
            self.Z.set_side(self.side_lbl[self.side])
            self.Screen_Layout.addWidget(self.Z)
            self.last_screen = 0
        elif screen_name == "Reflex":
            self.Screen_Layout.addWidget(self.R)
            self.last_screen = 1
        elif screen_name == "tone-decay":
            self.Screen_Layout.addWidget(self.D)
            self.last_screen = 2

    def timer_init(self):
        print(self.data_set)
        if self.time_ch0.isActive():
            self.time_ch0.stop()
        else:
            if self.data_set[3] == 'N/D':
                
                self.time_ch0.start(5)
            else:
                self.time_ch0.start(75)
            


    def timer_print(self):
        #print(self.memory)
        if self.memory[0] == -1:
            #self.resetLayout(self.Z.graph)
            #self.Z.create_graph(clear=True)
            self.memory[0] = 0
            self.memory[1] = []
            self.memory[2] = []
            i = 0
        else:
            i = self.memory[0] + 1

        self.memory[0] = i
        datalen = len(self.data_set[0]) - 1

        if i > datalen:
            self.time_ch0.stop()
            self.Z.lbl_p.setText(self.data_set[2])
            self.Z.lbl_c.setText(self.data_set[3])
            self.Z.lbl_v.setText(self.data_set[5])
            self.Z.lbl_g.setText(self.data_set[4])

            self.memory[0] = -1
        else:
            self.memory[1].append(self.data_set[0][i])
            self.memory[2].append(self.data_set[1][i])
            self.Z.update_graph(self.memory)
            

    def resetLayout(self, layout):
        for i in reversed(range(layout.count())): 
            widgetToRemove = layout.itemAt(i).widget()
            # remove it from the layout list
            layout.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)  


class Z_225_result():
    def __init__(self):
        pass
   
    def create_manual(self, c, p, g = 1, pmax = 200, num_pts=20, vol=1.8, unseal=False):
        self.compliance = round(c,2)
        self.presure = round(p,2)
        self.gradient = round(g,2)
        self.volume = round(vol,2)
        self.presure_max = pmax
        self.num_pts=num_pts
        if unseal:
            print(self.volume)
            self.zeros(unseal=unseal)
        else:
            self.curve_z()
    
    def create_auto(self, letter, vol=1.8):
        if letter == 'A':
            c = random.uniform(0.3, 1.6)
            p = random.randint(-100, 100)
            to = True
        
        if letter == 'As':
            c = random.uniform(0.01, 0.3)
            p = random.randint(-100, 100)
            to = True
        
        if letter =='C':
            c = random.uniform(0.3, 1.6)
            p = random.randint(-400, -100)
            to = True
        if letter =='B':
            c = random.uniform(0.0, 0.003)
            p = random.randint(-600, -200)
            to = False
        if letter =='N':
            c = 0
            p = 0
            to = False

        if to:
            self.create_manual(c, p, vol=vol)
        else: 
            self.create_manual(c, p, g = 0, vol=vol, unseal=True)


    def curve_z(self):
        c = self.compliance
        p = self.presure
        g = self.gradient
        vol = self.volume
        pmax = self.presure_max
        num_pts = self.num_pts
        
        side_neg = np.asfortranarray([
            [-pmax+p, p, p],
            [0.0, g , c],])
        side_pos = np.asfortranarray([
            [p, p, pmax+p],
            [c, g , 0],])
        
        curve1 = bezier.Curve(side_neg, degree=2)
        curve2 = bezier.Curve(side_pos, degree=2)
        s_vals = np.linspace(0.0, 1.0, num_pts)
        point1 = curve1.evaluate_multi(s_vals)
        point2 = curve2.evaluate_multi(s_vals)
        flip_point2_x = np.flip(point2[0,:])
        flip_point2_y = np.flip(point2[1,:])

        
        for idx, val in enumerate(point1[0,:]):
            dif = val - flip_point2_x[idx]
            if abs(dif)<=100:
                hp = idx
                break
            
        hp_heigth = c - point1[1,:][hp]
        hp_widht = flip_point2_x[hp] - point1[0,:][hp]

        hp_size = [hp_heigth, hp_widht]
        hp = [point1[0,:][hp],point1[1,:][hp]]
        x = np.append(point1[0,:],point2[0,:])
        y = np.append(point1[1,:],point2[1,:])

        x_neg = np.arange(-400, min(x)-10, 10)
        x_pos = np.arange(400, max(x)+10, 10)

        y_neg = np.zeros(len(x_neg))
        y_pos = np.zeros(len(x_pos))
        
        y = np.append(y_neg,y)
        y = np.append(y,y_pos)
        x = np.append(x_neg, x)
        self.x = np.append(x, x_pos)        
        y_noise = np.random.normal(0, .03, y.shape)
        self.y = y + y_noise
    
    def zeros(self, unseal=False):
        self.x = np.zeros(40)
        self.y = np.zeros(40)
        if unseal:
            self.presure = self.presure
        else:
            self.presure = 'N/D'
        self.compliance = 'N/D'
        self.gradient = 'N/D'
        self.volume = 'N/D'
        self.getDataSet()        
        #data_set = [x[::-1],y[::-1], presure, compliance, gradient, volume]
        #return data_set
    
    def getDataSet(self):
        c = str(self.compliance)
        p = str(self.presure)
        g = str(self.gradient)
        vol = str(self.volume)
        dataset = [self.x[::-1],self.y[::-1], p, c, g, vol]
        return dataset
        
        

if __name__ == "__main__":
    pass