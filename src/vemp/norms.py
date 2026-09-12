"""
Normativa del VEMP: latencia y amplitud esperadas por población y subtipo.

Lee el mismo JSON de siempre (resources/vemp/normative_data.json, el que el
docente puede pisar por curso desde courses.php vía la key
`normative_data.vemp`), pero devuelve las dos cosas que el examen necesita y
antes no estaban separadas:

- La AMPLITUD DE REFERENCIA es la que se mide con el músculo contraído al
  nivel de `protocol.EMG_REFERENCIA`. El motor la reescala con el EMG real
  del paciente, así que la normativa describe la respuesta CORREGIDA y no
  un número que solo vale si el paciente contrajo exactamente igual que la
  muestra normativa.
- La amplitud que se informa en un VEMP es la PICO-PICO del complejo, no la
  de un pico suelto: `pico_a_pico()` la arma sumando las dos magnitudes,
  que es lo que da la resta con signo de dos picos opuestos.

El JSON solo trae 500 y 1000 Hz, y solo para adultos; las otras poblaciones
traen 500. Lo que falta se resuelve acá con reglas declaradas (interpolar
750, caer a 500, caer a adulta) en vez de romper: el examen no puede quedar
sin normativa por una celda que no está en la tabla.
"""

import json

from core import app_config_store
from core.base import context
from vemp import protocol

_PATH_DEFECTO = 'vemp/normative_data.json'

# Cuánto cae la respuesta al subir la frecuencia del tone burst en un oído
# sin patología de oído interno. Se usa solo cuando la población no trae la
# frecuencia en la tabla (niño y adulto mayor, que solo tienen 500 Hz).
CAIDA_POR_FRECUENCIA = {'500Hz': 1.00, '1000Hz': 0.78}


