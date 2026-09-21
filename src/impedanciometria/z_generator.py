import numpy as np
import random



PROBE_1000_POSITIVE_PROB = {
    'A': 0.95,
    'Ad': 0.90,
    'C': 0.85,
    'Cs': 0.55,
    'As': 0.25,
    'B': 0.03,
    'N': 0.0,
}


# Edad hasta la cual la sonda de 226 Hz no sirve. Bajo los 6 meses la pared
# del conducto todavia es cartilaginosa y blanda, y su movimiento DOMINA la
# admitancia medida: el equipo dibuja un pico que es de la pared, no del
# oido medio. Por eso el estandar en lactantes es sonda de 1000 Hz.
INFANT_PROBE_MONTHS = 6.0


def edad_meses_del_caso(data):
    """Edad del paciente en meses, o None si el caso no la dice.

    'edad_horas' es lo fino (ver CaseForm::horasDeVida en el backend) y
    manda cuando esta. Sin eso queda 'edad' en anios enteros: si es 0, el
    paciente tiene menos de un anio y no hay forma de saber si son tres
    dias o once meses -- se asume lactante, que es el caso que hay que
    poder armar y el error que hay que poder cometer. Con la edad exacta
    cargada, un bebe de ocho meses se comporta como corresponde.
    """
    if not data:
        return None
    horas = data.get('edad_horas')
    if horas not in (None, ''):
        try:
            return float(horas) / 720.0
        except (TypeError, ValueError):
            pass
    edad = data.get('edad')
    if edad in (None, ''):
        return None
    try:
        return float(edad) * 12.0
    except (TypeError, ValueError):
        return None


def is_infant_ear(edad_meses):
    """True si a este oido la sonda de 226 Hz no le sirve.

    edad_meses None = no se sabe -> se asume que NO es lactante. Un caso
    viejo, sin edad exacta cargada, tiene que seguir comportandose como
    siempre; el hallazgo se arma a proposito, no por un dato faltante.
    """
    if edad_meses is None:
        return False
    try:
        return float(edad_meses) < INFANT_PROBE_MONTHS
    except (TypeError, ValueError):
        return False


def z1000_del_caso(data, side):
    """Que declaro el docente para la sonda de 1000 Hz en ese oido.

    'auto' (o un caso viejo, que no trae el campo) = derivarlo de la letra
    de 226 Hz, que es lo que el simulador hizo siempre. Ver
    CaseBuilder::Z1000_OPTIONS en el backend.
    """
    if not data:
        return 'auto'
    valor = data.get(f'Z1000_{side}')
    return valor if valor in ('positivo', 'negativo') else 'auto'


def map_letter_for_probe(letter, probe_freq, seed_key=None, edad_meses=None,
                         forzado='auto'):
    """Que dibuja el equipo segun la sonda, la letra del caso y la edad.

    Sonda 1000 Hz (protocolo Interacoustics): clasificacion binaria
    positivo/negativo segun presencia de peak, no letra Jerger. `forzado` es
    lo que el docente declaro en la ficha (Z1000_OD/Z1000_OI): con 'auto'
    --el default y lo que traen los casos viejos-- se deriva de la misma
    letra Z_OD/Z_OI ya cargada, con
    gradiente de probabilidad de "positivo" segun cuan rigido/movil es el
    oido en esa letra (A/Ad/C con peak franco -> casi siempre positivo;
    As borderline -> mayoria negativo pero no siempre; B/N sin peak -> casi
    siempre negativo). Se reusa la forma de curva A/B como proxy visual.

    Sonda 226 Hz en un lactante: el equipo dibuja una curva CON PICO aunque
    el oido medio este lleno. No es un bug del simulador, es el hallazgo --
    a esa edad la pared del conducto es blanda y su movimiento tapa al del
    oido medio, asi que un timpanograma "normal" a 226 Hz no descarta nada.
    El alumno tiene que darse cuenta de que la sonda esta mal elegida, y la
    unica forma de que pueda darse cuenta es que el equipo se lo deje hacer.
    La curva que sale es A (pico normal) y no la letra real del caso.

    seed_key (paciente, oido, sonda) fija el resultado -- mismo paciente
    siempre da el mismo positivo/negativo, no una moneda distinta por click.
    """
    if probe_freq != '1000':
        # 226 Hz en lactante: pico de la pared del conducto, no del oido
        # medio. Las rigidas siguen leyendose rigidas (As/Cs): lo que la
        # pared blanda enmascara es la AUSENCIA de pico, no una compliance
        # baja de por si.
        if is_infant_ear(edad_meses) and letter in ('B', 'N'):
            return 'A'
        return letter
    # Lo que el docente haya declarado manda sobre el sorteo: el lactante
    # con el oido medio ocupado que a 226 Hz se ve normal y solo la sonda de
    # 1000 Hz delata es un caso que se arma a proposito, no uno que salga si
    # la moneda acompana (ver Z1000_OPTIONS en el backend).
    if forzado == 'positivo':
        return 'A'
    if forzado == 'negativo':
        return 'B'
    prob = PROBE_1000_POSITIVE_PROB.get(letter, 0.5)
    draw = random.Random(str(seed_key)).random() if seed_key is not None else random.random()
    return 'A' if draw < prob else 'B'


