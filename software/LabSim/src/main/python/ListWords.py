# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - ListWords                    #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
import random

from PyQt6 import QtCore
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import QWidget

from lib.h_audio import create_word, create_word_response
from lib.logoaudiometry import CalculateLogo
from UI.Ui_ListWord import Ui_ListWords


class ListWords(QWidget, Ui_ListWords):
    def __init__(self,data):
        QWidget.__init__(self)
        # Inicialización de la ventana y propiedades
        self.la_super(data)
        self.setupUi(self)
        #self.channel_0 = QMediaPlayer(self)
        self.output_ch = QAudioOutput()
        self.channel_0 = QMediaPlayer()
        self.channel_0.setAudioOutput(self.output_ch)
        self.playable = [False, 0, None, False]
        self.time_1 = QtCore.QTimer(self)
        self.time_1.timeout.connect(self.timer)
        self.time_2 = QtCore.QTimer(self)
        self.time_2.timeout.connect(self.wait)
        self.wait_count = [10, 0]
        self.prev_int = 0
        self.continue_response = True
        self.list_response = [
                            0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0
                            ]
        self.btn_l1.clicked.connect(lambda:self.pushaudio(1))
        self.btn_l2.clicked.connect(lambda:self.pushaudio(2))
        self.btn_l3.clicked.connect(lambda:self.pushaudio(3))
        self.btn_l4.clicked.connect(lambda:self.pushaudio(4))
        self.btn_l5.clicked.connect(lambda:self.pushaudio(5))
        self.btn_l6.clicked.connect(lambda:self.pushaudio(6))
        self.btn_l7.clicked.connect(lambda:self.pushaudio(7))
        self.btn_l8.clicked.connect(lambda:self.pushaudio(8))
        self.btn_l9.clicked.connect(lambda:self.pushaudio(9))
        self.btn_l10.clicked.connect(lambda:self.pushaudio(10))
        self.btn_l11.clicked.connect(lambda:self.pushaudio(11))
        self.btn_l12.clicked.connect(lambda:self.pushaudio(12))
        self.btn_l13.clicked.connect(lambda:self.pushaudio(13))
        self.btn_l14.clicked.connect(lambda:self.pushaudio(14))
        self.btn_l15.clicked.connect(lambda:self.pushaudio(15))
        self.btn_l16.clicked.connect(lambda:self.pushaudio(16))
        self.btn_l17.clicked.connect(lambda:self.pushaudio(17))
        self.btn_l18.clicked.connect(lambda:self.pushaudio(18))
        self.btn_l19.clicked.connect(lambda:self.pushaudio(19))
        self.btn_l20.clicked.connect(lambda:self.pushaudio(20))
        self.btn_l21.clicked.connect(lambda:self.pushaudio(21))
        self.btn_l22.clicked.connect(lambda:self.pushaudio(22))
        self.btn_l23.clicked.connect(lambda:self.pushaudio(23))
        self.btn_l24.clicked.connect(lambda:self.pushaudio(24))
        self.btn_l25.clicked.connect(lambda:self.pushaudio(25))

        self.btn_f1.clicked.connect(lambda:self.pushaudio(1))
        self.btn_f2.clicked.connect(lambda:self.pushaudio(2))
        self.btn_f3.clicked.connect(lambda:self.pushaudio(3))
        self.btn_f4.clicked.connect(lambda:self.pushaudio(4))
        self.btn_f5.clicked.connect(lambda:self.pushaudio(5))
        self.btn_f6.clicked.connect(lambda:self.pushaudio(6))
        self.btn_f7.clicked.connect(lambda:self.pushaudio(7))
        self.btn_f8.clicked.connect(lambda:self.pushaudio(8))
        self.btn_f9.clicked.connect(lambda:self.pushaudio(9))
        self.btn_f10.clicked.connect(lambda:self.pushaudio(10))
        self.btn_f11.clicked.connect(lambda:self.pushaudio(11))
        self.btn_f12.clicked.connect(lambda:self.pushaudio(12))
        self.btn_f13.clicked.connect(lambda:self.pushaudio(13))
        self.btn_f14.clicked.connect(lambda:self.pushaudio(14))
        self.btn_f15.clicked.connect(lambda:self.pushaudio(15))
        self.btn_f16.clicked.connect(lambda:self.pushaudio(16))
        self.btn_f17.clicked.connect(lambda:self.pushaudio(17))
        self.btn_f18.clicked.connect(lambda:self.pushaudio(18))
        self.btn_f19.clicked.connect(lambda:self.pushaudio(19))
        self.btn_f20.clicked.connect(lambda:self.pushaudio(20))
        self.btn_f21.clicked.connect(lambda:self.pushaudio(21))
        self.btn_f22.clicked.connect(lambda:self.pushaudio(22))
        self.btn_f23.clicked.connect(lambda:self.pushaudio(23))
        self.btn_f24.clicked.connect(lambda:self.pushaudio(24))
        self.btn_f25.clicked.connect(lambda:self.pushaudio(25))

        self.btn_f1_2.clicked.connect(lambda:self.pushaudio(1))
        self.btn_f2_2.clicked.connect(lambda:self.pushaudio(2))
        self.btn_f3_2.clicked.connect(lambda:self.pushaudio(3))
        self.btn_f4_2.clicked.connect(lambda:self.pushaudio(4))
        self.btn_f5_2.clicked.connect(lambda:self.pushaudio(5))
        self.btn_f6_2.clicked.connect(lambda:self.pushaudio(6))
        self.btn_f7_2.clicked.connect(lambda:self.pushaudio(7))
        self.btn_f8_2.clicked.connect(lambda:self.pushaudio(8))
        self.btn_f9_2.clicked.connect(lambda:self.pushaudio(9))
        self.btn_f10_2.clicked.connect(lambda:self.pushaudio(10))
        self.btn_f11_2.clicked.connect(lambda:self.pushaudio(11))
        self.btn_f12_2.clicked.connect(lambda:self.pushaudio(12))
        self.btn_f13_2.clicked.connect(lambda:self.pushaudio(13))
        self.btn_f14_2.clicked.connect(lambda:self.pushaudio(14))
        self.btn_f15_2.clicked.connect(lambda:self.pushaudio(15))
        self.btn_f16_2.clicked.connect(lambda:self.pushaudio(16))
        self.btn_f17_2.clicked.connect(lambda:self.pushaudio(17))
        self.btn_f18_2.clicked.connect(lambda:self.pushaudio(18))
        self.btn_f19_2.clicked.connect(lambda:self.pushaudio(19))
        self.btn_f20_2.clicked.connect(lambda:self.pushaudio(20))
        self.btn_f21_2.clicked.connect(lambda:self.pushaudio(21))
        self.btn_f22_2.clicked.connect(lambda:self.pushaudio(22))
        self.btn_f23_2.clicked.connect(lambda:self.pushaudio(23))
        self.btn_f24_2.clicked.connect(lambda:self.pushaudio(24))
        self.btn_f25_2.clicked.connect(lambda:self.pushaudio(25))

        self.btn_g1.clicked.connect(lambda:self.pushaudio(1))
        self.btn_g2.clicked.connect(lambda:self.pushaudio(2))
        self.btn_g3.clicked.connect(lambda:self.pushaudio(3))
        self.btn_g4.clicked.connect(lambda:self.pushaudio(4))
        self.btn_g5.clicked.connect(lambda:self.pushaudio(5))
        self.btn_g6.clicked.connect(lambda:self.pushaudio(6))
        self.btn_g7.clicked.connect(lambda:self.pushaudio(7))
        self.btn_g8.clicked.connect(lambda:self.pushaudio(8))
        self.btn_g9.clicked.connect(lambda:self.pushaudio(9))
        self.btn_g10.clicked.connect(lambda:self.pushaudio(10))
        self.btn_g11.clicked.connect(lambda:self.pushaudio(11))
        self.btn_g12.clicked.connect(lambda:self.pushaudio(12))
        self.btn_g13.clicked.connect(lambda:self.pushaudio(13))
        self.btn_g14.clicked.connect(lambda:self.pushaudio(14))
        self.btn_g15.clicked.connect(lambda:self.pushaudio(15))
        self.btn_g16.clicked.connect(lambda:self.pushaudio(16))
        self.btn_g17.clicked.connect(lambda:self.pushaudio(17))
        self.btn_g18.clicked.connect(lambda:self.pushaudio(18))
        self.btn_g19.clicked.connect(lambda:self.pushaudio(19))
        self.btn_g20.clicked.connect(lambda:self.pushaudio(20))
        self.btn_g21.clicked.connect(lambda:self.pushaudio(21))
        self.btn_g22.clicked.connect(lambda:self.pushaudio(22))
        self.btn_g23.clicked.connect(lambda:self.pushaudio(23))
        self.btn_g24.clicked.connect(lambda:self.pushaudio(24))
        self.btn_g25.clicked.connect(lambda:self.pushaudio(25))

        self.btn_h1.clicked.connect(lambda:self.pushaudio(1))
        self.btn_h2.clicked.connect(lambda:self.pushaudio(2))
        self.btn_h3.clicked.connect(lambda:self.pushaudio(3))
        self.btn_h4.clicked.connect(lambda:self.pushaudio(4))
        self.btn_h5.clicked.connect(lambda:self.pushaudio(5))
        self.btn_h6.clicked.connect(lambda:self.pushaudio(6))
        self.btn_h7.clicked.connect(lambda:self.pushaudio(7))
        self.btn_h8.clicked.connect(lambda:self.pushaudio(8))
        self.btn_h9.clicked.connect(lambda:self.pushaudio(9))
        self.btn_h10.clicked.connect(lambda:self.pushaudio(10))
        self.btn_h11.clicked.connect(lambda:self.pushaudio(11))
        self.btn_h12.clicked.connect(lambda:self.pushaudio(12))
        self.btn_h13.clicked.connect(lambda:self.pushaudio(13))
        self.btn_h14.clicked.connect(lambda:self.pushaudio(14))
        self.btn_h15.clicked.connect(lambda:self.pushaudio(15))
        self.btn_h16.clicked.connect(lambda:self.pushaudio(16))
        self.btn_h17.clicked.connect(lambda:self.pushaudio(17))
        self.btn_h18.clicked.connect(lambda:self.pushaudio(18))
        self.btn_h19.clicked.connect(lambda:self.pushaudio(19))
        self.btn_h20.clicked.connect(lambda:self.pushaudio(20))
        self.btn_h21.clicked.connect(lambda:self.pushaudio(21))
        self.btn_h22.clicked.connect(lambda:self.pushaudio(22))
        self.btn_h23.clicked.connect(lambda:self.pushaudio(23))
        self.btn_h24.clicked.connect(lambda:self.pushaudio(24))
        self.btn_h25.clicked.connect(lambda:self.pushaudio(25))

    def la_super(self, data):
        #print(f"la_super: {data}")
        self.is_response = data['sector'] == "Camara_sono"
        gender = data['gender']
        ide = data['id']
        self.gender = "feme" if gender == 0 else "male"
        self.id = ide
        UMD = data["UMD"]
        self.is_mkg = self.ifMkg(data)
        prev = CalculateLogo(data, UMD)
        self.error_list = prev.get()

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

    def pushaudio(self, num):
        self.num = num
        btn = self.sender()
        self.text = (btn.text()).lower()
        file = f"LP_palacios_1_{self.text}.ogg"
        word = create_word(file)
        self.soundPlay(word)
   

    def soundPlay(self, word):
        self.changecalcule()
        if self.playable[0]:
            self.channel_0.setSource(word)
            #self.probe.setSource(self.channel_0)
            #self.probe.audioBufferProbed.connect(self.processProbe)
            self.channel_0.play()
            #self.time_1.start()
            self.lbl_list1.setText(f"Última : {self.text}")
            self.lbl_list2.setText(f"Última : {self.text}")
            self.lbl_list2_2.setText(f"Última : {self.text}")
            self.lbl_list3.setText(f"Última : {self.text}")
            self.lbl_list4.setText(f"Última : {self.text}")

    #def processProbe(self, buff):
        #print(buff.constData())

    def timer(self):
        if self.channel_0.MediaStatus() == 0:
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
        try:
            num = self.num - 1
            if self.list_response[num] == 1:
                media = create_word_response(self.text, self.gender, self.id)
            else:
                noneN = f"none{random.randint(1, 3)}"
                media = create_word_response(noneN, self.gender, self.id)
            self.channel_0.setSource(media)
            self.channel_0.play()
        except:
            pass

    def changecalcule(self):
        if self.prev_int != self.playable[1]:
            if self.playable[2] is None:
                self.playable[1] = 20
                self.calculate(0)
                self.prev_int = 20
            else:
                self.calculate(self.playable[2])
                self.prev_int = self.playable[1]

    def calculate(self, side):
        result = []

        if self.is_mkg[1]:
            contra = 1 if side == 0 else 0
            data = self.error_list[contra] if self.is_mkg[0] == side and self.playable[3] == False else self.error_list[side]

        else:
            data = self.error_list[side]

        intencity = self.playable[1]
        value = []
        keys = []
        for k, v in data.items():
            value.append(v)
            keys.append(int(k))

        if intencity <= keys[0]:
            range_error = 25
            self.continue_response = False
            result.extend(0 for _ in range(range_error))
        elif intencity <= keys[-1]:
            self.continue_response = True
            range_correct = data[str(intencity)]
            self._extracted_from_calculate_32(range_correct, result)
        else:
            range_correct = value[-1]
            self._extracted_from_calculate_32(range_correct, result)
        self.list_response = result
        print(self.list_response)

    # TODO Rename this here and in `calculate`
    def _extracted_from_calculate_32(self, range_correct, result):
        range_error = 25 - range_correct
        for _ in range(range_correct):
            result.append(1)
        for _ in range(range_error):
            result.append(0)
        random.shuffle(result)
        #print(result)




if __name__ == "__main__":
    pass
