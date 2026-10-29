"""El paciente de RinoSim: la geometría de cada fosa nasal, su mucosa y lo que
le hace el tiempo (ciclo nasal) y el vasoconstrictor. Port de js/modelo.js.

Sin interfaz: lo usan la rinomanometría, la rinometría y las pruebas.

Una fosa es un perfil ÁREA-DISTANCIA, A(x), desde la narina (x = 0) hasta
la rinofaringe (x ≈ 10 cm), en cm². Se arma con piezas, cada una con sus
parámetros, y TODO paciente (también los cuadros de ejemplo) es solo un
juego de parámetros: el docente puede editar cualquiera.

  esqueleto   el hueco libre de la fosa: narina, vestíbulo, cavidad y
              rinofaringe (perfil base, escalado por `narina`).
  válvula     el primer estrechamiento (escotadura I): a `pos` cm de la
              narina deja `area` cm². `colapso` (0-1) dice cuánto se cierra
              al inspirar: el tejido blando de la válvula cede con la
              presión (efecto Bernoulli, H26), y más cuanto más fuerte se
              inspira. En espiración no se cierra.
  cornete     la cabeza del cornete inferior (escotadura C) en `pos` y su
              cuerpo hacia atrás. Quita `oseo` cm² de esqueleto, que no se
              mueve, y hasta `mucosa` cm² de mucosa, según la congestión.
  desviación  del tabique, hacia esa fosa: quita `area` cm² centrados en
              `pos`, con `ancho` cm (ancho chico = espolón).
  meato       el meato medio, `meato` cm² entre ~4 y ~7 cm.
  pólipos     quitan `polipos` cm² entre ~4 y ~7,5 cm: llenan primero el
              meato y después la fosa. No responden al vasoconstrictor.
  congestión  de la mucosa, 0 (retraída del todo) a 1 (máxima). La mueven el
              ciclo nasal (las dos fosas en contrafase) y el vasoconstrictor,
              que la deja casi en cero y apaga el ciclo (Corey y cols.,
              1998, citado en H27). El vasoconstrictor NO toca nada de lo
              óseo, del tabique, de la válvula ni los pólipos.

Y una pieza del paciente entero: la perforación del tabique, en `pos` cm,
de `area` cm², que une las dos fosas (H26: invalida la técnica anterior).

Todas las cifras son órdenes de magnitud del modelo, elegidas para que las
curvas tengan la forma que describen H26 y H27: NO son valores normales de
ninguna población. Las referencias con fuente están en referencias.py.

El paciente es un dict con la forma del JSON de RinoSim (claves en español
tal cual: `lados`, `D`, `I`, `valvula`, `cornete`...): así se guarda en
cases.data['NASAL']. El estado de la medición es otro dict chico:
{'minuto': 40, 'vc': True}.
"""

import copy
import math

from .azar import a_texto, generador

LADOS = ['D', 'I']
NOMBRE_LADO = {'D': 'derecha', 'I': 'izquierda'}
SIGLA_LADO = {'D': 'FND', 'I': 'FNI'}


def js_round(x):
    """Math.round de JS (la mitad sube); round() de Python redondea al par."""
    return math.floor(x + 0.5)


# Rejilla de distancias, cm. Paso fino para que el mínimo caiga donde cae.
DX = 0.025
X_MAX = 12
# +(i * DX).toFixed(4): se redondea a 4 decimales para que 0.025*3 sea 0.075 y no 0.07500000000000001.
REJILLA = [float(f'{i * DX:.4f}') for i in range(js_round(X_MAX / DX) + 1)]

# Congestión que deja el vasoconstrictor (orden de magnitud del modelo).
CONGESTION_VASOCONSTRICTOR = 0.05
# Área mínima de una sección, cm²: una fosa nunca queda en cero exacto.
AREA_MINIMA = 0.01

