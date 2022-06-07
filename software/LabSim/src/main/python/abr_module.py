# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                          VER. 0.7.5                           #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
"""abr_module
    Returns:
    [type]: [description]
"""

import random
import sys

import numpy as np

from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtGui import QFont

import lib.bezier_prop as bz
from lib.ABR_generator import ABR_creator
from lib.ABR_graph import Graph
from lib.EEG import EEG
from UI.Ui_ABR_config import Ui_ABR_config
from UI.Ui_ABR_control import Ui_ABRSim
from UI.Ui_ABR_ctrl_graph import Ui_ABR_control_curve
from UI.Ui_ABR_detail import Ui_ABR_detail
from UI.Ui_ABR_lat_select import Ui_ABR_lat_select


class AbrControl(QWidget, Ui_ABR_config):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)


class AbrDetail(QWidget, Ui_ABR_detail):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)


class AbrLatSelect(QWidget, Ui_ABR_lat_select):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.data = {'lat_A':0, 'lat_B':0,'amp_AB':0, 'lat_AB':0,
                    'I':0,'Ip':0,'II':0,'IIp':0,
                    'III':0,'IIIp':0,'IV':0,'IVp':0,
                    'V':0,'Vp':0, 'I_III' : 0,
                    'III_V' : 0, 'I_V' : 0}
        self.update_data()

    def update_data(self, key=None, value=None):

        if key is not None and value is not None:
            self.data[key] = value
            if self.data['I'] != 0 and self.data['III'] != 0:
                self.data['I_III'] = self.data['III'] - self.data['I']
            if self.data['I'] != 0 and self.data['V'] != 0:
                self.data['I_V'] = self.data['V'] - self.data['I']
            if self.data['III'] != 0 and self.data['V'] != 0:
                self.data['III_V'] = self.data['V'] - self.data['III']

        self.lbl_1.setText('A:{:.1f}ms B:{:.1f}ms'.format(self.data['lat_A'], self.data['lat_B']))
        self.lbl_2.setText('A-B:{:.2f}μV'.format(self.data['amp_AB']))
        self.lbl_3.setText('A<>B:{:.2f}ms'.format(self.data['lat_AB']))
        self.lbl_4.setText("I:{:.1f}ms I':{:.1f}ms".format(self.data['I'],self.data['Ip']))
        self.lbl_5.setText("II:{:.1f}ms II':{:.1f}ms".format(self.data['II'],self.data['IIp']))
        self.lbl_6.setText("III:{:.1f}ms III':{:.1f}ms".format(self.data['III'],self.data['IIIp']))
        self.lbl_7.setText("IV:{:.1f}ms IV':{:.1f}ms".format(self.data['IV'],self.data['IVp']))
        self.lbl_8.setText("V:{:.1f}ms V':{:.1f}ms".format(self.data['V'],self.data['Vp']))
        self.lbl_9.setText("I-III:{:.1f}ms".format(self.data['I_III']))
        self.lbl_10.setText("III-V:{:.1f}ms".format(self.data['III_V']))
        self.lbl_11.setText("I-V:{:.1f}ms".format(self.data['I_V']))


class AbrCtrlCurve(QWidget, Ui_ABR_control_curve):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)


