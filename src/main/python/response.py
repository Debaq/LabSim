import random
from lib.helpers import CasesOffline
from lib.helpers import Preferences
from PySide6.QtCore import QTimer


c_voice = Preferences().get("command_voice")


"""_summary_
tipo->condición -> respuesta
in:estimulo out:bool respuesta
"""

class DelayActions:
    def __init__(self):
        self.time_1 = QTimer(self)
        self.time_2 = QTimer(self)
        self.time_1.timeout.connect(self.timer)
        self.time_2.timeout.connect(self.wait)
        self.trigger = 0
        
    
    def set_actions(self, action1, action2):
        self.action_init = action1
        self.action_end = action2
    
    def start(self, time=None)->None:
        if time:
            self.time_1.start(time)
        else:
            self.time_1.start()

    
    def timer(self):
        print("soy un ciclo del infierno")
        #self.set_action_init()
        
    def wait(self):
        #print("timer2")
        self.fowler_q(self.response_fowler)
        self.time_1.stop()
        self.time_2.stop()

class Response:
    def __init__(self):
        super().__init__()
        self.dbdata = self.profile_data_load("1")
        self.data = {}
        self.response=['X',False]


    
    def profile_data_load(self, profile:str):
        base_data = CasesOffline().get_cases("labsim")
        return base_data[profile]
        
    def set_command(self, cmd):
        state = c_voice[cmd]
        self.Action(state)
        
    def Action(self, action):
        pass
    
    
    def threshold(self):
        pass
    
    
class ResponseAudiometry(Response):
    def __init__(self,obj_audio):
        super().__init__()
        self.data["audio"]={'stimOn': [False, False], 'freq': 3, 'step': 5, 
                            'lvl': [20, 20], 'side': [0, 1],'trans': [0, 0], 
                            'stim': ['Tono', 'mkg']}
        self.obj_audio = obj_audio
        self.frecuency =         [125,250, 500,1000,2000,3000,4000,6000,8000]
        self.attenuations = [35, 40,  40,  40, 40,  45,  45,  50, 50]
        self.aerea = [[self.dbdata["Aerea"][i][0] for i in range(len(self.dbdata["Aerea"]))], 
                      [self.dbdata["Aerea"][i][1] for i in range(len(self.dbdata["Aerea"]))]]
        self.oseo = [[self.dbdata["Osea"][i][0] for i in range(len(self.dbdata["Osea"]))], 
                      [self.dbdata["Osea"][i][1] for i in range(len(self.dbdata["Osea"]))]]
        
        
    def response_aerea(self, side, frecuency,stim, mkg, cfmkg=0):
        if frecuency in self.frecuency:
            index_frecuency = self.frecuency.index(frecuency)
        else:
            index_frecuency = frecuency
            
        int_thr = self.aerea[side][index_frecuency]
        int_thr_cnt = self.aerea[int(not side)][index_frecuency]
        int_thr_o_cnt = self.oseo[int(not side)][index_frecuency]

        attenuation = self.attenuations[index_frecuency]
        if_need_mkg = int_thr > int_thr_o_cnt + attenuation
        if not if_need_mkg:
            #print("no necesita mkg")
            return stim >= int_thr
        #print("necesita mkg")
        if mkg==0:
            #print("el mkg esta apagado")
            sombra = list(range(0,15,5))
            random.shuffle(sombra)
            return stim - attenuation >= int_thr_o_cnt + sombra[0]
        if mkg > 0:
            int_thr_o = self.oseo[side][index_frecuency]
            #print("el mkg esta prendido")
            range_mkg = self.min_max_mkg_aereo(stim, int_thr,int_thr_cnt,int_thr_o,
                                            int_thr_o_cnt,attenuation,cfmkg)
            if range_mkg == 0:
                print("estamos en cero")
            if mkg in range_mkg:
                #print("esta enmascarado correctamente")
                return stim >= int_thr
            if mkg > range_mkg[-1]:
                #print("esta sobre enmascarado")
                return False
            elif mkg < range_mkg[0]:
                #print("esta subenmascarado")
                return stim - attenuation >= int_thr_cnt
        
    def min_max_mkg_aereo(self, stim, a_ipsi,a_contra,o_ipsi,o_contra, attenuation, cfmkg):
        #print(f"estimulo con:{a_ipsi}, le resto {attenuation}, pasan {a_ipsi-attenuation}")
        min_mkg = 5 + a_contra
        max_mkg = attenuation + a_contra + o_ipsi
        #min_mkg = a_ipsi - attenuation - o_contra + a_contra + cfmkg
        #max_mkg = o_ipsi + attenuation
        #print(f"{min_mkg}-{max_mkg}")
        return list(range(min_mkg, max_mkg,5)) if min_mkg < max_mkg else 0
    
    
    def response_th(self):
        stop_response = False
        stimOn = self.data["audio"]["stimOn"]
        freq = self.data["audio"]["freq"]
        lvl = self.data["audio"]["lvl"]
        side = self.data["audio"]["side"]
        stim = self.data["audio"]["stim"]
        if "Tono" in stim:
            mkg_exist = "mkg" in stim
            if mkg_exist:
                side_mkg = 0 if stim[0] == "mkg" else 1
                side_tone = int(not side_mkg)
                mkg = lvl[side_mkg] if stimOn[side_mkg] else 0
                
            else:
                if not False in stimOn:
                    print(f"ambos estimulos estan encendidos y ninguno es mkg : {stim}")
                    stop_response = True
                
                else:
                    lvl_tone = lvl[0] if stim[0] == "Tono" and stimOn[0] else lvl[1]
            
                
                
            
        if not stop_response:
            pass
        
        
        
        
        
    def Action(self, action):
        t,p,m = action.split("_")
        if t in ["THR", "S", "L"]:
            MKG = m == "MKG"
            self.response = (t, p, MKG)
        self.state = (t,p,m)
        
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
                    m = "mkg" if t[:2] == "Na" or t == "Sp" else t
                    l.append(m)
                i = l

            self.data["audio"][k] = i
    
    def activate(self):
        #print(f"entre al activador y haré:{self.response}")
        #print(self.data)
        if self.response[1] in ['A', 'O']:
            if self.data["audio"]['stimOn'][0]:
                self.response_th()
            else:
                self.downHand()
        elif self.response[0] == 'L':
            if self.response[1] == 'SDT':
                if self.data["audio"]['stimOn'][0]:
                    self.logo_sdt()
                else:
                    self.no()
        elif self.response[0] == 'S':
            if self.response[1] == 'LDL' and self.data["audio"]['stimOn'][0]:
                self.ldl()
            elif self.response[1] == 'LDL' or self.response[1] != 'FOWLER' and self.response[1] == 'CARHART' and not self.data['stimOn'][0]:
                self.no()
            elif self.response[1] != 'FOWLER' and self.response[1] == 'CARHART':
                self.carhart()
            elif self.response[1] == 'FOWLER':
                self.fowler()
                
                
        
    def upHand(self):
        self.obj_audio.lbl_response.setStyleSheet("background-color: rgb(170, 170, 255);")
    
    def downHand(self):
        self.obj_audio.lbl_response.setStyleSheet("background-color: rgb(255, 255, 255);")


    
        


class ResponseTimpanometry():
    pass

class ResponseAbr():
    pass

"""a = ResponseThresholdAudiometry()
side = 0
frecuencia = 125
mkg = 0
cfmkg = 0
lista = list(range(0,100,5))
lista.reverse()
for i in lista:
    intensidad = i
    response = a.response_aerea(side, frecuencia, intensidad, mkg, cfmkg)
    
    print(f"{i} - {response}")"""