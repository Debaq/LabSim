# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - Zmeter                       #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer
from datetime import datetime
import numpy as np

from UI.Ui_Z_control import Ui_Z_control
from lib.ZZscreen import ZZscreen
from lib.h_z import changeSide, changeSideText, sideText, printer, date_time
from lib.z_generator import Z_225
from lib.helpers import Storage


class ZControl(QWidget, Ui_Z_control):
    def __init__(self,):
        QWidget.__init__(self)
        self.setupUi(self)
        self.Z = ZZscreen()
        self.Screen_Layout.addWidget(self.Z)

        # BUTTONS
        self.btn_side.clicked.connect(self.side_change)
        self.btn_1.clicked.connect(lambda: self.move(-1))
        self.btn_2.clicked.connect(lambda: self.move(1))
        self.btn_stimulus.clicked.connect(self.timerAnimation)
        self.btn_print.clicked.connect(lambda: printer(self,  self.Z.winId()))

        # TIMERS
        self.time_ch0 = QTimer(self)
        self.time_ch0.timeout.connect(self.animation)
        self.time_ch1 = QTimer(self)
        self.time_ch1.timeout.connect(self.timeStamp)
        self.time_ch1.start(3000)

        # GLOBAL VARIABLE
        self.frame = Storage(3)
        self.frame.set(0, list())
        self.frame.set(1, list())

        self.side = 0
        self.test = 'Z_'
        self.store_data = [Storage(2), Storage(2)]
        self.new = [True, True]

    def laSuper(self, data):
        self.data = data
        if data['sector'] == 'Z_OI' or data['sector'] == 'Z_OD':
            self.preCharger()
        else:
            pass
            # otro examen que no es Z puede ser reflejos y deterioro

    def preCharger(self):
        side = sideText(self.data['sector'])
        if self.store_data[side].isNull(0):
            zGerger = self.data[self.data['sector']]
            vol = self.data['volume'][side]
            result = Z_225(letter=zGerger, vol=vol).getDataSet()
            self.store_data[side].set(0, result)
            self.new[side] = True

        else:
            val = self.store_data[side].get(0)
            try:
                c = float(val[2])
                p = int(val[3])
                vol = float(val[5])
            except:
                c = val[2]
                p = val[3]
                vol = val[5]
            result = Z_225(manual=True, c=c, p=p, vol=vol).getDataSet()
            self.store_data[side].set(0, result)
            self.new[side] = False

    def side_change(self):
        side_text = self.Z.get_side()
        if side_text == 'OD':
            self.Z.set_side('OI')
        else:
            self.Z.set_side('OD')
        self.refresh()
        # self.change_screen(self.screen_list[self.last_screen])

    def refresh(self):
        side_text = self.Z.get_side()
        side_text = self.test+side_text
        side = sideText(side_text)

        if self.new[side]:
            self.frame.clean()
            self.frame.set(2, 0)
            self.Z.clearData()
            self.Z.clear_lbl()

        else:
            memory = self.store_data[side].get(0)
            self.Z.update_graph(memory[0], memory[1])
            self.Z.lbl_p.setText(memory[3])
            self.Z.lbl_c.setText(memory[2])
            self.Z.lbl_v.setText(memory[5])
            self.Z.lbl_g.setText(memory[4])

    def timerAnimation(self):
        if self.time_ch0.isActive():
            self.time_ch0.stop()
        else:
            self.frame.clean()
            self.frame.set(2, 0)
            self.time_ch0.start(75)

    def animation(self):
        stop = False
        side_text = self.Z.get_side()
        side_text = self.test+side_text
        side = sideText(side_text)
        memory = self.store_data[side].get(0)
        try:
            memory_len = len(memory[0])
        except:
            stop = True
        if not stop:
            idx = self.frame.get(2)

            self.frame.agrege(0, memory[0][idx])
            self.frame.agrege(1, memory[1][idx])
            self.frame.set(2, idx+1)

            if memory_len <= idx+1:
                self.time_ch0.stop()
                self.new[side] = False
                self.Z.lbl_p.setText(memory[3])
                self.Z.lbl_c.setText(memory[2])
                self.Z.lbl_v.setText(memory[5])
                self.Z.lbl_g.setText(memory[4])

            x = self.frame.get(0)
            y = self.frame.get(1)

            self.Z.update_graph(x, y)
        else:
            self.time_ch0.stop()

    def move(self, pos):
        pos = self.Z.move_mark(pos)
        try:
            side_text = self.Z.get_side()
            side_text = self.test+side_text
            side = sideText(side_text)
            memory = self.store_data[side].get(0)
            self.Z.lbl_p.setText(str(pos))
            c = self.Z.find_nearest(memory[0], pos, memory[1])
            c = round(c, 2)
            self.Z.lbl_c.setText(str(c))
        except:
            pass

    def timeStamp(self):
        time = date_time()
        self.Z.lbl_timeDate.setText(time)


if __name__ == "__main__":
    pass
