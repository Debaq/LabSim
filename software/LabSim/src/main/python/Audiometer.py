# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : AudioSim                   #
#                       VER. 0.9 - Audiometro                   #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#   NOTA: si no hablas español, no es mi culpa, aprende         #
#################################################################
from typing import Text

import numpy as np
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import QWidget

#from lib.API_connector import API, PostData
from lib.h_audio import (calibrate, create_frecuency, create_intency,
                         create_sound, create_word, data_basic)
from lib.helpers import Preferences
from lib.response_A import Response
from base import context
from UI.Ui_Audiometer import Ui_Audiometer

context
class_pref = Preferences()
keyboard_shortcuts = class_pref.get("keyboard_shortcuts")
session = class_pref.get("session_pred")
URL = class_pref.get("API_URL")
intency_dict = class_pref.get("intency_dict")
frecuency_dict = class_pref.get("frecuency_dict")
output_list = class_pref.get("output_list")
stim_list = class_pref.get("stim_list")
stim_list_short = class_pref.get("stim_list_short")
test_list = class_pref.get("test_list")
trans_list = class_pref.get("trans_list")
reverse_list = class_pref.get("reverse_list")
tone_list = class_pref.get("tone_list")
pulsatile_time = class_pref.get("pulsatile_time")
alternate_time = class_pref.get("alternate_time")


