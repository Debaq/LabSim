# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - Zmeter                       #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
from PySide6.QtWidgets import QWidget, QAbstractSlider
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import QTimer, Qt
from datetime import datetime
import numpy as np

from impedanciometria.UI.Ui_Z_control import Ui_Z_control
from backend.log_queue import get_log_queue
from impedanciometria.ZZscreen import ZZscreen
from impedanciometria.ZRscreen import ZRscreen
from impedanciometria.ZDscreen import ZDscreen
from impedanciometria.ZETFscreen import ZETFscreen
from impedanciometria.h_z import changeSide, changeSideText, sideText, printer, date_time
from impedanciometria.z_generator import Z_225, Reflex_curve, map_letter_for_probe
from core.helpers import Storage

print("Z cargado")

class ZControl(QWidget, Ui_Z_control):
    def __init__(self,):
        #QWidget.__init__(self)
        super(ZControl, self).__init__()
        self.log_queue = get_log_queue()
        self.data = None
        self.appointment_id = None
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
        self.probe_freq = '226'
        self.btn_226.clicked.connect(lambda: self.set_probe_freq('226'))
        self.btn_1000.clicked.connect(lambda: self.set_probe_freq('1000'))

        self.btn_side.clicked.connect(self.side_change)
        self.btn_1.clicked.connect(self.btn1_click)
        self.btn_2.clicked.connect(self.btn2_click)
        self.btn_stimulus.clicked.connect(self.stimulus_click)
        self.btn_print.clicked.connect(lambda: printer(self,  self.Z.winId()))

        self.btn_toneDecay.setEnabled(True)
        self.btn_tymp.clicked.connect(lambda: self.show_screen(self.Z))
        self.btn_reflex_test.clicked.connect(lambda: self.show_screen(self.Z_reflex))
        self.btn_toneDecay.clicked.connect(lambda: self.show_screen(self.Z_decay))
        self.btn_etf.clicked.connect(lambda: self.show_screen(self.Z_etf))

        self.reflex_mode = 'IPSI'
        self.btn_reflex.setEnabled(False)
        self.btn_reflex.clicked.connect(self.reflex_mode_change)
        self.Z_reflex.start_clicked.connect(self.stimulus_click)
        self.Z_reflex.ipsi_clicked.connect(lambda: self.set_reflex_mode('IPSI'))
        self.Z_reflex.contra_clicked.connect(lambda: self.set_reflex_mode('CONTRA'))

        self.reflex_freq_labels = ['500', '1000', '2000', '4000']
        self.reflex_freq_idx = 0
        self.Z_reflex.set_freq(self.reflex_freq_labels[self.reflex_freq_idx])
        self.Z_reflex.set_nbn_enabled(False)

        # Resultados que el ALUMNO va registrando (dB al que probó y obtuvo
        # respuesta), no el umbral real del caso: el simulador nunca revela
        # el umbral verdadero, así el alumno puede equivocarse igual que en
        # un examen real.
        self.reflex_results = {
            0: {'IPSI': [None] * 4, 'CONTRA': [None] * 5},
            1: {'IPSI': [None] * 4, 'CONTRA': [None] * 5},
        }
        self.refresh_reflex_table()

        self.leak = self.dial.value()
        self.dB = 85
        self.etf_pressure = 0
        self.reflex_pressure = 0
        self.dial.setEnabled(True)
        self.dial.setTracking(True)
        self.dial.setSingleStep(5)
        self.dial.valueChanged.connect(self.dial_change)

        self.btn_up.setEnabled(False)
        self.btn_up.clicked.connect(lambda: self.updown_change(10))
        self.btn_down.setEnabled(False)
        self.btn_down.clicked.connect(lambda: self.updown_change(-10))

        # SHORTCUTS
        self.shortcut_dial_down = QShortcut(QKeySequence(Qt.Key_W), self)
        self.shortcut_dial_down.setAutoRepeat(False)
        self.shortcut_dial_down.activated.connect(
            lambda: self.dial.triggerAction(QAbstractSlider.SliderSingleStepSub))

        self.shortcut_dial_up = QShortcut(QKeySequence(Qt.Key_S), self)
        self.shortcut_dial_up.setAutoRepeat(False)
        self.shortcut_dial_up.activated.connect(
            lambda: self.dial.triggerAction(QAbstractSlider.SliderSingleStepAdd))

        self.shortcut_stimulus = QShortcut(QKeySequence(Qt.Key_V), self)
        self.shortcut_stimulus.setAutoRepeat(False)
        self.shortcut_stimulus.activated.connect(self.btn_stimulus.click)

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
        self.time_reflex = QTimer(self)
        self.time_reflex.timeout.connect(self.reflex_animate)

        # GLOBAL VARIABLE
        self.frame = Storage(3)
        self.frame.set(0, list())
        self.frame.set(1, list())

        self.side = 0
        self.test = 'Z_'
        self.store_data = [Storage(2), Storage(2)]
        self.new = [True, True]

    def _log(self, action, **payload):
        """Encola una interacción del alumno en el impedanciómetro (ver
        lib/backend/log_queue.py): escritura local, se sube al backend
        en lotes -- no bloquea la UI."""
        case_id = self.data.get("id") if self.data else None
        if case_id is not None:
            payload.setdefault("case_id", case_id)
        payload.setdefault("appointment_id", getattr(self, "appointment_id", None))
        payload.setdefault("con_paciente", case_id is not None)
        self.log_queue.push(action, payload)

    def la_super(self, data, appointment_id=None):
        self.appointment_id = appointment_id
        if data is None:
            self.data = None  # limpia el caso anterior: sin esto el log seguía marcando al paciente ya cerrado
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
            if self.data is not None:
                seed_key = (self.data.get('id'), self.Z.get_side(), self.probe_freq)
                zGerger = self.data[f"Z_{self.Z.get_side()}"]
                zGerger = map_letter_for_probe(zGerger, self.probe_freq, seed_key=seed_key)
                vol = self.data['volume'][side]
            else:
                seed_key = None
                zGerger = "N"
                vol = 1.8
            result = Z_225(letter=zGerger, vol=vol, win_neg=win_neg, win_pos=win_pos, seed_key=seed_key).getDataSet()
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

        self.update_reflex_volume()

    def set_probe_freq(self, freq):
        if freq == self.probe_freq:
            return
        self._log("z_probe_freq_change", freq=freq)
        self.probe_freq = freq
        self.Z.set_probe_freq(freq)
        self.store_data[0].clean()
        self.store_data[1].clean()
        self.new = [True, True]
        self.refresh()
        self.preCharger()

    def side_change(self):
        side_text = self.Z.get_side()
        self._log("z_side_change", side='OI' if side_text == 'OD' else 'OD')
        if side_text == 'OD':
            self.Z.set_side('OI')
        else:
            self.Z.set_side('OD')
        self.Z_reflex.set_side(self.Z.get_side())
        self.refresh()
        self.preCharger()
        self.Z_reflex.clear_response()
        self.refresh_reflex_table()
        self.update_reflex_volume()
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
        self._log("z_direction_change", direction=self.direction)

    def height_change(self):
        self.height_idx = (self.height_idx + 1) % len(self.height_values)
        self.Z.set_height(self.height_values[self.height_idx])
        self._log("z_height_change", height=self.height_values[self.height_idx])

    def window_change(self, side):
        if side == 'neg':
            self.window_neg_idx = (self.window_neg_idx + 1) % len(self.window_neg_values)
        else:
            self.window_pos_idx = (self.window_pos_idx + 1) % len(self.window_pos_values)
        self.Z.set_window(self.window_neg_values[self.window_neg_idx], self.window_pos_values[self.window_pos_idx])
        self._log(
            "z_window_change",
            side=side,
            window_neg=self.window_neg_values[self.window_neg_idx],
            window_pos=self.window_pos_values[self.window_pos_idx],
        )

    def show_screen(self, screen):
        screen_names = {self.Z: 'tymp', self.Z_reflex: 'reflex', self.Z_decay: 'decay', self.Z_etf: 'etf'}
        self._log("z_screen_change", screen=screen_names.get(screen, '?'))
        for s in self.screens:
            s.setVisible(s is screen)
        self.current_screen = screen
        if screen is self.Z_reflex:
            self.Z_reflex.set_side(self.Z.get_side())
            self.Z_reflex.clear_response()
            self.refresh_reflex_table()
            self.update_reflex_volume()
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
            self._log("z_dial_change", screen='tymp', leak=value)
            self.leak_change(value)
        elif self.current_screen in (self.Z_reflex, self.Z_decay):
            value = round(value / 5) * 5
            if value != self.dial.value():
                self.dial.blockSignals(True)
                self.dial.setValue(value)
                self.dial.blockSignals(False)
            self._log("z_dial_change", screen='reflex' if self.current_screen is self.Z_reflex else 'decay', dB=value)
            self.dB = value
            self.Z_reflex.set_intensity(self.dB)
            self.Z_decay.set_intensity(self.dB)
        elif self.current_screen is self.Z_etf:
            self._log("z_dial_change", screen='etf', pressure=value)
            self.etf_pressure = value
            self.Z_etf.set_pressure(self.etf_pressure)

    def reflex_mode_change(self):
        self.set_reflex_mode('CONTRA' if self.reflex_mode == 'IPSI' else 'IPSI')

    def set_reflex_mode(self, mode):
        if mode == self.reflex_mode:
            return
        self._log("z_reflex_mode_change", mode=mode)
        self.reflex_mode = mode
        freqs = self.reflex_freqs_for_mode()
        if self.reflex_freq_idx >= len(freqs):
            self.reflex_freq_idx = len(freqs) - 1
        self.Z_reflex.set_mode(self.reflex_mode)
        self.Z_reflex.set_freq(freqs[self.reflex_freq_idx])
        self.Z_reflex.set_nbn_enabled(self.reflex_mode == 'CONTRA')
        self.Z_reflex.clear_response()
        self.refresh_reflex_table()

    def reflex_freqs_for_mode(self):
        if self.reflex_mode == 'CONTRA':
            return self.reflex_freq_labels + ['NBN']
        return self.reflex_freq_labels

    def btn1_click(self):
        if self.current_screen is self.Z_reflex:
            freqs = self.reflex_freqs_for_mode()
            self.reflex_freq_idx = (self.reflex_freq_idx + 1) % len(freqs)
            self._log("z_reflex_freq_change", freq=freqs[self.reflex_freq_idx])
            self.Z_reflex.set_freq(freqs[self.reflex_freq_idx])
            self.Z_reflex.clear_response()
        elif self.current_screen is self.Z:
            self._log("z_move_mark", direction=-1)
            self.move(-1)

    def btn2_click(self):
        if self.current_screen is self.Z:
            self._log("z_move_mark", direction=1)
            self.move(1)

    def stimulus_click(self):
        if self.current_screen is self.Z_reflex:
            freqs = self.reflex_freqs_for_mode()
            self._log(
                "z_stimulus_click",
                screen='reflex',
                side=self.Z.get_side(),
                mode=self.reflex_mode,
                freq=freqs[self.reflex_freq_idx],
                dB=self.dB,
            )
            self.reflex_stimulus()
        else:
            self._log("z_stimulus_click", screen='tymp', side=self.Z.get_side(), leak=self.leak)
            self.timerAnimation()

    def reflex_stimulus(self):
        if not hasattr(self, 'data') or self.data is None or 'Reflex' not in self.data:
            return
        side = self.Z.get_side()
        probe_idx = 0 if side == 'OD' else 1
        freqs = self.reflex_freqs_for_mode()
        freq = freqs[self.reflex_freq_idx]
        row_idx = ['500', '1000', '2000', '4000', 'NBN'].index(freq)

        reflex_data = self.data['Reflex'].get(self.reflex_mode.lower(), [])
        threshold = reflex_data[row_idx][probe_idx] if row_idx < len(reflex_data) else None

        present = threshold is not None and self.dB >= threshold
        x, y = Reflex_curve(present=present, dB=self.dB, threshold=threshold).getDataSet()

        self.time_reflex.stop()
        self.Z_reflex.clear_response()
        self.reflex_anim_data = (x, y)
        self.reflex_anim_idx = 1
        self.reflex_anim_ctx = (probe_idx, row_idx, present)
        # Ventana completa (2s de traza) se dibuja en 1s reales, como el equipo real.
        self.time_reflex.start(round(1000 / len(x)))

    def reflex_animate(self):
        x, y = self.reflex_anim_data
        idx = self.reflex_anim_idx
        self.Z_reflex.plot_response(x[:idx + 1], y[:idx + 1])
        self.reflex_anim_idx += 1

        if self.reflex_anim_idx >= len(x):
            self.time_reflex.stop()
            probe_idx, row_idx, present = self.reflex_anim_ctx
            if present:
                # Se guarda el dB al que el ALUMNO estimuló, nunca el umbral
                # real del caso: si prueba muy arriba del umbral verdadero,
                # ese (impreciso) es el valor que queda registrado.
                self.reflex_results[probe_idx][self.reflex_mode][row_idx] = self.dB
                self.refresh_reflex_table()

    def refresh_reflex_table(self):
        side = self.Z.get_side()
        probe_idx = 0 if side == 'OD' else 1
        values = self.reflex_results[probe_idx][self.reflex_mode]
        self.Z_reflex.set_results(values)

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
            self._log("z_pressure_change", delta=delta)
            self.reflex_pressure = min(max(self.reflex_pressure + delta, -400), 200)
            self.Z_reflex.set_pressure(self.reflex_pressure)
            self.Z_decay.set_pressure(self.reflex_pressure)
            self.update_reflex_volume()

    def update_reflex_volume(self):
        side_text = self.test + self.Z.get_side()
        side = sideText(side_text)
        memory = self.store_data[side].get(0)
        try:
            c = self.Z.find_nearest(memory[0], self.reflex_pressure, memory[1])
            self.Z_reflex.set_volume(round(c, 2))
        except (TypeError, IndexError):
            self.Z_reflex.set_volume(None)

    def timeStamp(self):
        time = date_time()
        self.Z.lbl_timeDate.setText(time)


if __name__ == "__main__":
    pass