class MainWindow(QWidget, Ui_ABRSim):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.control = AbrControl()
        self.detail = AbrDetail()
        self.eeg = EEG()
        self.detail.layout_eeg.addWidget(self.eeg.pw)

        self.lat_select_R = AbrLatSelect()
        self.lat_select_L = AbrLatSelect()
        self.ctrl_curve_R = AbrCtrlCurve()
        self.ctrl_curve_L = AbrCtrlCurve()

        self.grph_R = Graph(0)
        self.grph_L = Graph(1)

        #LAYOUTS
        self.layout_left.addWidget(self.control)
        self.layout_left.addWidget(self.detail)
        self.layout_left.addWidget(self.eeg)


        self.layourt_ctrl_R.addWidget(self.lat_select_R)
        self.layourt_ctrl_L.addWidget(self.lat_select_L)
        self.layout_ctrl_curve_R.addWidget(self.ctrl_curve_R)
        self.layout_ctrl_curve_L.addWidget(self.ctrl_curve_L)

        self.ctrl_curve_R.btn_up.clicked.connect(lambda:self.up_down(0))
        self.ctrl_curve_R.btn_down.clicked.connect(lambda:self.up_down(0))
        self.ctrl_curve_L.btn_up.clicked.connect(lambda:self.up_down(1))
        self.ctrl_curve_L.btn_down.clicked.connect(lambda:self.up_down(1))

        self.layout_graph_R.addWidget(self.grph_R.win)
        self.layout_graph_L.addWidget(self.grph_L.win)
        self.store = {}
        self.data = ABR_creator()

        self.grph_R.data_info.connect(self.update_data)
        self.grph_L.data_info.connect(self.update_data)
        #self.grph_L.lat_info.connect(self.update_data)
        #self.grph_R.lat_info.connect(self.update_data)

        self.lat_select_R.btn_wave_I.clicked.connect(lambda:self.update_markers(0,0,0))
        self.lat_select_R.btn_wave_II.clicked.connect(lambda:self.update_markers(0,1,0))
        self.lat_select_R.btn_wave_III.clicked.connect(lambda:self.update_markers(0,2,0))
        self.lat_select_R.btn_wave_IV.clicked.connect(lambda:self.update_markers(0,3,0))
        self.lat_select_R.btn_wave_V.clicked.connect(lambda:self.update_markers(0,4,0))

        self.lat_select_R.btn_wave_Ip.clicked.connect(lambda:self.update_markers(1,0,0))
        self.lat_select_R.btn_wave_IIp.clicked.connect(lambda:self.update_markers(1,1,0))
        self.lat_select_R.btn_wave_IIIp.clicked.connect(lambda:self.update_markers(1,2,0))
        self.lat_select_R.btn_wave_IVp.clicked.connect(lambda:self.update_markers(1,3,0))
        self.lat_select_R.btn_wave_Vp.clicked.connect(lambda:self.update_markers(1,4,0))

        self.lat_select_L.btn_wave_I.clicked.connect(lambda:self.update_markers(0,0,1))
        self.lat_select_L.btn_wave_II.clicked.connect(lambda:self.update_markers(0,1,1))
        self.lat_select_L.btn_wave_III.clicked.connect(lambda:self.update_markers(0,2,1))
        self.lat_select_L.btn_wave_IV.clicked.connect(lambda:self.update_markers(0,3,1))
        self.lat_select_L.btn_wave_V.clicked.connect(lambda:self.update_markers(0,4,1))

        self.lat_select_L.btn_wave_Ip.clicked.connect(lambda:self.update_markers(1,0,1))
        self.lat_select_L.btn_wave_IIp.clicked.connect(lambda:self.update_markers(1,1,1))
        self.lat_select_L.btn_wave_IIIp.clicked.connect(lambda:self.update_markers(1,2,1))
        self.lat_select_L.btn_wave_IVp.clicked.connect(lambda:self.update_markers(1,3,1))
        self.lat_select_L.btn_wave_Vp.clicked.connect(lambda:self.update_markers(1,4,1))

        self.lat_select_R.btn_AB.clicked.connect(lambda: self.toogle_flag_ab(0))
        self.lat_select_L.btn_AB.clicked.connect(lambda: self.toogle_flag_ab(1))
        self.memAB = ["A", "A"]

        self.detail.btn_start.clicked.connect(self.capture)
        self.ctrl_curve_R.btn_del.clicked.connect(lambda: self.clear_curve(0))
        self.ctrl_curve_L.btn_del.clicked.connect(lambda: self.clear_curve(1))
        self.currentCurve = [None, None]
        #self.control.sb
        #self.control

    def la_super(self, data):
        self.super_data = data
        self.entry = self.super_data['sector'] != 'ABR'

    def up_down(self, side):
        widgets = self.sender()
        direction = widgets.objectName()
        _,text= direction.split('_')
        curve = self.currentCurve[side]
        if curve is not None:
            if side == 0:
                self.grph_R.move_graph(text)
            else:
                self.grph_L.move_graph(text)

    def toogle_flag_ab(self, side):
        widget = self.sender()
        text = widget.text()
        if text == "|A":
            text = "B|"
            new = "B"
        else:
            text = "|A"
            new = "A"
        widget.setText(text)
        self.memAB[side] = new

    def clear_curve(self, side):
        try:
            self.store[self.currentCurve[side]][5] = False
            self.update_flags_curves()
            self.update_graph(side)
        except:
            pass

    def select_curve(self):
        widget = self.sender()
        objName = widget.objectName()
        _,x = objName.split('_')
        side,_ = x.split(':')
        if side == 'R':
            side = 0
            self.grph_R.activeCurve(objName, 0)
        else:
            side = 1
            self.grph_L.activeCurve(objName, 1)
        self.currentCurve[side] = objName
    def data_config_test(self):
        stim = self.control.cb_stim.currentText()
        pol = self.control.cb_pol.currentText()
        intencity = self.control.sb_intencity.value()
        filter_down = self.control.cb_filter_down.currentText()
        filter_up = self.control.cb_filter_up.currentText()
        prom = self.control.sb_prom.value()
        side = self.control.cb_side.currentText()
        rate = self.control.sb_rate.value()
        if side == 'OD':
            side = 0
            letter = 'R'
        else:
            side = 1
            letter = 'L'

        return {
            "stim":stim, "pol":pol, "intencity":intencity, 
            "filter_down":filter_down, "filter_up":filter_up, 
            "prom":prom, "side":side, "rate":rate, "letter":letter
            }
        
    def capture(self):
        data_config = self.data_config_test()
        gap = 1.8
        name = "{}_{}:0".format(data_config["intencity"], data_config["letter"])
        if name in self.store:
            name, _ = self.number_name(name, data_config["letter"], data_config["intencity"], gap)
        try:
            gap = self.cal_gap(name, data_config["letter"], data_config["intencity"], gap)
        except:
            pass
        view = True
        repro = random.randint(80,99)
        self.store[name] = [[[],[]],[[],[]],data_config["side"], data_config["intencity"], repro, view, gap]
        self.data.set_intencity(data_config["intencity"])
        x, y, _,_ = abr_curve(data_config=data_config, data=self.super_data)
        self.store[name][0][0] = x
        self.store[name][0][1] = y
        self.disabled_in_capture()
        self.update_flags_curves()
        self.update_graph(data_config["side"])
        self.currentCurve[data_config["side"]] = name
        self.grph_R.activeCurve(name, data_config["side"])
        self.grph_L.activeCurve(name, data_config["side"])

    def update_graph(self,side):
        self.grph_R.update_data(self.store, side)
        self.grph_L.update_data(self.store, side)
        self.disabled_in_capture(False)

    def update_flags_curves(self):
        for i in reversed(range( self.ctrl_curve_R.layout_curves.count())):
            self.ctrl_curve_R.layout_curves.itemAt(i).widget().deleteLater()
        for i in reversed(range( self.ctrl_curve_L.layout_curves.count())):
            self.ctrl_curve_L.layout_curves.itemAt(i).widget().deleteLater()
        btns_Left = []
        btns_Right = []
        for k in self.store:
            if self.store[k][5]:
                y, x = k.split('_')
                l,num = x.split(':')
                name = "{}".format(y)
                short = "{} {}{}".format(y, l, num)
                idx = k
                btn = [name,idx, short]
                if l == 'L':
                    btns_Left.append(btn)
                else:
                    btns_Right.append(btn)

        self.btn_flags(btns_Right, 0)
        self.btn_flags(btns_Left, 1)

    def btn_flags(self, btns, side):
        def style(side):
            color = "255,0,0" if side == 0 else "0,0,255"
            return f'QWidget{{color:rgb(0, 0, 0);\
                    background-color:rgb({color});\
                    border-style: outset;border-width: 0px;}}'

        for i in range(len(btns)):
            btn = QPushButton(f'{btns[i][0]}')
            btn.setObjectName(btns[i][1])
            btn.setStyleSheet(style(side))
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(self.select_curve)
            btn.setMaximumHeight(30)
            btn.setMaximumWidth(30)
            font = QFont()
            font.setPointSize(7)
            btn.setFont(font)
            btn.setToolTip('{}'.format(btns[i][2]))
            btn.setChecked(True)
            if side == 0:
                self.ctrl_curve_R.layout_curves.addWidget(btn)
            else:
                self.ctrl_curve_L.layout_curves.addWidget(btn)

    def number_name(self, name, ltr, tin, gap):
        n = []
        g = []
        db = []
        for i in self.store:
            dbi,x = i.split('_')
            l,num = x.split(':')
            if l == ltr:
                n.append(int(num))
            g.append(self.store[i][6])
            db.append(dbi)

        n.sort()
        g.sort(reverse=True)
        resultG = g[-1] -0.6
        resultN = n[-1]+1
        name = "{}_{}:{}".format(tin,ltr,resultN)
        return name , resultG

    def cal_gap(self, name, ltr, tin, gap):
        g = []
        for i in self.store:
            _,x = i.split('_')
            l,_ = x.split(':')
            if l == ltr:
                g.append(self.store[i][6])

        g.sort(reverse=True)
        return g[-1] -0.4

    def disabled_in_capture(self, dis = True):
        self.detail.btn_start.setDisabled(dis)
        self.control.sb_intencity.setDisabled(dis)
        self.control.cb_side.setDisabled(dis)

    def update_data(self, data):
        side = data["side"]
        keys = data.keys()

        for i in keys:
            if side == 0:
                self.lat_select_R.update_data(key=i, value=data[i])
            else:
                self.lat_select_L.update_data(key=i, value=data[i])

        #if 'lat_A' in data or 'lat_B' in data:
        #    self.AB = [[data['lat_A'], data['lat_B']], [data,data]]
        
    def update_markers(self, idx, subidx, side ):
        if side == 0:
            text = self.memAB[0]
            self.grph_R.update_marks(idx,subidx,text)
        else:
            text = self.memAB[1]
            self.grph_L.update_marks(idx,subidx,text)