class Audiometer(QWidget, Ui_Audiometer):
    signal_speech = pyqtSignal(list)
    def __init__(self, thr):
        # Inicialización de la ventana y propiedades
        #super(Audiometer, self).__init__()
        super().__init__()
        self.thr = []
        self.response = Response()
        self.response.button.connect(self.respa)
        self.la_super(thr)
        self.setupUi(self)
        self.frecuency_list = create_frecuency(
            frecuency_dict, prueba="Umbrales")
        self.random_response = [0, 0]
        #activado, reverse, intensidad, side, contrankg
        self.datasignal_speech = [False, False, None, None, False]

        # Widgets
        # Diales
        # conecta dial con movimiento con el mouse
        self.dial_der.valueChanged.connect(lambda: self.MoveDial_mouse(0))
        # conecta dial con movimiento con el mouse
        self.dial_izq.valueChanged.connect(lambda: self.MoveDial_mouse(1))
        self.block_mouse = False
        self.dial_monitor_ch1.valueChanged.connect(lambda: self.monitor(1))
        self.dial_monitor_ch2.valueChanged.connect(lambda: self.monitor(2))

        self.dial_value_der = self.dial_der.value()
        self.dial_value_izq = self.dial_izq.value()

        # Keyboard shorcuts diales
        self.shcut_dial_up_der = QShortcut(
            QKeySequence(keyboard_shortcuts[0]), self)
        self.shcut_dial_up_der.activated.connect(
            lambda: self.MoveDial(0, True))
        self.shcut_dial_down_der = QShortcut(
            QKeySequence(keyboard_shortcuts[1]), self)
        self.shcut_dial_down_der.activated.connect(
            lambda: self.MoveDial(0, False))

        self.shcut_dial_up_izq = QShortcut(
            QKeySequence(keyboard_shortcuts[2]), self)
        self.shcut_dial_up_izq.activated.connect(
            lambda: self.MoveDial(1, True))
        self.shcut_dial_down_izq = QShortcut(
            QKeySequence(keyboard_shortcuts[3]), self)
        self.shcut_dial_down_izq.activated.connect(
            lambda: self.MoveDial(1, False))

        ### Steps and extend
        self.btn_step_1.clicked.connect(lambda: self.step(1))
        self.btn_step_3.clicked.connect(lambda: self.step(3))
        self.btn_step_5.clicked.connect(lambda: self.step(5))
        self.btn_ext_range.clicked.connect(self.ext_range)

        # BTN TEST
        self.btn_alt_frec.clicked.connect(self.high_frec)

        # Frecuency btns
        self.btn_freq_minus.clicked.connect(lambda: self.FrecChange(False))
        self.btn_freq_plus.clicked.connect(lambda: self.FrecChange(True))

        # Outputs btns
        self.btn_output_der_der.clicked.connect(lambda: self.output(0, 0))
        self.btn_output_izq_der.clicked.connect(lambda: self.output(0, 1))
        self.btn_output_sim_der.clicked.connect(lambda: self.output(0, 2))

        self.btn_output_der_izq.clicked.connect(lambda: self.output(1, 0))
        self.btn_output_izq_izq.clicked.connect(lambda: self.output(1, 1))
        self.btn_output_sim_izq.clicked.connect(lambda: self.output(1, 2))

        # Stims btns
        self.btn_stim_tone_der.clicked.connect(lambda: self.stim(0, 0))
        self.btn_stim_fm_der.clicked.connect(lambda: self.stim(0, 1))
        self.btn_stim_speech_der.clicked.connect(lambda: self.stim(0, 2))
        self.btn_stim_nbn_der.clicked.connect(lambda: self.stim(0, 3))
        self.btn_stim_wn_der.clicked.connect(lambda: self.stim(0, 4))
        self.btn_stim_sn_der.clicked.connect(lambda: self.stim(0, 5))
        self.btn_stim_pn_der.clicked.connect(lambda: self.stim(0, 6))

        self.btn_stim_tone_izq.clicked.connect(lambda: self.stim(1, 0))
        self.btn_stim_fm_izq.clicked.connect(lambda: self.stim(1, 1))
        self.btn_stim_speech_izq.clicked.connect(lambda: self.stim(1, 2))
        self.btn_stim_nbn_izq.clicked.connect(lambda: self.stim(1, 3))
        self.btn_stim_wn_izq.clicked.connect(lambda: self.stim(1, 4))
        self.btn_stim_sn_izq.clicked.connect(lambda: self.stim(1, 5))
        self.btn_stim_pn_izq.clicked.connect(lambda: self.stim(1, 6))

        ### revers and pulsatil
        self.btn_rever_ch0.clicked.connect(
            lambda: self.Helper_Stim(ch=0, btnrev=True))
        self.btn_rever_ch1.clicked.connect(
            lambda: self.Helper_Stim(ch=1, btnrev=True))
        self.lbl_revers = [self.lbl_rev_ch0, self.lbl_rev_ch1]

        # btn stimulus
        self.btn_stims = [self.btn_stim_ch0, self.btn_stim_ch1]
        self.btn_stims[0].pressed.connect(lambda: self.Helper_Stim(ch=0))
        self.btn_stims[0].released.connect(
            lambda: self.Helper_Stim(ch=0, play=False))
        self.btn_stims[1].pressed.connect(lambda: self.Helper_Stim(ch=1))
        self.btn_stims[1].released.connect(
            lambda: self.Helper_Stim(ch=1, play=False))

        # btn trans
        self.btn_trans_aer_der.clicked.connect(lambda: self.trans(0, 0))
        self.btn_trans_ose_der.clicked.connect(lambda: self.trans(0, 1))
        self.btn_trans_cl_der.clicked.connect(lambda: self.trans(0, 2))

        self.btn_trans_aer_izq.clicked.connect(lambda: self.trans(1, 0))
        self.btn_trans_ose_izq.clicked.connect(lambda: self.trans(1, 1))
        self.btn_trans_cl_izq.clicked.connect(lambda: self.trans(1, 2))

        # Logo
        self.btn_correcta.clicked.connect(lambda: self.logo_sumA(True))
        self.btn_incorrecta.clicked.connect(lambda: self.logo_sumA(False))
        self.btn_borrar.clicked.connect(self.logo_clean)

        # Labels
        self.lbl_stim = [self.lbl_stim_ch0, self.lbl_stim_ch1]
        self.lbl_output = [self.lbl_output_ch0, self.lbl_output_ch1]
        self.lbl_trans = [self.lbl_trans_ch0, self.lbl_trans_ch1]
        self.lbl_intencity = [self.lbl_int_ch0, self.lbl_int_ch1]
        self.lbl_contin = [self.lbl_contin_ch0, self.lbl_contin_ch1]

        # Audios channels
        self.channel_0 = QMediaPlayer(self)
        self.channel_1 = QMediaPlayer(self)
        self.audio_output_0 = QAudioOutput()
        self.audio_output_1 = QAudioOutput()
        self.channel_0.setAudioOutput(self.audio_output_0)
        self.channel_1.setAudioOutput(self.audio_output_1)
        self.channels = [self.channel_0, self.channel_1]
        self.outputs = [self.audio_output_0, self.audio_output_1]
        self.channel_on = [False, False]
        self.monitor(1)
        self.monitor(2)
        # self.channel_0.mediaStatusChanged.connect(self.response)

        # Timers
        self.time = QTimer(self)
        self.time.timeout.connect(self.counter)
        self.btn_time_start.clicked.connect(lambda: self.counter_stat(1))
        self.btn_time_stop.clicked.connect(lambda: self.counter_stat(2))
        self.btn_time_clear.clicked.connect(lambda: self.counter_stat(3))

        # Timers for tone pulsatil
        self.time_ch0 = QTimer(self)
        self.time_ch1 = QTimer(self)
        self.time_ch = [self.time_ch0, self.time_ch1]
        self.time_ch[0].timeout.connect(lambda: self.c_puls(0))
        self.time_ch[1].timeout.connect(lambda: self.c_puls(1))

        self.btn_puls_der.clicked.connect(lambda: self.pulsatil(0))
        self.btn_puls_izq.clicked.connect(lambda: self.pulsatil(1))
        self.puls_active = [False, False]
        self.time_acum_puls = [0, 0]
        self.puls_silence = [False, False]

        # Timers for tone alternado
        self.time_alternate = QTimer(self)
        self.time_alternate.timeout.connect(self.alternate_play)
        self.btn_alternado.clicked.connect(self.alternate_lbl)
        self.alternate_ipsi = [False, False, False]
        self.time_acum_alternate = 0
        self.alternate_active = {"active": False,
                                 "ipsi": 0, "contra": 1, "side": 0}

        # Timer response
        self.time_response = QTimer(self)
        self.time_response.timeout.connect(self.response_timer)

        # vuMeters and lbl_stim warning
        self.vu_meters = [self.vmeter_der, self.vmeter_izq]
        self.lbl_warnings = [
            self.lbl_warning_stim_der, self.lbl_warning_stim_izq]
        self.disabled_widgets()
        self.dial_talkback.valueChanged.connect(self.talkback_level)
        self.talkback_volume = 5
        self.btn_talkback.clicked.connect(self.talkback)
        self.activate_response = [0, 0]
        self.trans_idx = [0,0]


    def disabled_widgets(self):
        # Disabled BETA
        # self.btn_alternado.setDisabled(True)
        self.dial_talkback.setDisabled(True)
        # self.btn_talkback.setDisabled(True)
        self.btn_output_sim_der.setDisabled(True)
        self.btn_output_sim_izq.setDisabled(True)
        self.btn_trans_cl_der.setDisabled(True)
        self.btn_trans_cl_izq.setDisabled(True)
        self.btn_stim_wn_der.setDisabled(True)
        self.btn_stim_wn_izq.setDisabled(True)
        self.btn_stim_nbn_der.setDisabled(True)
        self.btn_stim_pn_der.setDisabled(True)
        self.btn_stim_pn_izq.setDisabled(True)
        self.btn_stim_sn_der.setDisabled(True)
        self.btn_stim_fm_izq.setDisabled(True)
        self.btn_stim_speech_izq.setDisabled(True)
        #self.btn_stim_tone_izq.setDisabled(True)

    def la_super(self, data):
        self.response.set_response(data)
        thr = data if data["sector"] == "camara_sono" else data_basic()
        gender = thr['gender']
        self.gender = "feme" if gender == 0 else "male"
        self.id = thr['id']
        result = []
        result1 = []
        self.curve_z = []
        self.curve_z.append(thr['Z_OD'])
        self.curve_z.append(thr['Z_OI'])
        result.append(thr['Aérea'])
        result.append(thr['Ósea'])
        result.append(thr['LDL'])
        result1.append(thr['Aérea_mkg'])
        result1.append(thr['Ósea_mkg'])
        self.thr = [result, result1]

    def supra(self, state):
        self.response.set_command(state)
        self.response.transmit_(talk = False)
        if state != "silencio":
            command = "{}.ogg".format(state)
            comandvoice = create_word(command)
            self.state_supra = [comandvoice, state]
        else:
            self.state_supra = [None, None]

    def respa(self, data):
        if data:
            self.lbl_response.setStyleSheet("background-color: rgb(170, 170, 255);")
        else:
            self.lbl_response.setStyleSheet("background-color: rgb(255, 255, 255);")

    def commandAction(self, command):
        if command != None and command == "colocar_fonos":
            self.activate_response = [1, 0]

    def talkback(self):
        if self.state_supra is not None:
            self.channels[0].stop()
            self.channels[1].stop()
            self.channels[0].setSource(self.state_supra[0])
            self.channels[0].play()
            self.response.transmit_(talk = True)
        self.commandAction(self.state_supra[1])

    def talkback_level(self):
        self.talkback_volume = self.dial_talkback.value()

    def vu_meters_mic(self, indata, outdata, frames, time, status):
        volume_norm = np.linalg.norm(indata)*self.talkback_volume

        self.vu_meters[0].setStyleSheet(self.vu_meters_colors(int(volume_norm)))
        self.vu_meters[1].setStyleSheet(self.vu_meters_colors(int(volume_norm)))

        self.vu_meters[0].setValue(int(volume_norm))
        self.vu_meters[1].setValue(int(volume_norm))

    def vu_meters_colors(self, level):
        colors = ["#ff557f", "#ffff7f", "#55ff7f"]
        if level <= 50:
            color = colors[2]
        if level > 50 and level < 75:
            color = colors[1]
        if level >= 75:
            color = colors[0]
        style = """
        QProgressBar::chunk {}
        background-color: {};
        {}""".format("{", color, "}")

    # response
    def response_timer(self):
        color = class_pref.get("response_color")
        state = int(self.time_var_response[0])
        timers = self.time_var_response[3:]
        end = self.time_var_response[1]
        count = self.time_var_response[2]

        def func(state, timers, color, end, count):
            if count == timers[state]:
                count += 100
                self.lbl_response.setStyleSheet(color[state])
                return bool(state), True, count
            else:
                count += 100
                if count <= timers[state]:
                    return bool(state), False, count

            if end:
                self.time_response.stop()
                return not(state), False, 0
        self.time_var_response[0:3] = func(state, timers, color, end, count)

    # Reproducir Sonidos
    def Helper_Stim(self, ch, play=True, btnrev=False):
        no_logo = self.no_Logo(ch)
        no_alternate = self.lbl_contin[0].text() != tone_list[2]
        
        if btnrev is False:
            if no_logo and no_alternate:
                if play:
                    self.puls_active[ch] = True
                    self.play(ch)
                    #self.response(activate=True)
                else:
                    self.puls_active[ch] = False
                    self.stop(ch)
                    #self.response(activate=False)
            elif no_alternate:
                if play:
                    self.play_papa(ch)

                else:
                    self.stop(ch)
        else:
            if no_alternate:
                self.reverse(ch)
        if btnrev is False:
            if no_alternate is False:
                if play:
                    contra = 0 if ch == 1 else 1
                    self.alternate_ipsi[ch] = True
                    self.alternate_active["active"] = True
                    self.alternate_active["ipsi"] = ch
                    self.alternate_active["contra"] = contra
                else:
                    self.alternate_active["active"] = False

    def no_Rev(self, ch):
        label = self.lbl_revers[ch].text()
        return label != reverse_list[1]

    def no_Logo(self, ch):
        label = self.lbl_stim[ch].text()
        return label != stim_list[2]

    def no_puls(self, ch):
        label = self.lbl_contin[ch].text()
        return label != tone_list[1]

    def update_logo(self, val):
        side = self.lbl_output_ch0.text()
        side = 0 if side == "Derecha" else 1
        self.datasignal_speech[2] = val
        self.datasignal_speech[3] = side
        self.signal_speech.emit(self.datasignal_speech)

    def reverse(self, ch):
        """[funcionalidad btn invertir funcion del btn estimulo]
            Ejecuta cambioos de estado y conecciones de los btn estimulos
            y ejecuta self.play(ch) si invertido esta activado
            además verifica estado de pulsatil e invoca a self.c_puls(ch) si esta activado

        Args:
            ch ([int]): [canal 0 o 1]
        """

        self.btn_stims[ch].disconnect()
        #lbl_rev = self.lbl_revers[ch].text()

        if self.no_Rev(ch):
            self.lbl_revers[ch].setText(reverse_list[1])
            self.puls_active[ch] = True

            self.btn_stims[ch].pressed.connect(
                lambda: self.Helper_Stim(ch=ch, play=False))
            self.btn_stims[ch].released.connect(
                lambda: self.Helper_Stim(ch=ch))

        else:
            self.lbl_revers[ch].setText(reverse_list[0])
            self.puls_active[ch] = False
            self.btn_stims[ch].pressed.connect(lambda: self.Helper_Stim(ch=ch))
            self.btn_stims[ch].released.connect(
                lambda: self.Helper_Stim(ch=ch, play=False))
        lbl = self.lbl_stim[ch].text()
        if lbl != "Habla":
            if self.channels[ch].mediaStatus() != 6 or self.channels[ch].mediaStatus() == 1:
                if self.no_puls(ch):
                    self.play(ch)
                    self.vu_meters[ch].setValue(50)
            else:
                self.stop(ch)
        elif self.lbl_revers[0].text() == "Invertido":
            self.datasignal_speech[1] = True
            int_der = int(self.lbl_intencity[0].text().split(' dB HL')[0])
            side = self.lbl_output_ch0.text()
            side = 0 if side == "Derecha" else 1
            self.datasignal_speech[2] = int_der
            self.datasignal_speech[3] = side

            self.signal_speech.emit(self.datasignal_speech)
            self.lbl_warnings[ch].setStyleSheet(
                "background-color: rgb(170, 170, 255);  color : rgb(170, 170, 255);")
            self.lbl_warnings[ch].setText("toc-toc")
                #print(self.lbl_revers[1].text(), self.lbl_stim[1].text())
            if self.lbl_revers[1].text() == "Invertido" and self.lbl_stim[1].text() == "Speech Noise":
                self.datasignal_speech[4] = True
            else:
                self.datasignal_speech[4] = False
            self.signal_speech.emit(self.datasignal_speech)

        else:
            self.datasignal_speech[1] = False
            self.signal_speech.emit(self.datasignal_speech)
            self.lbl_warnings[ch].setStyleSheet(
                "background-color: rgb(255, 255, 255);")
            self.lbl_warnings[ch].setText("")

    def play_papa(self,ch):
        if self.state_supra[1] == "pa_pa_pa":
            self.vu_meters[ch].setValue(50)
            self.lbl_warnings[ch].setStyleSheet("background-color: rgb(170, 170, 255);")
            self.channels[ch].setSource(self.state_supra[0])
            self.channels[ch].play()
            self.channel_on[ch] = True
            self.post_channel_on()

    def play(self, ch):
        lbl_out_1 = self.lbl_output[ch].text()
        if lbl_out_1 == "Derecha":
            lbl_out = "OD"
        elif lbl_out_1 == "Izquierda":
            lbl_out = "OI"
        else:
            lbl_out = "sim"
        stim = self.lbl_stim[ch].text()
        f = self.lbl_freq.text().split(' Hz')[0]
        sound = create_sound(stim=stim, f=f, ch=lbl_out)

        self.channels[ch].setSource(sound)
        self.channels[ch].play()
        self.vu_meters[ch].setValue(50)
        self.lbl_warnings[ch].setStyleSheet(
            "background-color: rgb(170, 170, 255);  color : rgb(170, 170, 255);")
        self.lbl_warnings[ch].setText("toc-toc")
        self.channel_on[ch] = True
        self.post_channel_on()

    def stop(self, ch):
        self.channels[ch].stop()
        self.lbl_warnings[ch].setStyleSheet(
            "background-color: rgb(255, 255, 255);")
        self.lbl_warnings[ch].setText("")
        self.vu_meters[ch].setValue(0)
        self.channel_on[ch] = False
        self.post_channel_on()

    def post_channel_on(self):
        self.response.transmit_(stimOn = self.channel_on)
        self.response.activate()

    # PRUEBAS
    def speech(self):
        self._extracted_from_threshold_2("0/25 : 0%", 1)

    def threshold(self, reset=False):
        if self.lbl_prueba.text() == test_list[1]:
            self._extracted_from_threshold_2("1000 Hz", 0)
            self.lbl_stim[0].setText(stim_list[0])
            self.lbl_stim[1].setText(stim_list[3])

    # TODO Rename this here and in `speech` and `threshold`
    def _extracted_from_threshold_2(self, arg0, arg1):
        self.lbl_freq.setFont(QFont('Noto Sans', 20))
        self.lbl_freq.setText(arg0)
        self.lbl_prueba.setText(test_list[arg1])
            #data = {'frecuency': 1000,
            #        'stim_type_ch0': stim_list[0], 'stim_type_ch1': stim_list[3]}
            #online = self.btn_online.isChecked()
            ##self.sendData.send(data, online)

    # Comandos
    def ext_range(self):
        lbl_ext = self.lbl_ext_der.text()
        if lbl_ext == "ext.":
            self.lbl_ext_der.setText("")
            #data = {'ext_range': False}
        else:
            self.lbl_ext_der.setText("ext.")
            #data = {'ext_range': True}
        #online = self.btn_online.isChecked()
        ##self.sendData.send(data, online)

    def high_frec(self):
        verify = self.lbl_prueba.text() == test_list[0]
        if verify:
            lbl_hf = self.lbl_ext_izq.text()

            if lbl_hf == "alt. frec.":
                self.lbl_ext_izq.setText("")
                #data = {'high_frec': False}

            else:
                self.lbl_ext_izq.setText("alt. frec.")
                #data = {'high_frec': True}
        #online = self.btn_online.isChecked()
        ##self.sendData.send(data, online)

    def stim(self, ch, stim):
        try:
            self.datasignal_speech[0] = stim == 2
            self.signal_speech.emit(self.datasignal_speech)
        except:
            pass

        verify = True
        contra = 0 if ch == 1 else 1
        verify_stim = self.lbl_stim[contra].text()

        if stim in [3, 4, 6]:
            verify = verify_stim != stim_list[2]
        if stim == 5:
            verify = verify_stim == stim_list[2]
        if stim == 2:
            compare_stim = [stim_list[0], stim_list[1],
                            stim_list[3], stim_list[4], stim_list[6]]
            compare_stim = set(compare_stim)
            if verify_stim in compare_stim:
                self.speech()
                self.lbl_stim[contra].setText(stim_list[5])
            else:
                self.speech()

        if stim in [0, 1]:
            compare_stim = [stim_list[2], stim_list[5]]
            compare_stim = set(compare_stim)
            if verify_stim in compare_stim:
                self.threshold()
                self.lbl_stim[contra].setText(stim_list[3])
            else:
                self.threshold()

        if verify:
            r_stim = stim_list[stim]
            self.lbl_stim[ch].setText(r_stim)
            stim_ch = ('stim_type_ch{}').format(ch)
            #data = {stim_ch: r_stim}
            #online = self.btn_online.isChecked()
            ##self.sendData.send(data, online)
        ch0 = self.lbl_stim[0].text()
        ch1 = self.lbl_stim[1].text()
        self.response.transmit_(stim = [ch0,ch1])
        self.reset_channels()

    def reset_channels(self):
        ch1 = self.no_Logo(0)
        ch2 = self.no_Logo(1)
        self.stop(0)
        self.stop(1)

        if ch1 and self.lbl_rev_ch0.text() == reverse_list[1]:
            self.play(0)
        if ch2 and self.lbl_rev_ch1.text() == reverse_list[1]:
            self.play(1)

    def trans(self, ch, trans):
        self.lbl_trans[ch].setText(trans_list[trans])
        trans = trans_list.index(self.lbl_trans[ch].text())
        self.trans_idx[ch] = trans
        self.response.transmit_(trans=self.trans_idx)

    def output(self, ch, out):
        r_output = output_list[out]
        self.lbl_output[ch].setText(r_output)

        def mod(text):
            if text == 'Derecha':
                return 0
            else:
                return 1
        ch0 = mod(self.lbl_output[0].text())
        ch1 = mod(self.lbl_output[1].text())

        #self.datasignal_speech[2] = val
        self.datasignal_speech[3] = ch0
        self.signal_speech.emit(self.datasignal_speech)
        self.response.transmit_(side = [ch0,ch1])
        self.reset_channels()

    def FrecChange(self, up):
        prueba = self.lbl_prueba.text()
        verify = prueba != test_list[1]
        if verify:
            self._extracted_from_FrecChange_None(prueba, up)
        else:
            self.logo_numberQ(up)

    def _extracted_from_FrecChange_None(self, prueba, up):

        high_f = self.lbl_ext_izq.text() != ""
        via = self.stim_output()
        self.frecuency_list = create_frecuency(
            frecuency_dict, prueba=prueba, transductor=via, Hf=high_f)
        old_hz = self.lbl_freq.text().split(' Hz')[0]
        old_hz = int(old_hz)
        if old_hz not in self.frecuency_list:
            old_hz = self.frecuency_list[-1] if up else self.frecuency_list[0]
        pos = self.frecuency_list.index(old_hz)
        if pos >= len(self.frecuency_list)-1:
            pos = -1

        if up :
            new_hz = self.frecuency_list[pos+1]
            fr_pos = pos+1
        else:
            new_hz = self.frecuency_list[pos-1]
            fr_pos = pos-1
        self.response.transmit_(freq=fr_pos)
        self.lbl_freq.setText("{} Hz".format(new_hz))
        self.lbl_ext_der.setText("")

        self.reset_channels()
        self.modify_max_int()

    def stim_output(self):
        trans_set = set([self.lbl_trans[0].text(), self.lbl_trans[1].text()])
        result = 0
        if trans_list[1] in trans_set:
            trans_set = list(trans_set)
            if trans_set[0] == trans_set[1]:
                result = 1
            if trans_set[0] == trans_list[1] and self.lbl_stim[0] in [
                stim_list[0],
                stim_list[1],
            ]:
                result = 1
            if trans_set[1] == trans_list[1] and self.lbl_stim[1] in [
                stim_list[0],
                stim_list[1],
            ]:
                result = 1
        return result

