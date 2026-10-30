"""Espirometría (H30 del libro): el pulmón del caso, la maniobra en vivo y lo
que el equipo calcula de ella.

Tres partes, como un espirómetro de verdad:

- **El paciente** (`Pulmon`, `Registro`): el modelo de espiración forzada de
  las figuras de H30 (libro-orl, material/ilustraciones/hacer_h30.py): el
  flujo máximo depende solo del volumen ya espirado,
  F(x) = PEF · (1 − e^(−x/τ)) · (1 − x)^p, con la p que da el FEV1 del caso.
  Encima va lo que depende del esfuerzo (el pico y la subida), un tope de
  flujo si hay obstrucción de la vía aérea superior, y lo que hace el
  paciente con lo que le dicen: respira tranquilo, inspira hasta TLC,
  sopla de golpe, sigue mientras lo animan, inspira rápido de vuelta. Cada
  maniobra tiene su propia variabilidad (semilla) y se rehace igual desde
  su receta (semilla + indicaciones con su muestra).
- **El equipo** (`analizar`): solo ve el flujo que pasa por la boquilla (con
  la fuga, el cero mal puesto y la calibración incluidos) y de ahí saca lo
  mismo que un espirómetro: tiempo cero por retroextrapolación, BEV, FEV1,
  FVC, PEF, TEF, meseta, CVIF, FEF50/FIF50.
- **Los criterios** (`aceptabilidad`, `resumen_fase`): los del manual SER
  2024 y ATS/ERS 2019 tal como los enseña H30 (tabla "Qué aprovecha cada
  hallazgo", grados A-F, repetibilidad de 0,150 L), y los previstos, el LIN
  y el z-score de GLI-2012 (`gli`).

La verdad (el pulmón, lo que hizo el paciente) no la ve el equipo: va a "Lo
que el equipo no sabe" y al log.

Sin `cases.data['ESPIRO']` no hay paciente: el equipo no mide.
"""

import json
import math
import random
from functools import lru_cache

from core.base import context

# ── GLI-2012 ───────────────────────────────────────────────────────────────
# Coeficientes de la tabla spline de GLI (Quanjer y cols., 2012), los mismos
# del libro (hacer_cap37_gli.py, del paquete R rspiro). El manual SER 2024
# recomienda el grupo "caucásico" para la población chilena; ATS/ERS 2022
# usa "otros" con ascendencia desconocida o mixta.

ETNIAS = (('caucasico', 'Caucásico'), ('otros', 'Otros / mixto'))
Z_LIN = -1.645          # percentil 5
PARES = ('FVC', 'FEV1', 'FEV1FVC')

_gli = None


def _tabla_gli():
    global _gli
    if _gli is None:
        with open(context.get_resource('nasal/gli2012.json'), encoding='utf-8') as f:
            _gli = json.load(f)
    return _gli


def lms(sexo, par, edad, talla_cm, etnia='caucasico'):
    """L, M (el previsto) y S de GLI-2012. sexo 'M' o 'F'; edad de 3 a 95."""
    d = _tabla_gli()[f'{sexo}_{par}']
    c = d['c']
    edad = min(max(float(edad), 3.0), 95.0)
    i = (edad - 3.0) / 0.25
    i0 = min(int(i), len(d['L']) - 2)
    fr = i - i0

    def sp(k):
        return d[k][i0] + (d[k][i0 + 1] - d[k][i0]) * fr

    otros = etnia == 'otros'
    L = c['q0'] + c['q1'] * math.log(edad) + sp('L')
    M = math.exp(c['a0'] + c['a1'] * math.log(talla_cm) + c['a2'] * math.log(edad)
                 + (c['a6'] if otros else 0) + sp('M'))
    S = math.exp(c['p0'] + c['p1'] * math.log(edad) + (c['p5'] if otros else 0) + sp('S'))
    return L, M, S


def previsto(sexo, par, edad, talla, etnia='caucasico'):
    return lms(sexo, par, edad, talla, etnia)[1]


def lin(sexo, par, edad, talla, etnia='caucasico'):
    L, M, S = lms(sexo, par, edad, talla, etnia)
    return M * (1 + L * S * Z_LIN) ** (1 / L)


def zscore(sexo, par, valor, edad, talla, etnia='caucasico'):
    L, M, S = lms(sexo, par, edad, talla, etnia)
    return ((valor / M) ** L - 1) / (L * S)


def gravedad(z):
    """Gradación de 2022 por z-score (H30, tabla "Gravedad")."""
    if z is None:
        return ''
    if z > Z_LIN:
        return 'normal'
    if z >= -2.5:
        return 'leve'
    if z >= -4:
        return 'moderada'
    return 'grave'


