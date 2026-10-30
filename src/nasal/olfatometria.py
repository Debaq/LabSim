"""Olfatometría psicofísica (H28 del libro): la batería completa de
bolígrafos (umbral, discriminación e identificación) con un paciente que
responde como una persona.

- **El paciente** (`Olfato`, `responder`): cada narina tiene su umbral
  (T, el puntaje de 1 a 16 que daría una escalera bien hecha), su
  discriminación y su identificación (aciertos esperados de 16). La
  respuesta a un trío es la de un sujeto de elección forzada: detecta con
  la logística de las figuras de H28 (hacer_h28.escalera_simulada,
  probabilidad = azar + (1 − azar) · logística) y, si no detecta, adivina;
  por eso un anósmico saca ~5 en D y ~4 en I. Lo que el alumno hace mal
  cambia la respuesta: sin venda en el umbral o la discriminación ve cuál
  bolígrafo es distinto; con menos de 20 s entre tríos la neurona se adapta
  (Kleene, 2008); si comió, fumó o se perfumó en la última hora, huele
  menos. Cuando no detecta, a veces dice «no huelo nada» y el alumno tiene
  que pedirle que elija igual (elección forzada).
- **La hoja** (`escalera`, `umbral_regla`): lo que el examinador anota.
  `umbral_regla` aplica la regla de Oleszkiewicz y cols. (2019) a los tríos
  que presentó el alumno (el promedio de las últimas cuatro inversiones);
  `paso_siguiente` dice qué paso tocaba, para marcar cuándo se salió de
  la regla. El T lo calcula el alumno: la app lo compara en "Lo que el
  equipo no sabe".
- **Las normas** (`NORMAS`, `categoria`, `p10`): la tabla 1 de
  Oleszkiewicz y cols. (2019), ambos sexos, y los cortes del TDI.

La lista de identificación es del simulador: 16 olores comunes con tres
distractores cada uno, no la de un producto comercial (H28: una lista debe
adaptarse y validarse en cada lugar).

Sin `cases.data['OLFATO']` no hay paciente: el equipo no mide.
"""

import math
import random

LADOS = ('D', 'I')
NARINAS = (('ambas', 'Ambas narinas'), ('D', 'Narina derecha'), ('I', 'Narina izquierda'))
PRUEBAS = (('T', 'Umbral'), ('D', 'Discriminación'), ('I', 'Identificación'))
N_ITEMS = 16              # tríos de discriminación e ítems de identificación
PASOS = 16                # diluciones del umbral; paso 1 = 4 %
AZAR = {'T': 1 / 3, 'D': 1 / 3, 'I': 1 / 4}
INTERVALO_S = 20          # entre tríos (o ítems); menos, adapta
ANCHO = 1.0               # pendiente de la logística del umbral, en pasos
# Centro de la logística respecto del T del caso, calibrado simulando la
# regla (tests/test_nasal_olfatometria.py): con −0,3 pasos, una escalera bien
# hecha da en promedio el T del caso ±0,6 entre 6 y 15 (la escalera aprieta
# hacia el medio: 6 da 6,6; 15 da 14,4). Bajo 5 sale más alto: el azar (1/9 de dos aciertos seguidos) arma inversiones falsas; un
# anósmico saca 3-4, como en la sala ("un puntaje bajo no es cero").
DESPLAZAMIENTO = -0.3

CONDUCTAS = (
    ('buena', 'Colabora'),
    ('distraida', 'Se distrae (contesta al azar a veces)'),
    ('exagera', 'Exagera la pérdida (elige mal adrede)'),
)
PREPARACIONES = (
    ('ok', 'Viene preparado'),
    ('fumo', 'Fumó hace un rato'),
    ('comio', 'Comió hace un rato'),
    ('perfume', 'Viene perfumado'),
)
ESPERA_PREPARACION_S = 60 * 60     # una hora (Delgado-Losada y cols., 2020)

# La lista del simulador: (olor, [cuatro opciones]); la primera es la correcta
# y se baraja al presentar.
IDENTIFICACION = (
    ('Naranja', ['Naranja', 'Frutilla', 'Mora', 'Piña']),
    ('Café', ['Café', 'Chocolate', 'Humo', 'Pan tostado']),
    ('Menta', ['Menta', 'Canela', 'Mostaza', 'Pino']),
    ('Plátano', ['Plátano', 'Coco', 'Cereza', 'Vainilla']),
    ('Limón', ['Limón', 'Manzana', 'Pomelo', 'Melón']),
    ('Ajo', ['Ajo', 'Cebolla', 'Repollo', 'Zanahoria']),
    ('Canela', ['Canela', 'Miel', 'Vainilla', 'Chocolate']),
    ('Rosa', ['Rosa', 'Jazmín', 'Lavanda', 'Pasto']),
    ('Clavo de olor', ['Clavo de olor', 'Pimienta', 'Canela', 'Mostaza']),
    ('Pescado', ['Pescado', 'Queso', 'Jamón', 'Cebolla']),
    ('Anís', ['Anís', 'Menta', 'Eucalipto', 'Limón']),
    ('Piña', ['Piña', 'Plátano', 'Durazno', 'Frutilla']),
    ('Chocolate', ['Chocolate', 'Café', 'Caramelo', 'Nuez']),
    ('Eucalipto', ['Eucalipto', 'Pino', 'Menta', 'Humo']),
    ('Vainilla', ['Vainilla', 'Coco', 'Leche', 'Canela']),
    ('Cuero', ['Cuero', 'Goma', 'Tierra', 'Madera']),
)

