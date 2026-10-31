import copy
import random
import time

from core.helpers import CasesOffline, debug_print
from core.helpers import Preferences
from PySide6.QtCore import QTimer
from audiometria.response_A import Response
from audiometria.h_audio import voz_del_paciente
from audiometria.Fowler import FOWLER_PATTERNS
from audiometria.masking_params import (  # re-export: los usan
    CE_TONAL, RUIDOS_ENMASCARANTES, STIM_FM, STIM_HABLA, STIM_NBN,  # noqa: F401
    STIM_PN, STIM_SN, STIM_TONO, STIM_WN, ce_tonal, es_ruido)  # el panel y los tests
from audiometria.logoaudiometry import CalculateLogo
from audiometria.comandos_voz import PREGUNTAS
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
# Texto que el audiometro pone en lbl_stimOn_chX mientras el canal suena (la
# letra va del color del fondo: no se ve, solo marca el estado). Es la unica
# forma en que este motor se entera de que se prendio o apago un estimulo.
ESTIMULO_ENCENDIDO = "estimulo_encendido"
alternate_time = class_pref.get("alternate_time")
# Estimulos que el paciente reconoce como "el pitito": tono puro y FM (warble)
STIMS_TONO = (STIM_TONO, STIM_FM)

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
        # Carhart enmascarado: la misma prueba, con la instruccion que avisa
        # del ruido en el otro oido. Antes iba al Stenger, que no lleva ruido
        # ni se instruye asi (ver response_stenger).
        'mano_levantada_en_ruido': {
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
    # Niveles del protocolo del laboratorio (2026-10-15, pedido del docente):
    # 100 dB HL en 500 y 2000 Hz, 105 dB HL en 1000 Hz -- los 110 dB SPL de
    # Jerger en fono supraaural --, con ruido blanco a 90 dB en el otro oído.
    # Indice de frecuencia del audiómetro -> dB HL.
    STAT_LEVEL_DB = {2: 100, 3: 105, 4: 100}
    STAT_LEVEL_TOL = 5     # +-5 dB HL: sigue siendo "administrado a nivel"
    STAT_NOISE_MIN_DB = 90  # el protocolo pone el ruido blanco a 90 dB
    # El valor del caso es el deterioro en la escala del Carhart (dB sobre el
    # umbral para sostener el minuto). Desde aca el oido es retrococlear y
    # tampoco sostiene el tono a 100 dB HL: es lo que el Stat busca (Jerger y
    # Jerger 1975). Leerlo como margen sobre el umbral dejaba el Stat negativo
    # en casi todo oido retrococlear: a 100 dB HL sobran 70-85 dB.
    STAT_POSITIVO_DB = 30

    # Instrucciones de umbral: "cada pito que escuche, levante la mano". Las
    # cuatro se responden igual -- el paciente no sabe si el alumno pensaba
    # enmascarar --; lo que cambia la respuesta es lo que suena y por donde.
    UMBRAL = ('colocar_fonos', 'colocar_vibrador', 'aerea_+_ruido', 'vibrador_+_ruido')
    # Instrucciones cuya respuesta se recalcula al mover una perilla con el
    # estimulo sonando (con el tono en continuo, subir el ruido tiene que
    # bajar la mano sin soltar el tono; subir el tono sostenido hasta el LDL
    # tiene que hacerlo hablar).
    RECALCULA = UMBRAL + ('escuche_mi_voz', 'solo_si_molesta', 'pitos_fuertes')
    # "Molesta" se dice una vez por nivel: el pulsado prende y apaga el tono
    # cada medio segundo y lo hacia repetir (cortandose) en cada pulso. Lo
    # vuelve a decir con otro nivel, oido o frecuencia, o si el tono estuvo
    # este rato sin molestarle.
    LDL_REPITE_S = 3
    # Talkback: el dial no esta calibrado; cada marca se toma como 5 dB HL
    # de voz en los fonos (ver docs/decisiones.md).
    TALKBACK_DB_POR_MARCA = 5
    # "¿Está muy fuerte mi voz?": dice que si desde 10 dB bajo su LDL.
    MUY_FUERTE_BAJO_LDL = 10

    def __init__(self,obj_audio):
        super().__init__()
        self.data = {}
        self.other_response = Response()
        # 'output' es el oido (0 OD, 1 OI); 'sim' marca el canal en
        # Simultaneo, que llega a los dos (su 'output' queda en OI para el
        # codigo que solo entiende un oido).
        self.data['audio']={'stimOn': [False, False], 'freq': 3, 'step': 5,
                            'int': [20, 20], 'output': [0, 1],'trans': [0, 0],
                            'stim': [0, 3], 'test':'Umbrales', 'contin':['Continuo', 'Continuo'],
                            'sim': [False, False]}
        # como estaba el equipo al apagar el ultimo estimulo: las preguntas en
        # pasado ("¿en qué oído lo escuchó?") se contestan sobre eso
        self._ultima = None
        self._ldl_dicho = (None, 0.0)   # (que le molesto, cuando)

        self.history_command= []
        self._pregunta = None   # pregunta del Fowler esperando que termine el talkback
        self.obj_audio = obj_audio
        self.mano = False
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
        self._logo = None   # el del SDT, se arma al primer uso (_detecta_sdt)
        self.other_response.voz = voz_del_paciente(dbdata)
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
            instruccion = self._instruccion()
            if instruccion in self.UMBRAL:
                # con o sin ruido, en cualquier canal: ver response_umbral
                self.response_umbral()
            elif instruccion in self.DECAY_TESTS:
                self.response_tone_decay(instruccion)
            elif instruccion == 'pitos_fuertes':
                self.ldl()
            elif instruccion == 'solo_si_molesta':
                self.ldl(con_la_mano=True)
            elif instruccion == 'dos_pitos':
                self.fowler()
            elif instruccion == 'cambie_de_volumen':
                # prender el tono portador no es un incremento: el
                # paciente responde recien cuando se sube la intensidad
                pass
            elif instruccion == 'escuche_mi_voz':
                self.response_sdt()
            elif instruccion is None:
                debug_print("no has dado comando alguno")
        else:
            pass
        if not any(self.data["audio"]['stimOn']):
            self.downHand()

    def _instruccion(self):
        """La ultima instruccion dada, saltando las preguntas: antes la
        pregunta pasaba a ser el comando vigente y tras "¿Me escucha?" el
        paciente dejaba de responder a los tonos."""
        for rol in self.history_command:
            if rol not in PREGUNTAS:
                return rol
        return None

    def set_config(self, data):
        debug_print("cambio el sender")
        name = data.objectName()
        str_ = data.text()
        name = name.split('_')

        if 'ch0' in name or 'ch1' in name:
            channel = 0 if name[-1] == 'ch0' else 1

        instruccion = self._instruccion()
        if 'int' in name:
            value = str_.split(' ')
            old_int = self.data['audio']['int'][channel]
            self.data['audio']['int'][channel] = int(value[0])
            if instruccion == 'cambie_de_volumen':
                self.response_sisi(channel, int(value[0]) - old_int)
        elif 'trans' in name:
            value = trans_list.index(str_)
            self.data['audio']['trans'][channel] = value
        elif 'output' in name:
            value = 0 if str_ == 'Derecha' else 1
            self.data['audio']['output'][channel] = value
            self.data['audio'].setdefault('sim', [False, False])[channel] = (
                str_ == output_list[2])
        elif 'stim' in name:
            value = stim_list.index(str_)
            self.data['audio']['stim'][channel] = value
        elif 'stimOn' in name:
            value = str_ == ESTIMULO_ENCENDIDO
            if not value and self.data['audio']['stimOn'][channel]:
                self._ultima = copy.deepcopy(self.data['audio'])
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

        if 'stimOn' not in name and instruccion in self.DECAY_TESTS:
            # cualquier cambio del equipo mientras corre un deterioro tonal lo
            # recalcula: subir el tono, mover el ruido contralateral, cambiar
            # de oído o de frecuencia. ('stimOn' no entra porque ya pasó por
            # response_(), que rutea a la prueba que corresponda.)
            self.response_tone_decay(instruccion)
        elif (instruccion in self.RECALCULA and any(self.data['audio']['stimOn'])
              and any(k in name for k in ('int', 'output', 'trans', 'freq'))):
            # mover una perilla con el estimulo sonando: el paciente responde
            # a lo que suena ahora, no a lo que sonaba al encenderlo
            self.response_()

        #print(self.data['audio'])

        #print(f'nombre: {data.objectName()} str:  {data.text()}')
        #print(self.data['audio']['stimOn'])


    def response_sdt(self):
        """Mano levantada del SDT: la voz en un canal y, si hay, un ruido en
        el otro, al otro oído. Lo decide CalculateLogo.detecta_sdt, el mismo
        modelo de las dos vías que las palabras (antes había uno propio acá:
        solo aceptaba Speech Noise y con ruido de más dejaba de responder de
        golpe)."""
        if self.data['audio']['test'] != 'Logoaudiometría':
            return
        audio = self.data['audio']
        encendidos = [ch for ch in (0, 1) if audio['stimOn'][ch]]
        habla = [ch for ch in encendidos if audio['stim'][ch] == STIM_HABLA]
        if len(habla) != 1:
            self.downHand()
            return
        ch = habla[0]
        int_mkg, stim_mkg = 0, None
        otro = [c for c in encendidos if c != ch]
        if otro:
            c = otro[0]
            if not es_ruido(audio['stim'][c]) or audio['output'][c] == audio['output'][ch]:
                # un tono, o el ruido en el mismo oído: no es un SDT
                self.downHand()
                return
            int_mkg, stim_mkg = audio['int'][c], audio['stim'][c]
        if self._detecta_sdt(audio['output'][ch], audio['int'][ch], int_mkg, stim_mkg):
            self.upHand()
        else:
            self.downHand()

    def _detecta_sdt(self, side, int_, int_mkg=0, stim_mkg=None):
        if self._logo is None:
            self._logo = CalculateLogo(self.dbdata, self.dbdata.get('UMD'))
        return self._logo.detecta_sdt(side, int_, int_mkg, stim_mkg)

    def ldl(self, con_la_mano=False):
        """LDL: el tono llega a su nivel de molestia. Con "pitos fuertes" lo
        dice; con "solo si molesta" levanta la mano (y la baja si no)."""
        if self.data['audio']['test'] != 'Umbrales':
            return
        a = self.data['audio']
        molestos = [ch for ch in self._tonos_encendidos() if self._le_molesta(ch)]
        if con_la_mano:
            if molestos:
                self.upHand()
            else:
                self.downHand()
            return
        if not molestos:
            return
        clave = tuple((a['freq'], a['int'][ch], tuple(self._oidos(ch))) for ch in molestos)
        ahora = time.monotonic()
        anterior, cuando = self._ldl_dicho
        self._ldl_dicho = (clave, ahora)
        if clave != anterior or ahora - cuando > self.LDL_REPITE_S:
            self.other_response.create_voice_('molesta')

    def _le_molesta(self, ch, a=None):
        """El canal `ch` suena a su LDL o mas en algun oido al que llega."""
        a = a or self.data['audio']
        return any(a['int'][ch] >= self.dbdata['LDL'][a['freq']][o]
                   for o in self._oidos(ch, a))

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
          A nivel, un deterioro de STAT_POSITIVO_DB o más (retrococlear) lo
          pierde antes del minuto; con menos, solo si a 100 dB HL no le
          alcanza el margen sobre el umbral. Si el nivel llega a su LDL, dice
          que le molesta y no hay resultado.
        """
        cfg = self.DECAY_TESTS[command]
        stim_on = self._tone_channel()
        if stim_on is None:
            self._decay_abort()
            return

        continuo = self.data['audio']['contin'][stim_on] == 'Continuo'
        via_aerea = self.data['audio']['trans'][stim_on] == 0
        if not (continuo and via_aerea) or self._binaural(stim_on):
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
                        and self._llega_a(other, o_n)
                        and self.data['audio']['stim'][other] == STIM_WN)
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
        nivel_stat = self.STAT_LEVEL_DB.get(freq, 100)
        if cfg.get('fixed_level') and abs(int_ - nivel_stat) > self.STAT_LEVEL_TOL:
            # el Stat no se busca subiendo: administrado a otro nivel el
            # paciente oye el tono (está sobre su umbral) pero no se evalúa
            # adaptación, así el alumno no obtiene un resultado que no
            # corresponde al test
            self.decay_timer.stop()
            self._decay_run = {}
            self.upHand()
            debug_print(f"[Stat] {side} {self.frecuency[freq]}Hz: presentado a {int_}dB HL, "
                  f"el test se administra a {nivel_stat}dB HL "
                  f"(+-{self.STAT_LEVEL_TOL}); sin resultado válido")
            return

        if cfg.get('fixed_level') and int_ >= self.dbdata['LDL'][freq][ear]:
            # el nivel del Stat le molesta (llega a su LDL): lo dice y en esa
            # frecuencia la prueba no se hace. Mirar el LDL antes es parte
            # del protocolo
            self.decay_timer.stop()
            self._decay_run = {}
            self.upHand()
            self.other_response.create_voice_('molesta')
            debug_print(f"[Stat] {side} {self.frecuency[freq]}Hz: {int_}dB HL llega al LDL "
                  f"({self.dbdata['LDL'][freq][ear]}dB HL); le molesta, sin resultado")
            return

        elapsed_ms = self._decay_elapsed_ms(cfg, command, ear, freq, int_)
        extra = int_ - threshold
        # Stat en oido retrococlear: no lo sostiene a 100 dB HL por mucho que
        # sobre margen sobre el umbral (ver STAT_POSITIVO_DB)
        stat_retro = (cfg.get('fixed_level')
                      and decay_total >= self.STAT_POSITIVO_DB)

        if extra >= decay_total and not stat_retro:
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
        frac = extra / decay_total
        if stat_retro:
            # cuanto mas deterioro, antes se pierde: 30 dB lo sostiene ~30 s,
            # 60 dB ~15 s. El hallazgo es no llegar al minuto, no el segundo
            # exacto
            frac = min(frac, self.STAT_POSITIVO_DB / (2 * decay_total))
        hold_ms = int(self.DECAY_HOLD_MS * frac) - elapsed_ms
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

    def _es_stenger(self):
        """El mismo tono, por vía aérea, en los dos oídos a la vez."""
        a = self.data['audio']
        return (a['test'] == 'Umbrales'
                and a['stimOn'] == [True, True]
                and a['stim'][0] == a['stim'][1] and a['stim'][0] in (0, 1)
                and a['trans'] == [0, 0]
                and a['output'][0] != a['output'][1])

    def _umbral_verdadero(self, freq, ear):
        """Umbral aéreo con el que el oído oye de verdad.

        El caso guarda el umbral que el paciente DA. En un oído orgánico es
        el mismo; en uno marcado 'Stenger' (pérdida no orgánica) es el que
        finge, y el verdadero no está en el caso: se toma el del otro oído
        (pérdida unilateral fingida en alguien que oye parejo), sin pasar
        del que da. Con los dos marcados no hay oído de referencia y se usa
        el que da (el Stenger necesita asimetría)."""
        dado = self.dbdata['Aerea_mkg'][freq]
        stenger = self.dbdata.get('Stenger') or [False, False]
        if stenger[ear] and not stenger[1 - ear]:
            return min(dado[ear], dado[1 - ear])
        return dado[ear]

    def response_stenger(self):
        """Stenger: el mismo tono en los dos oídos a la vez.

        Principio de Stenger: de dos tonos iguales y simultáneos se percibe
        solo el de mayor nivel de sensación, medido contra los umbrales
        VERDADEROS, y se oye en ese oído. Técnica clásica: 10 dB sobre el
        umbral del oído bueno y 10 dB bajo el que el paciente dio en el malo.

        - Pérdida orgánica: el tono del oído malo queda bajo su umbral real,
          se oye el del bueno y levanta la mano -> Stenger negativo.
        - Pérdida no orgánica: el tono del oído "malo" tiene más nivel de
          sensación, se oye solo en ese oído y, como finge no oír por ahí
          a ese nivel, no levanta la mano aunque el del bueno sea audible
          -> Stenger positivo.
        """
        if not self._es_stenger():
            return
        a = self.data['audio']
        freq = a['freq']
        nivel = [0, 0]
        for ch in (0, 1):
            nivel[a['output'][ch]] = a['int'][ch]
        sl = [nivel[o] - self._umbral_verdadero(freq, o) for o in (0, 1)]
        if max(sl) < 0:
            self.downHand()  # no oye ninguno de los dos
            return
        if sl[0] == sl[1]:
            self.upHand()    # mismo nivel de sensación: lo oye al centro
            return
        percibe = 0 if sl[0] > sl[1] else 1
        stenger = self.dbdata.get('Stenger') or [False, False]
        dado = self.dbdata['Aerea_mkg'][freq][percibe]
        if stenger[percibe] and nivel[percibe] < dado:
            # lo oye solo en el oído en que dice no oír a ese nivel
            self.downHand()
        else:
            self.upHand()

    def response_sisi(self, channel, delta):
        """SISI: con el tono portador sonando, cada subida de intensidad es
        un incremento y el paciente dice "si" si lo nota. Se decide por el
        tamano del salto, sin importar si el alumno esta familiarizando o
        midiendo -- el paciente no sabe en que etapa esta:
        - 5 dB o mas (familiarizacion): lo nota siempre.
        - 1 dB (la prueba): lo nota con el % SISI del caso.
        - entre medio (paso de 3 dB): interpolado entre ambos.
        Bajar la intensidad (volver al portador) no se responde, y un tono
        bajo el umbral no deja oir ningun incremento."""
        if delta <= 0 or self.data['audio']['test'] != 'Umbrales':
            return
        if self._tone_channel() != channel or self._binaural(channel):
            return
        output = self.data['audio']['output'][channel]
        freq = self.data['audio']['freq']
        if self.data['audio']['int'][channel] - delta < self.aerea[output][freq]:
            return
        if delta >= self.STEP_DB:
            pct = 100
        else:
            base = self.dbdata.get('SISI', [0, 0])[output]
            pct = base + (100 - base) * (delta - 1) / (self.STEP_DB - 1)
        if random.random() * 100 < pct:
            self.other_response.create_voice_('si')

    def _masking_calc(self, via, frecuency, o_e, o_n, ce=0):
        """
        Rango [mkg_min, mkg_max] de ruido de enmascaramiento valido, umbral
        real, curva sombra (umbral por cruce sin ruido) y los valores sin
        ordenar. Lo que mide el alumno con cada nivel de ruido lo arma
        _resolve_masked_threshold: sombra que sube dB a dB bajo el minimo,
        el real en la meseta y el real corrido dB a dB sobre el maximo.

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
            cruce = at + uone
            shadow = min(uae, cruce)
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
            cruce = uone + at
            shadow = min(uoe, cruce)
        else:
            raise ValueError(f"via desconocida: {via}")

        mkg_lo, mkg_hi = sorted([mkg_min, mkg_max])
        # Los valores SIN ordenar quedan para _resolve_masked_threshold: con
        # el dilema (mínimo sobre el máximo) el rango ordenado lo esconde.
        return {'mkg_min': mkg_lo, 'mkg_max': mkg_hi, 'real': real, 'shadow': shadow,
                'cruce': cruce, 'minimo': mkg_min, 'maximo': mkg_max}

    def _canal_ruido(self, o_n):
        """Canal encendido que esta entregando ruido en el oido `o_n`.

        Devuelve (canal, stim, ce) o None. Antes solo se reconocia el NBN y
        cualquier otro ruido se ignoraba en silencio: el alumno enmascaraba
        con ruido blanco, escuchaba el ruido, y el paciente respondia como si
        no hubiera nada. Ahora enmascaran los cuatro, cada uno con su CE.
        """
        audio = self.data['audio']
        for ch in (0, 1):
            if (audio['stimOn'][ch] and self._llega_a(ch, o_n)
                    and audio['stim'][ch] in RUIDOS_ENMASCARANTES):
                stim = audio['stim'][ch]
                return ch, stim, ce_tonal(stim)
        return None

    def _binaural(self, ch, a=None):
        """El canal suena en los dos oidos: Simultaneo o campo libre."""
        a = a or self.data['audio']
        return a.get('sim', [False, False])[ch] or a['trans'][ch] == 2

    def _llega_a(self, ch, oido, a=None):
        """El estimulo del canal `ch` llega al oido `oido`: por su fono, o a
        los dos si va en Simultaneo, por campo libre o por vibrador (en via
        osea la atenuacion interaural es ~0)."""
        a = a or self.data['audio']
        return (a['output'][ch] == oido or self._binaural(ch, a)
                or a['trans'][ch] == 1)

    def _oidos(self, ch, a=None):
        return [o for o in (0, 1) if self._llega_a(ch, o, a)]

    def _ruido_en(self, oido, a=None, excluir=None):
        """(nivel, CE) del ruido encendido que llega a `oido`, o (0, 0)."""
        a = a or self.data['audio']
        for ch in (0, 1):
            if (ch != excluir and a['stimOn'][ch] and self._llega_a(ch, oido, a)
                    and a['stim'][ch] in RUIDOS_ENMASCARANTES):
                return a['int'][ch], ce_tonal(a['stim'][ch])
        return 0, 0

    def _resolve_masked_threshold(self, via, frecuency, o_e, o_n, int_mkg,
                                  ce=0):
        """Umbral que mide el alumno con `int_mkg` de ruido en el oído no estudiado.

        El paciente contesta por el camino que primero oye el tono, así que
        el umbral es el menor de dos:

        - por el oído estudiado: su umbral real, que sube dB a dB cuando el
          ruido pasa el máximo (sobreenmascaramiento: el ruido cruza y lo tapa);
        - por cruce al oído no estudiado: la curva sombra, que sube dB a dB
          desde que el ruido empieza a tapar ese oído (subenmascaramiento).

        Entre el mínimo y el máximo gana el umbral real: la meseta del método
        de Hood. Antes era una escalera de tres peldaños (sombra fija, real,
        130) y el plateau se veía como un salto. Con el mínimo sobre el máximo
        no hay ruido que dé el umbral real: el dilema, sin programarlo aparte.
        """
        return min(130, *self._caminos(via, frecuency, o_e, o_n, int_mkg, ce))

    def _caminos(self, via, frecuency, o_e, o_n, int_mkg, ce=0):
        """(por_cruce, por_estudiado): el umbral por cada camino que puede
        tomar el tono (ver _resolve_masked_threshold)."""
        calc = self._masking_calc(via, frecuency, o_e, o_n, ce)
        real, cruce = calc['real'], calc['cruce']
        # El ruido empieza a tapar el oído no estudiado en `inicio`: el mínimo
        # es justo el nivel en que el cruce sube hasta el umbral real.
        inicio = calc['minimo'] - (real - cruce)
        por_cruce = cruce + max(0, int_mkg - inicio)
        por_estudiado = real + max(0, int_mkg - calc['maximo'])
        return por_cruce, por_estudiado

    def _percepcion(self, ch, a=None):
        """Por que oido oye el tono del canal `ch`: [(nivel de sensacion,
        oido)] de cada camino que lo deja oir, vacio si no lo oye.

        El oido estudiado y el que no se estudia salen del canal del TONO, no
        del numero de canal: antes se suponia el tono en el canal 0 y con el
        ruido en el 0 y el tono en el 1 el paciente no respondia nunca.

        - Monoaural: el tono llega por su oido (umbral real) o cruza al otro
          (curva sombra); el ruido que llega al otro oido corre la sombra y,
          pasado el maximo, tambien el real (_caminos). Un ruido en el MISMO
          oido no enmascara al otro: tapa el tono ahi mismo, hasta su nivel
          efectivo (el del dial menos su CE).
        - Binaural (Simultaneo, campo libre): cada oido con su umbral real,
          tapado por el ruido que le llegue.
        """
        a = a or self.data['audio']
        f = a['freq']
        int_ = a['int'][ch]
        via = 'osea' if a['trans'][ch] == 1 else 'aerea'
        if self._binaural(ch, a):
            tabla = self.dbdata['Osea_mkg' if via == 'osea' else 'Aerea_mkg'][f]
            caminos = []
            for o in (0, 1):
                nivel, ce = self._ruido_en(o, a, excluir=ch)
                caminos.append((int_ - max(tabla[o], nivel - ce), o))
            return [c for c in caminos if c[0] >= 0]
        o_e = a['output'][ch]
        o_n = 1 - o_e
        nivel_n, ce_n = self._ruido_en(o_n, a, excluir=ch)
        por_cruce, por_estudiado = self._caminos(via, f, o_e, o_n, nivel_n, ce_n)
        nivel_e, ce_e = self._ruido_en(o_e, a, excluir=ch)
        if nivel_e:
            por_estudiado = max(por_estudiado, nivel_e - ce_e)
        caminos = [(int_ - min(130, por_estudiado), o_e), (int_ - min(130, por_cruce), o_n)]
        return [c for c in caminos if c[0] >= 0]

    def _oye_tono(self, ch, a=None):
        return bool(self._percepcion(ch, a))

    def _tonos_encendidos(self, a=None):
        a = a or self.data['audio']
        return [ch for ch in (0, 1) if a['stimOn'][ch] and a['stim'][ch] in STIMS_TONO]

    def response_umbral(self):
        """Umbrales por via aerea u osea, con o sin ruido: el paciente levanta
        la mano si oye el tono, por el camino que sea (ver _percepcion).

        minimo: UAE - AT - UONE + UANE + CE      (aerea)
                (UOE - UONE) + UANE + CE + EO    (osea)
        maximo: UOE + AT

        UAE/UOE: umbral aereo/oseo estudiado; UANE/UONE: aereo/oseo no
        estudiado; AT: atenuacion interaural; CE: coeficiente de
        enmascaramiento; EO: efecto de oclusion.
        """
        a = self.data['audio']
        if a['test'] != 'Umbrales' or not any(a['stimOn']):
            return
        tonos = self._tonos_encendidos()
        if not tonos:
            # lo unico encendido es el ruido: lo oye, pero no es el pitito
            # por el que se le pidio levantar la mano
            self.downHand()
            return
        if len(tonos) == 2 and self._es_stenger():
            # el Stenger se instruye como los umbrales: lo que lo distingue
            # es el mismo tono en los dos oidos a la vez
            self.response_stenger()
            return
        if any(self._oye_tono(ch) for ch in tonos):
            self.upHand()
        else:
            self.downHand()

    # Nombres viejos: las cuatro instrucciones de umbral pasan por el mismo
    # motor (antes cada una suponia el tono en un canal fijo).
    response_aerea_w_msk = response_umbral
    response_osea_w_msk = response_umbral
    response_aerea_wout_msk = response_umbral

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


    def Action(self, action):
        t,p,m = action.split('_')
        if t in ['THR', 'S', 'L']:
            MKG = m == 'MKG'
            self.response = (t, p, MKG)
        self.state = (t,p,m)
        
    def rol_player(self, rol):
        if rol != 'pa_pa_pa':
            # largo de sobra: las preguntas quedan en la historia pero no
            # pueden empujar afuera la instruccion vigente (_instruccion)
            max_list = 12
            self.history_command.insert(0, rol)
            while len(self.history_command) > max_list:
                self.history_command.pop()
            debug_print(self.history_command)
        if rol == 'pa_pa_pa':
            debug_print("ahora somos papapa")
        if rol == 'dictar_palabras':
            pass
            #self.obj_audio()
        # Las preguntas se contestan cuando el talkback termina de decirlas
        # (talkback_termino): antes el "sí" del Fowler salía encima de la
        # pregunta, y las demás no se contestaban.
        self._pregunta = rol if rol in PREGUNTAS else None

    # Pausa del paciente entre el fin de la pregunta y su respuesta, en ms.
    PAUSA_RESPUESTA_MS = (400, 900)

    def talkback_termino(self):
        """Terminó lo que decía el talkback: si era una pregunta, contesta
        tras una pausa, con lo que esté sonando entonces."""
        pregunta, self._pregunta = self._pregunta, None
        if pregunta is None:
            return
        QTimer.singleShot(random.randint(*self.PAUSA_RESPUESTA_MS),
                          lambda: self.contestar(pregunta))

    def contestar(self, pregunta):
        """Contesta una pregunta del talkback con lo que este sonando (o con
        lo ultimo que sono, si ya no suena nada)."""
        fowler = pregunta == 'sonidos_iguales' or (
            pregunta == 'en_qué_oído' and self._instruccion() == 'dos_pitos')
        if fowler:
            self.other_response.fowler_q(1 if pregunta == 'sonidos_iguales' else 2,
                                         self.data)
            return
        respuesta = self.respuesta_a(pregunta)
        debug_print(f"[pregunta] {pregunta} -> {respuesta}")
        if respuesta is not None:
            self.other_response.create_voice_(respuesta)

    def respuesta_a(self, pregunta):
        """Lo que dice el paciente ('si', 'no', 'molesta', 'elderecho',
        'elizquierdo') o None si calla. Los textos estan en
        scripts/voces_comandos.py."""
        actual = self.data['audio']
        pasado = actual if any(actual['stimOn']) else (self._ultima or actual)
        if pregunta == 'escucha':                       # ¿Me escucha?
            return 'si' if self._oye_talkback() else None
        if pregunta in ('molesta', 'muy_fuerte'):       # ... mi voz
            if not self._oye_talkback():
                return None
            margen = self.MUY_FUERTE_BAJO_LDL if pregunta == 'muy_fuerte' else 0
            return 'si' if self._talkback_db() >= self._ldl_voz() - margen else 'no'
        if pregunta == 'dejo_de_escuchar':              # ¿Lo dejó de escuchar?
            tonos = self._tonos_encendidos()
            if not tonos:
                return 'si'
            if self._instruccion() in self.DECAY_TESTS:
                # en el deterioro tonal la mano es lo que percibe
                return 'no' if self.mano else 'si'
            return 'no' if any(self._oye_tono(ch) for ch in tonos) else 'si'
        if pregunta == 'en_qué_oído':                   # ¿En qué oído...?
            caminos = [c for ch in self._tonos_encendidos(pasado)
                       for c in self._percepcion(ch, pasado)]
            if not caminos:
                return 'no'
            return ('elderecho', 'elizquierdo')[max(caminos)[1]]
        if pregunta == 'molesto_o':                     # ¿Le molestó, o fuerte?
            encendidos = [ch for ch in (0, 1) if pasado['stimOn'][ch]]
            return ('molesta' if any(self._le_molesta(ch, pasado) for ch in encendidos)
                    else 'no')
        if pregunta == 'no_entiende':                   # ¿Escucha, pero no entiende?
            return self._no_entiende(pasado)
        return None

    def _talkback_db(self):
        dial = getattr(self.obj_audio, 'dial_talkback', None)
        if dial is None:
            return None
        return dial.value() * self.TALKBACK_DB_POR_MARCA

    def _oye_talkback(self):
        """Oye la voz del evaluador por los fonos: con el mejor oido."""
        nivel = self._talkback_db()
        if nivel is None:
            return True
        return nivel >= min(self.dbdata.get('SDT', [0, 0]))

    def _ldl_voz(self):
        """LDL para la voz: el promedio de 500-2000 Hz del oido mas
        sensible (la voz llega a los dos fonos)."""
        ldl = self.dbdata['LDL']
        return min(sum(ldl[f][o] for f in (2, 3, 4)) / 3 for o in (0, 1))

    def _no_entiende(self, a):
        """Con palabras sonando: 'si' si las detecta pero estan bajo su SRT,
        'no' si las entiende o si ni las oye. Sin palabras, por el talkback."""
        habla = [ch for ch in (0, 1) if a['stimOn'][ch] and a['stim'][ch] == STIM_HABLA]
        if not habla:
            return 'no' if self._oye_talkback() else None
        ch = habla[0]
        side, int_ = a['output'][ch], a['int'][ch]
        if not self._detecta_sdt(side, int_):
            return 'no'
        return 'si' if int_ < self.dbdata['SRT'][side] else 'no'

 
                
        
    def upHand(self):
        self._mano(True)

    def downHand(self):
        self._mano(False)

    def _mano(self, arriba):
        """Levanta o baja la mano del paciente y, si cambió, lo registra:
        es lo que vio el alumno, y el backend no tiene que recalcularlo."""
        color = '170, 170, 255' if arriba else '255, 255, 255'
        self.obj_audio.lbl_response.setStyleSheet(f'background-color: rgb({color});')
        if arriba != self.mano:
            self.mano = arriba
            log = getattr(self.obj_audio, "_log", None)
            if log is not None:
                log("audio_respuesta", mano=arriba)


    
        