# ── El pulmón ───────────────────────────────────────────────────────────────

class Curva:
    """Una espiración forzada del modelo de H30: FVC (L), PEF (L/s), forma p
    (1 = descenso recto; más de 1, cóncavo), τ del arranque y PIF (L/s)."""

    def __init__(self, fvc, pef, p, tau=0.05, pif=None):
        self.fvc, self.pef, self.p, self.tau = fvc, pef, p, tau
        self.pif = pif if pif is not None else pef * 0.7
        self._norm = _norma(p, tau)

    def F(self, x):
        """Flujo espiratorio máximo (L/s) cuando ya salió la fracción x de la FVC."""
        x = min(max(x, 0.0), 1.0)
        return self.pef * (1 - math.exp(-x / self.tau)) * (1 - x) ** self.p / self._norm

    def FI(self, y):
        """Flujo inspiratorio (L/s, positivo) cuando ya entró la fracción y."""
        y = min(max(y, 0.0), 1.0)
        return self.pif * math.sin(math.pi * y) ** 0.6

    def fev1(self, dt=0.002, x0=0.004):
        """FEV1 ideal (sin esfuerzo de por medio): integra dx/dt = F(x)/FVC un segundo."""
        return self._integrar(lambda t, x: t >= 1.0 - 1e-9, dt, x0) * self.fvc

    def fin(self, dt=0.004, x0=0.004):
        """Fracción de la capacidad vital que sale en una maniobra ideal hasta
        que el paciente se siente vacío (en el último segundo salió menos de
        VACIO_L) o pasan 15 s: con obstrucción, la cola de la curva no termina
        nunca."""
        paso = round(1 / dt)
        hist = []

        def parar(t, x):
            hist.append(x)
            return t >= 15 or (len(hist) > paso and (x - hist[-1 - paso]) * self.fvc < VACIO_L)

        return self._integrar(parar, dt, x0)

    def _integrar(self, parar, dt, x0):
        x, t = x0, 0.0
        while not parar(t, x):
            k1 = self.F(x) / self.fvc
            x = min(x + self.F(min(x + k1 * dt / 2, 1)) / self.fvc * dt, 1.0)
            t += dt
        return x


@lru_cache(maxsize=256)
def _norma(p, tau):
    return max((1 - math.exp(-(i / 2000) / tau)) * (1 - i / 2000) ** p for i in range(2001))


# El paciente se siente vacío cuando en el último segundo salió menos que
# esto: un poco bajo la meseta del equipo (0,025 L en 1 s), para que la haga.
VACIO_L = 0.02


@lru_cache(maxsize=64)
def forma_p(fvc, fev1, pef, tau=0.05):
    """La p del modelo con la que una maniobra perfecta da ese FEV1 (como
    `ajustar` de hacer_cap37.py)."""
    lo, hi = 0.3, 9.0
    for _ in range(40):
        p = (lo + hi) / 2
        if Curva(fvc, pef, p, tau).fev1() > fev1:
            lo = p
        else:
            hi = p
    return (lo + hi) / 2


@lru_cache(maxsize=64)
def ajustar(fvc, fev1, pef):
    """(capacidad vital, p) con que una maniobra ideal MIDE la FVC y el FEV1
    del caso. En el libro la FVC es la del modelo; aquí el paciente deja de
    soplar cuando ya casi no sale aire, y con obstrucción eso deja afuera la
    cola: la capacidad vital del pulmón queda algo mayor que la FVC medida."""
    vc = fvc
    for _ in range(6):
        p = forma_p(round(vc, 4), fev1, pef)
        vc = fvc / Curva(vc, pef, p).fin()
    return vc, forma_p(round(vc, 4), fev1, pef)


COLABORACION = {
    # esfuerzo (media, DE), probabilidad de un error propio por maniobra,
    # cuánto sigue soplando sin que lo animen (s)
    'buena': ((0.97, 0.025), 0.05, (5.0, 8.0)),
    'regular': ((0.92, 0.05), 0.2, (3.0, 5.5)),
    'mala': ((0.84, 0.08), 0.4, (1.8, 3.5)),
}


