from PyQt5.Qt import pyqtSignal
from PyQt5.QtWidgets import QWidget
from lib.logoaudiometry import CalculateLogo
from lib.h_audio import (data_basic, minMax, create_voice)
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtCore import QTimer
import random





class Response(QWidget):
    button = pyqtSignal(bool)
   
    def __init__(self):
        super(Response, self).__init__()
        self.data = {
            'stimOn': [False, False], 'freq': 3, 'step': 5,
            'lvl': [20, 20], 'side': [0, 1], 
            'trans': [0, 0], 'stim': ['Tono', 'mkg']
            }
        self.response=['X',False]
        self.channel_0 = QMediaPlayer()
        self.activate_fowler = [False, False]
        self.lastChoice_fowler = None
        self.time = QTimer(self)
        self.time.timeout.connect(self.counter)
        print("test")
        self.tim = 0

    def counter(self):
        if self.tim > 0:
            self.tim += 1
        if self.tim ==  self.carhart_random:
            self.tim = 0
            self.downHand()
            self.timer.stop()


    def set_response(self, thr):
        #thr = data_basic()
        UMD = thr["UMD"]

        self.Logo = CalculateLogo(thr, UMD)
        gender = thr['gender']
        if gender == 0:
            self.gender = "feme"
        else:
            self.gender = "male"


        self.id = thr['id']
        result = []
        result1 = []
        self.curve_z = []
        self.curve_z.append(thr['Z_OD'])
        self.curve_z.append(thr['Z_OI'])
        result.append(thr['Aérea'])
        result.append(thr['Ósea'])
        result1.append(thr['Aérea_mkg'])
        result1.append(thr['Ósea_mkg'])
        self.supra = []

        self.supra.append(thr['LDL'])
        self.supra.append(thr['Fowler'])
        self.supra.append(thr['Carhart'])
        print(self.supra[2])
        self.supra.append(thr['UMD'])
        self.thr = [result, result1]

    
    def set_command(self, cmd):
        if cmd == "colocar_fonos":
            self.state = "THR_A_X"
        elif cmd == "escuche_mi_voz":
            self.state = "L_SDT_X"
        elif cmd == "dictar_palabras":
            self.state = "L_UMD_X"
        elif cmd == "pitos_fuertes":
            self.state = "S_LDL_X"
        elif cmd == "aérea_+_ruido":
            self.state = "THR_A_MKG"
        elif cmd == "colocar_vibrador":
            self.state = "THR_O_X"
        elif cmd == "vibrador_+_ruido":
            self.state = "THR_O_MKG"
        elif cmd == "dos_pitos":
            self.state = "S_FOWLER_X"
        elif cmd == "cambie_de_volumen":
            self.state = "S_SISI_X"
        elif cmd == "mano_levantada":
            self.state = "S_CARHART_X"
        elif cmd == "mano_levantada_en_ruido":
            self.state = "S_STAT_X"
        elif cmd == "sonidos_iguales":
            self.fowler_q(1)
            #print("y por por aca")
        elif cmd == "en_qué_oído":
            self.fowler_q(2)
            #print("pase por aca")
        else:
            self.state = "X_X_X"
            self.command_2 = cmd
        self.Action(self.state)

    def Action(self, action):
        t,p,m = action.split("_")
        if m == "MKG":
            MKG = True
        else:
            MKG = False
        if t == "THR":
            self.response = (t, p, MKG)
        elif t == "S" or t == "L":
            self.response = (t, p, MKG)

    def transmit_(self, **kwargs):
        for k, i in kwargs.items():
            if k == "lvl":
                l = []
                for t in i:
                    ch = int(t.split(' dB HL')[0])
                    l.append(ch)
                i = l
            if k == "stim":
                l = []
                for t in i:
                    #print(t[0:2])
                    if t[0:2] == "Na" or t == "Sp":
                        m = "mkg"
                    else: 
                        m = t
                    l.append(m)
                i = l

            self.data[k] = i

        #print(self.data)

    def activate(self):
        #print("entre al activador y haré:{}".format(self.response))
        #print(self.data)
        
        if self.response[1] == 'A' or self.response[1] == 'O':
            if self.data['stimOn'][0]:
                self.resp_THR(mkg=self.response[2])
            else:
                self.downHand()
        elif self.response[0] == 'L':
            if self.response[1] == 'SDT':
                if self.data['stimOn'][0]:
                    self.logo_sdt()
                else:
                    self.downHand()
            elif self.response[1] == 'UMD':
                pass
            else:
                pass
        elif self.response[0] == 'S':
            if self.response[1] == 'LDL':
                if self.data['stimOn'][0]:
                    self.ldl()
                else:
                    self.downHand()
            elif self.response[1] == 'FOWLER':
                    self.fowler()
                
            elif self.response[1] == 'CARHART':
                if self.data['stimOn'][0]:
                    side = self.data["side"][0]
                    if side == 0:
                        true_carh = self.supra[2][0]
                    else:
                        true_carh = self.supra[2][1]
                    if true_carh == 1:
                        print("deteriora")
                        self.time.start(1000)
                        self.tim = 1
                        self.carhart()
                    else:
                        self.upHand()
                else:
                    self.downHand()
                    self.time.stop()
                    self.tim = 0


            else:
                pass
        else:
            pass

    def fowler_q(self, n):
        data = self.supra[1][1]
        freq = self.supra[1][0]
        if self.activate_fowler[0] and self.activate_fowler[1]:
            conti = True
        else:
            conti = False

        if freq == self.data['freq'] and conti:
            self.activate_fowler[0] = False
            self.activate_fowler[1] = False
            lvlch0 = self.data['lvl'][0]
            lvlch1 = self.data['lvl'][1]
            lvls = [[],[]]

            if self.data['side'][0] == 0:
                lvls[0] = lvlch0
            if self.data['side'][1] == 1:
                lvls[1] = lvlch1

            if self.data['side'][0] == 1:
                lvls[1] = lvlch0
            if self.data['side'][1] == 0:
                lvls[0] = lvlch1
            idx = self.bestEar(freq)
            #print (idx)
            if str(lvls[idx]) in data:
                p=data[str(lvls[idx])] 
                t=lvls[idx-1]
                if p < t:
                    #print("suena mas fuerte{}".format("OI"))
                    if n == 1:
                        voice_ldl = create_voice("no", self.gender, self.id)
                        self.channel_0.setMedia(voice_ldl)
                        self.channel_0.play()
                        self.lastChoice_fowler = "elizquierdo"
                elif p == t:
                    voice_ldl = create_voice("si", self.gender, self.id)
                    self.channel_0.setMedia(voice_ldl)
                    self.channel_0.play()
                    #print("suenan iguales")
                else:
                    #print("suena mas fuerte{}".format("OD"))
                    if n == 1:
                        voice_ldl = create_voice("no", self.gender, self.id)
                        self.channel_0.setMedia(voice_ldl)
                        self.channel_0.play()
                        self.lastChoice_fowler = "elderecho"
        
        if n == 2 and self.lastChoice_fowler!=None:
            voice_ldl = create_voice(self.lastChoice_fowler, self.gender, self.id)
            self.channel_0.setMedia(voice_ldl)
            self.channel_0.play()
            self.lastChoice_fowler = None



    def bestEar(self, f):
        OD = self.thr[1][1][f][0]
        OI = self.thr[1][1][f][1]
        if OD<OI:
            best = 0
        else:
            best = 1
        return best

    def fowler(self):
        if self.data['stimOn'][0]:
            self.activate_fowler[0] = True
        if self.data['stimOn'][1]:
            self.activate_fowler[1] = True
    

    def carhart(self):
        self.carhart_random = random.randint(10,40)
        self.upHand()
        
    def ldl(self):
        #print("estoy en ldl")
        side = self.data['side'][0]
        data = self.supra[0]
        freq = self.data['freq']
        lvl = self.data['lvl'][0]
        mol = data[freq][side]
        response = lvl>=mol
      
        if response:
            #print("molesta!")
            voice_ldl = create_voice("molesta", self.gender, self.id)
            self.channel_0.setMedia(voice_ldl)
            self.channel_0.play()

    def logo_sdt(self):
        #print("ahora ahre sdt")
        sdt = self.Logo.sdt
        side = self.data["side"][0]
        lvl = self.data["lvl"][0]
        response = lvl >= sdt[side]
    
        if response:
            self.upHand()
            #print("escucho!")
        else:
            self.downHand()
            #print("no escucho nadita")
    

    def resp_THR(self, mkg):
        #error el paciente puede no estar en la camara y yo darle instrucciones?
        chOn, chOn_c = self.isChOn() #esto esta malisimo no tiene sentido que revise cual esta activo para saber cual es el contra
        
        if mkg and self.data["stim"][chOn_c] == 'mkg':
            mkg_lvl = self.data["lvl"][chOn_c]

        if mkg and self.data["stim"][1] == 'mkg' and self.data["stimOn"][1]:
            thr = self.thr[1]
            #debo probar esto !!!!
        else:
            thr = self.thr[0]
        lvl = self.data["lvl"][chOn]
        trans_index =self.data['trans'][chOn]
        freq_index = self.data["freq"]
        ouput_index = self.data['side'][chOn]
        if ouput_index == 0:
            ouput_contra = 1
        else:
            ouput_contra = 0
        UA = thr[trans_index][freq_index][ouput_index]
        UO = thr[1][freq_index][ouput_index]
        UAOne = thr[trans_index][freq_index][ouput_contra]
        listforMinMax = [freq_index, UA, UO, UAOne]
        curve_z = self.curve_z[ouput_contra]
        test_minMax = minMax(trans_index, listforMinMax, curve_z=curve_z)
        if mkg:
            if mkg_lvl < test_minMax[0]:
                thr = self.thr[0]
                UA = thr[trans_index][freq_index][ouput_index]
            elif mkg_lvl > test_minMax[1]:
                UA = 130
            else:
                pass

        response = lvl >= UA
        if response :
            self.upHand()
            #print("Escucho!!")
        
    def isChOn(self):
        if self.data["stimOn"][0]:
            chOn = 0
            chOn_c = 1
        else:
            chOn = 1
            chOn_c = 0
        return chOn , chOn_c


    def upHand(self, hand = True):
        self.button.emit(hand)
            

    def downHand(self):
        hand = False
        self.button.emit(hand)
        #print("no escucho")
        #self.activate_fowler = False