# START LOGO #############################################

    def logo_display(self):
        label = self.lbl_freq.text().split(' : ')[0]
        total = int(label.split('/')[1])
        count = int(label.split('/')[0])
        percentage = (100 * count) / total
        return [total, count, percentage]

    def logo_numberQ(self, up):
        data = self.logo_display()
        percentage = (100 * data[1]) / data[0]
        total = data[0]+1 if up else data[0]-1
        total = max(total, 0)
        self.lbl_freq.setText(
            "{}/{} : {:.0f}%".format(data[1], total, percentage))

    def logo_sumA(self, plus):
        test = self.lbl_prueba.text()
        verify =  test == test_list[1]
        if verify:
            data = self.logo_display()
            count = data[1]+1 if plus else data[1]-1
            count = max(count, 0)
            percentage = (100 * count) / data[0]
            self.lbl_freq.setText(
                "{}/{} : {:.0f}%".format(count, data[0], percentage))

    def logo_clean(self):
        test = self.lbl_prueba.text()
        verify = test == test_list[1]
        if verify:
            data = self.logo_display()
            count = 0
            percentage = (100 * count) / data[0]
            self.lbl_freq.setText(
                "{}/{} : {:.0f}%".format(count, data[0], percentage))
# END LOGO #############################################

    def modify_max_int(self):
        f = self.lbl_freq.text().split(' Hz')[0]
        intency = create_intency(intency_dict, f=f, ext=False)
        len_intency = len(intency)
        new_int = intency[len_intency-1]
        int_der = int(self.lbl_intencity[0].text().split(' dB HL')[0])
        int_izq = int(self.lbl_intencity[1].text().split(' dB HL')[0])
        if int_der >= intency[-1]:
            self.lbl_intencity[0].setText("{} dB HL".format(new_int))
        if int_izq >= intency[-1]:
            self.lbl_intencity[1].setText("{} dB HL".format(new_int))

    def step(self, step=0):

        if step > 0:
            self.lbl_step_ch0.setText("Pasos: {} dB ".format(step))
            self.lbl_step_ch1.setText("Pasos: {} dB ".format(step))
        else:
            step = self.lbl_step_ch0.text().split(": ")[1]
            step = int(step.split("dB")[0])
        self.response.transmit_(step = step)
        return step

    def IntChange(self, ch, up):
        """[summary]

        Args:
            ch (int): 0 o 1, para el dial derecho o izquierdo
            up (bool): True o False, según la tecla presionada
        """
        # Se obtienen los datos básicos para generar la lista de frecuencias
        f = self.lbl_freq.text().split(' Hz')[0]
        ext = self.lbl_ext_der.text() != ""
        step = self.step()
        #trans = trans_list.index(self.lbl_trans[ch].text())
        trans = self.trans_idx[ch]
        # Se genera la lista de frecuencias
        intency = create_intency(
            intency_dict, step=step, f=f, transductor=trans, ext=ext)
        len_intency = len(intency)
        # Se busca el indice de la frecuencia actualmente seleccionada en el display
        old_int = self.lbl_intencity[ch].text()
        old_int = old_int.split(' dB HL')[0]
        old_int = int(old_int)
        intency_set = set(intency)
        if old_int not in intency_set:
            old_int = min(old_int, intency[-1])
            old_int = max(old_int, intency[0])
        if old_int / step != 0:
            old_int = calibrate(old_int, step)
        pos = intency.index(old_int)
        # condicionales para que no aumente la intensidad más allá del tope
        # y no de la vuelta al indice 0
        ok = True
        if up == 1 and pos >= len_intency - 1:
            pos = len_intency-1
            ok = False
        if up == -1 and pos <= 0:
            pos = 0
            ok = False
        # condicionales para cambiar la intensidad si esta en el medio del rango
        # o en los extremos
        if ok:
            new_int = intency[pos+1] if up == 1 else intency[pos-1]
        else:
            new_int = intency[pos] if up == 1 else intency[pos]
        # condicionales para actualizar el display según el dial usado
        self.lbl_intencity[ch].setText("{} dB HL".format(new_int))
        ch0 = self.lbl_intencity[0].text()
        ch1 = self.lbl_intencity[1].text()
        self.response.transmit_(lvl = [ch0,ch1])
        lvl_ch = 'level_ch{}'.format(ch)
        data = {lvl_ch: new_int}
        #online = self.btn_online.isChecked()
        #self.sendData.send(data, online)
        self.block_mouse = False
        self.random_response = [0, 0]
        lbl = self.lbl_stim[ch].text()
        if lbl == "Habla":
            self.update_logo(data[lvl_ch])