class Pulmon:
    """El pulmón del caso: la maniobra perfecta antes del broncodilatador
    (`pre`) y con su efecto pleno (`bd`), y el tope de flujo de una
    obstrucción de la vía aérea superior (espiratorio, inspiratorio o los dos:
    la fija)."""

    def __init__(self, bloque):
        pre = bloque['pre']
        bd = bloque.get('bd') or pre
        self.pre = {k: float(pre[k]) for k in ('fvc', 'fev1', 'pef')}
        self.bd = {k: float(bd.get(k, pre[k])) for k in ('fvc', 'fev1', 'pef')}
        self.tope_e = _num_o_none(bloque.get('tope_e'))
        self.tope_i = _num_o_none(bloque.get('tope_i'))
        self.colaboracion = bloque.get('colaboracion') if bloque.get('colaboracion') in COLABORACION else 'buena'
        self.vc_pre, self.p_pre = ajustar(self.pre['fvc'], self.pre['fev1'], self.pre['pef'])
        self.vc_bd, self.p_bd = ajustar(self.bd['fvc'], self.bd['fev1'], self.bd['pef'])

    def curva(self, frac_bd=0.0):
        """La curva perfecta con el efecto del broncodilatador en fracción 0-1."""
        f = min(max(frac_bd, 0.0), 1.0)

        def mezcla(a, b):
            return a + (b - a) * f

        return Curva(mezcla(self.vc_pre, self.vc_bd), mezcla(self.pre['pef'], self.bd['pef']),
                     mezcla(self.p_pre, self.p_bd))


def _num_o_none(v):
    if v in (None, '', 0):
        return None
    v = float(v)
    return v if v > 0 else None


def _rango(v, lo, hi, nombre):
    v = float(v)
    if not lo <= v <= hi:
        raise ValueError(f'{nombre} fuera de rango ({lo}-{hi}): {v}')
    return v


def normaliza(bloque):
    """Valida el bloque ESPIRO del caso y lo devuelve limpio (ValueError si no sirve)."""
    if not isinstance(bloque, dict) or not isinstance(bloque.get('pre'), dict):
        raise ValueError('falta ESPIRO.pre')
    out = {'talla': _rango(bloque.get('talla'), 90, 220, 'talla'),
           'peso': _rango(bloque.get('peso'), 12, 250, 'peso')}
    for fase in ('pre', 'bd'):
        d = bloque.get(fase)
        if fase == 'bd' and not d:
            continue
        out[fase] = {'fvc': _rango(d.get('fvc'), 0.5, 8, f'{fase}.fvc'),
                     'fev1': _rango(d.get('fev1'), 0.3, 7, f'{fase}.fev1'),
                     'pef': _rango(d.get('pef'), 1, 16, f'{fase}.pef')}
        if out[fase]['fev1'] >= out[fase]['fvc']:
            raise ValueError(f'{fase}: el FEV1 debe ser menor que la FVC')
    for k in ('tope_e', 'tope_i'):
        v = _num_o_none(bloque.get(k))
        out[k] = None if v is None else _rango(v, 0.3, 12, k)
    out['colaboracion'] = bloque.get('colaboracion') if bloque.get('colaboracion') in COLABORACION else 'buena'
    return out


def desde_caso(data):
    """`cases.data` -> {'pulmon', 'bloque', 'edad', 'sexo'} o None si el caso
    no trae espirometría (o la trae mal escrita: el equipo dice que no hay
    pulmón cargado en vez de medir otra cosa)."""
    if not isinstance(data, dict) or not isinstance(data.get('ESPIRO'), dict):
        return None
    try:
        bloque = normaliza(data['ESPIRO'])
        edad = float(data.get('edad'))
    except (TypeError, ValueError) as exc:
        print(f'espirometría: el caso trae ESPIRO inválido: {exc}')
        return None
    return {'pulmon': Pulmon(bloque), 'bloque': bloque, 'edad': edad,
            'sexo': 'F' if data.get('gender') == 1 else 'M'}


# ── La maniobra ─────────────────────────────────────────────────────────────

HZ = 100                 # muestras por segundo del equipo
DT = 1 / HZ
MAX_S = 90               # un registro no pasa de esto
PERIODO_CORRIENTE = 4.0  # s por respiración tranquila (15 por minuto)

INDICACIONES = (
    ('tranquilo', 'Respire tranquilo'),
    ('aire', 'Tome todo el aire'),
    ('sople', '¡Sople de golpe!'),
    ('siga', '¡Siga, siga, siga!'),
    ('inspire', '¡Tome aire rápido!'),
)

# Errores que se pueden simular a mano (y algunos los comete el paciente solo).
ERRORES = (
    ('tos', 'Tose en el primer segundo'),
    ('lento', 'Inicio lento'),
    ('no_tlc', 'No inspira al máximo'),
    ('glotis', 'Cierra la glotis'),
    ('fuga', 'Fuga por la boquilla'),
    ('obstruida', 'Muerde o tapa la boquilla'),
)
ERRORES_PROPIOS = ('tos', 'lento', 'no_tlc')


