"""
El paciente y su caso, leídos para el VEMP.

Traduce `cases.data` --el mismo caso que arma el editor del docente-- a lo
que el motor necesita, sin inventar nada: si el oído no tiene VEMP cargado,
devuelve None y el módulo no registra (memoria del proyecto: sin datos
reales del backend no se genera un examen sintético "normal").

Dos cosas que se leen acá y el módulo anterior no miraba:

- El AUDIOGRAMA del mismo caso. El VEMP aéreo lo apaga cualquier oído medio
  que no transmita, y ese gap ya está medido en `Aerea`/`Osea`. El caso lo
  dice dos veces (el perfil sube el umbral VEMP con `umbral_gap`, ver
  CaseProfile), pero el gap crudo es lo que permite que el ESTÍMULO ÓSEO
  salte la transmisión: mismo oído interno, otro camino.
- La FRECUENCIA del tone burst. El umbral del VEMP no es el mismo en 500 y
  en 1000 Hz, y en qué frecuencia responde mejor un oído es parte de lo que
  se busca. La regla está declarada acá (`_CORRIMIENTO_FREQ`) y no sale de
  una tabla normativa: el caso guarda UN umbral por subtipo.
"""

from vemp import protocol

# Índice de cada frecuencia en las tablas de umbrales del caso
# (['Aerea'][idx] == [OD, OI]). El orden es el de config_audiometer.json:
# 125, 250, 500, 1000, 2000... -- ver DebugMkg.FRECUENCIAS.
_IDX_FREQ = {500: 2, 1000: 3}

# Cuánto corre el umbral del VEMP al cambiar la frecuencia del tone burst,
# respecto del umbral de 500 Hz que guarda el caso. Un oído interno sano
# responde mejor en 500; un oído con el umbral MUY bajo (la firma de una
# ventana de más, tipo dehiscencia) invierte la sintonía y responde mejor
# en los agudos. Valores declarados, no normativos.
_CORRIMIENTO_FREQ = {'500 Hz': 0.0, '750 Hz': 3.0, '1000 Hz': 6.0}
_CORRIMIENTO_FREQ_INVERTIDO = {'500 Hz': 6.0, '750 Hz': 2.0, '1000 Hz': 0.0}
# Umbral por debajo del cual el oído se comporta como una ventana de más:
# sintonía invertida y respuesta más grande de lo normativo.
UMBRAL_SINTONIA_INVERTIDA = 55

# Defaults del caso -- los MISMOS de CaseBuilder::VEMP_DEFAULTS.
DEFAULTS = {
    'CVEMP': {'umbral': 60, 'average_objetivo': 200},
    'OVEMP': {'umbral': 65, 'average_objetivo': 300},
    'MVEMP': {'umbral': 70, 'average_objetivo': 300},
}
REPRO_VAR_DEFAULT = 0.2

# Piso del umbral óseo: por debajo de esto el vibrador ya no tiene rango
# útil y el examen no distingue nada.
UMBRAL_OSEO_MINIMO = 20


class SubtipoCaso:
    """Lo que el caso define para UN VEMP de UN oído."""

    __slots__ = ('subtipo', 'umbral', 'repro', 'repro_var',
                 'average_objetivo', 'desviaciones')

    def __init__(self, subtipo, umbral, repro, repro_var, average_objetivo,
                 desviaciones):
        self.subtipo = subtipo
        self.umbral = umbral
        self.repro = repro
        self.repro_var = repro_var
        self.average_objetivo = average_objetivo
        self.desviaciones = desviaciones

    def desviacion(self, pico, campo):
        return float((self.desviaciones.get(pico) or {}).get(campo, 0.0) or 0.0)


class OidoCaso:
    """Un oído del caso: la patología es del órgano, los umbrales del VEMP."""

    __slots__ = ('lado', 'tipo', 'subtipos', 'gap')

    def __init__(self, lado, tipo, subtipos, gap):
        self.lado = lado
        self.tipo = tipo
        self.subtipos = subtipos      # {subtipo: SubtipoCaso}
        self.gap = gap                # {500: dB, 1000: dB}

    def gap_db(self, freq):
        """Gap aéreo-óseo del audiograma en la frecuencia del tone burst."""
        hz = protocol.FREQ_HZ.get(freq, 500)
        if hz in self.gap:
            return self.gap[hz]
        return (self.gap.get(500, 0.0) + self.gap.get(1000, 0.0)) / 2

    def umbral(self, subtipo, transductor, freq):
        """Umbral del VEMP en las condiciones elegidas.

        Aéreo: el umbral del caso más lo que corra la frecuencia. El gap NO
        se suma acá -- el caso ya lo trae adentro del umbral cuando el
        cuadro es conductivo (CaseProfile lo arma con `umbral_gap`).

        Óseo: el mismo oído interno sin el oído medio en el medio. Se le
        descuenta el gap medido y la ventaja del vibrador.
        """
        caso = self.subtipos.get(subtipo)
        base = float(caso.umbral if caso else DEFAULTS[subtipo]['umbral'])
        if base <= UMBRAL_SINTONIA_INVERTIDA:
            base += _CORRIMIENTO_FREQ_INVERTIDO.get(freq, 0.0)
        else:
            base += _CORRIMIENTO_FREQ.get(freq, 0.0)
        if transductor == protocol.OSEO:
            base = base - self.gap_db(freq) - protocol.OSEO_VENTAJA_DB
            return max(base, UMBRAL_OSEO_MINIMO)
        return base

    def sintonia_invertida(self, subtipo):
        caso = self.subtipos.get(subtipo)
        umbral = caso.umbral if caso else DEFAULTS[subtipo]['umbral']
        return umbral <= UMBRAL_SINTONIA_INVERTIDA


