import numpy as np
import random


class Z_225():
    def __init__(self, manual=False, letter="A", c=1, p=0, g=1, pmax=200, num_pts=20, vol=1.8, unseal=False, win_neg=-400, win_pos=200):

        self.input = [letter, c, p, g, vol, pmax, num_pts, unseal, win_neg, win_pos]
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
        if letter == 'A':
            c = random.uniform(0.3, 1.6)
            p = random.randint(-100, 20)
        elif letter == 'As':
            c = random.uniform(0.01, 0.3)
            p = random.randint(-100, 20)
        elif letter == 'Ad':
            c = random.uniform(1.8, 4.0)
            p = random.randint(-100, 20)
        elif letter == 'C':
            c = random.uniform(0.3, 1.6)
            p = random.randint(-400, -100)
        elif letter == 'Cs':
            c = random.uniform(0.01, 1.3)
            p = random.randint(-400, -100)
        elif letter == 'B':
            c = random.uniform(0.0, 0.003)
            p = random.randint(-100, 20)
        elif letter == 'N':
            c = 0
            p = 0
            self.input[7] = True

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