# El hueco libre de una fosa (sin válvula, cornete ni nada), cm²: puntos de
# control (x en cm, área en cm²) unidos con una cúbica monótona (PCHIP), que
# no inventa valles ni lomas entre los puntos. El vestíbulo se escala con el
# área de la narina. Orden de magnitud del modelo.
ESQUELETO = [
    (0, 1.0), (0.8, 1.5), (1.6, 1.7), (2.4, 2.1), (3.2, 2.3), (4.5, 2.5), (6.0, 2.8),
    (7.0, 3.1), (8.0, 4.2), (9.0, 6.0), (10.0, 7.5), (12.0, 8.5),
]


def _gauss(x, mu, s):
    return math.exp(-0.5 * ((x - mu) / s) ** 2)


def _sigmoide(x, x0, w):
    return 1 / (1 + math.exp(-(x - x0) / w))


def _ventana(x, a, b, w):
    """Ventana suave entre a y b con bordes de ancho w."""
    return _sigmoide(x, a, w) * (1 - _sigmoide(x, b, w))


def acota(v, lo, hi):
    return min(hi, max(lo, v))


def _pendientes():
    """Pendientes de Fritsch-Carlson para la cúbica monótona."""
    n = len(ESQUELETO)
    d = [(ESQUELETO[i + 1][1] - ESQUELETO[i][1]) / (ESQUELETO[i + 1][0] - ESQUELETO[i][0])
         for i in range(n - 1)]
    m = [d[0]]
    for i in range(1, n - 1):
        m.append(0 if d[i - 1] * d[i] <= 0 else (2 * d[i - 1] * d[i]) / (d[i - 1] + d[i]))
    m.append(d[n - 2])
    return m


PENDIENTES = _pendientes()


def _esqueleto(x, narina):
    i = 0
    while i < len(ESQUELETO) - 2 and x > ESQUELETO[i + 1][0]:
        i += 1
    x0, a0 = ESQUELETO[i]
    x1, a1 = ESQUELETO[i + 1]
    h = x1 - x0
    t = acota((x - x0) / h, 0, 1)
    a = ((2 * t ** 3 - 3 * t ** 2 + 1) * a0 + (t ** 3 - 2 * t ** 2 + t) * h * PENDIENTES[i]
         + (-2 * t ** 3 + 3 * t ** 2) * a1 + (t ** 3 - t ** 2) * h * PENDIENTES[i + 1])
    # La narina escala el vestíbulo; detrás de la válvula la cavidad no cambia.
    peso = 1 - _sigmoide(x, 1.6, 0.25)
    return a * (1 + (narina - 1) * peso)


def lado_normal():
    """Una fosa normal (orden de magnitud del modelo)."""
    return {
        'narina': 1.0,
        'valvula': {'pos': 1.3, 'area': 0.65, 'colapso': 0.08},
        'cornete': {'pos': 3.2, 'oseo': 0.3, 'mucosa': 1.3},
        'desviacion': {'pos': 1.9, 'area': 0, 'ancho': 1.0},
        'meato': 0.5,
        'polipos': 0,
        'congestion': 0.4,
    }


def clona(o):
    """Copia profunda: lo que se edita no toca el cuadro original."""
    return copy.deepcopy(o)


def paciente_normal():
    """Un paciente normal: las dos fosas iguales, con ciclo nasal."""
    return {
        'nombre': 'Normal',
        'lados': {'D': lado_normal(), 'I': lado_normal()},
        # La congestión de cada fosa oscila ±amplitud alrededor de la suya, en
        # contrafase, con `periodo` minutos. Flanagan y Eccles (1997, en H26): en
        # muchos sujetos el ciclo no es regular; el modelo lo dibuja regular.
        'ciclo': {'amplitud': 0.3, 'periodo': 150, 'fase': 0},
        'perforacion': {'pos': 1.6, 'area': 0},
    }


def _cambia_normal(p):
    pass


def _cambia_desviacion_derecha(p):
    p['lados']['D']['desviacion'] = {'pos': 1.55, 'area': 0.35, 'ancho': 0.8}
    # El cornete del lado desviado suele ser chico, y el del otro lado,
    # grande (hipertrofia compensadora).
    p['lados']['D']['cornete']['mucosa'] = 0.6
    p['lados']['I']['cornete']['mucosa'] = 1.8


