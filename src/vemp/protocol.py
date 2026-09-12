"""
Vocabulario clínico del VEMP: qué se registra, de qué músculo y con qué.

Todo lo que el examen tiene de propio --y que un potencial auditivo no
tiene-- está declarado acá, en un solo lugar y sin Qt, para que el motor,
la UI y el informe lean lo mismo:

- El VEMP NO es una respuesta neural que se promedia y aparece: es una
  MODULACIÓN DE UNA CONTRACCIÓN MUSCULAR. Sin músculo contraído no hay nada
  que modular, y la amplitud cruda escala casi lineal con cuánto contrae el
  paciente (ver `MANIOBRAS` y `EMG_REFERENCIA`). Por eso la métrica del
  examen es la AMPLITUD CORREGIDA (cruda / EMG rectificado), y no la cruda.
- Cada subtipo registra OTRO músculo y por OTRA vía: el cVEMP es un reflejo
  inhibitorio ipsilateral del esternocleidomastoideo, el oVEMP es excitatorio
  y CRUZADO (se estimula un oído y se registra bajo el ojo CONTRARIO).
- El estímulo llega por vía aérea o por vibración ósea en mastoides. Eso
  importa: un oído medio que no transmite apaga el VEMP aéreo sin que haya
  una sola célula vestibular enferma, y el óseo lo salva (ver
  `umbral_oseo`).

Las claves de subtipo (CVEMP/OVEMP/MVEMP) y de pico (p13/n23/n10/p16) son
las mismas que guarda el caso (CaseForm::parseVemp) y las que edita el
docente en la ficha: acá no se renombra nada del contrato.
"""

CVEMP = 'CVEMP'
OVEMP = 'OVEMP'
MVEMP = 'MVEMP'
SUBTIPOS = (CVEMP, OVEMP, MVEMP)

LADOS = ('OD', 'OI')

# Nombre corto (píldoras, tablas) y largo (combo, informe).
SUBTIPO_CORTO = {CVEMP: 'cVEMP', OVEMP: 'oVEMP', MVEMP: 'mVEMP'}
# Corto a propósito: el combo del panel es angosto y el músculo completo ya
# está abajo, en la línea de montaje.
SUBTIPO_LABEL = {
    CVEMP: 'cVEMP · cervical',
    OVEMP: 'oVEMP · ocular',
    MVEMP: 'mVEMP · masetérico',
}

# Picos de cada subtipo, en orden de aparición. La inicial es la polaridad:
# p = deflexión positiva, n = negativa.
PEAKS = {
    CVEMP: ('p13', 'n23'),
    OVEMP: ('n10', 'p16'),
    MVEMP: ('p13', 'n23'),
}

# Músculo registrador y lado del registro respecto del oído estimulado.
# 'ipsi': el electrodo va del mismo lado que el oído estimulado.
# 'contra': va del lado contrario -- el oVEMP es una vía cruzada, y el
# alumno que pega el electrodo del mismo lado registra el oído equivocado.
MUSCULO = {
    CVEMP: ('esternocleidomastoideo', 'ipsi'),
    OVEMP: ('oblicuo inferior (infraorbitario)', 'contra'),
    MVEMP: ('masetero', 'ipsi'),
}

# Ventana de registro (ms). Empieza antes del estímulo: la línea de base
# pre-estímulo es con lo que se compara la respuesta.
VENTANA = {
    CVEMP: (-5.0, 60.0),
    OVEMP: (-5.0, 40.0),
    MVEMP: (-5.0, 60.0),
}
N_PUNTOS = 900

# Ancho (sigma, ms) de cada pico. El VEMP es una respuesta miogénica: sus
# picos duran milisegundos, no décimas. El complejo p13-n23 completo ocupa
# ~15 ms y por eso las dos gaussianas son anchas y se solapan.
SIGMA_PICO = {
    'p13': 2.6,
    'n23': 3.4,
    'n10': 1.5,
    'p16': 2.0,
}

# Componente tardío pequeño que sigue al complejo principal (n34/p44 del
# cVEMP). No se mide, pero sin él el trazo termina en una recta y se nota.
COLA = {
    CVEMP: (34.0, -0.22, 4.0),   # (latencia ms, fracción del pico 1, sigma)
    MVEMP: (34.0, -0.20, 4.0),
    OVEMP: (23.0, -0.18, 3.0),
}

# --- Maniobras -----------------------------------------------------------
# (etiqueta, EMG tónico medio en µV rectificados, fatiga por minuto).
#
# La PRIMERA de cada subtipo es la posición SIN contracción y es donde
# arranca el control: no es un default "correcto" precargado, es lo que el
# alumno tiene que darse cuenta de que falta.
#
# `fatiga` es cuánto pierde ese músculo por minuto de contracción sostenida.
# Elevar la cabeza en decúbito da mucho EMG y se cae rápido; la rotación
# cefálica da menos y aguanta. Es la decisión de técnica que el examen tiene
# y el módulo no mostraba.
MANIOBRAS = {
    CVEMP: (
        ('Relajado (decúbito)', 7.0, 0.00),
        ('Rotación cefálica sostenida', 52.0, 0.10),
        ('Presión contra la mano del examinador', 68.0, 0.18),
        ('Elevación de la cabeza en decúbito', 98.0, 0.34),
    ),
    OVEMP: (
        ('Mirada al frente', 6.0, 0.00),
        ('Mirada superior ~30°', 44.0, 0.08),
        ('Mirada superior forzada', 72.0, 0.22),
    ),
    MVEMP: (
        ('Mandíbula relajada', 5.0, 0.00),
        ('Mordida sostenida', 58.0, 0.12),
        ('Mordida máxima', 92.0, 0.30),
    ),
}