# ── Normas (Oleszkiewicz y cols., 2019, tabla 1, ambos sexos) ─────────────

# (edad desde, edad hasta, media del TDI, percentil 10 del TDI)
NORMAS = (
    (5, 10, 25.21, 19.4), (11, 20, 34.00, 28.5), (21, 30, 35.99, 30.75),
    (31, 40, 35.55, 30.5), (41, 50, 34.06, 28.15), (51, 60, 32.85, 27.25),
    (61, 70, 31.26, 24.88), (71, 80, 27.93, 19.2), (81, 120, 23.30, 13.0),
)
CORTES = ((16.0, 'anosmia', 'Anosmia funcional'), (30.5, 'hiposmia', 'Hiposmia'),
          (41.25, 'normosmia', 'Normosmia'), (48.0, 'superior', 'Olfato superior'))
CATEGORIAS = tuple((k, n) for _c, k, n in CORTES)
# Diferencia mínima importante (Gudziol y cols., 2006; Whitcroft y cols., 2023).
DMI = {'TDI': 5.5, 'T': 2.5, 'D': 3.0, 'I': 3.0}
# Diferencia entre narinas para seguir por separado (Whitcroft y cols., 2023).
ASIMETRIA = {'T': 2.5, 'I': 3.0}


def grupo_edad(edad):
    """(desde, hasta, media, p10) del grupo de la edad, o None (menor de 5)."""
    if edad is None:
        return None
    for fila in NORMAS:
        if fila[0] <= edad < fila[1] + 1:
            return fila
    return None


def p10(edad):
    g = grupo_edad(edad)
    return None if g is None else g[3]


def categoria(tdi):
    """Clave de la categoría del TDI (cortes de adultos jóvenes)."""
    for corte, clave, _n in CORTES:
        if tdi <= corte:
            return clave
    return CORTES[-1][1]


def nombre_categoria(clave):
    return dict(CATEGORIAS).get(clave, '')


# ── El caso ────────────────────────────────────────────────────────────────

def _num(v, lo, hi, nombre):
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ValueError(f'{nombre}: no es un número') from None
    if not (math.isfinite(x) and lo <= x <= hi):
        raise ValueError(f'{nombre}: fuera de {lo}-{hi}')
    return x


def normaliza(bloque):
    """Valida el bloque OLFATO del caso y lo devuelve limpio (ValueError si no
    sirve). Forma: {'lados': {'D': {'T', 'D', 'I'}, 'I': {...}},
    'conducta', 'preparacion'}; T de 1 a 16, D e I de 0 a 16."""
    if not isinstance(bloque, dict) or not isinstance(bloque.get('lados'), dict):
        raise ValueError('falta OLFATO.lados')
    lados = {}
    for lado in LADOS:
        d = bloque['lados'].get(lado)
        if not isinstance(d, dict):
            raise ValueError(f'falta OLFATO.lados.{lado}')
        lados[lado] = {'T': _num(d.get('T'), 1, 16, f'{lado}.T'),
                       'D': _num(d.get('D'), 0, 16, f'{lado}.D'),
                       'I': _num(d.get('I'), 0, 16, f'{lado}.I')}
    conducta = bloque.get('conducta') if bloque.get('conducta') in dict(CONDUCTAS) else 'buena'
    prep = bloque.get('preparacion') if bloque.get('preparacion') in dict(PREPARACIONES) else 'ok'
    return {'lados': lados, 'conducta': conducta, 'preparacion': prep}


def desde_caso(data):
    """`cases.data` -> {'olfato', 'edad', 'sexo'} o None si el caso no trae
    olfatometría (o la trae mal escrita)."""
    if not isinstance(data, dict) or not isinstance(data.get('OLFATO'), dict):
        return None
    try:
        bloque = normaliza(data['OLFATO'])
        edad = float(data.get('edad'))
    except (TypeError, ValueError) as exc:
        print(f'olfatometría: el caso trae OLFATO inválido: {exc}')
        return None
    return {'olfato': bloque, 'edad': edad, 'sexo': 'F' if data.get('gender') == 1 else 'M'}


def verdad_binasal(olfato):
    """Con las dos narinas huele el mejor lado (H28)."""
    return {k: max(olfato['lados'][l][k] for l in LADOS) for k in ('T', 'D', 'I')}


def capacidad(olfato, narina):
    """{'T', 'D', 'I'} verdaderos de lo que se presenta por esa narina."""
    if narina in LADOS:
        return dict(olfato['lados'][narina])
    return verdad_binasal(olfato)


# ── La respuesta del paciente ──────────────────────────────────────────────

