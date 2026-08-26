# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - Zmeter                       #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer
from datetime import datetime
import numpy as np

from UI.Ui_Z_control import Ui_Z_control
from lib.ZZscreen import ZZscreen
from lib.ZRscreen import ZRscreen
from lib.ZDscreen import ZDscreen
from lib.ZETFscreen import ZETFscreen
from lib.h_z import changeSide, changeSideText, sideText, printer, date_time
from lib.z_generator import Z_225
from lib.helpers import Storage

print("Z cargado")

class ZControl(QWidget, Ui_Z_control):
    def __init__(self,):
        #QWidget.__init__(self)
        super(ZControl, self).__init__()
        self.setupUi(self)
        self.Z = ZZscreen()
        self.Z_reflex = ZRscreen()
        self.Z_decay = ZDscreen()
        self.Z_etf = ZETFscreen()

        self.screens = [self.Z, self.Z_reflex, self.Z_decay, self.Z_etf]
        self.current_screen = self.Z
        for screen in self.screens:
            self.Screen_Layout.addWidget(screen)
            screen.setVisible(screen is self.Z)

        # BUTTONS
        self.btn_side.clicked.connect(self.side_change)
        self.btn_1.clicked.connect(lambda: self.move(-1))
        self.btn_2.clicked.connect(lambda: self.move(1))
        self.btn_stimulus.clicked.connect(self.timerAnimation)
        self.btn_print.clicked.connect(lambda: printer(self,  self.Z.winId()))

        self.btn_toneDecay.setEnabled(True)
        self.btn_tymp.clicked.connect(lambda: self.show_screen(self.Z))
        self.btn_reflex_test.clicked.connect(lambda: self.show_screen(self.Z_reflex))
        self.btn_toneDecay.clicked.connect(lambda: self.show_screen(self.Z_decay))
        self.btn_etf.clicked.connect(lambda: self.show_screen(self.Z_etf))

        self.reflex_mode = 'IPSI'
        self.btn_reflex.setEnabled(False)
        self.btn_reflex.clicked.connect(self.reflex_mode_change)

        self.leak = self.dial.value()
        self.dB = 85
        self.etf_pressure = 0
        self.reflex_pressure = 0
        self.dial.setEnabled(True)
        self.dial.valueChanged.connect(self.dial_change)

        self.btn_up.setEnabled(False)
        self.btn_up.clicked.connect(lambda: self.updown_change(10))
        self.btn_down.setEnabled(False)
        self.btn_down.clicked.connect(lambda: self.updown_change(-10))

        self.btn_3.setEnabled(True)
        self.btn_3.clicked.connect(self.direction_change)
        self.btn_5.setEnabled(True)
        self.btn_5.clicked.connect(lambda: self.window_change('neg'))
        self.btn_6.setEnabled(True)
        self.btn_6.clicked.connect(lambda: self.window_change('pos'))
        self.btn_4.setEnabled(True)
        self.btn_4.clicked.connect(self.height_change)

        # DIRECTION / WINDOW STATE
        self.direction = 'pos->neg'
        self.window_neg_values = [-100, -200, -400, -600]
        self.window_pos_values = [100, 200, 400, 600]
        self.window_neg_idx = 2
        self.window_pos_idx = 1
        self.Z.set_window(self.window_neg_values[self.window_neg_idx], self.window_pos_values[self.window_pos_idx])

        self.height_values = [1, 2, 5, 8]
        self.height_idx = 1
        self.Z.set_height(self.height_values[self.height_idx])

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

    def la_super(self, data):
        if data is None:
            return
        self.data = data
        self.preCharger()
        if data['sector'] == 'Z_OI' or data['sector'] == 'Z_OD':
            self.preCharger()
        else:
            pass
            # otro examen que no es Z puede ser reflejos y deterioro

    def preCharger(self):
        side = sideText(f"Z_{self.Z.get_side()}")
        print(self.data)
        win_neg = self.window_neg_values[self.window_neg_idx]
        win_pos = self.window_pos_values[self.window_pos_idx]
        if self.store_data[side].is_null(0):
            print(f"side : {side}")
            zGerger = self.data[f"Z_{self.Z.get_side()}"]
            vol = self.data['volume'][side]
            result = Z_225(letter=zGerger, vol=vol, win_neg=win_neg, win_pos=win_pos).getDataSet()
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
            result = Z_225(manual=True, c=c, p=p, vol=vol, win_neg=win_neg, win_pos=win_pos).getDataSet()
            self.store_data[side].set(0, result)
            self.new[side] = False

    def side_change(self):
        side_text = self.Z.get_side()
        if side_text == 'OD':
            self.Z.set_side('OI')
        else:
            self.Z.set_side('OD')
        self.refresh()
        self.preCharger()
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
            try:
                self.Z.set_gradient_box(float(memory[3]), float(memory[2]))
            except (ValueError, TypeError):
                self.Z.set_gradient_box(None, None)

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
            data_idx = memory_len - 1 - idx if self.direction == 'neg->pos' else idx

            self.frame.agrege(0, memory[0][data_idx])
            self.frame.agrege(1, memory[1][data_idx])
            self.frame.set(2, idx+1)

            if memory_len <= idx+1:
                self.time_ch0.stop()
                self.new[side] = False
                self.Z.lbl_p.setText(memory[3])
                self.Z.lbl_c.setText(memory[2])
                self.Z.lbl_v.setText(memory[5])
                self.Z.lbl_g.setText(memory[4])
                try:
                    self.Z.set_gradient_box(float(memory[3]), float(memory[2]))
                except (ValueError, TypeError):
                    self.Z.set_gradient_box(None, None)

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
            self.Z.lbl_p.setText(str(round(pos)))
            c = self.Z.find_nearest(memory[0], pos, memory[1])
            c = round(c, 2)
            self.Z.lbl_c.setText(str(c))

            if c > 0:
                y_minus = self.Z.find_nearest(memory[0], pos - 50, memory[1])
                y_plus = self.Z.find_nearest(memory[0], pos + 50, memory[1])
                gradient = round(min(max((y_minus + y_plus) / (2 * c), 0.0), 1.0), 2)
            else:
                gradient = 0.0
            self.Z.lbl_g.setText(str(gradient))
            self.Z.set_gradient_box(pos, c)
        except:
            pass

    def direction_change(self):
        if self.direction == 'pos->neg':
            self.direction = 'neg->pos'
            self.Z.set_direction('neg -> pos')
        else:
            self.direction = 'pos->neg'
            self.Z.set_direction('pos -> neg')

    def height_change(self):
        self.height_idx = (self.height_idx + 1) % len(self.height_values)
        self.Z.set_height(self.height_values[self.height_idx])

    def window_change(self, side):
        if side == 'neg':
            self.window_neg_idx = (self.window_neg_idx + 1) % len(self.window_neg_values)
        else:
            self.window_pos_idx = (self.window_pos_idx + 1) % len(self.window_pos_values)
        self.Z.set_window(self.window_neg_values[self.window_neg_idx], self.window_pos_values[self.window_pos_idx])

    def show_screen(self, screen):
        for s in self.screens:
            s.setVisible(s is screen)
        self.current_screen = screen
        self.btn_reflex.setEnabled(screen is self.Z_reflex)
        self.btn_up.setEnabled(screen in (self.Z_reflex, self.Z_decay))
        self.btn_down.setEnabled(screen in (self.Z_reflex, self.Z_decay))

        self.dial.blockSignals(True)
        if screen is self.Z:
            self.dial.setMinimum(1)
            self.dial.setMaximum(20)
            self.dial.setValue(self.leak)
        elif screen in (self.Z_reflex, self.Z_decay):
            self.dial.setMinimum(0)
            self.dial.setMaximum(120)
            self.dial.setValue(self.dB)
        elif screen is self.Z_etf:
            self.dial.setMinimum(-400)
            self.dial.setMaximum(200)
            self.dial.setValue(self.etf_pressure)
        self.dial.blockSignals(False)

    def dial_change(self, value):
        if self.current_screen is self.Z:
            self.leak_change(value)
        elif self.current_screen in (self.Z_reflex, self.Z_decay):
            self.dB = value
            self.Z_reflex.set_intensity(self.dB)
            self.Z_decay.set_intensity(self.dB)
        elif self.current_screen is self.Z_etf:
            self.etf_pressure = value
            self.Z_etf.set_pressure(self.etf_pressure)

    def reflex_mode_change(self):
        self.reflex_mode = 'CONTRA' if self.reflex_mode == 'IPSI' else 'IPSI'
        self.Z_reflex.set_mode(self.reflex_mode)

    def leak_change(self, value):
        self.leak = value
        ratio = (value - self.dial.minimum()) / (self.dial.maximum() - self.dial.minimum())
        r = int(152 + ratio * 100)
        g = int(152 - ratio * 100)
        b = int(152 - ratio * 100)
        self.label.setText(str(value))
        self.label.setStyleSheet(f"background-color: rgb({r}, {g}, {b});")

    def updown_change(self, delta):
        if self.current_screen in (self.Z_reflex, self.Z_decay):
            self.reflex_pressure = min(max(self.reflex_pressure + delta, -400), 200)
            self.Z_reflex.set_pressure(self.reflex_pressure)
            self.Z_decay.set_pressure(self.reflex_pressure)

    def timeStamp(self):
        time = date_time()
        self.Z.lbl_timeDate.setText(time)


if __name__ == "__main__":
    pass
