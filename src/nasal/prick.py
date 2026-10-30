"""Prick test (H29 del libro): la piel del antebrazo del caso y cómo
reacciona a lo que hace el alumno.

- **El paciente** (`normaliza`, `desde_caso`): la pápula que daría cada
  alérgeno a los 15-20 minutos con una punción bien hecha (mm de diámetro
  mayor; 0 = no sensibilizado), la de la histamina, el dermografismo y el
  último fármaco que tomó (cuál y hace cuántas horas).
- **La piel** (`papula`): la pápula de un sitio en un minuto dado. Crece y
  se va con el tiempo (la histamina llega a su máximo hacia los 8-10 min;
  los alérgenos entre los 15 y 20; a la hora ya no queda nada), la achica
  un antihistamínico que no se suspendió a tiempo (`supresion`), la agranda
  el dermografismo (también en el control negativo), y la ensucian los
  errores de H29: punciones a menos de 2 cm (el reflejo axónico de una
  pápula vecina), una lanceta que se reusó (lleva el alérgeno anterior) o
  secar arrastrando la gota. Cada sitio tiene su propia variación (semilla).
  La pápula es una elipse con su eritema alrededor y, a veces, seudópodos.

Lo que el equipo no tiene: no hay equipo. El alumno mide con la regla y
decide el resultado; la verdad va a "Lo que el equipo no sabe" y al log.

Sin `cases.data['PRICK']` no hay paciente: no se hace la prueba.
"""

import math
import random

# (clave, nombre en la hoja, abreviatura en la piel)
CONTROLES = (('neg', 'Control negativo (diluyente)', '−'),
             ('his', 'Control positivo (histamina 10 mg/mL)', 'H'))
# El panel de inhalantes de la guía europea (Heinzerling y cols., 2013).
ALERGENOS = (
    ('dpte', 'D. pteronyssinus', 'Dp'), ('dfar', 'D. farinae', 'Df'),
    ('gato', 'Gato (epitelio)', 'Ga'), ('perro', 'Perro (epitelio)', 'Pe'),
    ('cucaracha', 'Cucaracha', 'Cu'), ('pastos', 'Mezcla de pastos', 'Pa'),
    ('olivo', 'Olivo', 'Ol'), ('platano', 'Plátano oriental', 'Pl'),
    ('cipres', 'Ciprés', 'Ci'), ('abedul', 'Abedul', 'Ab'),
    ('avellano', 'Avellano', 'Av'), ('aliso', 'Aliso', 'Al'),
    ('artemisa', 'Artemisa', 'Ar'), ('ambrosia', 'Ambrosía', 'Am'),
    ('parietaria', 'Parietaria', 'Pr'), ('alternaria', 'Alternaria alternata', 'Alt'),
    ('cladosporium', 'Cladosporium herbarum', 'Cl'), ('aspergillus', 'Aspergillus fumigatus', 'As'),
)
EXTRACTOS = CONTROLES + ALERGENOS
NOMBRES = {k: n for k, n, _a in EXTRACTOS}
ABREV = {k: a for k, _n, a in EXTRACTOS}

# Fármacos de la tabla de H29: (clave, nombre, efecto máximo sobre la
# pápula 0-1, horas tras la última dosis en que deja de interferir). Los
# plazos son el borde largo de lo que dan Heinzerling (2013) y Bernstein
# (2008); los que no hace falta suspender tienen efecto 0.
FARMACOS = (
    ('hidroxizina', 'Hidroxizina', 1.0, 96),
    ('clorfenamina', 'Clorfenamina', 1.0, 72),
    ('cetirizina', 'Cetirizina', 1.0, 168),
    ('loratadina', 'Loratadina', 1.0, 168),
    ('ketotifeno', 'Ketotifeno', 1.0, 120),
    ('doxepina', 'Doxepina', 1.0, 168),
    ('famotidina', 'Famotidina (anti-H2)', 0.15, 24),
    ('corticoide_topico', 'Corticoide tópico en el antebrazo', 0.5, 168),
    ('omalizumab', 'Omalizumab', 0.7, 28 * 24),
    ('prednisona', 'Prednisona en curso corto', 0.05, 24),
    ('budesonida', 'Budesonida nasal', 0.0, 0),
    ('montelukast', 'Montelukast', 0.0, 0),
    ('salbutamol', 'Salbutamol inhalado', 0.0, 0),
)
NOMBRE_FARMACO = {k: n for k, n, _e, _h in FARMACOS}