# Rango que se sortea para cada letra de Jerger:
# [compliance mín (mL), compliance máx, presión mín del pico (daPa), máx].
#
# Espejo de CaseCharts::FORMAS_TIMPANOGRAMA (labsim_backend/src/CaseCharts.php)
# y de SHAPES en public/js/case/tympanogram.js: la ficha informa el rango y
# dibuja su centro, así que un rango que no es clínico acá sale impreso mal
# allá. Valores de adulto:
#  - A/C comparten la compliance normal (0,3-1,6 mL); lo que los separa es
#    dónde cae el pico.
#  - As y Cs son las rígidas: compliance BAJO (<0,3 mL). Cs no puede sortear
#    hasta 1,3, porque ahí es una C normal con otro nombre.
#  - Ad va sobre 1,8 mL. El tope es 3,0 y no 4,0: más arriba deja de ser una
#    curva que el equipo pueda mostrar (el eje abre en 2 cc).
#  - El pico de C/Cs llega hasta -250 daPa, no hasta -400: -400 es el borde
#    mismo de la ventana de barrido y ahí no queda pico que leer.
# Ancho de la curva, en daPa: es el TW (ancho a media altura) y también el
# semiancho del coseno alzado, porque en esa forma la media altura cae justo
# a pmax/2 de cada lado del pico.
#
# Antes era 200 daPa para TODAS las letras, y como la gradiente se lee a ±50
# daPa del pico, el equipo informaba 0,85 en cualquier curva con pico: un
# número que no decía nada. Un adulto normal tiene TW de 50 a 110 daPa.
#
# El ancho es fijo por letra y no sorteado a propósito: la ficha del caso
# anticipa la gradiente que el alumno va a leer en pantalla, y eso sólo se
# puede prometer si el ancho no cambia entre un barrido y otro.
#  - A y As comparten ancho: la rigidez baja la altura del pico, no lo
#    angosta (una otoesclerosis tiene TW normal).
#  - Ad es la más en punta: la disyunción osicular da pico alto y angosto.
#  - C abre un poco y Cs bastante: la curva redondeada de la retracción con
#    efusión incipiente es el hallazgo clásico de gradiente baja.
#  - B no tiene pico, así que su ancho no se lee; queda plana igual.
ANCHOS_JERGER = {
    'A': 80,
    'As': 80,
    'Ad': 60,
    'C': 100,
    'Cs': 160,
    'B': 400,
}


FORMAS_JERGER = {
    'A':  (0.3, 1.6, -100, 20),
    'As': (0.1, 0.3, -100, 20),
    'Ad': (1.8, 3.0, -100, 20),
    'C':  (0.3, 1.6, -250, -110),
    'Cs': (0.1, 0.3, -250, -110),
    'B':  (0.0, 0.003, -100, 20),
}


