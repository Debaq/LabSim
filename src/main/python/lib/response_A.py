import random

from PySide6.QtCore import QTimer, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QWidget

from lib.h_audio import create_voice, create_word, data_basic, minMax
from lib.logoaudiometry import CalculateLogo


class Response(QWidget):
    button = Signal(bool)
   
    def __init__(self):
        super(Response, self).__init__()
        self.data = {
            'stimOn': [False, False], 'freq': 3, 'step': 5,
            'lvl': [20, 20], 'side': [0, 1], 
            'trans': [0, 0], 'stim': ['Tono', 'mkg']
            }
        self.response=['X',False]
        self.output_ch = QAudioOutput()
        self.channel_0 = QMediaPlayer()
        self.channel_0.setAudioOutput(self.output_ch)
        self.activate_fowler = [False, False]
        self.last_choice_fowler = None
        self.state =  None
        self.create_timer()


    def set_response(self, thr):
        #thr = data_basic()
        UMD = thr["UMD"]
        #print(f"Logo: {thr}")

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
        result.append(thr['Aerea'])
        result.append(thr['Osea'])
        result1.append(thr['Aerea_mkg'])
        result1.append(thr['Osea_mkg'])
        self.supra = []

        self.supra.append(thr['LDL'])
        self.supra.append(thr['Fowler'])
        self.supra.append(thr['Carhart'])
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
        elif cmd == "Aerea_+_ruido":
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
            self.fowler_questions("sonidos_iguales", 1)
            print("y por por aca")
        elif cmd == "en_qu??_o??do":
            self.fowler_questions("en_que_oido", 2)
                #print("pase por aca")
        else:
            self.state = "X_X_X"
            self.command_2 = cmd
        self.Action(self.state)
        
    def create_timer(self):
        self.time_1 = QTimer(self)
        self.time_1.timeout.connect(self.timer)
        self.time_2 = QTimer(self)
        self.time_2.timeout.connect(self.wait)


    def soundPlay(self, word):
        self.channel_0.setSource(word)
        self.channel_0.play()
        self.time_1.start()

    def timer(self):
        print("timer1")
        stat = str(self.channel_0.mediaStatus())
        if stat == "PySide6.QtMultimedia.QMediaPlayer.MediaStatus.EndOfMedia":
            self.time_1.stop()
            ran_time = random.randrange(500 , 1100)
            self.time_2.start(ran_time)
                
    def wait(self):
        print("timer2")
        self.fowler_q(self.response_fowler)
        self.time_1.stop()
        self.time_2.stop()
    
    def fowler_questions(self, arg0, arg1):
        self.response_fowler = arg1
        voice_ldl = create_word(arg0)
        self.soundPlay(voice_ldl)

                        

    def Action(self, action):
        t,p,m = action.split("_")
        MKG = m == "MKG"

        if t in ["THR", "S", "L"]:
            self.response = (t, p, MKG)

    def transmit_(self, **kwargs):
        #print("voy a trabsmitir {}".format(kwargs))
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
                    m = "mkg" if t[:2] == "Na" or t == "Sp" else t
                    l.append(m)
                i = l

            self.data[k] = i

        #print(self.data)

    def activate(self):
        #print(f"entre al activador y har??:{self.response}")
        #print(self.data)
        if self.response[1] in ['A', 'O']:
            if self.data['stimOn'][0]:
                self.resp_THR(mkg=self.response[2])
            else:
                self.no()
        elif self.response[0] == 'L':
            if self.response[1] == 'SDT':
                if self.data['stimOn'][0]:
                    self.logo_sdt()
                else:
                    self.no()
        elif self.response[0] == 'S':
            if self.response[1] == 'LDL' and self.data['stimOn'][0]:
                self.ldl()
            elif self.response[1] == 'LDL' or self.response[1] != 'FOWLER' and self.response[1] == 'CARHART' and not self.data['stimOn'][0]:
                self.no()
            elif self.response[1] != 'FOWLER' and self.response[1] == 'CARHART':
                self.carhart()
            elif self.response[1] == 'FOWLER':
                self.fowler()
                
                
    def fowler_q(self, n):
        print(f"ntre al fowler {n}")
        data = self.supra[1][1]
        freq = self.supra[1][0]
        #print(f"la frecuencia actual es{self.data['freq']}")
        #print(f"la frecuencia es{freq}")
        if self.activate_fowler[0] and self.activate_fowler[1]:
            conti = True
        else:
            conti = False
        #print(f"se puede continuar?{conti}")

        if freq == self.data['freq'] and conti:
            #print("pase la priemra condicion")
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
            #print (f"el indice es {idx} y el lvl es{lvls}")
            #print(f"lo que busco es {lvls[idx]}")
            #print(f"lo busco en {data}")
            if str(lvls[idx]) in data:
                p=data[str(lvls[idx])] 
                t=lvls[idx-1]
                if p < t:
                    #print("suena mas fuerte{}".format("OI"))
                    if n == 1:
                        voice_ldl = create_voice("no", self.gender, self.id)
                        #print(voice_ldl)
                        self.channel_0.setSource(voice_ldl)
                        self.channel_0.play()
                        self.last_choice_fowler = "elizquierdo"
                elif p == t:
                    voice_ldl = create_voice("si", self.gender, self.id)
                    self.channel_0.setSource(voice_ldl)
                    self.channel_0.play()
                    #print("suenan iguales")
                else:
                    #print("suena mas fuerte{}".format("OD"))
                    if n == 1:
                        voice_ldl = create_voice("no", self.gender, self.id)
                        self.channel_0.setSource(voice_ldl)
                        self.channel_0.play()
                        self.last_choice_fowler = "elderecho"
        
        if n == 2 and self.last_choice_fowler!=None:
            voice_ldl = create_voice(self.last_choice_fowler, self.gender, self.id)
            self.channel_0.setSource(voice_ldl)
            self.channel_0.play()
            self.last_choice_fowler = None



    def bestEar(self, f):
        o_d = self.thr[1][1][f][0]
        o_i = self.thr[1][1][f][1]
        return 0 if o_d<o_i else 1

    def fowler(self):
        if self.data['stimOn'][0]:
            self.activate_fowler[0] = True
        if self.data['stimOn'][1]:
            self.activate_fowler[1] = True
    

    def carhart(self):
        self.upHand()
        #print("escucho")

    def ldl(self):
        side = self.data['side'][0]
        data = self.supra[0]
        freq = self.data['freq']
        lvl = self.data['lvl'][0]
        mol = data[freq][side]
        response = lvl>=mol
        response_text = "molesta" if response else "no"
        voice_ldl = create_voice(response_text, self.gender, self.id)
        self.channel_0.setSource(voice_ldl)
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
            self.no()
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


    def upHand(self):
        hand = True
        self.button.emit(hand)
            

    def no(self):
        hand = False
        self.button.emit(hand)
        #print("no escucho")
        #self.activate_fowler = False