############## DIALES ################

    def MoveDial_mouse(self, dial):
        #pos = self.dial_der.value() if dial == 0 else self.dial_izq.value()
        if self.block_mouse is False:
            self.MoveDial(dial, mouse=True)

    def MoveDial(self, dial, up=True, mouse=False):
        pos = self.dial_value_der if dial == 0 else self.dial_value_izq
        val = self.dial_der.value() if dial == 0 else self.dial_izq.value()

        if mouse is False:
            self.block_mouse = True
            val_p = val + (1 if up else -1)

            if val == 0:
                val = 1
            elif val <= 0:
                val = 100
            else:
                val = val_p
        if dial == 0:
            self.dial_der.setProperty("value", val) 
        else:
            self.dial_izq.setProperty("value", val)
        dir_dial = 1 if val > pos else -1
        self.dial_value_izq = self.dial_izq.value()
        self.dial_value_der = self.dial_der.value()
        self.IntChange(dial, dir_dial)

    def monitor(self, ch):
        value = self.dial_monitor_ch1.value() if ch == 1 else self.dial_monitor_ch2.value()
        new_value = (((value - 0) / (20 - 0)) * (100 - 0) + 0)/100
        if new_value < 0.5:
            new_value -= 0.1
            
        if ch == 1:
            self.audio_output_0.setVolume(new_value)
        if ch == 2:
            self.audio_output_1.setVolume(new_value)


    def alternate_lbl(self):
        if_alternate = self.lbl_contin[0].text()
        if if_alternate == tone_list[2]:
            self.lbl_contin[0].setText(tone_list[0])
            self.lbl_contin[1].setText(tone_list[0])
            state = False
        else:
            self.lbl_contin[0].setText(tone_list[2])
            self.lbl_contin[1].setText(tone_list[2])
            self.time_acum_alternate = 0
            state = True
        self.c_alternate_stat(state)

    def alternate_play(self):
        contra = self.alternate_active["contra"]
        ipsi = self.alternate_active["ipsi"]
        active = self.alternate_active["active"]

        #print("ipsi:{},contra:{}".format(ipsi,contra))

        #self.alternate_ipsi[ipsi] = True
        #self.alternate_ipsi[contra] = False

        ch = self.alternate_active["side"]

        #print(self.alternate_ipsi)

        if active:
            if self.alternate_ipsi[2] is False:
                if self.alternate_ipsi[ch]:
                    self.time_acum_alternate += 1
                    if self.time_acum_alternate == 1:
                        self.play(ch)
                    if self.time_acum_alternate >= alternate_time[0]:
                        #print("play {}".format(ch))
                        ch = 0 if ch == 1 else 1
                        self.alternate_active["side"] = ch

                        #print(self.alternate_ipsi)
                        self.alternate_ipsi[2] = True
                        self.alternate_ipsi[ch] = True
                        #self.alternate_ipsi[ipsi] = False
                        self.time_acum_alternate = 0
            else:
                self.stop(ipsi)
                self.stop(contra)
                self.time_acum_alternate += 1

                if self.time_acum_alternate >= alternate_time[1]:
                    self.alternate_ipsi[2] = False
                    self.time_acum_alternate = 0

        else:
            self.stop(ipsi)
            self.stop(contra)
            self.time_acum_alternate = 0
            self.alternate_ipsi[2] = False

    def pulsatil(self, ch):
        contra = 0 if ch == 1 else 1
        lbl_contra = self.lbl_contin[contra].text()
        if self.if_pulsatil(ch):
            self.lbl_contin[ch].setText(tone_list[0])
        else:
            self.lbl_contin[ch].setText(tone_list[1])
            self.time_acum_puls[ch] = 0
            if lbl_contra == tone_list[2]:
                self.lbl_contin[contra].setText(tone_list[0])

        self.c_puls_stat(ch)

    def if_pulsatil(self, ch):

        lbl = self.lbl_contin[ch].text()
        return lbl == tone_list[1]

