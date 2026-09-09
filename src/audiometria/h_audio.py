from pathlib import Path
import copy
import random
import subprocess
import sys

from PySide6.QtCore import QUrl

from core.base import context
from audiometria import audio_synth
from core.helpers import Preferences

class_pref = Preferences()
stim_list = class_pref.get("stim_list")
stim_list_short = class_pref.get("stim_list_short")
series_response = class_pref.get("series_response")

threshold_basic =  [[130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130]]

def normalize(s):
    replacements = (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
        ("ñ", "n")
    )
    for a, b in replacements:
        s = s.replace(a, b).replace(a.upper(), b.upper())
    return s

def data_basic():
    # deepcopy: threshold_basic no puede compartirse tal cual entre las 5
    # claves -- son listas anidadas mutables, y mutar una (p.ej. al cargar
    # un umbral) mutaría las otras 4 al ser el mismo objeto
    return {
        'gender' : 0,
        'id'    :   1,
        'Aerea' : copy.deepcopy(threshold_basic),
        'Osea' : copy.deepcopy(threshold_basic),
        'LDL' : copy.deepcopy(threshold_basic),
        'Aerea_mkg' : copy.deepcopy(threshold_basic),
        'Osea_mkg' : copy.deepcopy(threshold_basic),
        'Fowler': {'freq': None, 'cuts': [15, 30, 50]},
        'Stenger': [False, False],
        'SISI': [0, 0],
        'decay': [False, False],
        # deterioro tonal por prueba: lista de [od, oi] en dB, un elemento
        # por frecuencia del protocolo (Carhart/Rosemberg: 500/1k/2k/4k --
        # Stat: 500/1k/2k), ver ResponseAudiometry.DECAY_TESTS
        'Carhart': [[0, 0], [0, 0], [0, 0], [0, 0]],
        'Stat': [[0, 0], [0, 0], [0, 0]],
        'Rosemberg': [[0, 0], [0, 0], [0, 0], [0, 0]],
        "Z_OD": "A",
        "Z_OI": "A",
        "sector": "Camara_sono",
        "volume" : [0,0,"N/D"]
    }

def create_sound(stim, f, ch):
    if stim in [stim_list[4],stim_list[5],stim_list[6]]:
        f = ""
    if stim == stim_list[3]:
        stim = stim_list_short[0]
    if stim == stim_list[4]:
        stim = stim_list_short[1]
    if stim == stim_list[5]:
        stim = stim_list_short[2]
    if stim == stim_list[6]:
        stim = stim_list_short[3]

    # Los tonos y ruidos se sintetizan al vuelo (ver lib/audio_synth.py) en vez
    # de leerse de mp3 estaticos. Si la sintesis no aplica, se usa el archivo.
    generated = audio_synth.stimulus_file(
        stim, f, ch, context.get_resource("audio"))
    if generated is not None:
        return QUrl.fromLocalFile(generated)

    file = f"audio/{stim}_{f}_{ch}.mp3"
    file = normalize(file)
    return QUrl.fromLocalFile(context.get_resource(file))

def create_voice(name, gender, idx):
    file = f"audio/{name}_{gender}{idx}.mp3"
    file = normalize(file)
    return QUrl.fromLocalFile(context.get_resource(file))

# Filtros ffmpeg para dejar la palabra sonando solo en el oído correspondiente:
# OD = solo canal derecho, OI = solo canal izquierdo.
_PAN_FILTERS = {
    "OD": "pan=stereo|c0=0*c0|c1=c0",
    "OI": "pan=stereo|c0=c0|c1=0*c0",
}


def _panned_word_file(rel_path, side):
    """Genera (y cachea en resources/audio/_panned) una versión del archivo
    panneada solo al oído indicado, para que no suene por ambos fonos."""
    suffix = "OD" if side == 0 else "OI"
    src = Path(context.get_resource(rel_path))
    dst = src.parent / "_panned" / f"{src.stem}_{suffix}{src.suffix}"
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                 "-af", _PAN_FILTERS[suffix], str(dst)],
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return str(src)  # ffmpeg no disponible: se reproduce sin pannear
    return str(dst)


def create_word(name, side=None):
    file = f"audio/{name}.mp3"
    file = normalize(file)
    if side is None:
        return QUrl.fromLocalFile(context.get_resource(file))
    return QUrl.fromLocalFile(_panned_word_file(file, side))

def create_word_response(name, sex, number):
    file = f"audio/LP_palacios_r_{sex}{number}_{name}.mp3"
    file = normalize(file)
    return QUrl.fromLocalFile(context.get_resource(file))


def create_frecuency(frecuency_dict, prueba, transductor=0,
                     high_frecuency=False):
    min_fr = frecuency_dict[prueba][transductor][0][0]
    max_fr = frecuency_dict[prueba][transductor][0][1]
    extras_fr = frecuency_dict[prueba][transductor][1]
    result = []
    i = 1

    def for_two(prev):
        return prev * 2

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

    if high_frecuency:
        hf_fr = frecuency_dict[prueba][transductor][2]
        for i in hf_fr:
            result.append(i)
    result.sort()
    return result

def create_intency(intency_list, step=5, f="1000", transductor=0,
                   ext=False):
    try:
        int(f)
    except Exception:
        f = "LOGO"
    min_db = intency_list[f][transductor][0][0]
    max_db = intency_list[f][transductor][1][0] if ext else intency_list[f][transductor][0][1]
    return [*range(min_db, max_db+1, step)]


def calibrate(val, div=5):
    resto = val % div
    return val - resto

def verify_threshold(ch, side, stim_level, response_list):
    pass

def random_response(series=True, prev = None, faraway=0):
    if prev is None:
        prev = [0,0]
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
    u_one = thr[2]
    ua_one = thr[3]
    u_a = thr[1]
    frecuency = thr[0]
    f_wn = 15
    f_nbn = 0
    e_ocl = [0, 15, 15, 10, 0, 0, 0, 0, 0]
    ai_a = [35, 40, 40, 40, 45, 45, 50, 50, 50]
    r_b = f_nbn if type_mkg == "Narrow Band Noise" else f_wn
    eoclu = e_ocl[frecuency] if curve_z == 'A' else 0
    a_i = ai_a[trans] if trans == 0 else 0
    ai_a = ai_a[trans]
    a_min = u_a - a_i - u_one + ua_one + r_b
    a_max = ai_a+u_one
    o_min = u_a - a_i - u_one + ua_one + r_b + eoclu
    result = (a_max - a_min)/2 if trans == 0 else (a_max-o_min)/2
    result = int(result/5) * 5
    result = a_min + result
    return result , a_max