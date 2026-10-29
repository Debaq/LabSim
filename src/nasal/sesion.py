"""El paciente nasal en atención, compartido por los equipos de la nariz.

La rinomanometría y la rinometría miden la MISMA nariz: si el alumno pone
vasoconstrictor para la rinomanometría, la rinometría que haga después
también es "con vasoconstrictor", y el ciclo nasal corre para las dos. Por
eso el estado no vive en cada ventana sino aquí, uno por atención.

El tiempo del ciclo es el del reloj: una medición a los 2 minutos y otra a
los 40 no ven la misma congestión (H26: una sola medición es una foto). El
minuto en que entra el paciente sale de la atención, siempre el mismo para
esa atención (stable_seed, no hash(): ver core/rng.py).

Sin `cases.data['NASAL']` no hay paciente: el equipo no mide (no se rellena
con una nariz normal).
"""

import time

from core.rng import stable_seed
from nasal import modelo


def desde_caso(data):
    """`cases.data` -> paciente de RinoSim, o None si el caso no trae nariz.
    Un bloque mal escrito (un valor que no es número) también da None: el
    módulo dice que no hay nariz cargada en vez de medir otra cosa."""
    if not isinstance(data, dict):
        return None
    nasal = data.get('NASAL')
    if not isinstance(nasal, dict) or not isinstance(nasal.get('lados'), dict):
        return None
    try:
        return modelo.normaliza(nasal)
    except ValueError as exc:
        print(f'nasal: el caso trae NASAL inválido: {exc}')
        return None


class SesionNasal:
    def __init__(self, data, appointment_id, reloj=time.monotonic):
        self.paciente = desde_caso(data)
        self.appointment_id = appointment_id
        self._reloj = reloj
        self._inicio = reloj()
        # En qué punto del ciclo llega: 0-149 min, fijo por atención.
        periodo = (self.paciente or {}).get('ciclo', {}).get('periodo', 150) or 150
        self.minuto_llegada = stable_seed('nasal', appointment_id) % int(periodo)
        self.vc = False
        self._mediciones = 0

    @property
    def hay_paciente(self):
        return self.paciente is not None

    def minuto(self):
        return self.minuto_llegada + int((self._reloj() - self._inicio) // 60)

    def estado(self):
        """El `estado` que piden modelo, rinomanometria y rinometria."""
        return {'minuto': self.minuto(), 'vc': self.vc}

    def fase(self):
        return 'vc' if self.vc else 'reposo'

    def aplicar_vasoconstrictor(self):
        self.vc = True

    def semilla_medicion(self, equipo):
        """Cada medición con su propia variabilidad, reproducible por
        atención: la quinta medición de esta atención sale igual si se repite
        la atención con los mismos pasos."""
        self._mediciones += 1
        return f'{equipo}/{self.appointment_id}/{self._mediciones}'


_actual = None


def para(data, appointment_id):
    """La sesión de esta atención: la misma para todos los equipos nasales.
    Otra atención (u otro caso) arma una nueva."""
    global _actual
    if data is None:
        _actual = None
        return None
    if (_actual is None or _actual.appointment_id != appointment_id
            or _actual.paciente != desde_caso(data)):
        _actual = SesionNasal(data, appointment_id)
    return _actual
