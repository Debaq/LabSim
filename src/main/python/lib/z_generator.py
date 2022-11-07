import numpy as np
import random
import lib.bezier_prop as bezier


class Z_225():
    def __init__(self, manual=False, letter="A", c=1, p=0, g=1, pmax=200, num_pts=20, vol=1.8, unseal=False):

        self.input = [letter, c, p, g, vol, pmax, num_pts, unseal]
        if manual:
            self.create_manual()
        else:
            self.create_auto()

    def create_manual(self):
        unseal = self.input[7]
        self.num_pts = self.input[6]
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
        if letter == 'As':
            c = random.uniform(0.01, 0.3)
            p = random.randint(-100, 20)
        if letter == 'C':
            c = random.uniform(0.3, 1.6)
            p = random.randint(-400, -100)
        if letter == 'B':
            c = random.uniform(0.0, 0.003)
            p = random.randint(-600, -200)
        if letter == 'N':
            c = 0
            p = 0
            self.input[7] = True

        self.input[1] = c
        self.input[2] = p
        self.create_manual()

    def curve_z(self):
        c = self.compliance
        p = self.pressure
        g = 0
        pmax = self.pressure_max
        num_pts = self.num_pts

        side_neg = np.asfortranarray([
            [-pmax+p, p, p],
            [0.0, g, c], ])
        side_pos = np.asfortranarray([
            [p, p, pmax+p],
            [c, g, 0], ])

        curve1 = bezier.Curve(side_neg, degree=2)
        curve2 = bezier.Curve(side_pos, degree=2)
        s_vals = np.linspace(0.0, 1.0, num_pts)
        point1 = curve1.evaluate_multi(s_vals)
        point2 = curve2.evaluate_multi(s_vals)
        flip_point2_x = np.flip(point2[0, :])
        flip_point2_y = np.flip(point2[1, :])

        for idx, val in enumerate(point1[0, :]):
            dif = val - flip_point2_x[idx]
            if abs(dif) <= 100:
                hp = idx
                break

        hp_heigth = c - point1[1, :][hp]
        hp_widht = flip_point2_x[hp] - point1[0, :][hp]

        hp_size = [hp_heigth, hp_widht]
        hp = [point1[0, :][hp], point1[1, :][hp]]
        x = np.append(point1[0, :], point2[0, :])
        y = np.append(point1[1, :], point2[1, :])
        x_neg = np.arange(-400, min(x)-10, 10)
        x_pos = np.arange(400, max(x)+10, 10)

        y_neg = np.zeros(len(x_neg))
        y_pos = np.zeros(len(x_pos))
        
        y = np.append(y_neg,y)
        y = np.append(y,y_pos)
        x = np.append(x_neg, x)
        x = np.append(x, x_pos)        
        y_noise = np.random.normal(0, .03, y.shape)
        y = y + y_noise
        return x, y





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
