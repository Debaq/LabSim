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


def map_letter_for_probe(letter, probe_freq, seed_key=None):
    """Sonda 1000 Hz (protocolo Interacoustics): clasificación binaria
    positivo/negativo según presencia de peak, no letra Jerger. No hay campo
    de caso nuevo -- se deriva de la misma letra Z_OD/Z_OI ya cargada, con
    gradiente de probabilidad de "positivo" según cuán rígido/móvil es el
    oído en esa letra (A/Ad/C con peak franco -> casi siempre positivo;
    As borderline -> mayoría negativo pero no siempre; B/N sin peak -> casi
    siempre negativo). Se reusa la forma de curva A/B como proxy visual.

    seed_key (paciente, oído, sonda) fija el resultado -- mismo paciente
    siempre da el mismo positivo/negativo, no una moneda distinta por click."""
    if probe_freq != '1000':
        return letter
    prob = PROBE_1000_POSITIVE_PROB.get(letter, 0.5)
    draw = random.Random(str(seed_key)).random() if seed_key is not None else random.random()
    return 'A' if draw < prob else 'B'


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
        if letter == 'A':
            c = rng.uniform(0.3, 1.6)
            p = rng.randint(-100, 20)
        elif letter == 'As':
            c = rng.uniform(0.01, 0.3)
            p = rng.randint(-100, 20)
        elif letter == 'Ad':
            c = rng.uniform(1.8, 4.0)
            p = rng.randint(-100, 20)
        elif letter == 'C':
            c = rng.uniform(0.3, 1.6)
            p = rng.randint(-400, -100)
        elif letter == 'Cs':
            c = rng.uniform(0.01, 1.3)
            p = rng.randint(-400, -100)
        elif letter == 'B':
            c = rng.uniform(0.0, 0.003)
            p = rng.randint(-100, 20)
        elif letter == 'N':
            c = 0
            p = 0
            self.input[7] = True

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
        dataset = [self.x[::-1], self.y[::-1], c, p, g, vol]
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

            if curve_type == 'on':
                # Efecto "on": pico solo al inicio del estímulo, decae a línea
                # base y no se sostiene (a diferencia de la meseta normal).
                onset_w = 0.15
                shape = np.clip(1.0 - tt / onset_w, 0.0, 1.0)
            elif curve_type == 'on-off':
                # Efecto "on-off": pico al inicio Y al final del estímulo,
                # con retorno a línea base entre ambos.
                edge_w = 0.15
                onset = np.clip(1.0 - tt / edge_w, 0.0, 1.0)
                offset = np.clip(1.0 - (1.0 - tt) / edge_w, 0.0, 1.0)
                shape = np.maximum(onset, offset)
            else:
                # normal / invertido: flanco abrupto (onset/offset rápido del
                # reflejo) + meseta plana sostenida, no una curva suave tipo seno.
                shape = np.clip(np.minimum(tt / edge, (1.0 - tt) / edge), 0.0, 1.0)

            # invertido refleja la deflexión hacia arriba en vez de hacia abajo;
            # el resto (normal, on, on-off) usa la dirección normal.
            sign = 1.0 if curve_type == 'invertido' else -1.0
            y[in_stim] += sign * amp * shape

        self.x = t
        self.y = y

    def getDataSet(self):
        return self.x.tolist(), self.y.tolist()