class Registro:
    """Lo que pasa desde que se aprieta Iniciar hasta Terminar: el paciente
    respira, recibe indicaciones y el equipo mide el flujo en la boquilla.

    `receta` basta para rehacerlo idéntico: semilla, efecto del
    broncodilatador, errores, accesorios (pinza, fuga), cero y calibración, y
    las indicaciones con la muestra en que se dieron."""

    def __init__(self, pulmon, receta):
        self.pulmon = pulmon
        self.receta = receta
        self.rng = random.Random(receta['semilla'])
        r = self.rng
        errores = set(receta.get('errores') or ())
        colab = COLABORACION[pulmon.colaboracion]
        # Un error propio del paciente, a veces (además de los simulados).
        propio = r.choice(ERRORES_PROPIOS) if r.random() < colab[1] else None
        if propio:
            errores.add(propio)
        self.errores = errores
        self.propio = propio
        curva = pulmon.curva(receta.get('frac_bd', 0.0))
        # Variabilidad biológica entre maniobras (~1 % de la FVC, algo más en los flujos).
        self.vc = curva.fvc * (1 + r.gauss(0, 0.01))
        self.curva = Curva(self.vc, curva.pef * (1 + r.gauss(0, 0.015)), curva.p, curva.tau, curva.pif)
        self.esfuerzo = min(1.0, max(0.5, r.gauss(*colab[0])))
        self.persiste_base = r.uniform(*colab[2])
        self.f_tlc = r.uniform(0.86, 0.92) if 'no_tlc' in errores else r.uniform(0.985, 1.0)
        self.tau_subida = r.uniform(0.28, 0.45) if 'lento' in errores else 0.02
        self.t_tos = sorted(r.uniform(0.2, 0.75) for _ in range(r.choice((1, 2)))) if 'tos' in errores else []
        self.t_glotis = r.uniform(0.5, 2.5) if 'glotis' in errores else None
        self.max_retencion = r.uniform(5, 8)      # s que aguanta en TLC antes de soltar
        self.espera_rv = r.uniform(2, 4)          # s en RV antes de inspirar por su cuenta
        self.reaccion = {k: r.uniform(0.15, 0.5) for k, _ in INDICACIONES}
        self.erv = 0.3 * self.vc
        self.vt = max(0.35, 0.11 * self.vc)
        self.cero = receta.get('cero', 0.0)
        self.calibracion = receta.get('calibracion', 1.0)
        self.pinza = receta.get('pinza', True)
        self.ruido = random.Random(f"{receta['semilla']}/ruido")
        # Estado
        self.i = 0
        self.v = self.erv          # volumen sobre el residual (L)
        self.estado = 'corriente'
        self.t_estado = 0.0
        self.fase_corriente = r.uniform(0, 1)
        self.pendientes = []       # (muestra en que actúa, clave)
        self.comandos = [tuple(c) for c in receta.get('comandos') or ()]
        self._prox_cmd = 0
        self.persiste_hasta = None
        self.t_sople = None
        self.t_tlc = None
        self.flujos = []           # medido (L/s, + espiración)
        self.verdad = {'esfuerzo': self.esfuerzo, 'vc': self.vc, 'f_tlc': self.f_tlc,
                       'errores': sorted(errores), 'error_propio': propio,
                       'pausa_tlc': None, 'parto_tlc': None, 'fin': None, 't_tos': self.t_tos,
                       't_glotis': self.t_glotis, 'cvif_forzada': False, 'retuvo_de_mas': False}

    # --- indicaciones ---------------------------------------------------

    def indicar(self, clave):
        """Desde la ventana, en vivo: queda en la receta con su muestra."""
        self.comandos.append((self.i, clave))
        self.receta.setdefault('comandos', []).append([self.i, clave])

    def _al_oir(self, clave):
        demora = round(self.reaccion[clave] * HZ)
        self.pendientes.append((self.i + demora, clave))
        if clave == 'siga' and self.estado == 'espira':
            self.persiste_hasta = max(self.persiste_hasta, self._t() + 2.5)

    def _t(self):
        return self.i * DT

    def _cambiar(self, estado):
        self.estado = estado
        self.t_estado = self._t()
        self.v0 = self.v

    # --- el paciente ----------------------------------------------------

    def _actuar(self, clave):
        e = self.estado
        if clave == 'tranquilo':
            if e != 'corriente':
                self._cambiar('vuelve')
        elif clave == 'aire':
            if e in ('corriente', 'rv', 'vuelve'):
                self.objetivo = self.vc * self.f_tlc
                self._cambiar('inspira_max')
        elif clave == 'sople':
            if e != 'espira':
                if e == 'tlc':
                    self.verdad['pausa_tlc'] = self._t() - self.t_tlc
                self.verdad['parto_tlc'] = e == 'tlc'
                self.verdad['v_inicio'] = self.v
                pausa = self.verdad['pausa_tlc'] or 0
                # Una pausa larga en TLC baja el pico y algo el FEV1 (H30:
                # "sin pausa, o de 2 segundos o menos").
                self.k_pausa = 1 - 0.02 * min(max(pausa - 2, 0), 4)
                self.t_sople = self._t()
                self.v_hist = []
                self.persiste_hasta = self._t() + self.persiste_base
                self._cambiar('espira')
        elif clave == 'inspire':
            if e in ('espira', 'rv'):
                if e == 'espira':
                    self.verdad['fin'] = 'interrumpida por la indicación de inspirar'
                self.objetivo = self.vc
                self.verdad['cvif_forzada'] = True
                self._cambiar('inspira_forzada')

    def _flujo_verdadero(self):
        """dv/dt del paciente en esta muestra, en L/s (+ = espira)."""
        t, e, c = self._t(), self.estado, self.curva
        dur = t - self.t_estado
        if e == 'corriente':
            # Senoide en torno a la FRC: v = erv + vt·(1 − cos)/2.
            w = 2 * math.pi / PERIODO_CORRIENTE
            fase = w * t + 2 * math.pi * self.fase_corriente
            correccion = max(-0.3, min(0.3, (self.v - self._v_corriente(t)) * 2))
            return -self.vt / 2 * w * math.sin(fase) + correccion
        if e == 'vuelve':
            # Vuelve a la FRC en ~2 s y sigue respirando tranquilo.
            if abs(self.v - self.erv) < 0.02:
                self.fase_corriente = (-t / PERIODO_CORRIENTE) % 1
                self._cambiar('corriente')
                return 0.0
            # Relajado: ni la espiración pasiva desde TLC ni la vuelta desde
            # RV llegan al gatillo del equipo (PEF_MIN).
            return max(-0.6, min(0.6, (self.v - self.erv) / 1.2))
        if e == 'inspira_max':
            falta = self.objetivo - self.v
            if falta <= 0.005:
                self.t_tlc = t
                self._cambiar('tlc')
                return 0.0
            return -max(0.4, min(2.5, falta * 2.2))
        if e == 'tlc':
            if dur > self.max_retencion:
                self.verdad['retuvo_de_mas'] = True
                self._cambiar('vuelve')
            return 0.0
        if e == 'espira':
            self.v_hist.append(self.v)
            return self._espira(t - self.t_sople)
        if e == 'rv':
            if dur > self.espera_rv:
                self._cambiar('vuelve')
            return 0.0
        if e == 'inspira_forzada':
            total = self.objetivo - self.v0
            if total <= 0.01 or self.v >= self.objetivo - 0.005:
                self._cambiar('vuelve')
                return 0.0
            y = 0.01 + 0.99 * (self.v - self.v0) / total
            f = c.FI(y) * self.esfuerzo
            if self.pulmon.tope_i:
                f = min(f, self.pulmon.tope_i)
            return -max(f, 0.05)
        return 0.0

    def _v_corriente(self, t):
        w = 2 * math.pi / PERIODO_CORRIENTE
        return self.erv + self.vt * (1 - math.cos(w * t + 2 * math.pi * self.fase_corriente)) / 2

    def _espira(self, ts):
        c = self.curva
        x = max(1 - self.v / self.vc, 0.004)
        # Lo que depende del esfuerzo es el primer tramo: el pico baja con
        # menos fuerza y el final es el mismo (H30, "Por qué el flujo llega a
        # un tope"). Un factor que se apaga con el volumen, no un tope: el
        # tope aplana el pico y parece una obstrucción fija.
        f = c.F(x) * self.k_pausa * (1 - (1 - self.esfuerzo) * math.exp(-x / 0.25))
        # La subida en el tiempo: en un inicio explosivo casi no limita; en
        # uno lento redondea el arranque y agranda el BEV.
        f = min(f, c.pef * (1 - math.exp(-ts / self.tau_subida)))
        if self.pulmon.tope_e:
            f = min(f, self.pulmon.tope_e)
        for tc in self.t_tos:
            f *= 1 - 0.85 * math.exp(-((ts - tc) / 0.03) ** 2)
        fin = None
        if self.t_glotis is not None and ts >= self.t_glotis:
            fin = 'cierre de la glotis'
        elif ts >= 15:
            fin = '15 segundos'
        elif ts > 1 and self.v_hist[-HZ] - self.v < VACIO_L:
            fin = 'vació los pulmones'
        elif self._t() >= self.persiste_hasta:
            fin = 'dejó de soplar (nadie lo animó a seguir)'
        if fin:
            self.verdad['fin'] = fin
            self.verdad['t_fin'] = ts
            self._cambiar('rv')
            return 0.0
        return f

    # --- el equipo ------------------------------------------------------

    def avanzar(self, n=1):
        """n muestras más. Devuelve los flujos medidos nuevos."""
        nuevos = []
        for _ in range(n):
            if self.i >= MAX_S * HZ:
                break
            while self._prox_cmd < len(self.comandos) and self.comandos[self._prox_cmd][0] <= self.i:
                self._al_oir(self.comandos[self._prox_cmd][1])
                self._prox_cmd += 1
            for pend in [p for p in self.pendientes if p[0] <= self.i]:
                self.pendientes.remove(pend)
                self._actuar(pend[1])
            if self.estado == 'corriente' and self.i == 0:
                self.v = self._v_corriente(0)
            f = self._flujo_verdadero()
            if 'obstruida' in self.errores and self.estado in ('espira', 'inspira_forzada'):
                f = max(min(f, 0.5 * self.curva.pef), -0.45 * self.curva.pef)
            self.v = max(0.0, min(self.vc, self.v - f * DT))
            self.flujos.append(self._medido(f))
            nuevos.append(self.flujos[-1])
            self.i += 1
        return nuevos

    def _medido(self, f):
        """Lo que llega al neumotacógrafo: sin pinza se va aire por la nariz,
        con fuga por la comisura; el cero y la calibración del equipo."""
        k = 1.0
        forzado = self.estado in ('espira', 'inspira_forzada')
        if not self.pinza:
            k *= 0.93 if forzado else 0.75
        if 'fuga' in self.errores:
            k *= 0.86 if forzado else 0.97
        return (f * k + self.cero) * self.calibracion + self.ruido.gauss(0, 0.006)

    @property
    def terminada(self):
        """Ya hubo espiración forzada y el paciente volvió a respirar tranquilo
        (o pasó el tope)."""
        return (self.i >= MAX_S * HZ
                or (self.t_sople is not None and self.estado == 'corriente'
                    and self._t() - self.t_estado > 1.0))

    def rehacer(self, hasta):
        """Rehace la maniobra guardada hasta la muestra `hasta`."""
        self.avanzar(hasta - self.i)
        return self


