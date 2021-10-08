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

threshold_basic =  [[130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130]]




def data_basic():
    data_basic = {
        'gender' : 0,
        'id'    :   1,
        'Aérea' : threshold_basic,
        'Ósea' : threshold_basic,
        'LDL' : threshold_basic,
        'Aérea_mkg' :threshold_basic,
        'Ósea_mkg' : threshold_basic,
        "Z_OD": "A",
        "Z_OI": "A",
        "sector": "Camara_sono",
        "volume" : [0,0,"N/D"]
    }
    return data_basic

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

def create_voice(name, gender, id):
    file = "ogg/{}_{}{}.ogg".format(name, gender, id)
    result = QMediaContent(QUrl.fromLocalFile(appctxt.get_resource(file)))
    return result

def create_word(name):
    file = "ogg/{}".format(name)
    result = QMediaContent(QUrl.fromLocalFile(appctxt.get_resource(file)))
    return result

def create_word_response(name, sex, number):
    file = "ogg/LP_palacios_r_{}{}_{}.ogg".format(sex, number, name)
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




def minMax(trans, thr, type_mkg = "Narrow Band Noise", curve_z = "A"):
        UOne = thr[2]
        UAOne = thr[3]
        UA = thr[1]
        frecuency = thr[0]
        F_WN = 15
        F_NBN = 0
        EOCL = [0, 15, 15, 10, 0, 0, 0, 0, 0]
        AI_A = [35, 40, 40, 40, 45, 45, 50, 50, 50]
        if type_mkg == "Narrow Band Noise":
            RB = F_NBN
        else:
            RB = F_WN

        if curve_z == 'A':
            eoclu = EOCL[frecuency]
        else:
            eoclu = 0

        if trans == 0:
            AI = AI_A[trans]
        else:
            AI = 0

        AIa = AI_A[trans]

        Amin = UA - AI - UOne + UAOne + RB
        Amax = AIa+UOne
        Omin = UA - AI - UOne + UAOne + RB + eoclu
        if trans == 0:
            result = (Amax - Amin)/2
            result = int(result/5)
            result = result*5
            result = Amin + result

        else:
            result = (Amax-Omin)/2
            result = int(result/5)
            result = result*5
            result = Amin + result

        return result , Amax