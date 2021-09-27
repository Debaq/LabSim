import numpy as np
import bezier_prop as bz
import random
import collections
from helpers import Preferences

class_pref = Preferences()


class ABR_creator():
    def __init__(self, dBnHL = 80, VrelI = True):
        basicData = (class_pref.get("ABR_Normal"))[str(dBnHL)]
        self.intencity = dBnHL
        self.data = self.cal_data(basicData)

    def reset(self):
        self.intencity = 80
        self.basicData = class_pref.get("ABR_Normal")

    def cal_data(self, data):
        early = ["MC", "I", "II"]
        late = ["III", "IV", "V", "VI", "VII"]
        earlyGroup, lateGroup= {},{}
        for i in early:
            earlyGroup[i] = data[i]
        for i in late:
            lateGroup[i] = data[i]
        return [self.intencity, earlyGroup, lateGroup]       
  
    def get(self):
        pass

    def set_intencity(self, dBnHL):
        self.prevInt = self.data[0]
        self.data[0] = int(dBnHL)
        self.attenuator()
        self.updateCurve()

    def attenuator(self):
        if self.data[0] >=50:
            fvarLat = .15
            fvarAmp = .05
        else:
            fvarLat = .3
            fvarAmp = .06
        varInt = abs(self.prevInt - self.data[0])
        fvarInt = varInt/5
        if self.prevInt < self.data[0]:
            sideAmp = 1
            sideLat = -1
            #text = "subiendo"
        else:
            sideAmp = -1
            sideLat = 1
            #text = "bajando"

        varLat = (fvarLat * fvarInt) * sideLat
        varAmp = (fvarAmp * fvarInt) * sideAmp
        #print("{}:{} veces  amp:{}/lat:{} int:{}/prev:{} ".format(text, fvarInt, varAmp, varLat, self.data[0], self.prevInt))

        for k,i in self.data[2].items():
            newLat = round(i[0] + varLat,2)
            newAmp = round(i[2] + varAmp,2)
            newAmp = 0 if newAmp < 0 else newAmp
            self.data[2][k][0] = newLat
            self.data[2][k][2] = newAmp
        for k,i in self.data[1].items():
            newLat = round(i[0] + varLat,2)
            newAmp = round(i[2] + varAmp,2)
            newAmp = 0 if newAmp < 0 else newAmp
            self.data[1][k][0] = newLat
            self.data[1][k][2] = newAmp
        #self.cal_lat(varLat, varAmp)

        

    def updateCurve(self):
        prevPoints=[]
        data = dict(self.data[1], **self.data[2])
        
        print(data)
        for k,i in data.items():
            width = i[1]
            f1p = [i[0] - (width/2), 0]
            f2p = [i[0],i[1]]
            f3p = [i[0] + (width/2), 0]
            prevPoints.append(f1p) 
            prevPoints.append(f2p) 
            prevPoints.append(f3p)

        print(prevPoints)

       
        #Bezi = bz.Bezier()
        #path = Bezi.evaluate_bezier(points, 20)

        # extract x & y coordinates of points
        #x, y = points[:,0], points[:,1]
        #px, py = path[:,0], path[:,1]

        #y_noise = np.random.normal(0, .01, py.shape)
        #y_new = py + y_noise

        #return px, y_new


I = ABR_creator()
while True:
    i = input(":")
    if i==type("q"):
        break
    else:
        I.set_intencity(i)