def rehace(pulmon, receta):
    return Registro(pulmon, dict(receta)).rehacer(receta['muestras'])


# ── Lo que calcula el equipo ────────────────────────────────────────────────

PEF_MIN = 0.8            # L/s: menos que esto no es una espiración forzada


def analizar(flujos, hz=HZ):
    """De la señal de flujo (L/s, + espiración) a los números de la
    maniobra, o None si no hubo espiración forzada. Solo con la señal, como
    el equipo: no sabe qué hizo el paciente."""
    n = len(flujos)
    if n < hz:
        return None
    dt = 1 / hz
    vol = [0.0] * n                  # volumen espirado acumulado
    for i in range(1, n):
        vol[i] = vol[i - 1] + (flujos[i - 1] + flujos[i]) / 2 * dt
    i_pef = max(range(n), key=lambda i: flujos[i])
    pef = flujos[i_pef]
    if pef < PEF_MIN:
        return None
    # Inicio: el punto de máxima inspiración antes del pico; fin: donde el
    # flujo deja de ser espiratorio.
    i_s = i_pef
    while i_s > 0 and flujos[i_s - 1] > 0:
        i_s -= 1
    # La espiración dura hasta que empieza a inspirar de verdad (con
    # histéresis: el ruido en RV no la corta) y termina en el último
    # instante en que todavía salía aire. Con el cero corrido, ese "aire"
    # no se acaba nunca: el TEF se alarga y no hay meseta, como en el equipo.
    i_insp = i_pef
    while i_insp < n - 1 and flujos[i_insp + 1] > -UMBRAL_CRUCE:
        i_insp += 1
    i_e = i_insp
    while i_e > i_pef and sum(flujos[i_e - 5:i_e + 5]) / 10 <= FLUJO_FIN:
        i_e -= 1
    v0 = vol[i_s]
    V = [vol[i] - v0 for i in range(i_s, i_e + 1)]
    fvc = V[-1]
    # Tiempo cero: tangente en la pendiente máxima (80 ms), cortada con V = 0.
    w = max(1, round(0.08 * hz))
    j = max(range(len(V) - w), key=lambda k: V[k + w] - V[k]) if len(V) > w else 0
    pend = (V[j + w] - V[j]) / (w * dt) if len(V) > w else pef
    jm = j + w / 2
    vm = (V[j] + V[j + w]) / 2 if len(V) > w else V[0]
    t0 = jm * dt - vm / pend          # en s desde el inicio de la espiración
    bev = _interp(V, max(t0, 0) * hz)
    t_fin = (len(V) - 1) * dt
    cierre_1s = t_fin < t0 + 1.0
    fev1 = _interp(V, (t0 + 1.0) * hz) if not cierre_1s else fvc
    tef = t_fin - t0
    k1 = len(V) - 1 - hz
    meseta = k1 >= 0 and V[-1] - V[k1] < 0.025
    # FEF50: el flujo espiratorio cuando salió la mitad de la FVC.
    fef50 = next((flujos[i_s + k] for k in range(len(V)) if V[k] >= fvc / 2), None)
    # Inspiración que sigue (hasta que vuelve a espirar): CVIF, PIF y FIF50.
    cvif = pif = fif50 = None
    ki = i_insp
    if i_insp < n - 1:
        ki = i_insp + 1
        while ki < n - 1 and flujos[ki + 1] < UMBRAL_CRUCE:
            ki += 1
        tramo = range(i_insp, ki + 1)
        tope = vol[i_insp]
        cvif = tope - min(vol[i] for i in tramo)
        pif = -min(flujos[i] for i in tramo)
        fif50 = next((-flujos[i] for i in tramo if tope - vol[i] >= fvc / 2), None)
    # Volúmenes corrientes antes de la maniobra y si la línea de base se movió.
    corrientes, fines = _corrientes(flujos, vol, i_s)
    deriva = (fines[-1] - fines[0]) / (len(fines) - 1) if len(fines) >= 2 else None
    return {
        'fvc': fvc, 'fev1': fev1, 'pef': pef, 'tef': tef, 'bev': bev, 't0': t0,
        'bev_limite': max(0.100, 0.05 * fvc), 'meseta': meseta, 'cierre_1s': cierre_1s,
        'cvif': cvif, 'pif': pif, 'fef50': fef50, 'fif50': fif50,
        'corrientes': corrientes, 'deriva': deriva,
        'i_inicio': i_s, 'i_fin': i_e, 'i_fin_insp': ki,
    }