def p_detecta_umbral(t_verdadero, paso, adaptacion=0.0):
    """Probabilidad de percibir el bolígrafo con olor del paso (sin el azar).
    `adaptacion` en pasos: cuánto se corre el umbral hacia lo concentrado."""
    centro = t_verdadero + DESPLAZAMIENTO - adaptacion
    return 1 / (1 + math.exp(-(centro - paso) / ANCHO))


def p_conoce(esperado, prueba):
    """De los aciertos esperados de 16 a la probabilidad de reconocer de
    verdad (sin el azar)."""
    g = AZAR[prueba]
    return min(1.0, max(0.0, (esperado / N_ITEMS - g) / (1 - g)))


def adaptacion(dt):
    """Cuánto se adapta con `dt` segundos desde el último trío: nada desde
    20 s, como mucho un 40 % (o 2 pasos de umbral) presentando seguido."""
    if dt is None or dt >= INTERVALO_S:
        return 0.0
    return 1 - max(0.0, dt) / INTERVALO_S


PERDIDA_PREPARACION = 0.35   # de la capacidad, si no viene preparado


def responder(olfato, prueba, narina, *, paso=None, correcta, n_opciones, semilla,
              venda=True, dt=None, preparado=True):
    """La respuesta a un trío (T, D) o a un ítem (I).

    `correcta` es el índice (0..n_opciones−1) del bolígrafo con olor, del
    distinto o del nombre correcto. Devuelve {'eleccion', 'dice_nada',
    'detecto', 'vio'}: `eleccion` es la que daría si se le pide que elija;
    `dice_nada` es que primero contesta «no huelo nada»."""
    rng = random.Random(semilla)
    cap = capacidad(olfato, narina)
    a = adaptacion(dt)
    prep = 0.0 if preparado else PERDIDA_PREPARACION
    if prueba == 'T':
        p = p_detecta_umbral(cap['T'], paso, adaptacion=2 * a + 3 * prep)
    else:
        p = p_conoce(cap[prueba], prueba) * (1 - 0.4 * a) * (1 - prep)
    detecto = rng.random() < p
    vio = prueba in ('T', 'D') and not venda and rng.random() < 0.9
    conducta = olfato['conducta']
    if conducta == 'distraida' and rng.random() < 0.15:
        detecto = False
    otras = [i for i in range(n_opciones) if i != correcta]
    if vio:
        eleccion = correcta
    elif detecto:
        eleccion = correcta
        if conducta == 'exagera' and rng.random() < 0.85:
            eleccion = rng.choice(otras)
    else:
        eleccion = rng.randrange(n_opciones)
    # Sin percibir, lo honesto es decirlo; en elección forzada se le pide
    # que elija igual. El que exagera, en cambio, siempre "no huele".
    dice_nada = not (detecto or vio) and rng.random() < 0.7
    if conducta == 'exagera' and eleccion != correcta and rng.random() < 0.5:
        dice_nada = True
    return {'eleccion': eleccion, 'dice_nada': dice_nada, 'detecto': detecto, 'vio': vio, 'p': p}


# ── La hoja: la escalera del umbral ───────────────────────────────────────

def escalera(pasos_ok):
    """Recorre los tríos del umbral [(paso, acierto), ...] con la regla de
    H28 y devuelve {'inversiones': [índices], 'siguiente', 'direccion'}.

    Se parte en el paso 16 subiendo la concentración; dos aciertos seguidos
    en un paso diluyen (paso + 1) y, si se venía concentrando, son una
    inversión; un error concentra (paso − 1) y, si se venía diluyendo, es
    una inversión."""
    paso, direccion, seguidos = PASOS, 'sube', 0
    inversiones = []
    for i, (p, ok) in enumerate(pasos_ok):
        if p != paso:
            # El alumno presentó otro paso: la regla sigue desde ahí.
            paso, seguidos = p, 0
        if ok:
            seguidos += 1
            if seguidos == 2:
                seguidos = 0
                if direccion == 'sube':
                    inversiones.append(i)
                    direccion = 'baja'
                paso = min(PASOS, paso + 1)
        else:
            seguidos = 0
            if direccion == 'baja':
                inversiones.append(i)
                direccion = 'sube'
            paso = max(1, paso - 1)
    return {'inversiones': inversiones, 'siguiente': paso, 'direccion': direccion}


def umbral_regla(pasos_ok):
    """El T por la regla: promedio de los pasos de las últimas cuatro
    inversiones (None con menos de cuatro)."""
    inv = escalera(pasos_ok)['inversiones']
    if len(inv) < 4:
        return None
    return sum(pasos_ok[i][0] for i in inv[-4:]) / 4


def terminada(pasos_ok):
    """La escalera llegó a la séptima inversión."""
    return len(escalera(pasos_ok)['inversiones']) >= 7


def concentracion(paso):
    """% del paso (1 = 4 %, cada uno la mitad)."""
    return 4.0 / 2 ** (paso - 1)


def opciones_item(i, semilla):
    """Las cuatro opciones del ítem i, barajadas, y el índice de la correcta."""
    nombre, opciones = IDENTIFICACION[i]
    orden = list(opciones)
    random.Random(semilla).shuffle(orden)
    return orden, orden.index(nombre)