def _cambia_desviacion_izquierda(p):
    p['lados']['I']['desviacion'] = {'pos': 1.55, 'area': 0.35, 'ancho': 0.8}
    p['lados']['I']['cornete']['mucosa'] = 0.6
    p['lados']['D']['cornete']['mucosa'] = 1.8


def _cambia_cornetes(p):
    for lado in LADOS:
        p['lados'][lado]['cornete']['mucosa'] = 2.1
        p['lados'][lado]['congestion'] = 0.8
    p['ciclo']['amplitud'] = 0.15


def _cambia_colapso_valvular(p):
    for lado in LADOS:
        p['lados'][lado]['valvula'] = {'pos': 1.3, 'area': 0.52, 'colapso': 0.7}
        p['lados'][lado]['cornete']['mucosa'] = 0.9


def _cambia_polipos(p):
    p['lados']['D']['polipos'] = 2.4
    p['lados']['I']['polipos'] = 2.1


def _cambia_mixta(p):
    p['lados']['D']['desviacion'] = {'pos': 1.55, 'area': 0.32, 'ancho': 0.8}
    for lado in LADOS:
        p['lados'][lado]['cornete']['mucosa'] = 1.6
        p['lados'][lado]['congestion'] = 0.7


def _cambia_perforacion(p):
    p['perforacion'] = {'pos': 1.25, 'area': 0.6}


# Los cuadros de ejemplo. Cada uno parte del normal y cambia solo parámetros.
# Ninguno es un paciente real; las cifras son del modelo.
CUADROS = {
    'normal': {
        'nombre': 'Normal',
        'descripcion': 'Dos fosas sin obstrucción, con ciclo nasal: una algo más congestionada que la otra según el minuto.',
        'cambia': _cambia_normal,
    },
    'desviacion_derecha': {
        'nombre': 'Desviación septal derecha',
        'descripcion': 'El tabique se desvía hacia la fosa derecha en la zona de la válvula. Es esqueleto: el vasoconstrictor casi no la mueve. El cornete izquierdo, grande (compensador), sí responde.',
        'cambia': _cambia_desviacion_derecha,
    },
    'desviacion_izquierda': {
        'nombre': 'Desviación septal izquierda',
        'descripcion': 'El mismo cuadro, hacia la fosa izquierda, con el cornete derecho compensador.',
        'cambia': _cambia_desviacion_izquierda,
    },
    'cornetes': {
        'nombre': 'Hipertrofia de cornetes inferiores',
        'descripcion': 'Rinitis vasomotora o alérgica: mucosa de los cornetes muy congestionada en las dos fosas. Responde al vasoconstrictor.',
        'cambia': _cambia_cornetes,
    },
    'colapso_valvular': {
        'nombre': 'Colapso de la válvula nasal',
        'descripcion': 'Válvula estrecha y blanda: se cierra al inspirar, más cuanto más fuerte. Peor con la inspiración forzada; el vasoconstrictor casi no la cambia.',
        'cambia': _cambia_colapso_valvular,
    },
    'polipos': {
        'nombre': 'Poliposis nasal',
        'descripcion': 'Pólipos que llenan el meato medio y la parte posterior de las dos fosas. Los pólipos no responden al vasoconstrictor; lo que baja es la mucosa de los cornetes que los rodea.',
        'cambia': _cambia_polipos,
    },
    'mixta': {
        'nombre': 'Mixta: desviación y cornetes',
        'descripcion': 'Desviación septal derecha y cornetes congestionados en las dos fosas: el vasoconstrictor baja la resistencia pero no la normaliza en la derecha.',
        'cambia': _cambia_mixta,
    },
    'perforacion': {
        'nombre': 'Perforación septal',
        'descripcion': 'Perforación anterior del tabique. La rinomanometría anterior deja de ser válida: el tubo de presión ya no lee la rinofaringe.',
        'cambia': _cambia_perforacion,
    },
}


