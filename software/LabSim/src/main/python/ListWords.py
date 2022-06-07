# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - ListWords                    #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
import contextlib
import itertools
import random
from unittest import result

from PySide6 import QtCore
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QWidget
from numpy import number

from lib.h_audio import create_word, create_word_response
from lib.logoaudiometry import CalculateLogo
from UI.Ui_ListWord import Ui_ListWords


class ListWords(QWidget, Ui_ListWords):
    def __init__(self,data):
        QWidget.__init__(self)
        # Inicialización de la ventana y propiedades
        self.la_super(data)
        self.setupUi(self)
        self.playable = [False, 0, None, False] # playable, intencity, side, with_mkg
        self.wait_count = [10, 0]
        self.prev_int = 0
        self.continue_response = True
        self.list_response = [
                            0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0
                            ]
        self.list_intencity = [i*5 for i in range(21)]
        self.create_actions_btn()
        self.create_channels()
        self.create_timer()
        
        
    def create_channels(self):
        #self.channel_0 = QMediaPlayer(self)
        self.output_ch = QAudioOutput()
        self.channel_0 = QMediaPlayer()
        self.channel_0.setAudioOutput(self.output_ch)
        
        
    def create_timer(self):
        self.time_1 = QtCore.QTimer(self)
        self.time_1.timeout.connect(self.timer)
        self.time_2 = QtCore.QTimer(self)
        self.time_2.timeout.connect(self.wait)
        
        
        
    def create_actions_btn(self): 
        t = dir(self)
        letters = ["f","g","h","i", "l"]
        for letter, i in itertools.product(letters, range(26)):
            for btn in t:
                if btn == f"btn_{letter}{str(i)}":
                    getattr(self, btn).clicked.connect(self.pushaudio)

    def la_super(self, data):
        self.is_response = data['sector'] == "Camara_sono"
        gender = data['gender']
        ide = data['id']
        self.gender = "feme" if gender == 0 else "male"
        self.id = ide
        UMD = data["UMD"]
        self.is_mkg = self.ifMkg(data)
        self.prev = CalculateLogo(data, UMD)


    def ifMkg(self, data):
        mkg = False
        side = 0
        OD = (data["Osea_mkg"][2][0] + data["Osea_mkg"][3][0]
            + data["Osea_mkg"][4][0] + data["Osea_mkg"][6][0])/4
        OI = (data["Osea_mkg"][2][1] + data["Osea_mkg"][3][1]
            + data["Osea_mkg"][4][1] + data["Osea_mkg"][6][1])/4
        dif = abs(OD - OI)
        if dif >= 35:
            mkg = True
            side = 0 if OD>OI else 1
        return [side, mkg]

    def pushaudio(self):
        btn = self.sender()
        self.num  = int(''.join(filter(str.isdigit, self.sender().objectName())))
        self.text = (btn.text()).lower()
        file = f"LP_palacios_1_{self.text}"
        word = create_word(file)
        self.soundPlay(word)
   

    def soundPlay(self, word):
        self.changecalcule()
        if self.playable[0]:
            self.channel_0.setSource(word)
            #self.probe.setSource(self.channel_0)
            #self.probe.audioBufferProbed.connect(self.processProbe)
            self.channel_0.play()
            self.time_1.start()
            self.lbl_list1.setText(f"Última : {self.text}")
            self.lbl_list2.setText(f"Última : {self.text}")
            self.lbl_list2_2.setText(f"Última : {self.text}")
            self.lbl_list3.setText(f"Última : {self.text}")
            self.lbl_list4.setText(f"Última : {self.text}")

    #def processProbe(self, buff):
        #print(buff.constData())
    def update_state(self, state):
        intencity = state[2]
        side = state[3]
        with_mkg = state[4]
        self.calculate(intencity, side, with_mkg)
        
        
    def timer(self):
        stat = str(self.channel_0.mediaStatus())
        if stat == "MediaStatus.EndOfMedia":
            self.time_1.stop()
            ran_time = random.randrange(500 , 1100)
            if self.continue_response:
                self.time_2.start(ran_time)
    
    def wait(self):
        if self.is_response:        
            self.response()
        self.time_1.stop()
        self.time_2.stop()

    def response(self):
        with contextlib.suppress(Exception):
            num = self.num - 1
            if self.list_response[num] == 1:
                media = create_word_response(self.text, self.gender, self.id)
            else:
                none_n = f"none{random.randint(1, 3)}"
                media = create_word_response(none_n, self.gender, self.id)
            self.channel_0.setSource(media)
            self.channel_0.play()

    def changecalcule(self):
        if self.prev_int != self.playable[1]:
            if self.playable[2] is None:
                self.playable[1] = 20
                #self.calculate(0)
                self.prev_int = 20
            else:
                #self.calculate(self.playable[2])
                self.prev_int = self.playable[1]

    def calculate(self, intencity, side, with_mkg):
        data = self.prev.get(side, with_mkg, intencity)
        intencity = max(intencity, 0)
        data = (data[side][str(intencity)])
        number_success = int(data / 4)
        self.list_response = self.list_success(number_success)
        

        
    def list_success(self, number_success):
        range_error = 25 - number_success
        result = [1 for _ in range(number_success)] + [0 for _ in range(range_error)]
        random.shuffle(result)
        return result