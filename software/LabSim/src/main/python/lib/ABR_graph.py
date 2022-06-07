import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from lib.helpers import Storage


class Graph(QWidget):
    data_info = Signal(dict)
    lat_info = Signal(dict)
    def __init__(self, side):
        self.side = side
        QWidget.__init__(self)
        color_backgorund = pg.mkColor(255, 255, 255, 255)
        self.color_pen = pg.mkColor(0, 0, 0, 255)
        pg.setConfigOption('background', color_backgorund)
        pg.setConfigOption('foreground', self.color_pen)
        self.win = pg.GraphicsLayoutWidget(show=True)
        self.pw1 = self.win.addPlot(row=1,col=0)
        self.pw1.setRange(yRange=(-3, 3), xRange=(0, 13), disableAutoRange=True)
        self.pw1.showGrid(x=True, y=True)
        self.pw1.setMouseEnabled(x=False, y=False)
        self.pw1.setMenuEnabled(False)
        ay = self.pw1.getAxis('left')
        ay.setStyle(showValues=False)
        self.act_curve = str()
        self.marks = {}
        self.inf_a = None
        self.inf_b = None

    def find_nearest(self, array_in, value, array_out):
        array = np.asarray(array_in)
        idx = (np.abs(array - value)).argmin()
        return array_out[idx]

    def find_idx(self, array_in, value):
        array = np.asarray(array_in)
        return (np.abs(array - value)).argmin()

    def inifine_ab(self, pos_A = 0, pos_B = 12):
        if self.inf_a is not None and self.inf_b is not None:
            self.pw1.removeItem(self.inf_a)
            self.pw1.removeItem(self.inf_b)

        #Variables internas
        pen1 = pg.mkPen('b', width=.5, style=Qt.PenStyle.DashLine)         
        opst = {'position':0.9, 'color': (255,255,255), 'fill': (0,0,0,255), 'movable': True}
        name_a = "A{}".format(self.side)
        name_b = "B{}".format(self.side)
        #Lineas infinitas
        self.inf_a = pg.InfiniteLine(pos=pos_A, movable=True, angle=90, pen=pen1, label ="A", labelOpts=opst, name=name_a)
        self.inf_b = pg.InfiniteLine(pos=pos_B, movable=True, angle=90, pen=pen1, label ="B", labelOpts=opst, name=name_b)
        #Posición en X de las lineas infinitas
        self.inf_a.sigPositionChanged.connect(self.get_amplitude)
        self.inf_b.sigPositionChanged.connect(self.get_amplitude)
        #Se agregan lineas infinitas a la grafica
        self.pw1.addItem(self.inf_a)
        self.pw1.addItem(self.inf_b)

    def update_data(self, data, side):
        if self.side != side:
            return

        mem = {}
        for i in data:
            side_in = data[i][2]
            if side_in == self.side:
                mem[i] = data[i]
        self.data = mem
        marks_flags = [Storage(5),Storage(5)]
        for i, value in self.data.items():
            if value[2] == self.side and i not in self.marks:
                self.marks[i] = marks_flags
        self.update_graph()

    def update_graph(self):
        self.clearGraph()
        try:
            pos_A = self.inf_a.getXPos()
            pos_B = self.inf_b.getXPos()
        except:
            pass
        for i in self.data:
            if self.act_curve == i:
                act = True
            else:
                act = False
            if self.data[i][5]:
                color_name = self.data[i][2]
                if color_name == 0:
                    if act :
                        color = pg.mkColor(255, 0, 0, 255)
                        fill = (255,0,0)
                    else:
                        color = pg.mkColor(180, 0, 0, 255)
                        fill = (180,0,0)
                else:
                    if act:
                        color = pg.mkColor(50, 50, 255, 255)
                        fill = (50,50,255)
                    else:
                        color = pg.mkColor(0, 0, 100, 255)
                        fill = (0,0,180)

                lbl = """
                    <div style='text-align: center'>
                    <span style='color: #FFF; font-size: 7pt;'>{}dBnHl</span></div>
                    """.format(self.data[i][3])
                text = pg.TextItem(html=lbl, border="w", fill=fill)
                self.pw1.addItem(text)
                x = self.data[i][0][0]
                y = self.data[i][0][1]  + self.data[i][6]
                h = self.find_nearest(x,x.max(),y)
                text.setPos(12, h)
                self.pw1.plot(x,y, pen=color, name =i) #ahora cada curva tiene su nombre
            
            try:
                self.inifine_ab(pos_A, pos_B)
                self.refresh_keys()
            except:
                self.inifine_ab()
 
    def clearGraph(self):
        y, x = [],[]        
        self.pw1.plot(x, y, pen='w', clear=True)

    def create_marks(self, idx, subidx, curveName = None, useAct = True):
        curve = self.act_curve if useAct else curveName
        lbl_marks = [
            ["I","II","III","IV","V", "VI","VII"],
            ["I'","II'","III'","IV'","V'", "VI'", "VII'"]
            ]
        lbl = lbl_marks[idx][subidx]
        id_X = self.marks[curve][idx].get(subidx)
        lat = self.data[curve][0][0][id_X]
        amp = self.data[curve][0][1][id_X] + self.data[curve][6]
        curve_mark = "|{}".format(lbl)
        text = pg.TextItem(text = curve_mark, anchor=(0.34,0.5), color=(0,0,0,255))
        text.setPos(lat, amp+0.1)
        self.pw1.addItem(text)

    def refresh_keys(self):
        for k in self.data:
            curve = k
            for i in range(2):
                for d , val in enumerate(self.marks[curve][i].data):
                    if val is not None:
                        self.create_marks(i,d,curveName=curve, useAct=False)

    def update_marks(self,idx, subidx, btn='A'):
        lat = self.inf_a.getXPos() if btn == 'A' else self.inf_b.getXPos()
        curve = self.act_curve
        id_x = self.find_idx(self.data[curve][0][0], lat)
        self.marks[curve][idx].set(subidx, id_x)
        self.update_graph()

    def activeCurve(self, curve, side):
        if side == self.side:
            self.act_curve = curve
            self.update_graph()

    def move_graph(self, str_ud):
        curve = self.act_curve
        try:
            y = self.data[curve][6]
            if str_ud == "up":
                y = y + .1
            if str_ud == "down":
                y = y - .1
            self.data[curve][6] = y
            self.update_graph()
        except:
            pass
    
    def get_amplitude(self):
        x = self.data[self.act_curve][0][0]
        y = self.data[self.act_curve][0][1]
        lat_a = self.inf_a.getXPos()
        if lat_a > 12:
            pos_b = self.inf_b.getXPos()
            self.inifine_ab(pos_A=12, pos_B=pos_b)
        if lat_a < 0:
            pos_b = self.inf_b.getXPos()
            self.inifine_ab(pos_A=0, pos_B=pos_b)
        lat_b = self.inf_b.getXPos()
        if lat_b > 12:
            pos_a = self.inf_a.getXPos()
            self.inifine_ab(pos_A=pos_a, pos_B=12)
        if lat_b < 0:
            pos_a = self.inf_a.getXPos()
            self.inifine_ab(pos_A=pos_a, pos_B=0)
        amp_a = self.find_nearest(x, lat_a, y)
        amp_b = self.find_nearest(x, lat_b, y)
        order_amp = np.sort(np.array([amp_a,amp_b]))
        order_lat = np.sort(np.array([lat_a,lat_b]))
        dif_amp = order_amp[1] - order_amp[0]
        dif_lat = order_lat[1] - order_lat[0]
        response = {"side": self.side, "lat_A": lat_a, "lat_B": lat_b, "amp_AB": dif_amp, "lat_AB": dif_lat}
        self.data_info.emit(response)
