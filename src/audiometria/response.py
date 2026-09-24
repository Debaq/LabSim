import random
import time

from core.helpers import CasesOffline, debug_print
from core.helpers import Preferences
from PySide6.QtCore import QTimer
from audiometria.response_A import Response
from audiometria.Fowler import FOWLER_PATTERNS
from audiometria.masking_params import (  # re-export: los usan
    CE_TONAL, RUIDOS_ENMASCARANTES, STIM_HABLA, STIM_NBN,      # noqa: F401
    STIM_PN, STIM_SN, STIM_TONO, STIM_WN, ce_tonal)            # el panel y los tests
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
    DECAY_HOLD_MS = 60000  # 60s reales -- el alumno cronometra con el reloj de la UI, sin compresión
    MAX_OUTPUT_DB = 120   # techo de salida del equipo (constante, no depende de transductor)
    STEP_DB = 5

    # Pruebas de deterioro tonal: cada una define en qué frecuencias es
    # clínicamente válida (índices de self.frecuency) y qué debe pasar en el
    # oído contralateral. 'mask' = enmascarado en condiciones de umbral
    # aéreo (igual que colocar_fonos); 'white_noise' = ruido blanco
    # obligatorio; None = sin exigencia (Rosemberg es bilateral pero cada
    # oído se evalúa solo, uno a la vez).
    # 'fixed_level': el tono se presenta a un nivel unico de protocolo y no se
    # escala (Stat). 'cumulative': el minuto es total desde que empezo la
    # prueba y NO se reinicia al subir dB (Rosemberg); sin la marca, cada
    # subida reinicia el reloj (Carhart).
    DECAY_TESTS = {
        'mano_levantada': {                  # Carhart
            'data_key': 'Carhart', 'frequencies': [2, 3, 4, 6], 'contra': 'mask',
        },
        'ruido_blanco_contralateral': {       # Stat
            'data_key': 'Stat', 'frequencies': [2, 3, 4], 'contra': 'white_noise',
            'fixed_level': True,
        },
        'rosemberg_bilateral': {              # Rosemberg
            'data_key': 'Rosemberg', 'frequencies': [2, 3, 4, 6], 'contra': None,
            'cumulative': True,
        },
    }

    # Stat (Jerger): tono continuo a nivel fijo alto -- 110 dB SPL, que en
    # supraaural queda alrededor de 100 dB HL -- durante un minuto, con ruido
    # blanco contralateral. No se busca umbral ni se sube de a 5 dB como en el
    # Carhart: o sostiene el minuto a ese nivel (negativo) o no (positivo).
    STAT_LEVEL_DB = 100
    STAT_LEVEL_TOL = 5     # +-5 dB HL: sigue siendo "administrado a nivel"
    STAT_NOISE_MIN_DB = 80  # ruido contralateral bajo este nivel no enmascara

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
        # corrida en curso de una prueba acumulativa (Rosemberg): guarda con
        # que prueba/oido/frecuencia empezo y cuando, para que subir dB no
        # devuelva el minuto entero
        self._decay_run = {}


    def set_case(self,dbdata):
        self.dbdata = dbdata
        self.aerea = [[dbdata['Aerea'][i][0] for i in range(len(dbdata['Aerea']))], 
                      [dbdata['Aerea'][i][1] for i in range(len(dbdata['Aerea']))]]
        self.oseo = [[dbdata['Osea'][i][0] for i in range(len(dbdata['Osea']))], 
                      [dbdata['Osea'][i][1] for i in range(len(dbdata['Osea']))]]
        
    def response_(self):
        debug_print(f">>>{self.history_command}")
        list_ = [0,1,2]
        uphand = any(elem in self.data['audio']['stim'] for elem in list_)
        debug_print(uphand)
        #['dictar_palabras', 'vibrador_+_ruido', 'molesto_o', 'dictar_palabras']
        if uphand:        
            if self.history_command:
                if self.history_command[0] in ['colocar_fonos', 'colocar_vibrador']:
                    self.response_aerea_wout_msk()
                elif self.history_command[0] == 'mano_levantada':
                    self.response_tone_decay('mano_levantada')
                elif self.history_command[0] == 'mano_levantada_en_ruido':
                    self.response_stenger()
                elif self.history_command[0] == 'ruido_blanco_contralateral':
                    self.response_tone_decay('ruido_blanco_contralateral')
                elif self.history_command[0] == 'rosemberg_bilateral':
                    self.response_tone_decay('rosemberg_bilateral')
                elif self.history_command[0] =='pitos_fuertes':
                    self.ldl()
                elif self.history_command[0] =='dos_pitos':
                    self.fowler()
                elif self.history_command[0] == 'cambie_de_volumen':
                    self.response_sisi()
                elif self.history_command[0] =='aerea_+_ruido':
                    if self.data['audio']['stimOn'].count(True) == 2:
                        self.response_aerea_w_msk()
                    else:
                        # instruccion dada pero el ruido nunca se encendio: el
                        # paciente no deja de responder, responde sin
                        # enmascarar -> curva sombra
                        self.response_aerea_wout_msk()
                elif self.history_command[0] =='vibrador_+_ruido':
                    if self.data['audio']['stimOn'].count(True) == 2:
                        self.response_osea_w_msk()
                    else:
                        self.response_aerea_wout_msk()
                elif self.history_command[0] == 'escuche_mi_voz':

                    self.response_sdt()
            else:
                debug_print("no has dado comando alguno")
        else:
            pass
        if not any(self.data["audio"]['stimOn']):
            self.downHand()


        
    def set_config(self, data):
        debug_print("cambio el sender")
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

        if ('stimOn' not in name and self.history_command
                and self.history_command[0] in self.DECAY_TESTS):
            # cualquier cambio del equipo mientras corre un deterioro tonal lo
            # recalcula: subir el tono, mover el ruido contralateral, cambiar
            # de oído o de frecuencia. ('stimOn' no entra porque ya pasó por
            # response_(), que rutea a la prueba que corresponda.)
            self.response_tone_decay(self.history_command[0])

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
                    output = self.data['audio']['output'][stim_on] #derecho o izquierdo
                    o_n = int(not output)
                    int_ = self.data['audio']['int'][stim_on]
                    # sin canal de mkg -> ruido en 0 (curva sombra si hacia falta enmascarar)
                    threshold = self._resolve_sdt_threshold(output, o_n, int_, 0)
                    verify = int_ >= threshold
                    if verify:
                        self.upHand()
                    else:
                        self.downHand()
                else: #si no es habla
                    debug_print("ese es el mkg")
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
            self.downHand()
            return
        ch_habla = stim.index(2)
        ch_mkg = stim.index(5)
        if ch_habla == ch_mkg or output[ch_habla] == output[ch_mkg]:
            self.downHand()
            return

        o_e = output[ch_habla] #oido estudiado
        o_n = output[ch_mkg]   #oido enmascarado

        int_ = self.data['audio']['int'][ch_habla]
        int_mkg = self.data['audio']['int'][ch_mkg]

        threshold = self._resolve_sdt_threshold(o_e, o_n, int_, int_mkg)

        if threshold <= int_:
            self.upHand()
        else:
            self.downHand()

    def _resolve_sdt_threshold(self, o_e, o_n, int_, int_mkg):
        """
        Igual que _resolve_masked_threshold pero para logoaudiometria: el
        rango de mkg depende de la intensidad del estimulo (int_), no solo
        del oido/frecuencia, por eso no usa _masking_calc.
        """
        sdt = self.dbdata['SDT'] #umbral guardado en el perfil del paciente
        sdt_osea = self.calc_sdt(self.dbdata['Osea_mkg'])

        at = 45
        uae = sdt[o_e]
        uane = sdt[o_n]
        uoe = sdt_osea[o_e]
        uone = sdt_osea[o_n]

        mkg_min = int_ - at - uone + uane
        mkg_max = at + uoe
        mkg_lo, mkg_hi = sorted([mkg_min, mkg_max])

        if mkg_lo <= int_mkg <= mkg_hi:
            return uae
        elif int_mkg > mkg_hi:
            return 130
        else:
            return min(uae, at + uone)

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
                    # Un paciente real siempre responde algo a "¿suenan
                    # iguales?", en cualquier frecuencia -- si el docente no
                    # configuró un patrón de reclutamiento para la frecuencia
                    # que el alumno está probando, se responde como un oído
                    # normal (sin reclutar), no en silencio. El silencio solo
                    # tenía sentido para pruebas de umbral (no se oye algo
                    # bajo el umbral); acá siempre hay algo que comparar.
                    fdata = self.dbdata.get('Fowler', {})
                    if not isinstance(fdata, dict):
                        fdata = {}  # formato viejo (lista), caso aun no migrado
                    patterns = fdata.get('patterns')
                    if not isinstance(patterns, dict):
                        patterns = {}

                    freq = self.data['audio']['freq']
                    pattern = patterns.get(str(freq), 'none')
                    cuts = FOWLER_PATTERNS.get(pattern, FOWLER_PATTERNS['none'])
                    air_pair = self.dbdata['Aerea'][freq]
                    self.other_response.set_fowler_data(air_pair[0], air_pair[1], cuts, fdata.get('diplacusia', False))

    def _decay_total(self, cfg, freq, ear):
        """dB que hay que subir sobre el umbral para que el oído sostenga el
        tono el minuto completo en esta prueba/frecuencia/oído. None si la
        frecuencia no es válida para la prueba (fuera del protocolo clínico)."""
        try:
            pos = cfg['frequencies'].index(freq)
        except ValueError:
            return None
        data = self.dbdata.get(cfg['data_key']) or []
        return data[pos][ear] if pos < len(data) else 0

    def _tone_channel(self):
        """Canal que lleva el tono puro. No sirve `stimOn.index(True)`: en las
        pruebas con ruido contralateral hay dos canales encendidos y el tono
        puede estar en cualquiera de los dos."""
        tones = [ch for ch in (0, 1)
                 if self.data['audio']['stimOn'][ch]
                 and self.data['audio']['stim'][ch] == 0]
        return tones[0] if len(tones) == 1 else None

    def _decay_abort(self):
        """Corta la corrida: sin tono válido no hay prueba que cronometrar."""
        self.decay_timer.stop()
        self._decay_run = {}
        self.downHand()

    def _decay_elapsed_ms(self, cfg, command, ear, freq, int_):
        """Milisegundos que lleva corriendo esta presentación, medidos en
        tiempo real, no en llamadas al motor.

        Importa porque el alumno cronometra por fuera (el reloj del audiómetro
        o uno de pulsera): el minuto que él mide y el que corre acá tienen que
        ser el mismo. Por eso el reloj arranca una sola vez por presentación y
        cada recálculo re-arma el timer con lo que QUEDA, en vez de regalar el
        minuto entero de nuevo. Sin esto, mover cualquier perilla del equipo
        (transductor, continuo/pulsado, la frecuencia y volver) reiniciaba la
        cuenta y el paciente sostenía el tono más rato del que marca el
        cronómetro del alumno.

        Qué reinicia la cuenta es lo único que cambia entre pruebas:
        - Carhart: cambiar el nivel (cada subida de 5 dB abre un minuto nuevo).
        - Rosemberg y Stat: solo cambiar de oído o de frecuencia; el nivel no,
          porque ahí el minuto es total.
        """
        key = (command, ear, freq)
        if not (cfg.get('cumulative') or cfg.get('fixed_level')):
            key = key + (int_,)
        if self._decay_run.get('key') != key:
            self._decay_run = {'key': key, 'start': time.monotonic()}
            return 0
        return (time.monotonic() - self._decay_run['start']) * 1000

    def response_tone_decay(self, command):
        """Motor de deterioro tonal (Carhart/Stat/Rosemberg): tono puro
        continuo, se sostiene la mano mientras se percibe. El caso guarda,
        por prueba/frecuencia/oído, cuántos dB sobre el umbral hacen falta
        para sostener el minuto (`_decay_total`).

        Las tres se administran distinto y el motor las trata distinto:

        - Carhart: se sube de a STEP_DB y cada subida reinicia el minuto.
        - Rosemberg: se sube igual, pero el minuto es total y no se reinicia.
        - Stat: nivel único de protocolo (STAT_LEVEL_DB) con ruido blanco
          contralateral; no se escala. Fuera de ese nivel el paciente sigue
          respondiendo por audibilidad, pero la prueba no entrega resultado.
        """
        cfg = self.DECAY_TESTS[command]
        stim_on = self._tone_channel()
        if stim_on is None:
            self._decay_abort()
            return

        continuo = self.data['audio']['contin'][stim_on] == 'Continuo'
        via_aerea = self.data['audio']['trans'][stim_on] == 0
        if not (continuo and via_aerea):
            self._decay_abort()
            return

        other = int(not stim_on)
        ear = self.data['audio']['output'][stim_on]
        o_n = int(not ear)
        freq = self.data['audio']['freq']
        int_ = self.data['audio']['int'][stim_on]

        decay_total = self._decay_total(cfg, freq, ear)
        if decay_total is None:  # frecuencia fuera del protocolo de la prueba
            self._decay_abort()
            return

        if cfg['contra'] == 'white_noise':
            noise_on = (self.data['audio']['stimOn'][other]
                        and self.data['audio']['output'][other] == o_n
                        and self.data['audio']['stim'][other] == 4)  # 4 = Ruido blanco
            noise_lvl = self.data['audio']['int'][other] if noise_on else 0
            if not noise_on or noise_lvl < self.STAT_NOISE_MIN_DB:
                # a 100 dB HL el tono cruza al otro oído: sin ruido blanco que
                # lo tape, lo que se mida no es de este oído
                self._decay_abort()
                return
            # el nivel del ruido del Stat lo fija el protocolo, no el alumno:
            # a 90 dB sobre un oido normal la formula de enmascaramiento lo
            # daria por sobre-enmascarado, cuando en el test real el tono va a
            # 100 dB y se oye igual. Por eso aca se usa directo el umbral real
            # del oido estudiado en vez de pasar por _resolve_masked_threshold.
            int_mkg = None
            ce = 0
        elif cfg['contra'] == 'mask':
            # el tipo de ruido tambien cuenta aca: enmascarar con blanco
            # exige mas nivel que con NBN (ver CE_TONAL)
            ruido = self._canal_ruido(o_n)
            int_mkg = self.data['audio']['int'][ruido[0]] if ruido else 0
            ce = ruido[2] if ruido else 0
        else:
            int_mkg = 0
            ce = 0

        if int_mkg is None:
            threshold = self._masking_calc('aerea', freq, ear, o_n)['real']
        else:
            threshold = self._resolve_masked_threshold('aerea', freq, ear, o_n,
                                                       int_mkg, ce)
        if int_ < threshold:
            self._decay_abort()
            return

        side = 'OD' if ear == 0 else 'OI'
        if cfg.get('fixed_level') and abs(int_ - self.STAT_LEVEL_DB) > self.STAT_LEVEL_TOL:
            # el Stat no se busca subiendo: administrado a otro nivel el
            # paciente oye el tono (está sobre su umbral) pero no se evalúa
            # adaptación, así el alumno no obtiene un resultado que no
            # corresponde al test
            self.decay_timer.stop()
            self._decay_run = {}
            self.upHand()
            debug_print(f"[Stat] {side} {self.frecuency[freq]}Hz: presentado a {int_}dB HL, "
                  f"el test se administra a {self.STAT_LEVEL_DB}dB HL "
                  f"(+-{self.STAT_LEVEL_TOL}); sin resultado válido")
            return

        elapsed_ms = self._decay_elapsed_ms(cfg, command, ear, freq, int_)
        extra = int_ - threshold

        if extra >= decay_total:
            # sostiene el tono el minuto completo a este nivel
            self.decay_timer.stop()
            self.upHand()
            return

        # el hold que sigue se re-arma con el tiempo que QUEDA de esta
        # presentación, no con el minuto entero: un recálculo por mover otra
        # perilla no puede alargarle la vida al tono

        # tiempo que sostiene a este nivel: proporcional a qué tan cerca está
        # de decay_total (no todo-o-nada) -- así el alumno, cronómetro en mano
        # (btn_time_start/stop del audiómetro, o el reloj que tenga: son
        # relojes manuales, nadie los sincroniza con esto), ve que a más dB
        # sostiene más rato y puede calcular la velocidad de deterioro él
        # mismo, en vez de que quede fija en "60s o nada" en cualquier nivel
        # insuficiente. Por eso estos milisegundos tienen que ser tiempo real.
        hold_ms = int(self.DECAY_HOLD_MS * extra / decay_total) - elapsed_ms
        if hold_ms <= 0:
            # el tiempo que este nivel daba ya se consumió (en Rosemberg,
            # además, el minuto siguió corriendo mientras se subía el nivel)
            self.decay_timer.stop()
            self.downHand()
            return

        self.upHand()
        self.decay_timer.start(int(hold_ms))

        if cfg.get('fixed_level'):
            debug_print(f"[Stat] {side} {self.frecuency[freq]}Hz: a {int_}dB HL sostiene "
                  f"~{hold_ms/1000:.1f}s de {self.DECAY_HOLD_MS/1000:.0f}s -> positivo")
            return

        ceiling = min(self.MAX_OUTPUT_DB, self.dbdata['LDL'][freq][ear])
        if int_ >= ceiling:
            # techo (salida máxima o disconfort): este es el último nivel
            # posible, sostiene hold_ms y luego la mano baja para siempre
            debug_print(f"[{cfg['data_key']}] {side} {self.frecuency[freq]}Hz: "
                  f"llega al techo ({ceiling}dB HL), sostiene ~{hold_ms/1000:.1f}s de "
                  f"{self.DECAY_HOLD_MS/1000:.0f}s sin lograr el minuto completo")

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


    def _masking_calc(self, via, frecuency, o_e, o_n, ce=0):
        """
        Rango [mkg_min, mkg_max] de ruido de enmascaramiento valido y umbral
        aparente resultante en cada zona:
        - dentro del rango: umbral real del oido estudiado (bien enmascarado)
        - sobre mkg_max: sobre-enmascarado, no responde (130)
        - bajo mkg_min: sub-enmascarado / sin enmascarar -> "curva sombra":
          el paciente responde por cruce hacia el oido NO estudiado, no por
          su propio umbral real.

        En via osea la atenuacion interaural clinica es ~0dB (a diferencia
        de la via aerea, 35-50dB segun frecuencia), por eso no se usa
        self.attenuations aqui.
        """
        if via == 'aerea':
            uae = self.dbdata['Aerea_mkg'][frecuency][o_e]
            uane = self.dbdata['Aerea_mkg'][frecuency][o_n]
            uoe = self.dbdata['Osea_mkg'][frecuency][o_e]
            uone = self.dbdata['Osea_mkg'][frecuency][o_n]
            at = self.attenuations[frecuency]
            mkg_min = uae - at - uone + uane + ce
            mkg_max = uoe + at
            real = uae
            shadow = min(uae, at + uone)
        elif via == 'osea':
            uoe = self.dbdata['Osea_mkg'][frecuency][o_e]
            uone = self.dbdata['Osea_mkg'][frecuency][o_n]
            uane = self.dbdata['Aerea_mkg'][frecuency][o_n]
            at = 0
            # El auricular con el ruido va en el oido NO estudiado: es ese el
            # que queda ocluido y el que oye mejor el tono oseo cruzado, asi
            # que hace falta mas ruido para taparlo. Evaluarlo en el oido
            # estudiado daba el efecto en el oido equivocado.
            eo = self.oclusive_efect(frecuency, o_n)
            mkg_min = uoe - uone + uane + ce + eo
            # El tono oseo cruza sin atenuacion (at=0), pero el RUIDO se
            # entrega por auricular en el oido no estudiado: para volver a
            # tapar al estudiado tiene que cruzar por via aerea, o sea
            # perdiendo la atenuacion interaural aerea. Usar at=0 aqui daba
            # un maximo igual al umbral oseo del estudiado, casi siempre por
            # debajo del minimo, y el rango terminaba invertido.
            mkg_max = uoe + self.attenuations[frecuency]
            real = uoe
            shadow = min(uoe, uone + at)
        else:
            raise ValueError(f"via desconocida: {via}")

        mkg_lo, mkg_hi = sorted([mkg_min, mkg_max])
        return {'mkg_min': mkg_lo, 'mkg_max': mkg_hi, 'real': real, 'shadow': shadow}

    def _canal_ruido(self, o_n):
        """Canal encendido que esta entregando ruido en el oido `o_n`.

        Devuelve (canal, stim, ce) o None. Antes solo se reconocia el NBN y
        cualquier otro ruido se ignoraba en silencio: el alumno enmascaraba
        con ruido blanco, escuchaba el ruido, y el paciente respondia como si
        no hubiera nada. Ahora enmascaran los cuatro, cada uno con su CE.
        """
        audio = self.data['audio']
        for ch in (0, 1):
            if (audio['stimOn'][ch] and audio['output'][ch] == o_n
                    and audio['stim'][ch] in RUIDOS_ENMASCARANTES):
                stim = audio['stim'][ch]
                return ch, stim, ce_tonal(stim)
        return None

    def _resolve_masked_threshold(self, via, frecuency, o_e, o_n, int_mkg,
                                  ce=0):
        calc = self._masking_calc(via, frecuency, o_e, o_n, ce)
        if calc['mkg_min'] <= int_mkg <= calc['mkg_max']:
            return calc['real']
        elif int_mkg > calc['mkg_max']:
            return 130
        else:
            return calc['shadow']

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
                if any(s in self.data['audio']['stim']
                       for s in RUIDOS_ENMASCARANTES):
                    if self.data['audio']['output'][0] != self.data['audio']['output'][1]:
                        if self.data['audio']['trans'] == [0,0]:
                            o_e = 0 if self.data['audio']['output'][0] == 0 else 1
                            o_n = int(not o_e)
                            ch_tone = 0 if self.data['audio']['stim'][0] == 0 else 1
                            ruido = self._canal_ruido(o_n)
                            if ruido is None:
                                return
                            ch_mkg, _stim, ce = ruido
                            frecuency = self.data['audio']['freq'] #indice
                            int_ = self.data['audio']['int'][ch_tone]
                            int_mkg = self.data['audio']['int'][ch_mkg]
                            threshold = self._resolve_masked_threshold(
                                'aerea', frecuency, o_e, o_n, int_mkg, ce)

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
        At: atenuación interaural (~0 en via osea)
        """
        if self.data['audio']['test'] == 'Umbrales':
            if self.data['audio']['stimOn'].count(True) == 2:
                debug_print(self.data)
                if (any(s in self.data['audio']['stim']
                        for s in RUIDOS_ENMASCARANTES)
                        and 1 in self.data['audio']['trans']):
                    o_e = 0 if self.data['audio']['output'][0] == 0 else 1 #solución parche ya que supone que el oido estudiado es el ch 0
                    o_n = int(not o_e)
                    ch_tone = 0 if self.data['audio']['stim'][0] == 0 else 1   #aca se generaria un problema de inmediato con o_e
                    ruido = self._canal_ruido(o_n)
                    if ruido is None:
                        return
                    ch_mkg, _stim, ce = ruido
                    frecuency = self.data['audio']['freq'] #indice
                    int_ = self.data['audio']['int'][ch_tone]
                    int_mkg = self.data['audio']['int'][ch_mkg]
                    threshold = self._resolve_masked_threshold(
                        'osea', frecuency, o_e, o_n, int_mkg, ce)
                    if threshold <= int_:
                        self.upHand()
                    else:
                        self.downHand()


    def oclusive_efect(self, f:int, o:int)->int:
        """Efecto oclusivo del oido `o`: cuanto mejora su audicion por via
        osea al taparlo con el auricular.

        Ocurre solo en frecuencias graves y solo si ese oido tiene el oido
        medio sano: la oclusion atrapa la energia que normalmente escapa por
        el conducto. Un oido con patologia de transmision ya se comporta como
        ocluido, asi que no gana nada mas (por eso Bing es negativo cuando
        hay gap: es el mismo fenomeno).
        """
        # Indices: 125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000 Hz.
        # Estos son los valores que ensena la docente y se dejan tal cual a
        # proposito. Ojo: la mayoria de las tablas publicadas para supraaural
        # crecen hacia los graves (250 > 500 > 1000) en vez de quedar planas
        # de 125 a 500; queda pendiente preguntarle la fuente antes de
        # tocarlos (ver TODO.md).
        list_values = [15, 15, 15, 10, 0, 0, 0, 0, 0]
        if f >= len(list_values):
            return 0  # alta frecuencia: fuera de la via osea clinica
        value_oclusive = list_values[f]
        uone = self.dbdata['Osea_mkg'][f][o]
        uane = self.dbdata['Aerea_mkg'][f][o]
        gap = uane - uone
        return 0 if gap > 5 else value_oclusive


    def response_aerea_wout_msk(self):
        #aca se debe manejar la situación que esl estudiante no puso el fono en su lugar, ni el vibrador, eso no lo maneja
        if self.data['audio']['test'] == 'Umbrales':
            if self.data['audio']['stimOn'].count(True) == 1:
                stim_on = self.data['audio']['stimOn'].index(True)
                if self.data['audio']['stim'][stim_on] in RUIDOS_ENMASCARANTES:
                    # lo unico encendido es el ruido: lo oye, pero no es el
                    # pitito por el que se le pidio levantar la mano
                    self.downHand()
                    return
                trans = self.data['audio']['trans'][stim_on]
                via = 'aerea' if trans == 0 else 'osea'
                output = self.data['audio']['output'][stim_on] #derecho o izquierdo
                o_n = int(not output)
                frecuency = self.data['audio']['freq'] #indice
                debug_print(frecuency)
                int_ = self.data['audio']['int'][stim_on]
                # sin canal de mkg encendido = ruido de enmascaramiento en 0
                # (submascarado en cuanto haga falta enmascarar -> curva sombra)
                value = self._resolve_masked_threshold(via, frecuency, output, o_n, 0)
                verify = True if int_ >= value else False

                #print(f"la intensidad de estimulación es {int}, el umbral es {value} superaste el umbral {verify}")
                if verify:
                    self.upHand()
                else:
                    self.downHand()

            elif self.data['audio']['stimOn'].count(True) == 2:
                debug_print("escucho en ambos oidos")
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
            debug_print(self.history_command)
        if rol == 'pa_pa_pa':
            debug_print("ahora somos papapa")
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


    
        
