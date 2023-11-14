import random
from lib.helpers import CasesOffline
from lib.helpers import Preferences
from PySide6.QtCore import QTimer
from lib.response_A import Response
class_pref = Preferences()

c_voice = class_pref.get('command_voice')
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

'''_summary_
tipo->condición -> respuesta
in:estimulo out:bool respuesta
'''

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
        print('soy un ciclo del infierno')
        #self.set_action_init()
        
    def wait(self):
        #print('timer2')
        self.fowler_q(self.response_fowler)
        self.time_1.stop()
        self.time_2.stop()
"""
class Response:
    def __init__(self):
        super().__init__()
        self.dbdata = self.profile_data_load('1')
        self.data = {}
        self.response=['X',False]


    
    def profile_data_load(self, profile:str):
        base_data = CasesOffline().get_cases('labsim')
        return base_data[profile]
        
    def set_command(self, cmd):
        state = c_voice[cmd]
        self.Action(state)
        
    def Action(self, action):
        pass
    
    
    def threshold(self):
        pass
"""    
    
class ResponseAudiometry():
    def __init__(self,obj_audio):
        super().__init__()
        self.data = {}
        self.other_response = Response()
        self.data['audio']={'stimOn': [False, False], 'freq': 3, 'step': 5, 
                            'int': [20, 20], 'output': [0, 1],'trans': [0, 0], 
                            'stim': [0, 3], 'test':'Tono', 'contin':['Continuo', 'Continuo']}
        
        self.history_command= []
        self.obj_audio = obj_audio
        self.frecuency =         [125,250, 500,1000,2000,3000,4000,6000,8000]
        self.attenuations = [35, 40,  40,  40, 40,  45,  45,  50, 50]

        
    def set_case(self,dbdata):
        self.dbdata = dbdata
        self.aerea = [[dbdata['Aerea'][i][0] for i in range(len(dbdata['Aerea']))], 
                      [dbdata['Aerea'][i][1] for i in range(len(dbdata['Aerea']))]]
        self.oseo = [[dbdata['Osea'][i][0] for i in range(len(dbdata['Osea']))], 
                      [dbdata['Osea'][i][1] for i in range(len(dbdata['Osea']))]]
        
    def response_(self):
        list_ = [0,1,2]
        uphand = any(elem in self.data['audio']['stim'] for elem in list_)
        if uphand:        
            if self.history_command:
                if self.history_command[0] == 'colocar_fonos':
                    self.response_aerea_wout_msk()
                elif self.history_command[0] =='escuche_mi_voz':
                    self.response_aerea_wout_msk()
                elif self.history_command[0] =='pitos_fuertes':
                    self.ldl()
                elif self.history_command[0] =='dos_pitos':
                    self.fowler()
                elif self.history_command[0] =='aerea_+_ruido':
                    self.response_aerea_w_msk()

                    
            else:
                print("no has dado comando alguno")
        else:
            pass
            
        if not any(self.data["audio"]['stimOn']):
            self.downHand()
        elif  self.history_command[0] == 'aerea_+_ruido' and self.data['audio']['stimOn'].count(True) < 2:
            self.downHand()


        
    def set_config(self, data):
        name = data.objectName()
        str_ = data.text()
        name = name.split('_')

        if 'ch0' in name or 'ch1' in name:
            channel = 0 if name[-1] == 'ch0' else 1

        if 'int' in name:
            value = str_.split(' ')
            self.data['audio']['int'][channel] = int(value[0])
        elif 'trans' in name:
            value = trans_list.index(str_)
            self.data['audio']['trans'][channel] = value
        elif 'output' in name:
            value = 0 if str_ == 'Derecha' else 1
            self.data['audio']['output'][channel] = value
        elif 'stim' in name:
            value = stim_list.index(str_)
            self.data['audio']['stim'][channel] = value
        elif 'stimOn' in name:
            value = True if str_ == 'toc-toc' else False
            self.data['audio']['stimOn'][channel] = value
            self.response_()
        elif 'freq' in name:
            if self.data['audio']['test'] == 'Tono':
                try:
                    str_ = str_.split(' ')
                    value = self.frecuency.index(int(str_[0]))
                    self.data['audio']['freq'] = value
                except ValueError:
                    pass
                    #print("el error de la prueba")
        elif 'prueba' in name:
            self.data['audio']['test'] = str_
            #print(f"la prueba es {self.data['audio']['test']}")
        elif 'contin' in name:
            self.data['audio']['contin'][channel] = str_


        #print(f'nombre: {data.objectName()} str:  {data.text()}')
        #print(self.data['audio']['stimOn'])



    def ldl(self):
        if self.data['audio']['test'] == 'Tono':
            if self.data['audio']['stimOn'].count(True) == 1:
                stim_on = self.data['audio']['stimOn'].index(True)
                trans = self.data['audio']['trans'][stim_on]
                if trans == 0:
                    output = self.data['audio']['output'][stim_on] #derecho o izquierdo
                    frecuency = self.data['audio']['freq'] #indice
                    int_ = self.data['audio']['int'][stim_on]
                    value = self.dbdata['LDL'][frecuency][output]
                    verify = True if int_ >= value else False
                    
                    if verify:
                        self.other_response.create_voice_('molesta')
                else:
                    print("lo esta haciendo con la osea")

    def fowler(self):
        if self.data['audio']['test'] == 'Tono':
            if all(x == 0 for x in self.data['audio']['stim']):
                if all(x == 'Alternado' for x in self.data['audio']['contin']):

                    self.other_response.set_fowler_data(self.dbdata['Fowler'])


 
    def response_aerea_w_msk(self):
        """
        minimo: UAE - AT - UONE + UANE + CE
        maximo: UOE + AT
        
        donde:
        UAE: umbral aereo estudiado
        AT: Atenuación interaural
        UONE: umbral oseo no estudiado
        UOE: umbral oseo estudiado
        UANE: umbral aereo no estudiado
        CE: coeficiente de enmascaramiento
        uae:40 - 40 - 15 + 15 + 0
        """
        if self.data['audio']['test'] == 'Tono':
            if self.data['audio']['stimOn'].count(True) == 2:
                #{'audio': {'stimOn': [True, True], 'freq': 3, 'step': 5, 'int': [25, 20], 'output': [0, 1], 'trans': [0, 0], 'stim': [0, 3], 'test': 'Tono', 'contin': ['Continuo', 'Continuo']}}
                #No existe una logica de cuando le pongan mkg pero en realidad no lo necesite
                if 3 in self.data['audio']['stim']:
                    if self.data['audio']['output'][0] != self.data['audio']['output'][1]:
                        if self.data['audio']['trans'] == [0,0]:

                            o_e = 0 if self.data['audio']['output'][0] == 0 else 1
                            o_n = int(not o_e)
                            print(f"estudio el {o_e} y enmascaro el {o_n}")
                            trans = self.data['audio']['trans'][o_e]
                            trans = 'Aerea' if trans == 0 else 'Osea'
                            frecuency = self.data['audio']['freq'] #indice
                            int_ = self.data['audio']['int'][o_e] #hay un error en el sentido de los oidos estan al contrario
                            int_mkg = self.data['audio']['int'][o_n]
                            uae = self.dbdata[trans][frecuency][o_e]
                            uane = self.dbdata[trans][frecuency][o_n]
                            ce = 0
                            at = self.attenuations[frecuency]
                            uone = self.dbdata['Osea_mkg'][frecuency][o_n]
                            uoe = self.dbdata['Osea_mkg'][frecuency][o_e]
                            mkg_min = uae - at - uone + uane + ce
                            print(f"{uae} - {at} - {uone} + {uane} + {ce}")
                            mkg_max = uoe + at
                            mkg = [mkg_min, mkg_max]
                            mkg.sort()
                            print(mkg)
                            if mkg[0] <= int_mkg <= mkg[1]:
                                threshold = self.dbdata['Aerea_mkg'][frecuency][o_e]
                                
                            else:
                                if int_mkg > mkg[1]:
                                    threshold = 130
                                if int_mkg < mkg[0]:
                                    threshold = uae

                            if threshold <= int_:
                                self.upHand()

                            print(f"{threshold} :: {int_}")
                                    
                print(self.data)
            else: 
                self.response_aerea_wout_msk()


    def response_aerea_wout_msk(self):
        print(self.data)

        if self.data['audio']['test'] == 'Tono':
            if self.data['audio']['stimOn'].count(True) == 1:
                stim_on = self.data['audio']['stimOn'].index(True)
                trans = self.data['audio']['trans'][stim_on]
                trans = 'Aerea' if trans == 0 else 'Osea'
                output = self.data['audio']['output'][stim_on] #derecho o izquierdo
                frecuency = self.data['audio']['freq'] #indice
                int_ = self.data['audio']['int'][stim_on]
                value = self.dbdata[trans][frecuency][output]
                verify = True if int_ >= value else False

                #print(f"la intencidad de estimulación es {int}, el umbral es {value} superaste el umbral {verify}")
                if verify:
                    self.upHand()
                
            elif self.data['audio']['stimOn'].count(True) == 2:
                print("escucho en ambos oidos")
                #deberia tener umbral en el mejor
        else:
            if self.data['audio']['test']!= 'Tono':
                #print(f"stimon {self.data['audio']['stimOn']}")
                if any(self.data['audio']['stimOn']):
                    stim_on = self.data['audio']['stimOn'].index(True)
                    stim = self.data['audio']['stim'][stim_on]
                    if stim == 2:
                        int_ = self.data['audio']['int'][stim_on]
                        value = self.dbdata['SDT'][stim_on]
                        verify = True if int_ >= value else False
                        if verify:
                            self.upHand()

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
            #print('no necesita mkg')
            return stim >= int_thr
        #print('necesita mkg')
        if mkg==0:
            #print('el mkg esta apagado')
            sombra = list(range(0,15,5))
            random.shuffle(sombra)
            return stim - attenuation >= int_thr_o_cnt + sombra[0]
        if mkg > 0:
            int_thr_o = self.oseo[side][index_frecuency]
            #print('el mkg esta prendido')
            range_mkg = self.min_max_mkg_aereo(stim, int_thr,int_thr_cnt,int_thr_o,
                                            int_thr_o_cnt,attenuation,cfmkg)
            if range_mkg == 0:
                print('estamos en cero')
            if mkg in range_mkg:
                #print('esta enmascarado correctamente')
                return stim >= int_thr
            if mkg > range_mkg[-1]:
                #print('esta sobre enmascarado')
                return False
            elif mkg < range_mkg[0]:
                #print('esta subenmascarado')
                return stim - attenuation >= int_thr_cnt
        
    def min_max_mkg_aereo(self, stim, a_ipsi,a_contra,o_ipsi,o_contra, attenuation, cfmkg):
        #print(f'estimulo con:{a_ipsi}, le resto {attenuation}, pasan {a_ipsi-attenuation}')
        min_mkg = 5 + a_contra
        max_mkg = attenuation + a_contra + o_ipsi
        #min_mkg = a_ipsi - attenuation - o_contra + a_contra + cfmkg
        #max_mkg = o_ipsi + attenuation
        #print(f'{min_mkg}-{max_mkg}')
        return list(range(min_mkg, max_mkg,5)) if min_mkg < max_mkg else 0
    
    
    def response_th(self):
        stop_response = False
        stimOn = self.data['audio']['stimOn']
        freq = self.data['audio']['freq']
        lvl = self.data['audio']['lvl']
        side = self.data['audio']['side']
        stim = self.data['audio']['stim']
        if 'Tono' in stim:
            mkg_exist = 'mkg' in stim
            if mkg_exist:
                side_mkg = 0 if stim[0] == 'mkg' else 1
                side_tone = int(not side_mkg)
                mkg = lvl[side_mkg] if stimOn[side_mkg] else 0
                
            else:
                if not False in stimOn:
                    print(f'ambos estimulos estan encendidos y ninguno es mkg : {stim}')
                    stop_response = True
                
                else:
                    lvl_tone = lvl[0] if stim[0] == 'Tono' and stimOn[0] else lvl[1]
            
        if not stop_response:
            pass
        
    def Action(self, action):
        t,p,m = action.split('_')
        if t in ['THR', 'S', 'L']:
            MKG = m == 'MKG'
            self.response = (t, p, MKG)
        self.state = (t,p,m)
        
    def rol_player(self, rol):
        
        if rol != 'pa_pa_pa':
            max_list = 4
            self.history_command.insert(0, rol)
            while len(self.history_command) > max_list:
                self.history_command.pop()

            print(self.history_command)
        if rol == 'dictar_palabras':
            pass
            #self.obj_audio()
        if rol == 'sonidos_iguales':
            freq = self.data['audio']['freq']
            thr = self.dbdata['Aerea_mkg'][freq]
            self.other_response.fowler_q(1, self.data, thr)
        if rol == "en_qué_oído":
            freq = self.data['audio']['freq']
            thr = self.dbdata['Aerea_mkg'][freq]
            self.other_response.fowler_q(2, self.data, thr)

    def activate(self):
        #print(f'entre al activador y haré:{self.response}')
        #print(self.data)
        pass
        """
        if self.response[1] in ['A', 'O']:
            if self.data['audio']['stimOn'][0]:
                self.response_th()
            else:
                self.downHand()
        elif self.response[0] == 'L':
            if self.response[1] == 'SDT':
                if self.data['audio']['stimOn'][0]:
                    self.logo_sdt()
                else:
                    self.no()
        elif self.response[0] == 'S':
            if self.response[1] == 'LDL' and self.data['audio']['stimOn'][0]:
                self.ldl()
            elif self.response[1] == 'LDL' or self.response[1] != 'FOWLER' and self.response[1] == 'CARHART' and not self.data['stimOn'][0]:
                self.no()
            elif self.response[1] != 'FOWLER' and self.response[1] == 'CARHART':
                self.carhart()
            elif self.response[1] == 'FOWLER':
                self.fowler()
        """        
                
        
    def upHand(self):
        self.obj_audio.lbl_response.setStyleSheet('background-color: rgb(170, 170, 255);')
    
    def downHand(self):
        self.obj_audio.lbl_response.setStyleSheet('background-color: rgb(255, 255, 255);')


    
        


class ResponseTimpanometry():
    pass

class ResponseAbr():
    pass

'''a = ResponseThresholdAudiometry()
side = 0
frecuencia = 125
mkg = 0
cfmkg = 0
lista = list(range(0,100,5))
lista.reverse()
for i in lista:
    intensidad = i
    response = a.response_aerea(side, frecuencia, intensidad, mkg, cfmkg)
    
    print(f'{i} - {response}')'''