def _interp(V, k):
    if k <= 0:
        return V[0]
    if k >= len(V) - 1:
        return V[-1]
    a = int(k)
    return V[a] + (V[a + 1] - V[a]) * (k - a)


UMBRAL_CRUCE = 0.05     # L/s
FLUJO_FIN = 0.01        # L/s (promedio de 0,1 s): bajo esto ya no sale aire


def _corrientes(flujos, vol, hasta):
    """Respiraciones tranquilas completas antes de la inspiración máxima, y el
    volumen al final de cada espiración (para ver si la base se corre)."""
    # La inspiración máxima empieza en el último cruce espiración→inspiración
    # antes de `hasta`. Con histéresis: el ruido en torno a cero (la pausa en
    # TLC) no cuenta como respiraciones.
    cruces, espirando = [], None
    for i in range(hasta):
        if flujos[i] > UMBRAL_CRUCE:
            espirando = True
        elif flujos[i] < -UMBRAL_CRUCE:
            if espirando:
                cruces.append(i)
            espirando = False
    if not cruces:
        return 0, []
    previos = cruces[:-1]
    return len(previos), [vol[i] for i in previos]


# ── Criterios ──────────────────────────────────────────────────────────────

ORDEN = {'no': 0, 'utilizable': 1, 'aceptable': 2}
NOMBRE_CAL = {'no': 'ninguna', 'utilizable': 'utilizable', 'aceptable': 'aceptable'}
REPETIBLE_L = 0.150

