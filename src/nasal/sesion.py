"""El paciente nasal en atención, compartido por los equipos de la nariz.

La rinomanometría y la rinometría miden la MISMA nariz: si el alumno pone
vasoconstrictor para la rinomanometría, la rinometría que haga después
también es "con vasoconstrictor", y el ciclo nasal corre para las dos. Por
eso el estado no vive en cada ventana sino aquí, uno por atención.

El tiempo del ciclo es el del reloj: una medición a los 2 minutos y otra a
los 40 no ven la misma congestión (H26: una sola medición es una foto). El
minuto en que entra el paciente sale de la atención, siempre el mismo para
esa atención (stable_seed, no hash(): ver core/rng.py).

El vasoconstrictor se pone en una fosa o en las dos, y hace efecto
pasados 15 minutos de reloj (H26: "tras 15 minutos"): lo que se mida antes
cuenta como "con vasoconstrictor" pero la mucosa sigue igual, como en la
consulta. El modelo de RinoSim lo trata como todo o nada.

El ambiente de la sala (temperatura y humedad) es el que muestra el equipo:
fijo por atención, con una deriva lenta. No mueve el modelo; se anota.

Sin `cases.data['NASAL']` no hay paciente: el equipo no mide (no se rellena
con una nariz normal).
"""

import math
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


# Tiempo de acción del vasoconstrictor, segundos (H26).
ESPERA_VC_S = 15 * 60
# Los que se pueden elegir: (clave, nombre en pantalla e informe).
VASOCONSTRICTORES = (('oximetazolina', 'Oximetazolina 0,05 %'),
                     ('xilometazolina', 'Xilometazolina 0,1 %'))


class SesionNasal:
    def __init__(self, data, appointment_id, reloj=time.monotonic):
        self.paciente = desde_caso(data)
        self.appointment_id = appointment_id
        self._reloj = reloj
        self._inicio = reloj()
        # En qué punto del ciclo llega: 0-149 min, fijo por atención.
        periodo = (self.paciente or {}).get('ciclo', {}).get('periodo', 150) or 150
        self.minuto_llegada = stable_seed('nasal', appointment_id) % int(periodo)
        self.vc_puesto = {}       # lado -> {'t', 'farmaco', 'puff'}
        self._mediciones = 0

    @property
    def hay_paciente(self):
        return self.paciente is not None

    def minuto(self):
        return self.minuto_llegada + int((self._reloj() - self._inicio) // 60)

    def estado(self, lado=None):
        """El `estado` que piden modelo, rinomanometria y rinometria para
        medir `lado` (sin lado: con vasoconstrictor si alguna fosa lo tiene
        en acción)."""
        vc = self.vc_activo(lado) if lado else any(self.vc_activo(l) for l in modelo.LADOS)
        return {'minuto': self.minuto(), 'vc': vc}

    def fase(self, lado=None):
        """Cómo se rotula lo que se mida: "con VC" desde que se puso."""
        puesto = lado in self.vc_puesto if lado else bool(self.vc_puesto)
        return 'vc' if puesto else 'reposo'

    @property
    def vc(self):
        """Se puso vasoconstrictor en alguna fosa."""
        return bool(self.vc_puesto)

    def aplicar_vasoconstrictor(self, lados=modelo.LADOS, farmaco='oximetazolina', puff=2, ya=False):
        """`ya`: sin esperar el tiempo de acción (al retomar la atención)."""
        t = self._reloj() - (ESPERA_VC_S if ya else 0)
        for lado in lados:
            if lado not in self.vc_puesto:
                self.vc_puesto[lado] = {'t': t, 'farmaco': farmaco, 'puff': int(puff)}

    def falta_vc(self, lado):
        """Segundos que faltan para que haga efecto en esa fosa (0 si ya), o None sin VC."""
        v = self.vc_puesto.get(lado)
        if v is None:
            return None
        return max(0.0, ESPERA_VC_S - (self._reloj() - v['t']))

    def vc_activo(self, lado):
        return self.falta_vc(lado) == 0

    def saltar_espera(self):
        """Para el docente: da por pasado el tiempo de acción."""
        for v in self.vc_puesto.values():
            v['t'] = min(v['t'], self._reloj() - ESPERA_VC_S)

    def vc_informe(self):
        """Lo que va al informe: dónde, qué y cuánto (o None)."""
        if not self.vc_puesto:
            return None
        nombres = dict(VASOCONSTRICTORES)
        return {'lados': sorted(self.vc_puesto),
                'farmaco': {l: nombres.get(v['farmaco'], v['farmaco']) for l, v in self.vc_puesto.items()},
                'puff': {l: v['puff'] for l, v in self.vc_puesto.items()}}

    def restaurar_vc(self, guardado):
        """Del informe guardado: un bool (informes de antes) o vc_informe()."""
        if isinstance(guardado, dict):
            claves = {n: k for k, n in VASOCONSTRICTORES}
            for lado in guardado.get('lados') or []:
                if lado in modelo.LADOS:
                    nombre = (guardado.get('farmaco') or {}).get(lado)
                    self.aplicar_vasoconstrictor([lado], claves.get(nombre, 'oximetazolina'),
                                                 (guardado.get('puff') or {}).get(lado, 2), ya=True)
        elif guardado:
            self.aplicar_vasoconstrictor(ya=True)

    def ambiente(self):
        """Temperatura (°C) y humedad relativa (%) de la sala, como las
        muestra el equipo. Del simulador: una sala de consulta (20-24 °C,
        35-60 %), fija por atención, que se mueve poco con las horas."""
        base = stable_seed('nasal-ambiente', self.appointment_id)
        t0 = 20.0 + (base % 400) / 100
        h0 = 35 + (base // 400) % 26
        horas = (self._reloj() - self._inicio) / 3600
        return (round(t0 + 0.4 * math.sin(horas * 2.1 + base % 7), 1),
                int(round(h0 + 2 * math.sin(horas * 1.3 + base % 5))))

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


# ── Lo que hace el alumno, acción por acción ──────────────────────────────
# Como el audiómetro y el impedanciómetro: cada acción va a action_logs
# (backend/log_queue.py, escritura local que sube en lotes) con la atención y
# el caso. Las mediciones llevan además lo que el equipo no sabe (la
# resistencia verdadera, la congestión, si el vasoconstrictor ya actuaba):
# el modelo solo existe en la app, así que el backend no podría calcularlo
# después. El alumno no ve los payloads (my_attendances solo resume).

_cola = None


def cola():
    global _cola
    if _cola is None:
        from backend.log_queue import get_log_queue
        _cola = get_log_queue()
    return _cola


def redondear(v, d=4):
    """Para el log: floats cortos, dentro de listas y diccionarios también."""
    if isinstance(v, float):
        return round(v, d) if math.isfinite(v) else None
    if isinstance(v, dict):
        return {str(k): redondear(x, d) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [redondear(x, d) for x in v]
    return v


def registrar(accion, data, appointment_id, **payload):
    case_id = data.get('id') if isinstance(data, dict) else None
    payload = redondear(payload)
    payload.setdefault('case_id', case_id)
    payload.setdefault('appointment_id', appointment_id)
    payload.setdefault('con_paciente', case_id is not None)
    try:
        cola().push(accion, payload)
    except Exception as exc:  # noqa: BLE001 -- sin log el examen sigue
        print(f'nasal: no se pudo registrar {accion}: {exc}')