# El antebrazo volar, en mm: el pliegue del codo en y = 0 y el de la
# muñeca en y = LARGO; el ancho baja de ANCHO_CODO a ANCHO_MUNECA.
LARGO = 240
ANCHO_CODO = 74
ANCHO_MUNECA = 56
MARGEN_PLIEGUE = 30        # mm a los pliegues (H29: 2 a 3 cm o más)
DISTANCIA_MIN = 20         # mm entre punciones (H29: nunca menos de 2 cm)
LECTURA_MIN = (15, 20)     # ventana de lectura de los alérgenos
UMBRAL_MM = 3              # positivo: 3 mm o más (y 3 sobre el negativo)

PICO_MIN = {'his': 10.0}   # la histamina antes; el resto a los 17 min
PICO_ALERGENO = 17.0


def _num(v, lo, hi, nombre):
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ValueError(f'{nombre}: no es un número') from None
    if not (math.isfinite(x) and lo <= x <= hi):
        raise ValueError(f'{nombre}: fuera de {lo}-{hi}')
    return x


def normaliza(bloque):
    """Valida el bloque PRICK del caso (ValueError si no sirve). Forma:
    {'histamina': mm, 'alergenos': {clave: mm}, 'dermografismo': mm,
    'farmaco': None | {'clave', 'horas'}}."""
    if not isinstance(bloque, dict):
        raise ValueError('PRICK no es un objeto')
    out = {'histamina': _num(bloque.get('histamina'), 0, 15, 'histamina'),
           'dermografismo': _num(bloque.get('dermografismo') or 0, 0, 8, 'dermografismo')}
    alerg = bloque.get('alergenos') or {}
    if not isinstance(alerg, dict):
        raise ValueError('alergenos no es un objeto')
    out['alergenos'] = {k: _num(alerg.get(k) or 0, 0, 25, k) for k, _n, _a in ALERGENOS}
    f = bloque.get('farmaco')
    if isinstance(f, dict) and f.get('clave') in NOMBRE_FARMACO:
        out['farmaco'] = {'clave': f['clave'], 'horas': _num(f.get('horas'), 0, 24 * 60, 'farmaco.horas')}
    else:
        out['farmaco'] = None
    return out


def desde_caso(data):
    """`cases.data` -> {'piel', 'edad', 'sexo'} o None si el caso no trae
    prick (o lo trae mal escrito)."""
    if not isinstance(data, dict) or not isinstance(data.get('PRICK'), dict):
        return None
    try:
        piel = normaliza(data['PRICK'])
    except ValueError as exc:
        print(f'prick: el caso trae PRICK inválido: {exc}')
        return None
    edad = data.get('edad')
    return {'piel': piel, 'edad': edad, 'sexo': 'F' if data.get('gender') == 1 else 'M'}


def supresion(farmaco):
    """Cuánto achica la pápula el fármaco (0 = nada, 1 = la borra)."""
    if not farmaco:
        return 0.0
    for clave, _n, efecto, lavado in FARMACOS:
        if clave == farmaco['clave']:
            if lavado <= 0:
                return 0.0
            return efecto * max(0.0, 1 - farmaco['horas'] / lavado) ** 0.5
    return 0.0


def curso(minuto, pico):
    """Fracción del tamaño máximo a los `minuto` desde la punción."""
    if minuto <= 0:
        return 0.0
    u = minuto / pico
    return u * u * math.exp(2 * (1 - u))


def esperado(piel, extracto):
    """El diámetro mayor (mm) a su pico, sin variación ni errores."""
    if extracto == 'neg':
        return 0.0
    if extracto == 'his':
        return piel['histamina']
    return piel['alergenos'].get(extracto, 0.0)


def _variacion(semilla):
    r = random.Random(semilla)
    return {'factor': max(0.6, 1 + r.gauss(0, 0.12)),
            'razon': r.uniform(0.72, 0.95),             # menor / mayor
            'angulo': r.uniform(-30, 30),               # grados desde el eje del brazo
            'seudopodos': [r.uniform(0, 360) for _ in range(r.choice((0, 0, 1, 2)))]}


def distancia(a, b):
    return math.hypot(a['x'] - b['x'], a['y'] - b['y'])


def contaminantes(sitios, i):
    """Lo que llega al sitio i además de su gota: [(extracto, fracción, causa)]."""
    s = sitios[i]
    out = []
    lanceta = s.get('lanceta')
    if s.get('puncion') is not None and lanceta is not None:
        # La lanceta reusada lleva lo de la punción anterior con ella.
        previas = [o for o in sitios if o is not s and o.get('lanceta') == lanceta
                   and o.get('puncion') is not None and o['puncion'] < s['puncion']]
        if previas:
            out.append((max(previas, key=lambda o: o['puncion'])['extracto'], 0.6, 'lanceta'))
    for o in sitios:
        if o is s:
            continue
        if o.get('arrastre') and distancia(o, s) < 25:
            out.append((o['extracto'], 0.4, 'arrastre'))
    return out


