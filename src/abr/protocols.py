"""Protocolos de registro por potencial evocado.

El módulo se llama "ABR" pero el combo `cb_test` ya lista los otros
potenciales (ASSR, MLR, P300, MMN, ECochG, CAEP, Stacked ABR) que van a
colgar de la misma ventana: mismo equipo, mismos electrodos, mismo
promediador, distinto protocolo. Esta tabla es la costura -- todo lo que
cambia entre potenciales (ventana de registro, filtros, tasa, cuántas
promediaciones, qué estímulos tienen sentido, qué montaje se usa) vive acá
y no repartido por la UI.

`implemented` dice si hay generador detrás. Los que no lo tienen quedan
seleccionables solo cuando se implementen (ver AbrControl.disable_unimplemented_tests),
pero su protocolo ya está descrito: cuando llegue el generador, el equipo
se configura solo.

Las ventanas y filtros son los valores clínicos de rutina:
- ECochG mira los primeros milisegundos (MP/PA), ventana corta.
- ABR/Stacked ABR: tronco, 10-15 ms.
- MLR: respuesta de vía tálamo-cortical, decenas de ms.
- CAEP/MMN/P300: corteza, cientos de ms y filtros muy bajos.
- ASSR no se lee en el tiempo sino en frecuencia; la ventana es nominal.
"""
from dataclasses import dataclass


# Estímulos tal como los rotula cb_stim (ver ABR_generator.STIM_MAP).
CLICK = 'Click'
CHIRPS = ('Ls-chirp', 'Chirp')
BURSTS = ('Burst 500Hz', 'Burst 1kHz', 'Burst 2kHz', 'Burst 4kHz')


@dataclass(frozen=True)
class Protocol:
    """Configuración de registro de un potencial evocado."""
    name: str
    window_ms: float            # largo de la ventana de registro
    filter_high: float          # pasa-alto (Hz)
    filter_low: float           # pasa-bajo (Hz)
    rate: float                 # tasa de estimulación (estímulos/s)
    averages: int               # promediaciones de rutina
    montage: str                # clave de technical_factors.electrode_montage
    stimuli: tuple = ()         # estímulos con sentido clínico para esta prueba
    implemented: bool = False
    note: str = ''

    @property
    def window_range(self) -> tuple:
        """Rango razonable de ventana para el spinbox (ms)."""
        return (max(self.window_ms / 2, 2.0), self.window_ms * 2)


PROTOCOLS = {
    'ABR': Protocol(
        name='ABR', window_ms=12, filter_high=100, filter_low=3000,
        rate=21.1, averages=2000, montage='vertex_mastoid',
        stimuli=(CLICK,) + CHIRPS + BURSTS, implemented=True,
        note='Tronco cerebral. Burst para umbrales por frecuencia, chirp para sincronizar.'),
    'ECochG': Protocol(
        name='ECochG', window_ms=5, filter_high=10, filter_low=3000,
        rate=11.1, averages=1500, montage='tympanic',
        stimuli=(CLICK,) + BURSTS,
        note='Microfónica coclear, potencial de sumación y PA. Necesita electrodo timpánico.'),
    'Stacked ABR': Protocol(
        name='Stacked ABR', window_ms=15, filter_high=100, filter_low=3000,
        rate=21.1, averages=4000, montage='vertex_mastoid',
        stimuli=(CLICK,),
        note='Click con ruido de banda suprimida: suma las contribuciones por región coclear.'),
    'ASSR': Protocol(
        name='ASSR', window_ms=100, filter_high=30, filter_low=300,
        rate=80.0, averages=1000, montage='vertex_mastoid',
        stimuli=BURSTS,
        note='Se analiza en frecuencia (fase/amplitud del modulador), no en el tiempo.'),
    'MLR': Protocol(
        name='MLR', window_ms=100, filter_high=10, filter_low=300,
        rate=7.1, averages=1000, montage='vertex_mastoid',
        stimuli=(CLICK,) + BURSTS,
        note='Na-Pa. Muy sensible al sueño y a la edad.'),
    'CAEP': Protocol(
        name='CAEP', window_ms=500, filter_high=1, filter_low=30,
        rate=1.0, averages=150, montage='vertex_mastoid',
        stimuli=(CLICK,) + BURSTS,
        note='P1-N1-P2 cortical. Requiere paciente despierto.'),
    'MMN': Protocol(
        name='MMN', window_ms=500, filter_high=1, filter_low=30,
        rate=1.5, averages=200, montage='vertex_mastoid',
        stimuli=(CLICK,) + BURSTS,
        note='Paradigma odd-ball; se lee la resta desviante menos frecuente.'),
    'P300': Protocol(
        name='P300', window_ms=800, filter_high=0.5, filter_low=30,
        rate=1.0, averages=50, montage='vertex_mastoid',
        stimuli=(CLICK,) + BURSTS,
        note='Odd-ball con tarea atencional: el paciente cuenta los estímulos raros.'),
}

DEFAULT_TEST = 'ABR'


def get_protocol(test: str) -> Protocol:
    """Protocolo de la prueba, o el de ABR si el nombre no está en la tabla."""
    return PROTOCOLS.get(test, PROTOCOLS[DEFAULT_TEST])


def implemented_tests() -> tuple:
    return tuple(name for name, p in PROTOCOLS.items() if p.implemented)