class Normativa:
    """La tabla normativa, ya resuelta para un paciente."""

    def __init__(self, path=None):
        if path is None:
            path = context.get_resource(_PATH_DEFECTO)
        with open(path, 'r', encoding='utf-8') as fh:
            self._json = json.load(fh)
        self._cache = {}

    # ------------------------------------------------------------------
    # Población
    # ------------------------------------------------------------------

    @staticmethod
    def poblacion(edad=None, genero=None):
        """Clave de población del paciente.

        genero: 0 = hombre, 1 = mujer (mismo criterio que cases.data).
        La edad manda sobre el sexo, que solo separa a los adultos --
        MISMO criterio que la vista previa del backend (js/case/vemp.js).
        """
        try:
            edad = float(edad)
        except (TypeError, ValueError):
            return 'adult_female'
        if edad < 18:
            return 'child'
        if edad >= 65:
            return 'elderly'
        return 'adult_male' if str(genero) == '0' else 'adult_female'

    # ------------------------------------------------------------------
    # Baseline
    # ------------------------------------------------------------------

    def baseline(self, poblacion, subtipo, freq='500 Hz'):
        """{pico: {'lat': ms, 'amp': µV con signo}} para esa combinación.

        La amplitud sale CON SIGNO (p13 arriba, n23 abajo): el signo es del
        pico, no un detalle de dibujo, y es lo que hace que la pico-pico sea
        una resta y no una suma arbitraria.
        """
        clave = (poblacion, subtipo, freq)
        if clave in self._cache:
            return {p: dict(v) for p, v in self._cache[clave].items()}

        if freq == '750 Hz':
            base = self._interpolar(poblacion, subtipo)
        else:
            base = self._tabla(poblacion, subtipo, protocol.FREQ_NORMA.get(freq, '500Hz'))

        base = self._aplicar_modificadores(poblacion, base)
        base = self._aplicar_override_curso(subtipo, base)
        for pico, valores in base.items():
            valores['amp'] = abs(valores['amp']) * protocol.signo_pico(pico)
        self._cache[clave] = base
        return {p: dict(v) for p, v in base.items()}

    def _tabla(self, poblacion, subtipo, freq_key):
        poblaciones = self._json.get('populations', {})
        pob = poblaciones.get(poblacion) or poblaciones.get('adult_female') or {}
        tb = (pob.get('air_conduction', {}).get('tone_burst', {}))
        datos = (tb.get(freq_key, {}) or {}).get(subtipo)
        if datos:
            return {p: dict(v) for p, v in datos.items()}
        # Esa población no tiene la frecuencia: se la deriva de su propia
        # tabla de 500 Hz antes de caer a la población adulta, que sería
        # cambiarle la edad al paciente para llenar una celda.
        base500 = (tb.get('500Hz', {}) or {}).get(subtipo)
        if base500:
            factor = CAIDA_POR_FRECUENCIA.get(freq_key, 1.0)
            salto = self._salto_latencia(freq_key)
            return {p: {'lat': v['lat'] + salto, 'amp': v['amp'] * factor}
                    for p, v in base500.items()}
        adulta = (poblaciones['adult_female']['air_conduction']['tone_burst']
                  ['500Hz'].get(subtipo, {}))
        return {p: dict(v) for p, v in adulta.items()}

    @staticmethod
    def _salto_latencia(freq_key):
        """Un tone burst más agudo tiene un ciclo más corto: la respuesta
        aparece un poco más temprano en el papel pero el burst tarda menos
        en llegar a su pico, y en la tabla del JSON la latencia SUBE ~1.2 ms
        de 500 a 1000. Se replica eso para las poblaciones que no la traen."""
        return 1.2 if freq_key == '1000Hz' else 0.0

    def _interpolar(self, poblacion, subtipo):
        """750 Hz: punto medio entre las dos frecuencias de la tabla."""
        a = self._tabla(poblacion, subtipo, '500Hz')
        b = self._tabla(poblacion, subtipo, '1000Hz')
        salida = {}
        for pico, va in a.items():
            vb = b.get(pico, va)
            salida[pico] = {'lat': (va['lat'] + vb['lat']) / 2,
                            'amp': (va['amp'] + vb['amp']) / 2}
        return salida

    def _aplicar_modificadores(self, poblacion, base):
        """Los `physiological_modifiers` del JSON.

        Sobre una COPIA: la versión anterior multiplicaba el dict del JSON
        cargado en memoria, así que cada llamada devolvía una amplitud un
        10% más alta que la anterior.
        """
        mods = self._json.get('physiological_modifiers', {})
        salida = {p: dict(v) for p, v in base.items()}
        if poblacion == 'adult_female':
            boost = (mods.get('sex', {}) or {}).get('female_amp_boost', 1.0)
            for valores in salida.values():
                valores['amp'] = valores['amp'] * boost
        return salida

    @staticmethod
    def _aplicar_override_curso(subtipo, base):
        """Normativa editada por el docente para su curso.

        Shape que guarda courses.php: {subtipo: {pico: {lat, amp}}}, con
        valores ABSOLUTOS (ver CourseParams::'normative_data.vemp').
        """
        override = app_config_store.get('normative_data.vemp')
        if not isinstance(override, dict):
            return base
        delsub = override.get(subtipo)
        if not isinstance(delsub, dict):
            return base
        salida = {p: dict(v) for p, v in base.items()}
        for pico, valores in delsub.items():
            if pico not in salida or not isinstance(valores, dict):
                continue
            if 'lat' in valores:
                salida[pico]['lat'] = float(valores['lat'])
            if 'amp' in valores:
                salida[pico]['amp'] = float(valores['amp'])
        return salida

    # ------------------------------------------------------------------
    # Derivados
    # ------------------------------------------------------------------

    @staticmethod
    def pico_a_pico(base):
        """Amplitud pico-pico del complejo normativo (µV, a EMG de
        referencia). Con dos picos de signo opuesto, la resta con signo es
        la suma de las magnitudes."""
        amps = [abs(v.get('amp', 0.0)) for v in (base or {}).values()]
        if len(amps) < 2:
            return sum(amps)
        return sum(sorted(amps)[-2:])

    def modificadores_patologia(self, patologia):
        return self._json.get('pathology_modifiers', {}).get(patologia, {})


_instancia = None


def normativa():
    """Instancia compartida (el JSON se lee una vez por proceso)."""
    global _instancia
    if _instancia is None:
        _instancia = Normativa()
    return _instancia