# EMG con el que está medida la amplitud normativa de cada subtipo: es el
# divisor de la amplitud corregida.
EMG_REFERENCIA = {CVEMP: 50.0, OVEMP: 40.0, MVEMP: 55.0}

# Banda de EMG dentro de la cual el equipo acepta los barridos. Fuera de
# ella el barrido se descarta (músculo flojo = nada que modular; músculo
# disparado = artefacto).
EMG_BANDA = {CVEMP: (30.0, 150.0), OVEMP: (20.0, 120.0), MVEMP: (25.0, 140.0)}

# --- Estímulo ------------------------------------------------------------
AEREO = 'Inserto (vía aérea)'
OSEO = 'Vibrador óseo (mastoides)'
TRANSDUCTORES = (AEREO, OSEO)

FRECUENCIAS = ('500 Hz', '750 Hz', '1000 Hz')
FREQ_HZ = {'500 Hz': 500, '750 Hz': 750, '1000 Hz': 1000}
# Clave de la normativa (normative_data.json solo trae 500 y 1000; 750 se
# interpola, ver norms.baseline).
FREQ_NORMA = {'500 Hz': '500Hz', '1000 Hz': '1000Hz'}

POLARIDADES = ('Rarefacción', 'Condensación', 'Alternante')

# Rango de intensidad por transductor (dB). El aéreo se expresa en dB SPL,
# que es la escala en la que el caso guarda el umbral del paciente; el óseo
# en dB FL, con el tope de salida del vibrador.
RANGO_INTENSIDAD = {AEREO: (50, 125), OSEO: (20, 75)}
PASO_INTENSIDAD = 5

# Ventaja del vibrador: a igualdad de oído interno, el umbral óseo del VEMP
# cae por debajo del aéreo. El valor es DECLARADO (no sale de una tabla
# normativa): sirve para que el óseo tenga un rango de trabajo propio y
# para que el examen aéreo y el óseo no compartan escala.
OSEO_VENTAJA_DB = 15.0

# Intensidad a la que está definida la normativa.
INTENSIDAD_REFERENCIA = 100.0
# Nivel de sensación al que la amplitud ya llegó a la normativa: por encima
# del umbral el VEMP crece rápido y satura.
SL_SATURACION_DB = 25.0
# Corrimiento de latencia por intensidad: en el VEMP es casi plano.
PENDIENTE_LAT_MS_10DB = 0.06

# --- Registro ------------------------------------------------------------
TASA_HZ = (3.1, 20.0)          # rango del control de tasa de estímulo
PROMEDIOS = (50, 1000)         # rango del control de promediaciones
FILTRO_PASA_ALTO = (1.0, 30.0)
FILTRO_PASA_BAJO = (500.0, 3000.0)
# Nivel de rechazo de artefactos, como múltiplo del EMG tónico esperado.
# Por debajo de 2 el equipo rechaza casi todo; por encima de 8 no rechaza
# nada y entran los artefactos al promedio.
RECHAZO = (2.0, 8.0)


def maniobras_de(subtipo):
    return [nombre for nombre, _emg, _fat in MANIOBRAS.get(subtipo, MANIOBRAS[CVEMP])]


def maniobra_emg(subtipo, maniobra):
    """(EMG tónico µV, fatiga por minuto) de la maniobra. Sin maniobra
    válida devuelve la primera, que es la posición sin contracción."""
    opciones = MANIOBRAS.get(subtipo, MANIOBRAS[CVEMP])
    for nombre, emg, fatiga in opciones:
        if nombre == maniobra:
            return emg, fatiga
    return opciones[0][1], opciones[0][2]


def emg_en_banda(subtipo, emg):
    lo, hi = EMG_BANDA.get(subtipo, EMG_BANDA[CVEMP])
    return lo <= float(emg) <= hi


def estado_emg(subtipo, emg):
    """'insuficiente' | 'ok' | 'excesivo' -- lo que muestra el medidor."""
    lo, hi = EMG_BANDA.get(subtipo, EMG_BANDA[CVEMP])
    if emg < lo:
        return 'insuficiente'
    if emg > hi:
        return 'excesivo'
    return 'ok'


def signo_pico(pico):
    """Polaridad del pico: la dice su inicial (p arriba, n abajo)."""
    return -1.0 if str(pico).lower().startswith('n') else 1.0


def lado_registro(subtipo, lado_estimulado):
    """De qué lado va el electrodo para estimular ese oído.

    El oVEMP es cruzado: estimular el OD se registra bajo el ojo IZQUIERDO.
    """
    _musculo, via = MUSCULO.get(subtipo, MUSCULO[CVEMP])
    if via == 'ipsi':
        return lado_estimulado
    return 'OI' if lado_estimulado == 'OD' else 'OD'


def descripcion_montaje(subtipo, lado_estimulado):
    musculo, via = MUSCULO.get(subtipo, MUSCULO[CVEMP])
    lado = lado_registro(subtipo, lado_estimulado)
    cruce = 'cruzado' if via == 'contra' else 'ipsilateral'
    return f'{musculo} {lado} ({cruce})'