class Z_225():
    def __init__(self, manual=False, letter="A", c=1, p=0, g=1, pmax=200, num_pts=20, vol=1.8, unseal=False, win_neg=-400, win_pos=200, seed_key=None):

        self.input = [letter, c, p, g, vol, pmax, num_pts, unseal, win_neg, win_pos]
        self.seed_key = seed_key
        if manual:
            self.create_manual()
        else:
            self.create_auto()

    def create_manual(self):
        unseal = self.input[7]
        self.num_pts = self.input[6]
        self.win_neg = self.input[8]
        self.win_pos = self.input[9]
        try:
            self.compliance = round(self.input[1], 2)
            self.pressure = self.input[2]
            self.gradient = self.input[3]
            self.volume = round(self.input[4], 2)
            self.pressure_max = self.input[5]
        except:
            self.compliance = self.input[1]
            self.pressure = self.input[2]
            self.gradient = self.input[3]
            self.volume = self.input[4]
            self.pressure_max = self.input[5]
            unseal = True

        if unseal:
            self.zeros(unseal=unseal)
        else:
            self.x, self.y = self.curve_z()

    def create_auto(self):
        letter = self.input[0]
        # rng fija (seed_key = paciente+oído+sonda) para que el mismo
        # paciente siempre caiga en el mismo punto de la curva; random
        # global sólo se usa cuando no hay paciente (caso legacy/demo).
        rng = random.Random(str(self.seed_key)) if self.seed_key is not None else random
        if letter == 'N':
            c = 0
            p = 0
            self.input[7] = True
        else:
            c_min, c_max, p_min, p_max = FORMAS_JERGER.get(letter, FORMAS_JERGER['A'])
            c = rng.uniform(c_min, c_max)
            p = rng.randint(int(p_min), int(p_max))
            self.input[5] = ANCHOS_JERGER.get(letter, ANCHOS_JERGER['A'])

        if letter != 'N' and self.seed_key is not None:
            # jitter mínimo encima del valor estable del paciente -- no
            # redibuja desde el rango completo cada vez, sólo tiembla un poco
            c = max(0.0, c * random.uniform(0.97, 1.03))
            p = p + random.randint(-2, 2)

        self.input[1] = c
        self.input[2] = p
        self.create_manual()

    def curve_z(self):
        c = self.compliance
        p = self.pressure
        pmax = self.pressure_max
        num_pts = self.num_pts

        # Curva en coseno alzado: pendiente cero en ambos extremos de cada
        # tramo, tanto en el peak como en el empalme con la línea base.
        # Evita el "nudito"/quiebre filoso que dejaba el bezier anterior
        # (llegaba y salía del peak en tangente vertical).
        t = np.linspace(0.0, 1.0, num_pts)
        x_left = (-pmax + p) + t * pmax
        y_left = c * (0.5 - 0.5 * np.cos(np.pi * t))
        x_right = p + t * pmax
        y_right = c * (0.5 + 0.5 * np.cos(np.pi * t))

        x = np.append(x_left, x_right[1:])
        y = np.append(y_left, y_right[1:])

        x_neg = np.arange(self.win_neg-10, min(x)-10, 10)
        x_pos = np.arange(max(x)+10, self.win_pos+10, 10)

        y_neg = np.zeros(len(x_neg))
        y_pos = np.zeros(len(x_pos))

        y = np.append(y_neg,y)
        y = np.append(y,y_pos)
        x = np.append(x_neg, x)
        x = np.append(x, x_pos)

        noise_std = max(0.005, 0.02 * abs(c))
        y_noise = np.random.normal(0, noise_std, y.shape)
        y = y + y_noise

        self.gradient = self._calc_gradient(x, y, p, c)

        return x, y

    def _calc_gradient(self, x, y, p, c):
        if not c or c <= 0:
            return 0.0
        order = np.argsort(x)
        xs = x[order]
        ys = y[order]
        y_minus = np.interp(p - 50, xs, ys)
        y_plus = np.interp(p + 50, xs, ys)
        gradient = (y_minus + y_plus) / (2 * c)
        return round(min(max(gradient, 0.0), 1.0), 2)





    def zeros(self, unseal=False):
        self.x = np.zeros(40)
        self.y = np.zeros(40)
        if not unseal:
            self.volume = 'N/D'
        self.compliance = 'N/D'
        self.gradient = 'N/D'
        self.pressure = 'N/D'
        #data_set = [x[::-1],y[::-1], presure, compliance, gradient, volume]
        # return data_set

    def getDataSet(self):
        c = str(self.compliance)
        p = str(self.pressure)
        g = str(self.gradient)
        vol = str(self.volume)
        self.x = self.x.tolist()
        self.y = self.y.tolist()
        # El ancho viaja en el dataset porque al recargar la curva guardada
        # (Z.preCharger con manual=True) ya no hay letra de la que sacarlo, y
        # sin él la curva se redibujaría con el ancho por defecto.
        dataset = [self.x[::-1], self.y[::-1], c, p, g, vol, self.pressure_max]
        return dataset