def abr_peak(data, data_config):
    side = data_config["side"]
    if data is None:
        return [1.3,3.9,5.9,0.6]
    print(data['abr_peak'])
    if data_config["rate"] > 27.7:
        _extracted_from_abr_peak_7(data_config, data, side)
    print(data['abr_peak'])
    return data['abr_peak'][side]

# TODO Rename this here and in `abr_peak` fijarse como no debe hacer return
def _extracted_from_abr_peak_7(data_config, data, side):
    lat_plus = data_config["rate"]*0.01
    data['abr_peak'][side][0] += lat_plus / 4
    data['abr_peak'][side][1] += lat_plus - 0.2
    data['abr_peak'][side][2] += lat_plus - 0.1
    data['abr_peak'][side][3] += (-lat_plus)

def pathology(data, data_config):
    side = data_config["side"]
    if data is None:
        return 'Normal',True,True,True,True,True
    return data['abr_pathology'][side]

def abr_thr(data, data_config):
    if data is None:
        return 40,0.001,True, False

    side = data_config["side"]
    if data_config["filter_down"] == '3000' and data_config["filter_up"] == '100':
        noise = data['abr_threshold_other'][side][1]
    else:
        noise = 0.1
    if data_config["prom"] < 800:
        noise += 0.01
    elif data_config["prom"] < 2000:
        noise += 0.005
    elif data_config["prom"] < 3000:
        noise += 0.0001
    else:
        noise = 0.001

    data['abr_threshold_other'][side][1] = noise
    return data['abr_threshold_other'][side]