class CasoVemp:
    """El caso completo, ya leído para el examen."""

    __slots__ = ('edad', 'genero', 'poblacion', 'oidos')

    def __init__(self, edad, genero, poblacion, oidos):
        self.edad = edad
        self.genero = genero
        self.poblacion = poblacion
        self.oidos = oidos

    def oido(self, lado):
        return self.oidos.get(lado)

    @property
    def descripcion(self):
        sexo = 'mujer' if str(self.genero) != '0' else 'hombre'
        if self.edad is None:
            return sexo
        return f'{sexo}, {self.edad} años'


def desde_caso(data):
    """`cases.data` -> CasoVemp, o None si el caso no trae VEMP.

    Acepta también los casos viejos, que guardaban UN subtipo con sus
    valores en la raíz del oído (antes de que la ficha armara los tres).
    """
    if not isinstance(data, dict):
        return None
    vemp = data.get('VEMP')
    if not isinstance(vemp, dict):
        return None

    oidos = {}
    for lado in protocol.LADOS:
        oido = _leer_oido(lado, vemp.get(lado), data)
        if oido is not None:
            oidos[lado] = oido
    if not oidos:
        return None

    from vemp.norms import Normativa
    edad = data.get('edad')
    genero = data.get('gender')
    return CasoVemp(edad=edad, genero=genero,
                    poblacion=Normativa.poblacion(edad, genero),
                    oidos=oidos)


def _leer_oido(lado, crudo, data):
    if not isinstance(crudo, dict) or not crudo:
        return None
    guardados = crudo.get('subtipos')
    subtipos = {}
    for subtipo in protocol.SUBTIPOS:
        sub = None
        if isinstance(guardados, dict) and isinstance(guardados.get(subtipo), dict):
            sub = guardados[subtipo]
        elif str(crudo.get('subtipo') or '').upper() == subtipo:
            sub = crudo          # caso viejo: los valores estaban en la raíz
        sub = sub or {}
        default = DEFAULTS[subtipo]
        desviaciones = sub.get('desviaciones')
        desviaciones = desviaciones if isinstance(desviaciones, dict) else {}
        subtipos[subtipo] = SubtipoCaso(
            subtipo=subtipo,
            umbral=int(sub.get('umbral', default['umbral'])),
            repro=bool(sub.get('repro', True)),
            repro_var=float(sub.get('repro_var', REPRO_VAR_DEFAULT)),
            average_objetivo=int(sub.get('average_objetivo', default['average_objetivo'])),
            # Solo los picos de ESTE subtipo: cVEMP y mVEMP comparten los
            # nombres (p13/n23) y cada uno trae los suyos.
            desviaciones={p: dict(desviaciones.get(p) or {})
                          for p in protocol.PEAKS[subtipo]},
        )
    return OidoCaso(lado=lado, tipo=str(crudo.get('type', 'normal') or 'normal'),
                    subtipos=subtipos, gap=_gap_audiograma(lado, data))


def _gap_audiograma(lado, data):
    """Gap aéreo-óseo del caso en 500 y 1000 Hz, por oído.

    Sale de `Aerea_mkg`/`Osea_mkg`, que son las tablas que consulta el motor
    de la audiometría (las que ve el alumno pueden diferir a propósito: ver
    DebugMkg). Sin ellas, las que ve el alumno; sin ninguna, 0.
    """
    idx_lado = 0 if lado == 'OD' else 1
    aerea = data.get('Aerea_mkg') or data.get('Aerea') or []
    osea = data.get('Osea_mkg') or data.get('Osea') or []
    gap = {}
    for hz, idx in _IDX_FREQ.items():
        try:
            a = float(aerea[idx][idx_lado])
            o = float(osea[idx][idx_lado])
        except (IndexError, TypeError, ValueError):
            gap[hz] = 0.0
            continue
        # 130 dB es "sin respuesta" en las tablas: con el aéreo en el tope y
        # el óseo también, el gap real no se puede leer y queda en 0.
        if a >= 125 and o >= 125:
            gap[hz] = 0.0
        else:
            gap[hz] = max(0.0, a - o)
    return gap
