# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - ListWords                    #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from lib.helpers import Preferences
from PyQt5.QtMultimedia import QMediaPlayer
import random

from lib.h_audio import create_word, create_word_response

from UI.Ui_ListWord import Ui_ListWords







class ListWords(QWidget, Ui_ListWords):
    def __init__(self,data):
        QWidget.__init__(self)
        # Inicialización de la ventana y propiedades
        self.laSuper(data)
        
        
        self.setupUi(self)
        self.channel_0 = QMediaPlayer(self)
        self.playable = [False, 0, None]
        self.time_1 = QtCore.QTimer(self)
        self.time_1.timeout.connect(self.timer)
        self.time_2 = QtCore.QTimer(self)
        self.time_2.timeout.connect(self.wait)
        self.wait_count = [10, 0]
        self.prevINT = 0

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

    def laSuper(self, data):
        if data['sector'] == "Camara_sono":
            self.isResponse = True
        else:
            self.isResponse = False
        gender = data['gender']
        id = data['id']
        if gender == 0 :
            self.gender = "feme"
        else:
            self.gender = "male"
        self.id = id

       
        prev = CalculateLogo(data)
        self.error_list = prev.get()



    def pushaudio(self, num):
        self.num = num
        btn = self.sender()
        self.text = (btn.text()).lower()
        file = "LP_palacios_1_{}.ogg".format(self.text)
        word = create_word(file)
        self.soundPlay(word)
   

    def soundPlay(self, word):
        self.changecalcule()
        if self.playable[0]:
            self.channel_0.setMedia(word)
            self.channel_0.play()
            self.time_1.start()
            self.lbl_list1.setText("Última : {}".format(self.text))
            self.lbl_list2.setText("Última : {}".format(self.text))
            self.lbl_list3.setText("Última : {}".format(self.text))
            self.lbl_list4.setText("Última : {}".format(self.text))


    def timer(self):
        if self.channel_0.state() == 0:
            self.time_1.stop()
            ran_time = random.randrange(500 , 1100)
            if self.continue_response:
                self.time_2.start(ran_time)
    
    def wait(self):
        if self.isResponse:        
            self.response()
        self.time_1.stop()
        self.time_2.stop()

    def response(self):
        try:
            num = self.num - 1
            if self.list_response[num] == 1:
                media = create_word_response(self.text, self.gender, self.id)
            else:
                noneN = "none{}".format(random.randint(1 , 3))
                media = create_word_response(noneN, self.gender, self.id)
            self.channel_0.setMedia(media)
            self.channel_0.play()
        except:
            pass

    def changecalcule(self):
        if self.prevINT != self.playable[1]:
            if self.playable[2] != None:
                self.calculate(self.playable[2])
                self.prevINT = self.playable[1]
            else:
                self.playable[1] = 20
                self.calculate(0)
                self.prevINT = 20

                
        else:
            pass

    def calculate(self, side):

        result = []
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
            for i in range(range_error):
                result.append(0)
        else:
            self.continue_response = True 
            if intencity >=keys[-1]:
                range_correct = 25
                for i in range(range_correct):
                    result.append(1)
            else:
                range_correct = data[str(intencity)]
                range_error = 25 - range_correct
                for i in range(range_correct):
                    result.append(1)
                for i in range(range_error):
                    result.append(0)
                random.shuffle(result)
        
        self.list_response = result
        print(result)




if __name__ == "__main__":
    appctxt = ApplicationContext()     
    app = QApplication([])
    window = ListWords()
    window.show()
    sys.exit(app.exec())
