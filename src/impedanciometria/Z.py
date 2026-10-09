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
from impedanciometria.ZETFscreen import (ZETFscreen, PRUEBA_INTEGRA, PRUEBA_PERFORADA)
from impedanciometria.h_z import changeSide, changeSideText, sideText, printer, date_time
from impedanciometria.z_generator import (Z_225, Reflex_curve, decay_curve, edad_meses_del_caso,
                                          etf_prueba_integra, etf_prueba_perforada,
                                          is_infant_ear, map_letter_for_probe,
                                          z1000_del_caso)
from impedanciometria.ZDscreen import DECAY_FRECUENCIAS
from impedanciometria.z_audio import ProbeTone, ReflexTone
from core.helpers import Storage, debug_print
from core import atajos, keyboard_monitor
from core.preferencias import preferencias


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

        # SHORTCUTS -- las teclas las arma _aplicar_atajos (ver
        # core/atajos.py): con el controlador S sube, con el teclado del
        # computador W sube (o lo que el alumno haya configurado).
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

        self.kb_monitor = keyboard_monitor.monitor()
        self.kb_monitor.connection_changed.connect(self._aplicar_atajos)
        preferencias().cambiaron.connect(self._aplicar_atajos)
        self._aplicar_atajos()

        self.btn_3.setEnabled(True)
        self.btn_3.clicked.connect(self.btn3_click)
        self.btn_5.setEnabled(True)
        self.btn_5.clicked.connect(self.btn5_click)
        self.btn_6.setEnabled(True)
        self.btn_6.clicked.connect(self.btn6_click)
        self.btn_4.setEnabled(True)
        self.btn_4.clicked.connect(self.btn4_click)

        # Tone Decay: comparte modo (IPSI/CONTRA), intensidad y presión con
        # los reflejos; la frecuencia es solo 500 o 1000 Hz.
        self.decay_freq_idx = 1
        self.Z_decay.set_freq(DECAY_FRECUENCIAS[self.decay_freq_idx])
        self.Z_decay.start_clicked.connect(self.stimulus_click)
        self.Z_decay.ipsi_clicked.connect(lambda: self.set_reflex_mode('IPSI'))
        self.Z_decay.contra_clicked.connect(lambda: self.set_reflex_mode('CONTRA'))

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
        self.time_decay = QTimer(self)
        self.time_decay.timeout.connect(self.decay_animate)
        self.time_etf = QTimer(self)
        self.time_etf.timeout.connect(self.etf_animate)

        # AUDIO: tono de sonda (timpanograma) y tono/ruido activador (reflejos),
        # ambos con fundido de entrada/salida (ver impedanciometria/z_audio.py).
        self.probe_tone = ProbeTone(self)
        self.reflex_tone = ReflexTone(self)

        # GLOBAL VARIABLE
        self.frame = Storage(3)
        self.frame.set(0, list())
        self.frame.set(1, list())

        self.side = 0
        self.test = 'Z_'
        self.store_data = [Storage(2), Storage(2)]
        self.new = [True, True]


    def _aplicar_atajos(self, *_):
        teclas = atajos.teclas(self.kb_monitor.is_connected(), preferencias().atajos())
        self.shortcut_dial_up.setKey(QKeySequence(teclas["z_subir"]))
        self.shortcut_dial_down.setKey(QKeySequence(teclas["z_bajar"]))
        self.shortcut_stimulus.setKey(QKeySequence(teclas["z_estimulo"]))

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
        # Cambio de paciente (o cierre): se corta lo que estuviera sonando o
        # barriendo y se borra lo medido; sin esto el paciente 2 veía el
        # timpanograma y los reflejos del 1
        self.time_ch0.stop()
        self.probe_tone.stop()
        self.time_reflex.stop()
        self.reflex_tone.stop()
        self._parar_decay_y_etf()
        self.store_data[0].clean()
        self.store_data[1].clean()
        self.new = [True, True]
        self.reflex_results = {
            0: {'IPSI': [None] * 4, 'CONTRA': [None] * 5},
            1: {'IPSI': [None] * 4, 'CONTRA': [None] * 5},
        }
        self.Z_reflex.clear_response()
        self.refresh_reflex_table()
        self.data = data  # None limpia el caso anterior: sin esto el log seguía marcando al paciente ya cerrado
        self.refresh()
        if data is None:
            return
        self.preCharger()

    def preCharger(self):
        side = sideText(f"Z_{self.Z.get_side()}")
        # El caso entero (umbrales, letra del timpanograma, volumen): para
        # el alumno es la respuesta del ejercicio, ver helpers.debug_print.
        debug_print(self.data)
        win_neg = self.window_neg_values[self.window_neg_idx]
        win_pos = self.window_pos_values[self.window_pos_idx]
        if self.store_data[side].is_null(0):
            debug_print(f"side : {side}")
            if self.data is not None:
                seed_key = (self.data.get('id'), self.Z.get_side(), self.probe_freq)
                zGerger = self.data.get(f"Z_{self.Z.get_side()}")
                try:
                    vol = self.data['volume'][side]
                except (KeyError, IndexError, TypeError):
                    vol = None
                if not zGerger or vol in (None, ''):
                    # caso sin timpanograma cargado para este oido: el modulo
                    # queda sin curva, no se inventa una
                    self.update_reflex_volume()
                    return
                # La edad decide si la sonda elegida sirve: bajo los 6
                # meses la de 226 Hz dibuja el pico de la pared del
                # conducto y tapa un oido medio lleno.
                zGerger = map_letter_for_probe(
                    zGerger, self.probe_freq, seed_key=seed_key,
                    edad_meses=edad_meses_del_caso(self.data),
                    forzado=z1000_del_caso(self.data, self.Z.get_side()))
            else:
                # Sin paciente no hay oído: la sonda queda abierta y no se
                # dibuja nada (ver refresh / ZZscreen.set_sonda_abierta). Antes
                # salía una curva plana con 1.8 ml inventados.
                self.update_reflex_volume()
                return
            result = Z_225(letter=zGerger, vol=vol, win_neg=win_neg, win_pos=win_pos, seed_key=seed_key).getDataSet()
            self.store_data[side].set(0, result)
            self.new[side] = True

        else:
            val = self.store_data[side].get(0)
            # El ancho de la curva es el que se guardó con ella: depende de la
            # letra de Jerger y acá ya no hay letra de la que sacarlo. Una
            # curva vieja, guardada antes de que el ancho viajara en el
            # dataset, se redibuja con el ancho por defecto.
            try:
                pmax = float(val[6])
            except (IndexError, ValueError, TypeError):
                pmax = 200
            try:
                c = float(val[2])
                p = int(val[3])
                vol = float(val[5])
            except:
                c = val[2]
                p = val[3]
                vol = val[5]
            result = Z_225(manual=True, c=c, p=p, vol=vol, pmax=pmax, win_neg=win_neg, win_pos=win_pos).getDataSet()
            self.store_data[side].set(0, result)
            self.new[side] = False

        self.update_reflex_volume()

    def set_probe_freq(self, freq):
        if freq == self.probe_freq:
            return
        self._log("z_probe_freq_change", freq=freq)
        self.probe_freq = freq
        self.Z.set_probe_freq(freq)
        if self.time_ch0.isActive():
            # barrido en curso: el tono de sonda cambia en caliente, como en
            # el equipo real (no se corta ni se reinicia el barrido)
            self.probe_tone.play(freq)
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
        self.Z_decay.set_side(self.Z.get_side())
        self.Z_etf.set_side(self.Z.get_side())
        self._parar_decay_y_etf()
        # barrido a medias: se corta antes de cambiar de curva (la del otro
        # oido puede ser mas corta y el tono de sonda seguia sonando)
        self.time_ch0.stop()
        self.probe_tone.stop()
        self.refresh()
        self.preCharger()
        self.time_reflex.stop()
        self.reflex_tone.stop()
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
        self.Z.set_sonda_abierta(self.data is None)

    def timerAnimation(self):
        if self.time_ch0.isActive():
            self.time_ch0.stop()
            self.probe_tone.stop()
        else:
            self.frame.clean()
            self.frame.set(2, 0)
            self.time_ch0.start(75)
            self.probe_tone.play(self.probe_freq)

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
            if idx >= memory_len:
                self.time_ch0.stop()
                self.probe_tone.stop()
                return
            data_idx = memory_len - 1 - idx if self.direction == 'neg->pos' else idx

            self.frame.agrege(0, memory[0][data_idx])
            self.frame.agrege(1, memory[1][data_idx])
            self.frame.set(2, idx+1)

            if memory_len <= idx+1:
                self.time_ch0.stop()
                self.probe_tone.stop()
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
            self.probe_tone.stop()

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
        if self.current_screen is self.Z_reflex and screen is not self.Z_reflex:
            self.time_reflex.stop()
            self.reflex_tone.stop()
        if self.current_screen in (self.Z_decay, self.Z_etf) and screen is not self.current_screen:
            self._parar_decay_y_etf()
        self.current_screen = screen
        if screen is self.Z_reflex:
            self.Z_reflex.set_side(self.Z.get_side())
            self.Z_reflex.clear_response()
            self.refresh_reflex_table()
            self.update_reflex_volume()
        elif screen is self.Z_decay:
            self.Z_decay.set_side(self.Z.get_side())
            self.Z_decay.set_mode(self.reflex_mode)
            self.Z_decay.set_intensity(self.dB)
            self.Z_decay.set_pressure(self.reflex_pressure)
            self.update_reflex_volume()
        elif screen is self.Z_etf:
            self.Z_etf.set_side(self.Z.get_side())
        self.btn_reflex.setEnabled(screen in (self.Z_reflex, self.Z_decay))
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
        self.Z_decay.set_mode(self.reflex_mode)
        self.Z_decay.clear_response()
        self.time_decay.stop()
        self.Z_reflex.set_freq(freqs[self.reflex_freq_idx])
        self.Z_reflex.set_nbn_enabled(self.reflex_mode == 'CONTRA')
        self.time_reflex.stop()
        self.reflex_tone.stop()
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
            self.time_reflex.stop()
            self.reflex_tone.stop()
            self.Z_reflex.clear_response()
        elif self.current_screen is self.Z:
            self._log("z_move_mark", direction=-1)
            self.move(-1)
        elif self.current_screen is self.Z_decay:
            self.decay_freq_idx = (self.decay_freq_idx + 1) % len(DECAY_FRECUENCIAS)
            self._log("z_decay_freq_change", freq=DECAY_FRECUENCIAS[self.decay_freq_idx])
            self.Z_decay.set_freq(DECAY_FRECUENCIAS[self.decay_freq_idx])
            self.time_decay.stop()
            self.reflex_tone.stop()
            self.Z_decay.clear_response()
        elif self.current_screen is self.Z_etf:
            prueba = PRUEBA_INTEGRA if self.Z_etf.prueba == PRUEBA_PERFORADA else PRUEBA_PERFORADA
            self._log("z_etf_prueba_change", prueba=prueba)
            self.time_etf.stop()
            self.Z_etf.set_prueba(prueba)

    def btn2_click(self):
        if self.current_screen is self.Z:
            self._log("z_move_mark", direction=1)
            self.move(1)
        elif self.current_screen is self.Z_decay:
            self.decay_stimulus()
        elif self.current_screen is self.Z_etf:
            if self.Z_etf.prueba == PRUEBA_PERFORADA:
                self.etf_perforada()
            else:
                self.etf_maniobra('reposo')

    def btn3_click(self):
        if self.current_screen is self.Z:
            self.direction_change()
        elif self.current_screen is self.Z_etf and self.Z_etf.prueba == PRUEBA_INTEGRA:
            self.etf_maniobra('valsalva')

    def btn4_click(self):
        if self.current_screen is self.Z:
            self.height_change()
        elif self.current_screen is self.Z_etf and self.Z_etf.prueba == PRUEBA_INTEGRA:
            self.etf_maniobra('toynbee')

    def btn5_click(self):
        if self.current_screen is self.Z:
            self.window_change('neg')

    def btn6_click(self):
        if self.current_screen is self.Z:
            self.window_change('pos')

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
        elif self.current_screen is self.Z_decay:
            self.decay_stimulus()
        elif self.current_screen is self.Z_etf:
            if self.Z_etf.prueba == PRUEBA_PERFORADA:
                self.etf_perforada()
            else:
                self.etf_maniobra('reposo')
        else:
            self._log("z_stimulus_click", screen='tymp', side=self.Z.get_side(), leak=self.leak)
            if self.data is None:
                # Sonda abierta: no hay barrido que hacer.
                self.Z.set_sonda_abierta(True)
                return
            self.timerAnimation()

    def reflex_stimulus(self):
        if not hasattr(self, 'data') or self.data is None:
            return
        reflex = self.data.get('Reflex')
        # Sin reflejos cargados PHP lo manda como lista vacia, no como dict
        if not isinstance(reflex, dict):
            return
        side = self.Z.get_side()
        probe_idx = 0 if side == 'OD' else 1
        side_key = 'od' if side == 'OD' else 'oi'
        freqs = self.reflex_freqs_for_mode()
        freq = freqs[self.reflex_freq_idx]
        row_idx = ['500', '1000', '2000', '4000', 'NBN'].index(freq)

        reflex_data = reflex.get(self.reflex_mode.lower(), [])
        # El umbral puede venir como texto ("85") o vacio: se pasa a numero y
        # lo que no se pueda leer cuenta como sin reflejo
        try:
            threshold = float(reflex_data[row_idx][probe_idx])
        except (IndexError, KeyError, TypeError, ValueError):
            threshold = None

        present = threshold is not None and self.dB >= threshold
        tipos = reflex.get('tipo')
        curve_type = tipos.get(side_key, 'normal') if isinstance(tipos, dict) else 'normal'
        x, y = Reflex_curve(present=present, dB=self.dB, threshold=threshold, curve_type=curve_type).getDataSet()

        self.time_reflex.stop()
        self.Z_reflex.clear_response()
        self.reflex_anim_data = (x, y)
        self.reflex_anim_idx = 1
        self.reflex_anim_ctx = (probe_idx, row_idx, present, curve_type)
        # Ventana completa (2s de traza) se dibuja en 1s reales, como el equipo real.
        tick_ms = round(1000 / len(x))
        self.time_reflex.start(tick_ms)

        # Rafaga de audio sincronizada con la ventana del estimulo (0.5s-1.5s
        # de los 2s de traza -> 25%-75% del tiempo real dibujado). El volumen
        # sube con el dial (asi se nota el "subir de a poco" real) pero nunca
        # pasa el techo de la salida (ver _MAX_VOLUME en z_audio.py).
        total_ms = tick_ms * len(x)
        level = max(0.0, min(1.0, (self.dB - 40) / 80))
        self.reflex_tone.burst(
            freq,
            delay_ms=round(total_ms * 0.25), duration_ms=round(total_ms * 0.5),
            volume=(0.15 + 0.35 * level),
        )

    def reflex_animate(self):
        x, y = self.reflex_anim_data
        idx = self.reflex_anim_idx
        self.Z_reflex.plot_response(x[:idx + 1], y[:idx + 1])
        self.reflex_anim_idx += 1

        if self.reflex_anim_idx >= len(x):
            self.time_reflex.stop()
            probe_idx, row_idx, present, curve_type = self.reflex_anim_ctx
            # El equipo real solo detecta y marca automáticamente en la tabla
            # cuando la curva es "normal" (meseta sostenida); invertido/on/
            # off/on-off son solo visuales en la pantalla, no gatillan la marca.
            if present and curve_type == 'normal':
                # Se guarda el dB al que el ALUMNO estimuló, nunca el umbral
                # real del caso: si prueba muy arriba del umbral verdadero,
                # ese (impreciso) es el valor que queda registrado.
                self.reflex_results[probe_idx][self.reflex_mode][row_idx] = self.dB
                self.refresh_reflex_table()

    # ------------------------------------------------------------------
    # Tone Decay
    # ------------------------------------------------------------------

    def _umbral_reflejo(self, row_idx, probe_idx):
        """Umbral del reflejo del caso en el modo actual, o None si no hay."""
        reflex = (self.data or {}).get('Reflex')
        if not isinstance(reflex, dict):
            return None
        try:
            return float(reflex.get(self.reflex_mode.lower(), [])[row_idx][probe_idx])
        except (IndexError, KeyError, TypeError, ValueError):
            return None

    def decay_stimulus(self):
        """10 s de tono a la intensidad del dial; decae si el oído ESTIMULADO
        es retrococlear (tipo de curva 'off' en el caso).

        En IPSI el estimulado es el de la sonda; en CONTRA, el otro: el decay
        es del nervio que recibe el tono, no del oído donde se mide."""
        if self.data is None:
            return
        side = self.Z.get_side()
        probe_idx = 0 if side == 'OD' else 1
        freq = DECAY_FRECUENCIAS[self.decay_freq_idx]
        row_idx = ['500', '1000', '2000', '4000', 'NBN'].index(freq)
        threshold = self._umbral_reflejo(row_idx, probe_idx)
        present = threshold is not None and self.dB >= threshold
        estimulado = probe_idx if self.reflex_mode == 'IPSI' else 1 - probe_idx
        tipos = (self.data.get('Reflex') or {}).get('tipo') if isinstance(self.data.get('Reflex'), dict) else None
        tipo = tipos.get('od' if estimulado == 0 else 'oi', 'normal') if isinstance(tipos, dict) else 'normal'
        x, y, pct5, pct10 = decay_curve(present, dB=self.dB, threshold=threshold, decae=(tipo == 'off'))
        self._log("z_stimulus_click", screen='decay', side=side, mode=self.reflex_mode, freq=freq, dB=self.dB)

        self.time_decay.stop()
        self.Z_decay.clear_response()
        self.decay_anim = (x, y, 1, pct5, pct10)
        # 12 s de traza dibujados en 6 s reales: el doble de rápido, como
        # los 2 s del reflejo que se dibujan en 1.
        tick_ms = round(6000 / len(x))
        self.time_decay.start(tick_ms)
        total_ms = tick_ms * len(x)
        level = max(0.0, min(1.0, (self.dB - 40) / 80))
        self.reflex_tone.burst(freq, delay_ms=round(total_ms / 12), duration_ms=round(total_ms * 10 / 12),
                               volume=(0.15 + 0.35 * level))

    def decay_animate(self):
        x, y, idx, pct5, pct10 = self.decay_anim
        self.Z_decay.plot_response(x[:idx + 1], y[:idx + 1])
        idx += 1
        self.decay_anim = (x, y, idx, pct5, pct10)
        if idx >= len(x):
            self.time_decay.stop()
            self.Z_decay.set_result(pct5, pct10)

    # ------------------------------------------------------------------
    # ETF
    # ------------------------------------------------------------------

    def _etf_del_oido(self):
        etf = (self.data or {}).get('ETF')
        idx = 0 if self.Z.get_side() == 'OD' else 1
        try:
            return str(etf[idx])
        except (IndexError, KeyError, TypeError):
            return 'Normal'

    def etf_perforada(self):
        """Conducto presurizado (dial) y tres degluciones en 10 s."""
        if self.data is None:
            return
        etf = self._etf_del_oido()
        x, y, final = etf_prueba_perforada(etf, self.etf_pressure)
        self._log("z_etf_test", prueba=PRUEBA_PERFORADA, side=self.Z.get_side(), pressure=self.etf_pressure)
        self.time_etf.stop()
        self.Z_etf.plot_presion([], [])
        self.Z_etf.set_resultado_perforada(self.etf_pressure, None)
        self.etf_anim = (x, y, 1, final)
        self.time_etf.start(round(5000 / len(x)))   # 10 s dibujados en 5

    def etf_animate(self):
        x, y, idx, final = self.etf_anim
        self.Z_etf.plot_presion(x[:idx + 1], y[:idx + 1])
        idx += 1
        self.etf_anim = (x, y, idx, final)
        if idx >= len(x):
            self.time_etf.stop()
            self.Z_etf.set_resultado_perforada(self.etf_pressure, final)

    def etf_maniobra(self, maniobra):
        """Timpanograma de la prueba de membrana íntegra tras la maniobra."""
        if self.data is None:
            return
        side = self.Z.get_side()
        idx = 0 if side == 'OD' else 1
        letra = self.data.get(f"Z_{side}") or 'A'
        try:
            vol = self.data['volume'][idx]
        except (KeyError, IndexError, TypeError):
            vol = 1.0
        x, y, c, p, *_ = etf_prueba_integra(self._etf_del_oido(), letra, vol, maniobra,
                                            seed_key=(self.data.get('id'), side, 'etf'))
        try:
            pico = int(round(float(p))) if float(c) > 0.05 else None
        except (TypeError, ValueError):
            pico = None
        self._log("z_etf_test", prueba=PRUEBA_INTEGRA, side=side, maniobra=maniobra)
        self.Z_etf.plot_timpanograma(maniobra, x, y, pico)

    def _parar_decay_y_etf(self):
        self.time_decay.stop()
        self.time_etf.stop()
        self.Z_decay.clear_response()
        self.Z_etf.set_prueba(self.Z_etf.prueba)

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
            c = round(self.Z.find_nearest(memory[0], self.reflex_pressure, memory[1]), 2)
        except (TypeError, IndexError):
            c = None
        self.Z_reflex.set_volume(c)
        self.Z_decay.set_volume(c)

    def timeStamp(self):
        time = date_time()
        self.Z.lbl_timeDate.setText(time)


if __name__ == "__main__":
    pass