def paciente(cuadro='normal', semilla=None):
    """Un paciente a partir de un cuadro.

    Sin semilla (o None), el cuadro tal cual; con semilla, una variante
    individual: cada parámetro corrido un poco (el mismo paciente para la
    misma semilla), para que no todos los alumnos vean la misma nariz.
    """
    c = CUADROS.get(cuadro)
    if not c:
        raise ValueError(f'cuadro desconocido: {cuadro}')
    p = paciente_normal()
    c['cambia'](p)
    p['cuadro'] = cuadro
    p['nombre'] = c['nombre']
    p['semilla'] = semilla
    if semilla is None or semilla == '':
        return p
    r = generador(f'{cuadro}/{a_texto(semilla)}')

    def f(de):
        return max(0.5, r.normal(1, de))

    for lado in LADOS:
        s = p['lados'][lado]
        s['narina'] *= f(0.06)
        s['valvula']['area'] *= f(0.07)
        s['valvula']['pos'] += r.normal(0, 0.08)
        s['cornete']['oseo'] *= f(0.15)
        s['cornete']['mucosa'] *= f(0.12)
        s['cornete']['pos'] += r.normal(0, 0.12)
        s['desviacion']['area'] *= f(0.1)
        s['polipos'] *= f(0.1)
        s['congestion'] = acota(s['congestion'] + r.normal(0, 0.05), 0, 1)
    p['ciclo']['fase'] = r.entre(0, 2 * math.pi)
    p['ciclo']['periodo'] *= f(0.2)
    p['perforacion']['area'] *= f(0.1)
    return p


def congestion(p, lado, estado=None):
    """Congestión de una fosa en un estado: `minuto` del ciclo nasal y si
    tiene vasoconstrictor (`vc`). El vasoconstrictor deja la mucosa retraída
    y apaga el ciclo."""
    estado = estado or {}
    if estado.get('vc'):
        return CONGESTION_VASOCONSTRICTOR
    s = p['lados'][lado]
    ci = p['ciclo']
    signo = 1 if lado == 'D' else -1
    t = estado.get('minuto')
    if t is None:
        t = 0
    return acota(s['congestion'] + signo * ci['amplitud'] * math.sin((2 * math.pi * t) / ci['periodo'] + ci['fase']), 0, 1)


def piezas(s, x, c):
    """Las piezas de la sección a la distancia x, por separado, en cm². Sirve
    para explicar (qué tapa qué) y para los tests (qué mueve el vasoconstrictor).
      base        el hueco libre con la válvula.
      estructural lo que quita lo que no es mucosa (cornete óseo, desviación,
                  pólipos): el vasoconstrictor no lo mueve.
      mucoso      lo que quita la mucosa, con la congestión del estado.
    """
    v = s['valvula']
    libre = _esqueleto(x, s['narina']) + s['meato'] * _ventana(x, 4.0, 7.0, 0.3)
    # La válvula: un valle angosto que baja el hueco hasta `area` en `pos`.
    en_valvula = _esqueleto(v['pos'], s['narina'])
    base = libre - max(0, en_valvula - v['area']) * _gauss(x, v['pos'], 0.3)
    k = s['cornete']
    # Cabeza del cornete y su cuerpo, que sigue (algo menos) hacia atrás.
    cabeza = _gauss(x, k['pos'], 0.45)
    forma = cabeza + (1 - cabeza) * 0.55 * _ventana(x, k['pos'] + 0.4, 7.2, 0.35)
    d = s['desviacion']
    desv = d['area'] * _gauss(x, d['pos'], max(0.15, d['ancho'] / 2))
    pol = s['polipos'] * _ventana(x, 4.0, 7.5, 0.3)
    estructural = k['oseo'] * forma + desv + pol
    # La mucosa del cornete; un poco también en la válvula (la cabeza del
    # cornete forma parte de ella).
    mucoso = k['mucosa'] * c * forma + 0.14 * k['mucosa'] * c * _gauss(x, v['pos'], 0.3)
    return {'base': base, 'estructural': estructural, 'mucoso': mucoso}


def perfil(p, lado, estado=None, colapso=0):
    """El perfil área-distancia de una fosa en un estado, sobre REJILLA.

    `colapso` (0-1) es el cierre dinámico de la válvula en ese instante: lo
    pone la rinomanometría según la presión; la rinometría mide en apnea (0).
    """
    s = p['lados'][lado]
    c = congestion(p, lado, estado)
    out = []
    for x in REJILLA:
        q = piezas(s, x, c)
        a = q['base'] - q['estructural'] - q['mucoso']
        if colapso > 0:
            a *= 1 - colapso * _gauss(x, s['valvula']['pos'], 0.5)
        out.append(max(AREA_MINIMA, a))
    return out


