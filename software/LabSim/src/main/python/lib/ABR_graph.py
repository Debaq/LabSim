
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from lib.h_z import storage


class Graph(QWidget):
    data_info = pyqtSignal(dict)
    lat_info = pyqtSignal(dict)
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
        ax = self.pw1.getAxis('bottom')
        ay = self.pw1.getAxis('left')
        ay.setStyle(showValues=False)
        self.actCurve = str()
        self.inifineA_B()
        self.marks = dict()
        #self.x = 0
        #self.y = 0
        #self.marks = {'I': None, 'II':None, 'III':None, 'IV':None, 'V':None,
        #              'Ip': None, 'IIp':None, 'IIIp':None, 'IVp':None, 'Vp':None}
        #self.change_mark = False


    def find_nearest(self, array_in, value, array_out):
        array = np.asarray(array_in)
        idx = (np.abs(array - value)).argmin()
        return array_out[idx]

    def find_idx(self, array_in, value):
        array = np.asarray(array_in)
        idx = (np.abs(array - value)).argmin()
        return idx

    def inifineA_B(self, pos_A = 0, pos_B = 12):
        try:
            self.pw1.removeItem(self.inf_A)
            self.pw1.removeItem(self.inf_B)
        except:
            pass

        #Variables internas
        pen1 = pg.mkPen('b', width=.5, style=Qt.DashLine)         
        opst = {'position':0.9, 'color': (255,255,255), 'fill': (0,0,0,255), 'movable': True}
        #Lineas infinitas
        self.inf_A = pg.InfiniteLine(pos=pos_A, movable=True, angle=90, pen=pen1, label ="A", labelOpts=opst)
        self.inf_B = pg.InfiniteLine(pos=pos_B, movable=True, angle=90, pen=pen1, label ="B", labelOpts=opst)
        #self.inf_B.setBounds(0,10)
        #Posición en X de las lineas infinitas
        self.inf_A.sigPositionChanged.connect(self.get_amplitude)
        self.inf_B.sigPositionChanged.connect(self.get_amplitude)
        #Se agregan lineas infinitas a la grafica
        self.pw1.addItem(self.inf_A)
        self.pw1.addItem(self.inf_B)

    def update_graph(self, side):
        self.clearGraph()
        pos_A = self.inf_A.getXPos()
        pos_B = self.inf_B.getXPos()
        for i in self.data:
            if self.actCurve == i:
                act = True
            else:
                act = False
            if self.data[i][2] == side:
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
                    self.pw1.plot(x,y, pen=color)
            self.inifineA_B(pos_A, pos_B)
            try:
                self.refresh_keys()
            except:
                pass
 

    def clearGraph(self):
        y, x = [],[]        
        self.pw1.plot(x, y, pen='w', clear=True)

    def update_data(self, data, side):
        Marks = [storage(5),storage(5)]
        self.data = data
        for i in self.data:
            if self.data[i][2] == side:
                if not i in self.marks:
                    self.marks[i] = Marks
        self.update_graph(side)

    def create_marks(self, idx, subidx, curveName = None, useAct = True):
        if useAct:
            curve = self.actCurve
        else:
            curve = curveName

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
        
    """
    def change_keys(self, key=None, value=None):
        if key is not None and value is not None:
            self.change_mark = True
            self.marks[key] =  value
            self.update_graph()
    """

    def refresh_keys(self):
        for k in self.data:
            curve = k
            for i in range(2):
                for d , val in enumerate(self.marks[curve][i].data):
                    if val is not None:
                        self.create_marks(i,d,curveName=curve, useAct=False)

    def update_marks(self,side, idx, subidx, btn='A'):
        if btn == 'A':
            lat = self.inf_A.getXPos()
        else:
            lat = self.inf_B.getXPos()
        curve = self.actCurve
        id_X = self.find_idx(self.data[curve][0][0], lat)
        self.marks[curve][idx].set(subidx, id_X)
        self.update_graph(side)
        self.refresh_keys()

    def activeCurve(self, curve, side):
        self.actCurve = curve
        self.update_graph(side)

    def move_graph(self, str_ud, curve, side):
        try:
            y = self.data[curve][6]
            if str_ud == "up":
                y = y + .1
            if str_ud == "down":
                y = y - .1
            self.data[curve][6] = y
            self.update_graph(side)
        except:
            pass
    
    def get_amplitude(self):
        x = self.data[self.actCurve][0][0]
        y = self.data[self.actCurve][0][1]

        lat_A = self.inf_A.getXPos()
        
        if lat_A > 12:
            pos_B = self.inf_B.getXPos()
            self.inifineA_B(pos_A=12, pos_B=pos_B)
        if lat_A < 0:
            pos_B = self.inf_B.getXPos()
            self.inifineA_B(pos_A=0, pos_B=pos_B)
        
        
        lat_B = self.inf_B.getXPos()
        if lat_B > 12:
            pos_A = self.inf_A.getXPos()
            self.inifineA_B(pos_A=pos_A, pos_B=12)
        if lat_B < 0:
            pos_A = self.inf_A.getXPos()
            self.inifineA_B(pos_A=pos_A, pos_B=0)

        amp_A = self.find_nearest(x, lat_A, y)
        amp_B = self.find_nearest(x, lat_B, y)
        order_amp = np.sort(np.array([amp_A,amp_B]))
        order_lat = np.sort(np.array([lat_A,lat_B]))
        
        dif_amp = order_amp[1] - order_amp[0]
        dif_lat = order_lat[1] - order_lat[0]
        
        response = {"side": self.side, "lat_A": lat_A, "lat_B": lat_B, "amp_AB": dif_amp, "lat_AB": dif_lat}
        #print(amp_B)
        self.data_info.emit(response)
        #self.lat_info.emit(self.marks)