# Lo que el operador marca en una maniobra al mirar las curvas y al paciente
# (lo que el equipo no puede ver: tabla de H30 "Qué aprovecha cada hallazgo").
MARCAS = (
    ('', 'Nada'),
    ('tos1', 'Tos en el primer segundo'),
    ('glotis1', 'Cierre de glotis en el primer segundo'),
    ('glotis', 'Cierre de glotis después del primer segundo'),
    ('fuga', 'Fuga'),
    ('obstruida', 'Boquilla obstruida'),
    ('descartar', 'Descartar'),
)
_POR_MARCA = {'tos1': ('no', 'aceptable'), 'glotis1': ('no', 'no'), 'glotis': ('aceptable', 'utilizable'),
              'fuga': ('utilizable', 'utilizable'), 'obstruida': ('utilizable', 'utilizable'),
              'descartar': ('no', 'no')}


def aceptabilidad(m, fvc_otras=(), marca=''):
    """(FEV1, FVC, motivos) de una maniobra: 'aceptable', 'utilizable' o 'no'.
    `fvc_otras`: las FVC de las demás maniobras de la fase (criterio de fin
    por repetibilidad)."""
    fev1, fvc, motivos = 'aceptable', 'aceptable', []

    def bajar(a, b, motivo):
        nonlocal fev1, fvc
        fev1 = min(fev1, a, key=ORDEN.get)
        fvc = min(fvc, b, key=ORDEN.get)
        motivos.append(motivo)

    if m['bev'] > m['bev_limite']:
        bajar('no', 'no', f'volumen extrapolado {m["bev"] * 1000:.0f} mL (límite {m["bev_limite"] * 1000:.0f})')
    if m['cierre_1s']:
        bajar('no', 'no', 'la espiración terminó antes del primer segundo')
    otras = [f for f in fvc_otras if f is not None]
    repite = bool(otras) and m['fvc'] >= max(otras) - REPETIBLE_L
    if not (m['meseta'] or m['tef'] >= 15 or repite):
        bajar('aceptable', 'utilizable', 'sin criterio de fin (ni meseta, ni 15 s, ni FVC repetida)')
    if m['cvif'] is not None and m['cvif'] - m['fvc'] > max(0.100, 0.05 * m['fvc']):
        bajar('utilizable', 'utilizable', f'CVIF mayor que la FVC en {(m["cvif"] - m["fvc"]) * 1000:.0f} mL: '
              'no partió de TLC')
    if marca in _POR_MARCA:
        a, b = _POR_MARCA[marca]
        bajar(a, b, dict(MARCAS)[marca].lower())
    return fev1, fvc, motivos


