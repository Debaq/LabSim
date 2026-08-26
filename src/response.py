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
    DECAY_HOLD_MS = 6000  # sustituto simulado de los 60s clínicos del test de decaimiento tonal

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

        self.decay_timer = QTimer()
        self.decay_timer.setSingleShot(True)
        self.decay_timer.timeout.connect(self._decay_timeout)


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
                if self.history_command[0] in ['colocar_fonos', 'colocar_vibrador']:
                    self.response_aerea_wout_msk()
                elif self.history_command[0] == 'mano_levantada':
                    self.response_decay()
                elif self.history_command[0] == 'mano_levantada_en_ruido':
                    self.response_stenger()
                elif self.history_command[0] =='pitos_fuertes':
                    self.ldl()
                elif self.history_command[0] =='dos_pitos':
                    self.fowler()
                elif self.history_command[0] == 'cambie_de_volumen':
                    self.response_sisi()
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
        try:  
            if not any(self.data["audio"]['stimOn']):
                self.downHand()
            elif  self.history_command[0] == 'aerea_+_ruido' and self.data['audio']['stimOn'].count(True) < 2:
                self.downHand()
            elif  self.history_command[0] == 'vibrador_+_ruido' and self.data['audio']['stimOn'].count(True) < 2:
                self.downHand()
        except IndexError:
            print("no has dado comando alguno")


        
    def set_config(self, data):
        print("cambio el sender")
        name = data.objectName()
        str_ = data.text()
        name = name.split('_')

        if 'ch0' in name or 'ch1' in name:
            channel = 0 if name[-1] == 'ch0' else 1

        if 'int' in name:
            value = str_.split(' ')
            self.data['audio']['int'][channel] = int(value[0])
            if self.history_command and self.history_command[0] == 'mano_levantada' and self.decay_timer.isActive():
                # el docente subió el nivel: el paciente "reacciona" de nuevo, se reinicia el reloj de adaptación
                self.decay_timer.start(self.DECAY_HOLD_MS)
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
        """
        sdt responde la mejor aerea con atenuación 45
        lo verifico contra los umbrales aereos del contra y su osea
        minr = int_est - at (45) - uone + uaone
        max = at(45) + uoe
        si sobrepaso el maximo no hay respuesta
        """
   
        if self.data['audio']['test'] == 'Logoaudiometría':
            count = self.data['audio']['stimOn'].count(True)
            if count == 1:
                stim_on = self.data['audio']['stimOn'].index(True)
                #verifica si es habla o ruido
                if self.data['audio']['stim'][stim_on] == 2: #si es habla el oido que se estimula
                    sdt = self.dbdata['SDT'] #umbral guardado en el perfil del paciente
                    output = self.data['audio']['output'][stim_on] #derecho o izquierdo
                    int_ = self.data['audio']['int'][stim_on]
                    verify = int_ >= sdt[output]
                    if verify:
                        self.upHand()
                    else:
                        self.downHand()
                else: #si no es habla
                    print("ese es el mkg")
                    self.downHand()
            elif count == 2:
                self.response_sdt_w_mkg()

    def response_sdt_w_mkg(self):
        """
        Logoaudiometría con enmascaramiento: ruido de habla (Speech Noise) en el oido no estudiado.
        at fijo en 45, no depende de frecuencia (a diferencia de la via tonal).
        minimo: int_est - at - uone + uane
        maximo: at + uoe
        uae/uane: umbral aereo de habla (SDT guardado en el perfil) del oido estudiado/no estudiado
        uoe/uone: umbral oseo (predicho por Fletcher, no hay SDT oseo) del oido estudiado/no estudiado
        """
        stim = self.data['audio']['stim']
        output = self.data['audio']['output']
        if 2 not in stim or 5 not in stim:
            return
        ch_habla = stim.index(2)
        ch_mkg = stim.index(5)
        if ch_habla == ch_mkg or output[ch_habla] == output[ch_mkg]:
            return

        o_e = output[ch_habla] #oido estudiado
        o_n = output[ch_mkg]   #oido enmascarado

        sdt = self.dbdata['SDT'] #umbral guardado en el perfil del paciente
        sdt_osea = self.calc_sdt(self.dbdata['Osea_mkg'])

        at = 45
        int_ = self.data['audio']['int'][ch_habla]
        int_mkg = self.data['audio']['int'][ch_mkg]
        uae = sdt[o_e]
        uane = sdt[o_n]
        uoe = sdt_osea[o_e]
        uone = sdt_osea[o_n]

        mkg_min = int_ - at - uone + uane
        mkg_max = at + uoe
        mkg = sorted([mkg_min, mkg_max])

        threshold = 130 if int_mkg > mkg[1] else uae

        if threshold <= int_:
            self.upHand()
        else:
            self.downHand()

    def calc_sdt(self, lista):
        # Promedio de Fletcher: mejores 2 de 500/1000/2000 Hz (indices 2,3,4)
        sublista = lista[2:5]
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
                output = self.data['audio']['output'][stim_on] #derecho o izquierdo
                frecuency = self.data['audio']['freq'] #indice
                int_ = self.data['audio']['int'][stim_on]
                value = self.dbdata['LDL'][frecuency][output]
                verify = True if int_ >= value else False

                if verify:
                    self.other_response.create_voice_('molesta')

    def fowler(self):
        if self.data['audio']['test'] == 'Umbrales':
            if all(x == 0 for x in self.data['audio']['stim']):
                if all(x == 'Alternado' for x in self.data['audio']['contin']):
                    fdata = self.dbdata.get('Fowler', {'freq': None, 'cuts': [15, 30, 50]})
                    if not isinstance(fdata, dict):
                        # formato viejo (lista), caso aun no migrado desde el form: prueba no configurada
                        return
                    if fdata['freq'] == self.data['audio']['freq']:
                        thr = self.dbdata['Aerea'][fdata['freq']]
                        self.other_response.set_fowler_data(thr[0], thr[1], fdata['cuts'])

    def response_decay(self):
        """Test de decaimiento tonal: umbral normal + si el caso marca 'decay'
        para ese oído, el paciente deja de responder tras sostener el tono."""
        self.response_aerea_wout_msk()
        if self.data['audio']['stimOn'].count(True) == 1:
            stim_on = self.data['audio']['stimOn'].index(True)
            output = self.data['audio']['output'][stim_on]
            trans = self.data['audio']['trans'][stim_on]
            continuo = self.data['audio']['contin'][stim_on] == 'Continuo'
            decay = self.dbdata.get('decay', [False, False])[output]
            if trans == 0 and continuo and decay:
                self.decay_timer.start(self.DECAY_HOLD_MS)
            else:
                self.decay_timer.stop()
        else:
            self.decay_timer.stop()

    def _decay_timeout(self):
        self.downHand()  # el paciente "se adapta" y deja de percibir el tono

    def response_stenger(self):
        """Stenger: tono simultaneo en ambos oidos. Si el oido peor esta
        marcado como funcional/no organico ('Stenger'), el paciente no
        responde pese a oir claramente por el oido sano."""
        if self.data['audio']['test'] != 'Umbrales':
            return
        if self.data['audio']['stimOn'].count(True) != 2:
            return
        out = self.data['audio']['output']
        if out[0] == out[1]:
            return
        freq = self.data['audio']['freq']
        thr = self.dbdata['Aerea'][freq]
        stenger = self.dbdata.get('Stenger', [False, False])
        worse = 0 if thr[0] > thr[1] else 1
        better = int(not worse)
        int_worse = self.data['audio']['int'][out.index(worse)]
        int_better = self.data['audio']['int'][out.index(better)]
        audible_worse = int_worse >= thr[worse]
        audible_better = int_better >= thr[better]
        if stenger[worse] and audible_worse and audible_better:
            self.downHand()
        elif audible_worse or audible_better:
            self.upHand()
        else:
            self.downHand()

    def response_sisi(self):
        """SISI: cada pulsación del comando simula un incremento de 1dB;
        la probabilidad de detectarlo es el score % guardado en el caso."""
        if self.data['audio']['test'] == 'Umbrales':
            if self.data['audio']['stimOn'].count(True) == 1:
                stim_on = self.data['audio']['stimOn'].index(True)
                output = self.data['audio']['output'][stim_on]
                pct = self.dbdata.get('SISI', [0, 0])[output]
                if random.randint(1, 100) <= pct:
                    self.other_response.create_voice_('si')


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
                            else:
                                self.downHand()


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
                    else:
                        self.downHand()


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
                else:
                    self.downHand()

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
            self.other_response.fowler_q(1, self.data)
        if rol == "en_qué_oído":
            self.other_response.fowler_q(2, self.data)

 
                
        
    def upHand(self):
        self.obj_audio.lbl_response.setStyleSheet('background-color: rgb(170, 170, 255);')
    
    def downHand(self):
        self.obj_audio.lbl_response.setStyleSheet('background-color: rgb(255, 255, 255);')


    
        