# Lista de los parámetros editables, para la ficha del paciente.
PARAMETROS = [
    {'ruta': 'narina', 'nombre': 'Narina (escala del vestíbulo)', 'min': 0.5, 'max': 1.6, 'paso': 0.05},
    {'ruta': 'valvula.pos', 'nombre': 'Válvula: distancia (cm)', 'min': 0.8, 'max': 2.2, 'paso': 0.05},
    {'ruta': 'valvula.area', 'nombre': 'Válvula: área (cm²)', 'min': 0.15, 'max': 1.2, 'paso': 0.01},
    {'ruta': 'valvula.colapso', 'nombre': 'Válvula: colapso al inspirar (0-1)', 'min': 0, 'max': 0.9, 'paso': 0.01},
    {'ruta': 'cornete.pos', 'nombre': 'Cornete inferior: cabeza (cm)', 'min': 2.4, 'max': 4.2, 'paso': 0.05},
    {'ruta': 'cornete.oseo', 'nombre': 'Cornete: componente óseo (cm²)', 'min': 0, 'max': 1.5, 'paso': 0.05},
    {'ruta': 'cornete.mucosa', 'nombre': 'Cornete: mucosa máxima (cm²)', 'min': 0, 'max': 2.2, 'paso': 0.05},
    {'ruta': 'desviacion.pos', 'nombre': 'Desviación: distancia (cm)', 'min': 0.8, 'max': 6, 'paso': 0.05},
    {'ruta': 'desviacion.area', 'nombre': 'Desviación: área que quita (cm²)', 'min': 0, 'max': 1.5, 'paso': 0.01},
    {'ruta': 'desviacion.ancho', 'nombre': 'Desviación: ancho (cm; chico = espolón)', 'min': 0.3, 'max': 3, 'paso': 0.05},
    {'ruta': 'meato', 'nombre': 'Meato medio (cm²)', 'min': 0, 'max': 1.2, 'paso': 0.05},
    {'ruta': 'polipos', 'nombre': 'Pólipos (cm²)', 'min': 0, 'max': 2.5, 'paso': 0.05},
    {'ruta': 'congestion', 'nombre': 'Congestión de la mucosa (0-1)', 'min': 0, 'max': 1, 'paso': 0.01},
]


def lee(obj, ruta):
    for k in ruta.split('.'):
        obj = obj[k]
    return obj


def escribe(obj, ruta, valor):
    ks = ruta.split('.')
    ultimo = ks.pop()
    for k in ks:
        obj = obj[k]
    obj[ultimo] = valor


def _es_numero(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def normaliza(entrada):
    """Un paciente escrito a mano (JSON del caso): lo que falte se completa
    con el normal, así un dict puede traer solo lo que cambia. Los valores
    que no son números se rechazan (ValueError)."""
    p = paciente_normal()
    entrada = entrada if isinstance(entrada, dict) else {}

    def mezcla(dst, src, ruta):
        if not isinstance(src, dict):
            return
        for k, v in src.items():
            if k not in dst:
                continue
            if isinstance(dst[k], dict):
                mezcla(dst[k], v, f'{ruta}{k}.')
            elif isinstance(dst[k], (int, float)):
                if not _es_numero(v):
                    raise ValueError(f'{ruta}{k} tiene que ser un número')
                dst[k] = float(v)

    mezcla(p['lados'], entrada.get('lados'), 'lados.')
    mezcla(p['ciclo'], entrada.get('ciclo'), 'ciclo.')
    mezcla(p['perforacion'], entrada.get('perforacion'), 'perforacion.')
    p['nombre'] = entrada['nombre'] if isinstance(entrada.get('nombre'), str) else 'Paciente editado'
    cuadro = entrada.get('cuadro')
    p['cuadro'] = cuadro if isinstance(cuadro, str) and cuadro in CUADROS else None
    p['semilla'] = entrada.get('semilla')
    return p
