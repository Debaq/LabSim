from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaContent
import random

from lib.helpers import Preferences

appctxt = ApplicationContext()
class_pref = Preferences()
stim_list = class_pref.get("stim_list")
stim_list_short = class_pref.get("stim_list_short")
series_response = class_pref.get("series_response")



def create_sound(stim, f, ch):
    if stim == stim_list[4] or stim == stim_list[5] or stim == stim_list[6]:
        f = ""
    if stim == stim_list[3]:
        stim = stim_list_short[0]
    if stim == stim_list[4]:
        stim = stim_list_short[1]
    if stim == stim_list[5]:
        stim = stim_list_short[2]
    if stim == stim_list[6]:
        stim = stim_list_short[3]

    file = "ogg/{}_{}_{}.ogg".format(stim, f, ch)
    result = QMediaContent(QUrl.fromLocalFile(appctxt.get_resource(file)))
    return result


def create_frecuency(frecuency_dict, prueba, transductor=0,
                     Hf=False):
    min_fr = frecuency_dict[prueba][transductor][0][0]
    max_fr = frecuency_dict[prueba][transductor][0][1]
    extras_fr = frecuency_dict[prueba][transductor][1]
    result = []
    i = 1

    def for_two(prev):
        r = prev * 2
        return r

    while True:
        if i == 1:
            result.append(min_fr)
            i = 0
        if result[-1] > max_fr:
            result.pop(-1)
            break
        new = for_two(result[-1])
        result.append(new)
    for i in extras_fr:
        result.append(i)

    if Hf:
        hf_fr = frecuency_dict[prueba][transductor][2]
        for i in hf_fr:
            result.append(i)
    result.sort()
    return result


def create_intency(intency_list, step=5, f="1000", transductor=0,
                   ext=False):
    try:
        int(f)
    except:
        f = "LOGO"
    min_db = intency_list[f][transductor][0][0]
    max_db = intency_list[f][transductor][1][0] if ext else intency_list[f][transductor][0][1]
    result = [*range(min_db, max_db+1, step)]
    return result


def calibrate(val, div=5):
    resto = val % div
    result = val - resto
    return result

def verify_threshold(ch, side, stim_level, response_list):
    pass

def random_response(series=True, prev = [0,0], faraway=0):
    series =[series_response["series_0"],
             series_response["series_25"],
             series_response["series_50"],
             series_response["series_75"],
             series_response["series_100"]
             ] 
    faraway_list = [-3,-2,-1,0,1]
    faraway_index = faraway_list.index(faraway)
    result = series[faraway_index][prev[0]][prev[1]] #me gusrtaria que comenzara en una lista aleatoria
     
    dif_list = [7,6,5,4,3]
    dif = dif_list[faraway_index] 
     
    rise = random.randint(1,dif)*100
        
    if prev[1] < 5:
        prev[1] = prev[1] + 1
    if prev[1] >= 5:
        if prev[0] < 3:
            prev[0] = prev[0]+1
        if prev[0] >=3:
            prev[0] = 0
        prev[1] = 0

    return  result , prev, rise


