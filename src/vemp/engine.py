"""
Motor del VEMP: de los parámetros del equipo a la traza que se ve crecer.

La diferencia de fondo con el generador anterior es que acá SE PROMEDIAN
BARRIDOS de verdad. Antes había una curva "objetivo" y un factor de
crecimiento que la iba revelando: la promediación era una animación y daba
lo mismo pedir 60 barridos que 600. Acá cada tick genera un lote de
barridos con su propio ruido, el equipo acepta o rechaza cada uno, y la
curva que se dibuja es el promedio acumulado de los aceptados. De ahí salen
solas tres cosas que antes había que fingir:

- el ruido baja con la raíz de los barridos aceptados,
- un barrido rechazado no mejora nada (y con el músculo fuera de banda se
  rechazan casi todos: el examen corre y la curva no limpia),
- pedir más barridos cuesta tiempo real, a la tasa de estímulo elegida.

La otra diferencia es la amplitud. La normativa describe la respuesta con
el músculo contraído a `protocol.EMG_REFERENCIA`; acá la respuesta CRUDA se
escala con el EMG real del paciente, así que la única amplitud comparable
entre dos registros es la CORREGIDA (cruda / EMG). Es la métrica del examen
y ahora sale del modelo, no de una convención de la tabla.
"""

import math
from dataclasses import dataclass, field

import numpy as np

from core import dsp
from vemp import patient, protocol
from vemp.norms import normativa as _normativa


@dataclass
class Ajustes:
    """Lo que el equipo tiene puesto en el momento de registrar."""
    subtipo: str = protocol.CVEMP
    lado: str = 'OD'
    transductor: str = protocol.AEREO
    freq: str = '500 Hz'
    polaridad: str = 'Rarefacción'
    intensidad: int = 100
    tasa: float = 5.1
    promedios: int = 200
    filtro_alto: float = 10.0      # pasa-alto (Hz)
    filtro_bajo: float = 1500.0    # pasa-bajo (Hz)
    rechazo: float = 4.0           # nivel de rechazo de artefactos
    maniobra: str = ''

    def copia(self):
        return Ajustes(**self.__dict__)

    def clave_registro(self):
        """Qué hace que dos curvas sean "la misma condición" (para la serie
        de umbral y la de sintonía)."""
        return (self.subtipo, self.lado, self.transductor, self.freq)


@dataclass
class Lote:
    """Un tick de promediación ya resuelto."""
    promedio: np.ndarray
    aceptados: int
    rechazados: int
    emg: float
    info: dict = field(default_factory=dict)


# Ruido de fondo de un barrido, como múltiplo del EMG tónico rectificado.
# El cuello registra el músculo entero y es ruidosísimo; bajo el ojo el
# electrodo toma mucho menos.
RUIDO_POR_EMG = {protocol.CVEMP: 2.2, protocol.OVEMP: 1.1, protocol.MVEMP: 2.0}

# Probabilidad de que un barrido traiga un artefacto grande (parpadeo,
# deglución, movimiento). El oVEMP vive al lado del párpado.
ARTEFACTO_BASE = {protocol.CVEMP: 0.05, protocol.OVEMP: 0.12, protocol.MVEMP: 0.06}

# Techo de la ganancia por contracción: contraer más sube la respuesta,
# pero el músculo satura (y el ruido sigue subiendo igual).
GANANCIA_EMG_MAX = 1.7

# Cuánto pierde la respuesta por encima de 5/s de tasa de estímulo.
CAIDA_POR_TASA = 0.012
CAIDA_POR_TASA_MIN = 0.75

# Un oído con sintonía invertida (umbral muy bajo) no solo responde en
# agudos: responde MÁS grande que la normativa.
GANANCIA_SINTONIA_INVERTIDA = 1.8

# Qué fracción de la amplitud normativa queda justo en el umbral. Es lo que
# hace que el umbral sea un punto y no un borde: ahí todavía hay algo.
UMBRAL_FRACCION = 0.08