class Reflex_curve():
    def __init__(self, present, dB=None, threshold=None, curve_type='normal', num_pts=100,
                 duration=2.0, stim_start=0.5, stim_dur=1.0, max_amp=100):
        self.present = present
        self.curve_type = curve_type
        t = np.linspace(0.0, duration, num_pts)
        y = np.random.normal(0, 3, num_pts)

        if present:
            excess = max((dB - threshold), 0) if dB is not None and threshold is not None else 40
            amp = max_amp * min(1.0, 0.3 + excess / 40)
            in_stim = (t >= stim_start) & (t <= stim_start + stim_dur)
            tt = (t[in_stim] - stim_start) / stim_dur
            edge = 0.05

            if curve_type == 'off':
                # Efecto "off": línea base plana durante TODO el estímulo (nada
                # se suma dentro de in_stim); el pico aparece recién después
                # de apagarse, y regresa sola a la base.
                shape = np.zeros_like(tt)
                offset_w = 0.15
                stim_end = stim_start + stim_dur
                post_dur = offset_w * stim_dur
                post_mask = (t > stim_end) & (t <= stim_end + post_dur)
                tp = (t[post_mask] - stim_end) / post_dur
                post_shape = np.clip(1.0 - tp, 0.0, 1.0)
                y[post_mask] += -1.0 * amp * post_shape
            elif curve_type == 'on-off':
                # Efecto "on-off": pico al inicio Y al final del estímulo,
                # con retorno a línea base entre ambos.
                edge_w = 0.15
                onset = np.clip(1.0 - tt / edge_w, 0.0, 1.0)
                offset = np.clip(1.0 - (1.0 - tt) / edge_w, 0.0, 1.0)
                shape = np.maximum(onset, offset)
                # entre ambos picos la línea no queda plana en 0: leve
                # abombamiento positivo y redondeado (fisiológico).
                mid_t = np.clip((tt - edge_w) / (1.0 - 2 * edge_w), 0.0, 1.0)
                baseline_bump = np.sin(np.pi * mid_t) ** 2
                y[in_stim] += 0.24 * amp * baseline_bump
            else:
                # normal / on / invertido: "on" es sinónimo de "normal" (el ON
                # real es la meseta sostenida, no un pico transitorio). Flanco
                # abrupto (onset/offset rápido) + meseta plana sostenida.
                shape = np.clip(np.minimum(tt / edge, (1.0 - tt) / edge), 0.0, 1.0)

            # invertido refleja la deflexión hacia arriba en vez de hacia abajo;
            # el resto (normal, on, off, on-off) usa la dirección normal.
            sign = 1.0 if curve_type == 'invertido' else -1.0
            y[in_stim] += sign * amp * shape

        self.x = t
        self.y = y

    def getDataSet(self):
        return self.x.tolist(), self.y.tolist()