def papula(piel, sitios, i, minuto, semilla):
    """La pápula del sitio i a los `minuto` desde SU punción.

    Devuelve {'mayor', 'menor', 'angulo', 'eritema', 'seudopodos',
    'verdad'}; mayor 0 si no hay pápula. `sitios` son los de la hoja:
    {'extracto', 'x', 'y', 'puncion' (minuto de reloj o None), 'lanceta',
    'arrastre'}. Sin punción no hay nada."""
    s = sitios[i]
    vacio = {'mayor': 0.0, 'menor': 0.0, 'angulo': 0.0, 'eritema': 0.0, 'seudopodos': [],
             'verdad': {'propio': 0.0, 'extra': 0.0, 'supresion': 0.0}}
    if s.get('puncion') is None or minuto <= 0:
        return vacio
    v = _variacion(semilla)
    sup = supresion(piel['farmaco'])
    pico = PICO_MIN.get(s['extracto'], PICO_ALERGENO)
    propio = esperado(piel, s['extracto']) * v['factor'] * curso(minuto, pico)
    extra = 0.0
    for ext, frac, _causa in contaminantes(sitios, i):
        extra = max(extra, esperado(piel, ext) * frac * curso(minuto, PICO_MIN.get(ext, PICO_ALERGENO)))
    # Reflejo axónico: una pápula vecina a menos de 2 cm hace pápula aquí.
    for j, o in enumerate(sitios):
        if j == i or o.get('puncion') is None:
            continue
        d = distancia(o, s)
        if d < DISTANCIA_MIN:
            m = minuto + (s['puncion'] - o['puncion'])
            vecino = esperado(piel, o['extracto']) * curso(m, PICO_MIN.get(o['extracto'], PICO_ALERGENO))
            extra = max(extra, 0.35 * vecino * (1 - d / DISTANCIA_MIN))
    dermo = piel['dermografismo'] * curso(minuto, 8.0)
    # Lo que llega de otro sitio se suma a la pápula propia (se juntan).
    mayor = max(propio + extra, dermo) * (1 - sup)
    if mayor < 0.6:
        mayor = 0.0
    eritema = 0.0 if mayor == 0 else mayor * 2.6 + 4
    return {'mayor': mayor, 'menor': mayor * v['razon'], 'angulo': v['angulo'], 'eritema': eritema,
            'seudopodos': v['seudopodos'] if mayor >= 5 else [],
            'verdad': {'propio': propio, 'extra': extra, 'dermografismo': dermo, 'supresion': sup}}


def ancho_en(y):
    """Ancho del antebrazo a la altura y (mm desde el codo)."""
    t = min(1.0, max(0.0, y / LARGO))
    return ANCHO_CODO + (ANCHO_MUNECA - ANCHO_CODO) * t


def dentro(x, y):
    """El punto está en la piel del antebrazo (x desde la línea media)."""
    return 0 <= y <= LARGO and abs(x) <= ancho_en(y) / 2 - 4


def avisos_sitio(sitios, i):
    """Lo que está mal en dónde se puso el sitio i (claves para el log)."""
    s = sitios[i]
    out = []
    if s['y'] < MARGEN_PLIEGUE or s['y'] > LARGO - MARGEN_PLIEGUE:
        out.append('pliegue')
    if any(distancia(o, s) < DISTANCIA_MIN for j, o in enumerate(sitios) if j != i):
        out.append('cerca')
    return out


def resultado_correcto(sitios, mayores):
    """Lo que debía concluir el alumno con las pápulas que midió:
    {indice: 'positivo'|'negativo'|'valido'|'no_valido'}. `mayores` es el
    diámetro mayor verdadero de cada sitio al leer."""
    neg = max([mayores[i] for i, s in enumerate(sitios) if s['extracto'] == 'neg'] or [0.0])
    out = {}
    for i, s in enumerate(sitios):
        m = mayores[i]
        if s['extracto'] == 'neg':
            out[i] = 'valido' if m < UMBRAL_MM else 'no_valido'
        elif s['extracto'] == 'his':
            out[i] = 'valido' if m >= UMBRAL_MM else 'no_valido'
        else:
            out[i] = 'positivo' if m >= UMBRAL_MM and m - neg >= UMBRAL_MM else 'negativo'
    return out