class MotorVemp:
    """Genera los barridos de UN paciente."""

    def __init__(self, caso, norma=None, rng=None):
        self.caso = caso
        self.norma = norma or _normativa()
        self.rng = rng or np.random.default_rng()

    # ------------------------------------------------------------------
    # Eje
    # ------------------------------------------------------------------

    @staticmethod
    def eje(subtipo):
        inicio, fin = protocol.VENTANA.get(subtipo, protocol.VENTANA[protocol.CVEMP])
        return np.linspace(inicio, fin, protocol.N_PUNTOS)

    @staticmethod
    def _fs(subtipo):
        inicio, fin = protocol.VENTANA.get(subtipo, protocol.VENTANA[protocol.CVEMP])
        return protocol.N_PUNTOS / ((fin - inicio) / 1000.0)

    # ------------------------------------------------------------------
    # Respuesta esperada
    # ------------------------------------------------------------------

    def picos(self, ajustes, emg_uv):
        """{pico: {'lat','amp'}} de la respuesta de ESTE paciente, con la
        amplitud ya escalada por la contracción real.

        Devuelve además el umbral usado y la ganancia, que son lo que el
        panel de estado necesita para explicar por qué no hay respuesta.
        """
        subtipo = ajustes.subtipo
        oido = self.caso.oido(ajustes.lado) if self.caso else None
        base = self.norma.baseline(self.caso.poblacion if self.caso else 'adult_female',
                                   subtipo, ajustes.freq)
        if oido is None:
            return {}, {}

        umbral = oido.umbral(subtipo, ajustes.transductor, ajustes.freq)
        sl = ajustes.intensidad - umbral
        ganancia = self._ganancia_sl(sl)
        if oido.sintonia_invertida(subtipo):
            ganancia *= GANANCIA_SINTONIA_INVERTIDA

        ganancia *= self._factor_tasa(ajustes.tasa)
        ganancia_emg = min(emg_uv / protocol.EMG_REFERENCIA[subtipo], GANANCIA_EMG_MAX)

        caso_sub = oido.subtipos.get(subtipo)
        mods = self.norma.modificadores_patologia(oido.tipo)
        picos = {}
        nombres = protocol.PEAKS[subtipo]
        for i, pico in enumerate(nombres):
            valores = base.get(pico)
            if not valores:
                continue
            lat = valores['lat'] + self._corrimiento_latencia(ajustes.intensidad)
            amp = abs(valores['amp']) * ganancia

            lat_pat, factor_pat = self._patologia(oido.tipo, subtipo, pico, i, nombres, mods)
            lat += lat_pat
            amp *= factor_pat

            if caso_sub is not None:
                lat += caso_sub.desviacion(pico, 'lat')
                amp += caso_sub.desviacion(pico, 'amp')

            amp = max(amp, 0.0) * ganancia_emg
            picos[pico] = {'lat': lat, 'amp': amp * protocol.signo_pico(pico)}

        info = {
            'umbral': umbral,
            'sl': sl,
            'ganancia': ganancia,
            'ganancia_emg': ganancia_emg,
            'patologia': oido.tipo,
            'gap': oido.gap_db(ajustes.freq),
            'p2p_normativo': self.norma.pico_a_pico(base),
        }
        return picos, info

    @staticmethod
    def _ganancia_sl(sl):
        """Crecimiento de la respuesta sobre el umbral.

        Por encima del umbral crece rápido y satura a `SL_SATURACION_DB`; por
        debajo cae exponencial, no se apaga de golpe --así el alumno ve la
        respuesta achicarse mientras baja la intensidad, que es como se
        busca un umbral.
        """
        if sl >= 0:
            # En el umbral la respuesta existe pero es chica (8% de la
            # normativa) y crece más rápido que lineal hasta saturar: con una
            # recta, un oído al que le faltan 5 dB para el umbral ya medía un
            # tercio de lo normal y la serie no mostraba ningún umbral.
            fraccion = min(sl / protocol.SL_SATURACION_DB, 1.0)
            return max(UMBRAL_FRACCION, fraccion ** 1.3)
        return UMBRAL_FRACCION * math.exp(sl / 6.0)

    @staticmethod
    def _corrimiento_latencia(intensidad):
        pasos = (protocol.INTENSIDAD_REFERENCIA - intensidad) / 10.0
        return pasos * protocol.PENDIENTE_LAT_MS_10DB

    @staticmethod
    def _factor_tasa(tasa):
        return max(CAIDA_POR_TASA_MIN, 1.0 - CAIDA_POR_TASA * max(0.0, tasa - 5.0))

    @staticmethod
    def _patologia(tipo, subtipo, pico, indice, nombres, mods):
        """(corrimiento de latencia, factor de amplitud) del cuadro del oído.

        Qué VEMP toca cada patología es anatomía y no elección del docente:
        el sáculo lo mide el cVEMP (y el mVEMP, que cuelga de la misma vía),
        el utrículo el oVEMP, y una lesión del nervio los baja a los dos.
        """
        if tipo == 'sacular' and subtipo in (protocol.CVEMP, protocol.MVEMP):
            if pico == 'p13':
                return (mods.get('cvemp_p13_lat_prolongation_ms', 1.5),
                        mods.get('cvemp_p13_amp_reduction', 0.25))
            return 0.0, mods.get('cvemp_n23_amp_reduction', 0.30)
        if tipo == 'utricular' and subtipo == protocol.OVEMP:
            if pico == 'n10':
                return (mods.get('ovemp_n10_lat_prolongation_ms', 1.2),
                        mods.get('ovemp_n10_amp_reduction', 0.20))
            return 0.0, mods.get('ovemp_p16_amp_reduction', 0.25)
        if tipo == 'neural':
            lat = mods.get('interpeak_prolongation_ms', 1.5) if indice == len(nombres) - 1 else 0.0
            return lat, mods.get('amplitude_reduction_uniform', 0.40)
        return 0.0, 1.0

    def plantilla(self, ajustes, emg_uv, jitter_ms=0.0):
        """Traza limpia de la respuesta (sin ruido ni artefactos)."""
        t = self.eje(ajustes.subtipo)
        y = np.zeros_like(t)
        picos, info = self.picos(ajustes, emg_uv)
        if not picos:
            return t, y, info

        primero = None
        for pico, valores in picos.items():
            sigma = protocol.SIGMA_PICO.get(pico, 2.5)
            y += self._gaussiana(t, valores['lat'] + jitter_ms, valores['amp'], sigma)
            if primero is None:
                primero = valores['amp']

        cola = protocol.COLA.get(ajustes.subtipo)
        if cola and primero:
            lat_cola, fraccion, sigma_cola = cola
            y += self._gaussiana(t, lat_cola + jitter_ms, abs(primero) * fraccion, sigma_cola)

        # La respuesta no existe antes del estímulo: la ventana pre-estímulo
        # es la línea de base contra la que se mira todo lo demás.
        y[t < 0] = 0.0
        return t, y, info

    @staticmethod
    def _gaussiana(t, centro, amp, sigma):
        return amp * np.exp(-0.5 * ((t - centro) / sigma) ** 2)

    # ------------------------------------------------------------------
    # Barridos
    # ------------------------------------------------------------------

    def lote(self, ajustes, emg_uv, n_barridos):
        """Promedia `n_barridos` barridos nuevos y devuelve el promedio del
        lote, cuántos entraron y cuántos rechazó el equipo.

        El promedio de k barridos independientes tiene el ruido dividido por
        raíz de k: se genera así, de una, en vez de sumar k trazas --el
        resultado es el mismo y el tick no cuesta k veces más.
        """
        subtipo = ajustes.subtipo
        t = self.eje(subtipo)

        rechazados = self._rechazados(ajustes, emg_uv, n_barridos)
        aceptados = max(n_barridos - rechazados, 0)
        if aceptados == 0:
            return Lote(promedio=np.zeros_like(t), aceptados=0,
                        rechazados=rechazados, emg=emg_uv, info={})

        jitter = self._jitter_registro(ajustes)
        _t, limpio, info = self.plantilla(ajustes, emg_uv, jitter_ms=jitter)

        ruido = self._ruido(subtipo, emg_uv, aceptados, ajustes)
        artefacto = self._artefacto_estimulo(t, ajustes, emg_uv, aceptados)
        crudo = limpio + ruido + artefacto
        promedio = self._filtrar(crudo, ajustes, subtipo)
        return Lote(promedio=promedio, aceptados=aceptados, rechazados=rechazados,
                    emg=emg_uv, info=info)

    def _rechazados(self, ajustes, emg_uv, n_barridos):
        """Cuántos barridos tira el equipo.

        Dos causas distintas: el músculo FUERA DE BANDA (el equipo no acepta
        registrar con el paciente relajado ni disparado) y los artefactos
        sueltos, que el nivel de rechazo deja pasar o no.
        """
        estado = protocol.estado_emg(ajustes.subtipo, emg_uv)
        if estado != 'ok':
            # El equipo mira el EMG ANTES de sumar el barrido: con el músculo
            # fuera de banda no entra ninguno. Es lo que hace que el registro
            # de un paciente relajado no avance nunca, en vez de avanzar sucio.
            return n_barridos

        base = ARTEFACTO_BASE.get(ajustes.subtipo, 0.06)
        # Nivel de rechazo bajo = el equipo es exigente y tira más.
        exigencia = np.clip((protocol.RECHAZO[1] - ajustes.rechazo) /
                            (protocol.RECHAZO[1] - protocol.RECHAZO[0]), 0.0, 1.0)
        proporcion = base * (0.5 + 1.5 * exigencia)
        return int(self.rng.binomial(n_barridos, min(proporcion, 0.98)))

    def _jitter_registro(self, ajustes):
        """Corrimiento de latencia de este registro cuando el caso dice que
        la respuesta no es reproducible."""
        oido = self.caso.oido(ajustes.lado) if self.caso else None
        caso_sub = oido.subtipos.get(ajustes.subtipo) if oido else None
        if caso_sub is None or caso_sub.repro:
            return 0.0
        return float(self.rng.uniform(-caso_sub.repro_var, caso_sub.repro_var))

    def _ruido(self, subtipo, emg_uv, aceptados, ajustes):
        """Ruido del promedio de `aceptados` barridos.

        Es EMG de fondo (banda ancha, algo rosa) proporcional a cuánto está
        contrayendo el paciente: contraer más sube la respuesta Y el ruido,
        que es por lo que contraer al máximo no es gratis.
        """
        n = protocol.N_PUNTOS
        blanco = self.rng.normal(0.0, 1.0, n)
        rosa = self._rosa(n)
        mezcla = 0.78 * blanco + 0.22 * rosa

        nivel = RUIDO_POR_EMG.get(subtipo, 2.0) * max(emg_uv, 1.0)
        # Un electrodo mal puesto sube el piso de ruido; el nivel de rechazo
        # alto deja entrar barridos sucios al promedio.
        laxitud = 1.0 + 0.12 * max(0.0, ajustes.rechazo - 4.0)
        return mezcla * (nivel * laxitud / math.sqrt(aceptados))

    def _rosa(self, n):
        blanco = self.rng.normal(0.0, 1.0, n)
        fft = np.fft.rfft(blanco)
        freqs = np.fft.rfftfreq(n)
        fft[1:] /= np.sqrt(freqs[1:])
        fft[0] = 0.0
        rosa = np.fft.irfft(fft, n)
        desvio = float(np.std(rosa))
        return rosa / desvio if desvio > 0 else rosa

    def _artefacto_estimulo(self, t, ajustes, emg_uv, aceptados):
        """Artefacto del transductor en los primeros milisegundos.

        Se cancela promediando polaridades alternadas --que es para lo que
        existe la opción-- y es más grande con el vibrador óseo, que mete
        más señal eléctrica en el electrodo que un inserto.
        """
        if ajustes.polaridad == 'Alternante':
            factor = 0.12
        else:
            factor = 1.0
        if ajustes.transductor == protocol.OSEO:
            factor *= 2.4
        nivel = 0.05 * max(emg_uv, 1.0) * factor
        if nivel <= 0:
            return np.zeros_like(t)
        # Oscilación amortiguada arrancando en el estímulo.
        art = np.sin(2 * np.pi * 0.9 * t) * np.exp(-np.maximum(t, 0.0) / 0.8)
        art[t < 0] = 0.0
        return art * nivel

    def _filtrar(self, y, ajustes, subtipo):
        """Filtros del equipo, aplicados al promedio.

        No son decoración: un pasa-alto alto le come la parte lenta del
        complejo (y con eso amplitud), y un pasa-bajo bajo redondea los
        picos. Son controles que el alumno tiene que poder equivocar.
        """
        fs = self._fs(subtipo)
        nyq = fs / 2.0
        salida = np.asarray(y, dtype=float)
        try:
            alto = float(ajustes.filtro_alto)
            if 0 < alto < nyq:
                salida = dsp.filtfilt(dsp.butter(2, alto / nyq, 'high'), salida)
            bajo = float(ajustes.filtro_bajo)
            if 0 < bajo < nyq:
                salida = dsp.filtfilt(dsp.butter(4, bajo / nyq, 'low'), salida)
        except ValueError:
            return salida
        return salida * self._ventana_bordes(len(salida))

    @staticmethod
    def _ventana_bordes(n, fraccion=0.04):
        """Rampa en los extremos de la ventana.

        Los filtros dejan un transitorio en el primer y el último
        milisegundo --un pico que no es del paciente y que además descoloca
        la escala automática del gráfico--. El equipo real muestra la
        ventana ya asentada; acá se la suaviza igual.
        """
        largo = max(int(n * fraccion), 2)
        rampa = 0.5 * (1 - np.cos(np.linspace(0, np.pi, largo)))
        ventana = np.ones(n)
        ventana[:largo] = rampa
        ventana[-largo:] = rampa[::-1]
        return ventana

    # ------------------------------------------------------------------
    # EMG del paciente
    # ------------------------------------------------------------------

    def emg_instantaneo(self, subtipo, maniobra, segundos_sostenido=0.0):
        """EMG rectificado del músculo, con la fatiga de sostener la maniobra.

        Sostener una contracción fuerte no es gratis: el paciente afloja, la
        respuesta cruda se cae con él y el examen largo termina midiendo otra
        cosa. La corrección por EMG es justamente lo que salva esa medición.
        """
        base, fatiga = protocol.maniobra_emg(subtipo, maniobra)
        if base <= 0:
            return 0.0
        caida = 1.0 - fatiga * (segundos_sostenido / 60.0)
        caida = max(caida, 0.45)
        nivel = base * caida
        # El músculo nunca contrae parejo.
        nivel *= float(self.rng.normal(1.0, 0.06))
        return max(nivel, 0.0)


def duracion_segundos(promedios, tasa):
    """Cuánto dura, en el paciente, pedir esos barridos a esa tasa."""
    if tasa <= 0:
        return 0.0
    return float(promedios) / float(tasa)