def abr_curve(data_config=None, data=None):
    """
    Calculate the ABR curve
    """
    nHL = data_config["intencity"]

    if data_config["stim"] == "Chirp":
        plus_lat_chirp = -0.2 if nHL > 40 else 0.2
        plus_amp_chirp = 0.3
    else:
        plus_amp_chirp = 0
        plus_lat_chirp = 0


    p_I,p_III,p_V,a_V = abr_peak(data,data_config)
    pato,I,II, III, IV, V = pathology(data,data_config)
    threshold, noise, VrelI, zeros = abr_thr(data, data_config)
    att = 0
    lam = 0
    varInt = abs(80 - nHL)
    fvarInt = varInt/5
    if pato == 'Neural':
        var_lat_init = .1
        var_lat_end = .3

    elif pato == 'Normal':
        var_lat_init = -.05
        var_lat_end = .05

    else:
        var_lat_init = 0
        var_lat_end = 0

    lat_random = random.uniform(var_lat_init,var_lat_end)
    amp_random = random.uniform(var_lat_init, var_lat_end)

    if nHL > 80:
        sideAmp = 1
        sideLat = -1
    else:
        sideAmp = -1
        sideLat = 1

    if nHL >=50:
        fvarLat = .15
        fvarAmp = .04
    elif pato != 'Sensorial':
        fvarLat = .2
        fvarAmp = .06
    else:
        fvarLat = .3
        fvarAmp = .08

    att = (fvarLat * fvarInt) * sideLat
    lam = (fvarAmp * fvarInt) * sideAmp

    peak_I =  p_I + att  + lat_random
    peak_II =  p_I+1+ att  + lat_random

    peak_III =  p_III + att  + lat_random
    peak_V =  p_V + att  + lat_random + plus_lat_chirp

    peak_IV = peak_V-.5  + lat_random
    end = 12 + att
    amp_V = a_V + lam + amp_random + plus_amp_chirp
    amp_V = max(amp_V, 0)
    if threshold == nHL:
        amp_V += 0.1
    elif threshold > nHL:
        amp_V = 0
        n = random.random()*.01
        noise += n
    else:
        n = random.random()*.1
        amp_V += n

    amp_I = amp_V / 3 if VrelI else amp_V / 1.5
    amp_I = amp_I + lam
    amp_I = max(amp_I, 0)
    amp_Ip = -(amp_I/2)
    amp_II = amp_Ip+0.1
    amp_IIp = amp_II-.02

    if amp_Ip == 0:
        amp_II = 0
        amp_IIp=0

    amp_III = 0.3 +lam + amp_random
    amp_III = max(amp_III, 0)
    amp_IIIp = 0

    if III == False:
        amp_III = 0
        amp_IIIp = 0

    amp_VI = amp_V -.3

    amp_VI = max(amp_VI, 0)
    curve_cm = (0.6+att, 0.15)
    curve_cmp = (0.7+att, -0.05)

    curve_I = (peak_I,amp_I/2)
    curve_Ip = (curve_I[0]+.5,amp_Ip)

    curve_II = (peak_II, amp_II)
    curve_IIp = (curve_II[0]+.3,curve_II[1]-.02)

    curve_III = (peak_III,amp_III)
    curve_IIIp = (curve_III[0]+.9,amp_IIIp)

    #curve_III = (peak_III,amp_III)
    #curve_IIIp = (curve_III[0]+.9,0)


    VrefIII = (random.uniform(-.1,.1)) + curve_III[1]
    curve_V = (peak_V,VrefIII)

    amp_IV = VrefIII-.05
    amp_IV = max(amp_IV, 0)
    amp_IVp = amp_IV-.05
    amp_IVp = max(amp_IVp, 0)
    sn10refV = curve_V[1] - amp_V
    sn10refV = min(sn10refV, 0)
    sn10 = (curve_V[0]+1,sn10refV)

    curve_IV = (peak_IV, amp_IV)
    curve_IVp = (curve_IV[0]+.05, amp_IVp)

    curve_VI = (sn10[0]+1.5, amp_VI)
    curve_VIp = (curve_VI[0]+1.5, curve_VI[1]-.3)
    curve_VII = (curve_VIp[0]+1.5, curve_VIp[1]+.6)

    #print(sn10refV)

    points = np.array([
            [0,0],


            [curve_cmp[0],curve_cmp[1]],

            [curve_I[0],curve_I[1]],
            [curve_Ip[0],curve_Ip[1]],

            [curve_II[0],curve_II[1]],
            [curve_IIp[0],curve_IIp[1]],

            [curve_III[0],curve_III[1]],
            [curve_IIIp[0],curve_IIIp[1]],

            [curve_IV[0], curve_IV[1]],
            [curve_IVp[0], curve_IVp[1]],

            [curve_V[0],curve_V[1]],
            [sn10[0],sn10[1]],

            [curve_VI[0],curve_VI[1]],
            [curve_VIp[0],curve_VIp[1]],
            [curve_VII[0],curve_VII[1]],
            [end,0]        
    ])
    Bezi = bz.Bezier()
    path = Bezi.evaluate_bezier(points, 20)

    # extract x & y coordinates of points
    x, y = points[:,0], points[:,1]
    px, py = path[:,0], path[:,1]
    rho = 1
    sigma = rho * np.sqrt(noise/2)
    y_noise = np.random.normal(0,sigma , py.shape)
    y_new = py + y_noise
    if zeros:
        px = np.zeros(20)
        y_new = np.zeros(20)
    return px, y_new, x, y

#px, y_new = ABR_Curve()