def grado(valores_aceptables, hay_utilizable):
    """Grado de calidad A-F de FEV1 o de FVC (H30, tabla del manual SER 2024)."""
    v = sorted(valores_aceptables, reverse=True)
    if not v:
        return 'U' if hay_utilizable else 'F'
    if len(v) == 1:
        return 'E'
    dif = v[0] - v[1]
    if len(v) >= 3 and dif <= REPETIBLE_L + 1e-9:
        return 'A'
    if dif <= REPETIBLE_L + 1e-9:
        return 'B'
    if dif <= 0.200 + 1e-9:
        return 'C'
    if dif <= 0.250 + 1e-9:
        return 'D'
    return 'E'


def resumen_fase(maniobras):
    """maniobras: [{'r': analizar(...), 'marca': str}] de una fase. Califica
    cada una y devuelve lo que se informa: la mayor FVC y el mayor FEV1 de
    las aceptables (aunque sean de maniobras distintas), los grados y la
    mejor curva (la de mayor FEV1 + FVC)."""
    cal = []
    for i, m in enumerate(maniobras):
        otras = [x['r']['fvc'] for j, x in enumerate(maniobras) if j != i]
        cal.append(aceptabilidad(m['r'], otras, m.get('marca', '')))
    out = {'calificacion': cal}
    for par, k in (('fev1', 0), ('fvc', 1)):
        acept = [m['r'][par] for m, c in zip(maniobras, cal) if c[k] == 'aceptable']
        util = [m['r'][par] for m, c in zip(maniobras, cal) if c[k] == 'utilizable']
        out[f'grado_{par}'] = grado(acept, bool(util))
        out[f'n_{par}'] = len(acept)
        orden = sorted(acept, reverse=True)
        out[f'dif_{par}'] = orden[0] - orden[1] if len(orden) >= 2 else None
        out[par] = max(acept) if acept else (max(util) if util else None)
    validas = [i for i, c in enumerate(cal) if c[0] != 'no' and c[1] != 'no']
    preferidas = [i for i in validas if cal[i][0] == 'aceptable' and cal[i][1] == 'aceptable'] or validas
    out['mejor'] = (max(preferidas, key=lambda i: maniobras[i]['r']['fev1'] + maniobras[i]['r']['fvc'])
                    if preferidas else None)
    return out


def respuesta_bd(pre, post, prev):
    """Cambio post − pre en litros y como % del previsto (H30: significativa
    si pasa de 10 %)."""
    if pre is None or post is None or not prev:
        return None, None
    return post - pre, (post - pre) * 100 / prev


# ── Verificación con la jeringa de 3 L ──────────────────────────────────────

JERINGA_L = 3.0
FLUJOS_VERIFICACION = (('bajo', 0.5), ('medio', 1.5), ('alto', 6.0))


def verificar(calibracion, semilla):
    """Tres descargas de la jeringa a flujo bajo, medio y alto (linealidad);
    cada una dentro de ±3 % (H30, "Verificación diaria")."""
    r = random.Random(semilla)
    out = []
    for nombre, flujo in FLUJOS_VERIFICACION:
        medido = JERINGA_L * calibracion * (1 + r.gauss(0, 0.004))
        out.append({'flujo': nombre, 'l_s': flujo, 'medido': medido,
                    'error_pct': (medido / JERINGA_L - 1) * 100})
    return out, all(abs(x['error_pct']) <= 3 for x in out)
