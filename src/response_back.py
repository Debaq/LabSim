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

    
class ResponseAudiometry():
    def __init__(self,obj_audio):
        super().__init__()
        self.data = {}
        self.other_response = Response()
        self.data['audio']={'stimOn': [False, False], 'freq': 3, 'step': 5, 
                            'int': [20, 20], 'output': [0, 1],'trans': [0, 0], 
                            'stim': [0, 3], 'test':'Umbrales', 'contin':['Continuo', 'Continuo']}
        
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
        print(f">>>{self.history_command}")
        list_ = [0,1,2]
        uphand = any(elem in self.data['audio']['stim'] for elem in list_)
        print(uphand)
        #['dictar_palabras', 'vibrador_+_ruido', 'molesto_o', 'dictar_palabras']
        if uphand:        
            if self.history_command:
                if self.history_command[0] in ['colocar_fonos', 'colocar_vibrador', 'mano_levantada_en_ruido', 'mano_levantada']:
                    self.response_aerea_wout_msk()
                elif self.history_command[0] =='pitos_fuertes':
                    self.ldl()
                elif self.history_command[0] =='dos_pitos':
                    self.fowler()
                elif self.history_command[0] =='aerea_+_ruido':
                    self.response_aerea_w_msk()
                elif self.history_command[0] =='vibrador_+_ruido':
                    self.response_osea_w_msk()
                elif self.history_command[0] == 'escuche_mi_voz':
                    
                    self.response_sdt()
            else:
                print("no has dado comando alguno")
        else:
            pass
            
        if not any(self.data["audio"]['stimOn']):
            self.downHand()
        elif  self.history_command[0] == 'aerea_+_ruido' and self.data['audio']['stimOn'].count(True) < 2:
            self.downHand()
        elif  self.history_command[0] == 'vibrador_+_ruido' and self.data['audio']['stimOn'].count(True) < 2:
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
            if self.data['audio']['test'] == 'Umbrales':
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

        #print(self.data['audio'])

        #print(f'nombre: {data.objectName()} str:  {data.text()}')
        #print(self.data['audio']['stimOn'])


    def response_sdt(self):
        print("escucha mi voz?")
        if self.data['audio']['test'] == 'Logoaudiometría':
            if self.data['audio']['stimOn'].count(True) == 1:
                stim_on = self.data['audio']['stimOn'].index(True)
                output = self.data['audio']['output'][stim_on] #derecho o izquierdo
                int_ = self.data['audio']['int'][stim_on]                    
                ths = self.dbdata['Aerea_mkg']
                sdt = self.calc_sdt(ths)
                print(sdt)
                verify = int_ >= sdt[output]
                if verify:
                    self.upHand()

                 

    def calc_sdt(self, lista):
        # Extraer los elementos de la lista desde el índice 1 hasta el 6 (inclusive)
        sublista = lista[1:7]
        # Calcular el promedio para a y b
        minimos_a = sorted(item[0] for item in sublista)[:2]
        minimos_b = sorted(item[1] for item in sublista)[:2]

        # Calcular el promedio de los dos números más bajos
        promedio_minimos_a = sum(minimos_a) / len(minimos_a)
        promedio_minimos_b = sum(minimos_b) / len(minimos_b)

        # Redondear hacia abajo al múltiplo de 5 más cercano
        promedio_minimos_a_redondeado = (promedio_minimos_a // 5) * 5
        promedio_minimos_b_redondeado = (promedio_minimos_b // 5) * 5

        return [promedio_minimos_a_redondeado, promedio_minimos_b_redondeado]


    def ldl(self):
        if self.data['audio']['test'] == 'Umbrales':
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
        if self.data['audio']['test'] == 'Umbrales':
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
        if self.data['audio']['test'] == 'Umbrales':
            if self.data['audio']['stimOn'].count(True) == 2:
                #{'audio': {'stimOn': [True, True], 'freq': 3, 'step': 5, 'int': [25, 20], 'output': [0, 1], 'trans': [0, 0], 'stim': [0, 3], 'test': 'Tono', 'contin': ['Continuo', 'Continuo']}}
                #No existe una logica de cuando le pongan mkg pero en realidad no lo necesite
                if 3 in self.data['audio']['stim']:
                    if self.data['audio']['output'][0] != self.data['audio']['output'][1]:
                        if self.data['audio']['trans'] == [0,0]:
                            o_e = 0 if self.data['audio']['output'][0] == 0 else 1
                            o_n = int(not o_e)
                            ch_tone = 0 if self.data['audio']['stim'][0] == 0 else 1   
                            ch_mkg = int(not ch_tone)                        
                            print(f"estudio el {o_e} y enmascaro el {o_n}")
                            trans = self.data['audio']['trans'][o_e]
                            trans = 'Aerea' if trans == 0 else 'Osea'
                            frecuency = self.data['audio']['freq'] #indice
                            int_ = self.data['audio']['int'][ch_tone] 
                            int_mkg = self.data['audio']['int'][ch_mkg]
                            uae = self.dbdata[trans][frecuency][o_e]
                            uane = self.dbdata[trans][frecuency][o_n]
                            ce = 0
                            at = self.attenuations[frecuency]
                            uone = self.dbdata['Osea_mkg'][frecuency][o_n]
                            uoe = self.dbdata['Osea_mkg'][frecuency][o_e]
                            mkg_min = uae - at - uone + uane + ce
                            print(f"se calcula el minimo : {uae} - {at} - {uone} + {uane} + {ce}")
                            mkg_max = uoe + at
                            mkg = [mkg_min, mkg_max]
                            mkg.sort()
                            print(f"minimo y maximo{mkg}, la intensidad del mkg es:{int_mkg}")
                            if mkg[0] <= int_mkg <= mkg[1]:
                                threshold = self.dbdata['Aerea_mkg'][frecuency][o_e]
                                
                            else:
                                if int_mkg > mkg[1]:
                                    threshold = 130
                                if int_mkg < mkg[0]:
                                    threshold = uae

                            if threshold <= int_:
                                self.upHand()

                                   
                #print(self.data)

                
    def response_osea_w_msk(self):
        """
        minimo:
        (UOE - UONE) + UANOE + CE + EO
        (45 - 10)
        max:
        AT+UOE

        UOE : umbral oseo oido estudiado
        UONE: umbral oseo no estudiado
        UANOE: umbral aereo no estudiado
        CE: coeficiente de enmascaramiento
        EO: efecto de oclusión
        At: atenuación interaural
        """
        if self.data['audio']['test'] == 'Umbrales':
            if self.data['audio']['stimOn'].count(True) == 2:
                print(self.data)
                if 3 in self.data['audio']['stim'] and 1 in self.data['audio']['trans']:
                    print("todo ok")
                    o_e = 0 if self.data['audio']['output'][0] == 0 else 1 #solución parche ya que supone que el oido estudiado es el ch 0
                    o_n = int(not o_e)
                    ch_tone = 0 if self.data['audio']['stim'][0] == 0 else 1   #aca se generaria un problema de inmediato con o_e
                    ch_mkg = int(not ch_tone)                        
                    print(f"estudio el {o_e} y enmascaro el {o_n}")
                    frecuency = self.data['audio']['freq'] #indice
                    int_ = self.data['audio']['int'][ch_tone] 
                    int_mkg = self.data['audio']['int'][ch_mkg]
                    uoe = self.dbdata['Osea_mkg'][frecuency][o_e]
                    uone = self.dbdata['Osea_mkg'][frecuency][o_n]
                    ce = 0
                    eo = self.oclusive_efect(frecuency,o_e)
                    at = self.attenuations[frecuency]
                    uane = self.dbdata['Aerea_mkg'][frecuency][o_n]
                    mkg_min = uoe - uone + uane + ce + eo
                    print(f"se calcula el minimo : {uoe} - {uone} + {uane} + {ce} + {eo}")
                    mkg_max = uoe + at
                    mkg = [mkg_min, mkg_max]
                    mkg.sort()
                    print(f"minimo y maximo{mkg}, la intensidad del mkg es:{int_mkg}")
                    if mkg[0] <= int_mkg <= mkg[1]:
                        threshold = self.dbdata['Osea_mkg'][frecuency][o_e]
                    else:
                        if int_mkg > mkg[1]:
                            threshold = 130
                        if int_mkg < mkg[0]:
                            threshold = uone
                    if threshold <= int_:
                        self.upHand()




    def oclusive_efect(self, f:int, o:int)->int:
        list_values = [15,15,15,10,0,0,0,0,0]
        value_oclusive = list_values[f]
        uone = self.dbdata['Osea_mkg'][f][o]
        uane = self.dbdata['Aerea_mkg'][f][o]
        diff = uane - uone
        if diff < 0:
            return 0
        elif 0 <= diff <= 5:
            return 0
        elif diff > 5:
            return value_oclusive


    def response_aerea_wout_msk(self):
        #aca se debe manejar la situación que esl estudiante no puso el fono en su lugar, ni el vibrador, eso no lo maneja
        if self.data['audio']['test'] == 'Umbrales':
            if self.data['audio']['stimOn'].count(True) == 1:
                stim_on = self.data['audio']['stimOn'].index(True)
                trans = self.data['audio']['trans'][stim_on]
                trans_letter = 'Aerea' if trans == 0 else 'Osea'
                output = self.data['audio']['output'][stim_on] #derecho o izquierdo
                frecuency = self.data['audio']['freq'] #indice
                print(frecuency)
                int_ = self.data['audio']['int'][stim_on]
                value = self.dbdata[trans_letter][frecuency][output]
                verify = True if int_ >= value else False

                #print(f"la intencidad de estimulación es {int}, el umbral es {value} superaste el umbral {verify}")
                if verify:
                    self.upHand()
                
            elif self.data['audio']['stimOn'].count(True) == 2:
                print("escucho en ambos oidos")
                #deberia tener umbral en el mejor
        
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
        if rol == 'pa_pa_pa':
            print("ahora somos papapa")
        if rol == 'dictar_palabras':
            pass
            #self.obj_audio()
        if rol == 'sonidos_iguales':
            freq = self.data['audio']['freq']
            thr = self.dbdata['Aerea_mkg'][freq] #umbrales de ambos oidos
            self.other_response.fowler_q(1, self.data, thr)
        if rol == "en_qué_oído":
            freq = self.data['audio']['freq']
            thr = self.dbdata['Aerea_mkg'][freq]
            self.other_response.fowler_q(2, self.data, thr)

 
                
        
    def upHand(self):
        self.obj_audio.lbl_response.setStyleSheet('background-color: rgb(170, 170, 255);')
    
    def downHand(self):
        self.obj_audio.lbl_response.setStyleSheet('background-color: rgb(255, 255, 255);')


    
        