############## timers ####################

    def c_puls(self, ch):
        if not self.puls_active[ch]:
            return
        if self.puls_silence[ch] is False:
            self.time_acum_puls[ch] += 1
            if self.time_acum_puls[ch] == 1:
                self.play(ch)

            if self.time_acum_puls[ch] >= pulsatile_time[0]:
                self.puls_silence[ch] = True
                self.time_acum_puls[ch] = 0

        else:
            self.time_acum_puls[ch] += 1
            self.stop(ch)

            if self.time_acum_puls[ch] >= pulsatile_time[1]:
                self.puls_silence[ch] = False
                self.time_acum_puls[ch] = 0

    def c_puls_stat(self, ch):
        if self.if_pulsatil(ch):
            self.time_ch[ch].start(10)
        else:
            self.time_ch[ch].stop()

    def c_alternate_stat(self, state):

        if state:
            self.time_alternate.start(100)
        else:
            #print("stop")
            self.time_alternate.stop()

    def counter(self, state=1):
        time = self.lbl_time.text().split(":")
        second = int(time[1])
        minutes = int(time[0])
        second += 1
        if second == 60:
            second = 0
            minutes += 1
        self.lbl_time.setText("{}:{}".format(minutes, second))

    def counter_stat(self, state=1):
        if state == 1:
            self.time.start(1000)

        if state == 2:
            self.time.stop()

        if state == 3:
            self.lbl_time.setText("0:0")
