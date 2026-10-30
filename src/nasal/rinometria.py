"""La rinometría acústica de RinoSim: de la geometría de cada fosa (modelo.py)
a la curva área-distancia que dibujaría el equipo, con sus errores, como la
enseña H27. Port de js/rinometria.js.

El equipo NO ve la nariz tal cual es. El modelo parte del perfil verdadero
y le aplica, en este orden, lo que H27 dice que le pasa al eco:

  adaptador que aprieta   deforma la narina y el vestíbulo: la entrada y la
                          válvula salen más chicas (Hilberg y Pedersen, 2000).
  perforación septal      detrás de ella el pulso pasa también a la otra
                          fosa y suma parte de su área (H27, errores).
  senos y rinofaringe     pasados unos 5 cm el sonido entra a los senos por
                          sus ostium y a la rinofaringe: área que no es de
                          la fosa, más con la mucosa descongestionada
                          (Hilberg y Pedersen, 1996; Cakmak y cols., 2003).
  estrechamiento marcado  detrás de un estrechamiento muy cerrado llega poca
                          energía y la curva se subestima: lo de atrás se
                          aplana hacia el mínimo (Cakmak y cols., 2005).
  fuga en el adaptador    el sonido que se escapa se lee como sección que se
                          abre: las áreas salen sobreestimadas, y más hacia
                          atrás (Hilberg y Pedersen, 2000).
  resolución              el pulso tiene un ancho de banda: el perfil sale
                          suavizado unos milímetros.
  repetición              cada registro varía un poco (posición, sello):
                          Hilberg y cols. (1989) dan un coeficiente de
                          variación de las áreas menor de 2 %.

Todos estos errores son CUALITATIVOS: dan el sentido del error que describe
la literatura, con tamaños elegidos por el modelo, no medidos.

Notas del port: las sumas son bucles a mano (sum() de Python 3.12+ compensa
el error y no daría lo mismo que el JS); las claves de los resultados van en
snake_case (segundo_claro) salvo las que no tienen mayúsculas (dist1, mca1,
vol05, vol25).
"""

import math

from .azar import a_fijo, a_texto, generador
from .modelo import DX, REJILLA, congestion, js_round, perfil

# Hasta dónde dibuja la curva el equipo, cm.
X_CURVA = 10
# Hasta dónde se cree la curva (H27): pasados ~5 cm, no se lee como área de la fosa.
X_CONFIABLE = 5
# Debajo de esta área, lo de atrás se subestima. Orden de magnitud del modelo, cm².
AREA_CRITICA = 0.3
# Criterio del protocolo del libro (H27): tres registros con MCA1 y MCA2 a 0,03 cm² o menos.
CRITERIO_REPETICION = 0.03
# Coeficiente de variación entre registros del modelo, bajo el < 2 % de Hilberg y cols. (1989).
CV_REGISTRO = 0.005

I_CURVA = js_round(X_CURVA / DX)


def _sigmoide(x, x0, w):
    return 1 / (1 + math.exp(-(x - x0) / w))


def _suaviza(A, sigma):
    """Suavizado gaussiano de un perfil sobre la rejilla, σ en cm."""
    r = math.ceil((3 * sigma) / DX)
    w = [math.exp(-0.5 * (((k - r) * DX) / sigma) ** 2) for k in range(2 * r + 1)]
    out = []
    n_a = len(A)
    for i in range(n_a):
        s = 0
        n = 0
        for k in range(-r, r + 1):
            j = min(n_a - 1, max(0, i + k))
            s += A[j] * w[k + r]
            n += w[k + r]
        out.append(s / n)
    return out


def curva_del_equipo(p, lado, estado=None, errores=None):
    """Lo que el equipo vería sin la variación entre registros: el perfil
    verdadero con los errores físicos del método y los de técnica pedidos en
    `errores` ({aprieta, fuga})."""
    errores = errores or {}
    A = perfil(p, lado, estado)
    c = congestion(p, lado, estado)
    if errores.get('aprieta'):
        A = [a * (1 - 0.25 * (1 - _sigmoide(REJILLA[i], 1.7, 0.2))) for i, a in enumerate(A)]
    perf = p['perforacion']
    if perf and perf['area'] > 0:
        otro = perfil(p, 'I' if lado == 'D' else 'D', estado)
        m = min(0.6, 0.6 * perf['area'])
        A = [a + m * otro[i] * _sigmoide(REJILLA[i], perf['pos'] + 0.2, 0.15) for i, a in enumerate(A)]
    # Senos y rinofaringe: más área con la mucosa retraída (ostium abiertos).
    A = [a + 0.9 * (1 + 0.6 * (1 - c)) * _sigmoide(REJILLA[i], 6.0, 0.45) for i, a in enumerate(A)]
    # Detrás de un estrechamiento marcado: se aplana hacia el mínimo.
    m = math.inf
    out = []
    for i, a in enumerate(A):
        x = REJILLA[i]
        if x < 0.3:
            visto = a
        elif m < AREA_CRITICA:
            visto = m + (a - m) * (m / AREA_CRITICA) ** 1.5
        else:
            visto = a
        if x >= 0.3:
            m = min(m, a)
        out.append(visto)
    A = out
    if errores.get('fuga'):
        A = [a * (1.2 + 0.45 * (1 - math.exp(-REJILLA[i] / 2.5))) for i, a in enumerate(A)]
    return _suaviza(A, 0.08)


def registro(p, lado, estado=None, opciones=None, k=0):
    """Un registro: la curva del equipo con la variación de esa repetición. El
    registro `k` de la misma semilla sale siempre igual."""
    estado = estado or {}
    opciones = opciones or {}
    semilla = opciones.get('semilla', 1)
    errores = opciones.get('errores') or {}
    base = opciones.get('base')
    if base is None:
        base = curva_del_equipo(p, lado, estado, errores)
    minuto = estado.get('minuto')
    r = generador(f"ra/{a_texto(semilla)}/{lado}/{'vc' if estado.get('vc') else 'reposo'}/{a_texto(0 if minuto is None else minuto)}/{k}")
    malo = errores.get('fuga') or errores.get('respira')
    g = r.normal(1, 0.06 if malo else CV_REGISTRO)
    corrimiento = r.normal(0, 0.12 if malo else 0.03)
    ondas = []
    for _ in range(2):
        a_ = r.normal(0, 0.04 if malo else 0.002)
        f_ = r.entre(0.3, 0.9)
        fase_ = r.entre(0, 6.3)
        ondas.append({'a': a_, 'f': f_, 'fase': fase_})
    # Al respirar o tragar se mueve el paladar: la parte de atrás cambia mucho.
    atras = r.normal(0, 0.25) if errores.get('respira') else 0
    A = []
    x = []
    n_b = len(base)
    for i in range(I_CURVA + 1):
        xi = REJILLA[i]
        j = min(n_b - 1, max(0, i - corrimiento / DX))
        j0 = math.floor(j)
        a = base[j0] + (base[min(n_b - 1, j0 + 1)] - base[j0]) * (j - j0)
        f = g
        for o in ondas:
            f += o['a'] * math.sin(2 * math.pi * o['f'] * xi + o['fase'])
        f += atras * _sigmoide(xi, 4.5, 0.4)
        x.append(xi)
        A.append(max(0.01, a * f))
    return {'x': x, 'A': A}


def _minimos(x, A, a, b):
    """Los mínimos locales de una curva entre a y b cm, con su prominencia."""
    out = []
    for i in range(1, len(A) - 1):
        if x[i] < a or x[i] > b:
            continue
        if A[i] <= A[i - 1] and A[i] < A[i + 1]:
            # Prominencia: cuánto sube la curva antes de volver a bajar más.
            izq = A[i]
            j = i - 1
            while j >= 0 and A[j] >= A[i]:
                izq = max(izq, A[j])
                j -= 1
            der = A[i]
            j = i + 1
            while j < len(A) and A[j] >= A[i]:
                der = max(der, A[j])
                j += 1
            out.append({'i': i, 'prom': min(izq, der) - A[i]})
    return out


def _hombro(x, A, a, b):
    """Donde la curva sube menos entre a y b cm (el hombro que deja un valle borrado)."""
    k = -1
    menor = math.inf
    h = 10  # la pendiente sobre ±0,25 cm, para que el ruido no la mueva
    for i in range(h, len(x) - h):
        if x[i] < a or x[i] > b:
            continue
        pendiente = (A[i + h] - A[i - h]) / (x[i + h] - x[i - h])
        if pendiente < menor:
            menor = pendiente
            k = i
    return k


def volumen(x, A, a, b):
    """Volumen (cm³) bajo la curva entre a y b cm, por trapecios."""
    v = 0
    for i in range(1, len(x)):
        x0 = max(a, x[i - 1])
        x1 = min(b, x[i])
        if x1 <= x0:
            continue
        v += ((A[i - 1] + A[i]) / 2) * (x1 - x0)
    return v


def medidas(x, A):
    """Lo que se anota de una curva (H27): Dist 1 y MCA1 (primer mínimo, la
    válvula), Dist 2 y MCA2 (segundo mínimo, la cabeza del cornete), Vol 1
    (de la narina al segundo mínimo), Vol 0-5 (el «Vol 2» del libro) y Vol 2-5
    (el que piden las normas para los cambios de la mucosa; Hilberg y
    Pedersen, 2000)."""
    PROM = 0.02
    lista = [m for m in _minimos(x, A, 0.4, 5.6) if m['prom'] >= PROM]

    def en_ventana(a, b):
        k = -1
        for i in range(len(x)):
            if a <= x[i] <= b and (k < 0 or A[i] < A[k]):
                k = i
        return k

    i1 = lista[0]['i'] if lista else en_ventana(0.4, 2.6)
    sig = next((m for m in lista if x[m['i']] >= x[i1] + 0.6), None)
    # Si no hay un segundo valle claro (lo de atrás aplanado o un cornete ya
    # retraído), se marca el hombro: donde la curva sube menos en la zona del
    # cornete. El equipo lo marca igual, y el informe debe decirlo.
    i2 = sig['i'] if sig else _hombro(x, A, x[i1] + 0.8, 5.0)
    return {
        'dist1': x[i1], 'mca1': A[i1],
        'dist2': x[i2], 'mca2': A[i2],
        'segundo_claro': sig is not None,
        'vol1': volumen(x, A, 0, x[i2]),
        'vol05': volumen(x, A, 0, 5),
        'vol25': volumen(x, A, 2, 5),
    }


CAMPOS = ['dist1', 'mca1', 'dist2', 'mca2', 'vol1', 'vol05', 'vol25']


def mide_fosa(p, lado, estado=None, opciones=None):
    """El examen de una fosa: tres registros (o los que se pidan), sus
    medidas, el promedio y si cumplen el criterio de repetición del libro."""
    estado = estado or {}
    opciones = opciones or {}
    n = opciones.get('registros', 3)
    errores = opciones.get('errores') or {}
    base = curva_del_equipo(p, lado, estado, errores)
    registros = []
    for k in range(n):
        curva = registro(p, lado, estado, {**opciones, 'base': base}, k)
        curva['medidas'] = medidas(curva['x'], curva['A'])
        registros.append(curva)
    return fosa(p, lado, estado, registros)


# Registros por fosa del protocolo del libro (H27).
REGISTROS_PROTOCOLO = 3


def fosa(p, lado, estado, registros, pedidos=None):
    """Lo que se anota de una fosa con los registros ya tomados (de
    registro(), con sus medidas): el promedio, si cumplen el criterio de
    repetición y los avisos. Con `pedidos`, si faltan registros no se da por
    repetible."""
    estado = estado or {}
    n = len(registros)
    promedio = {}
    for c in CAMPOS:
        tot = 0
        for r in registros:
            tot += r['medidas'][c]
        promedio[c] = tot / n

    def rango(c):
        vs = [r['medidas'][c] for r in registros]
        return max(vs) - min(vs)

    parecidos = rango('mca1') <= CRITERIO_REPETICION and rango('mca2') <= CRITERIO_REPETICION
    faltan = bool(pedidos) and n < pedidos
    repetible = parecidos and not faltan
    avisos = []
    if faltan:
        avisos.append(f'Faltan registros: {n} de {pedidos}.')
    if not parecidos:
        avisos.append(f"Registros que no se parecen (MCA1 ±{a_fijo(rango('mca1'), 2)}, MCA2 ±{a_fijo(rango('mca2'), 2)} cm²): revisar sello, posición y apnea.")
    if promedio['mca1'] < AREA_CRITICA:
        avisos.append('Primer mínimo muy cerrado: lo que está detrás no se puede evaluar.')
    if not all(r['medidas']['segundo_claro'] for r in registros):
        avisos.append('Sin segundo mínimo claro: MCA2 se marca en el hombro de la zona del cornete.')
    # La verdad, para el docente: el perfil sin errores, medido igual.
    verdadero = perfil(p, lado, estado)[:I_CURVA + 1]
    xv = REJILLA[:I_CURVA + 1]
    return {
        'lado': lado, 'estado': dict(estado), 'registros': registros, 'promedio': promedio,
        'repetible': repetible,
        'rango': {'mca1': rango('mca1'), 'mca2': rango('mca2')},
        'avisos': avisos,
        'verdad': {'x': xv, 'A': verdadero, 'medidas': medidas(xv, verdadero)},
        'congestion': congestion(p, lado, estado),
    }


# --- La toma en vivo (el equipo de LabSim; RinoSim no la tiene) ---------
#
# El equipo manda un pulso tras otro. Cada pulso es la curva de la toma (el
# registro de su semilla: posición del adaptador, sello) con su propia
# variación, chica cerca de la narina y grande hacia atrás, donde el eco
# llega débil y mezclado (senos, rinofaringe). La pantalla muestra el
# promedio de los últimos pulsos y sus límites; al detener, el promedio es
# el registro. Tamaños elegidos por el modelo, como los errores de arriba.

# Pulsos que entran al promedio y a los límites.
VENTANA_PULSOS = 8
# Los límites: el promedio ± tantas desviaciones estándar entre pulsos (del log del área).
DE_LIMITES = 2


def dispersion(x):
    """Desviación estándar relativa entre pulsos a x cm de la narina: ~0,3 %
    adelante, ~4 % a 5 cm y ~20 % al fondo."""
    return 0.003 + 0.20 * _sigmoide(x, 6.5, 1.0)


def pulso(p, lado, semilla, receta, base=None):
    """Un pulso de la toma `semilla`. receta: {k, estado, errores}, lo que
    había al mandarlo; con ella sale siempre igual. `base` (opcional) es
    curva_del_equipo con ese estado y esos errores."""
    estado = receta.get('estado') or {}
    errores = receta.get('errores') or {}
    toma = registro(p, lado, estado, {'semilla': semilla, 'errores': errores, 'base': base}, 0)
    r = generador(f"ra-pulso/{a_texto(semilla)}/{lado}/{a_texto(receta.get('k', 0))}")
    escala = 3 if errores.get('respira') else 2 if errores.get('fuga') else 1
    # Tres ondas lentas a lo largo de la fosa, de varianza total 1.
    ondas = [(r.normal(0, 0.8165), r.entre(0.15, 0.6), r.entre(0, 6.3)) for _ in range(3)]
    # Al respirar o tragar se mueve el paladar: lo de atrás salta de un pulso a otro.
    paladar = r.normal(0, 0.3) if errores.get('respira') else 0
    A = []
    for xi, a in zip(toma['x'], toma['A']):
        campo = 0
        for amp, f, fase in ondas:
            campo += amp * math.sin(2 * math.pi * f * xi + fase)
        # En exponente: proporcional al área y nunca negativa, aunque atrás se mueva mucho.
        A.append(max(0.01, a * math.exp(escala * dispersion(xi) * campo + paladar * _sigmoide(xi, 4.5, 0.4))))
    return {'x': toma['x'], 'A': A}


def banda(curvas):
    """Promedio punto a punto de los pulsos y sus límites. La variación es
    proporcional al área: la desviación estándar se toma sobre el log del
    área y los límites son promedio · e^(±DE_LIMITES·DE), siempre positivos
    (con un pulso, los límites son él)."""
    n = len(curvas)
    x = curvas[0]['x']
    media, sup, inf = [], [], []
    for i in range(len(x)):
        tot = 0
        tot_log = 0
        for c in curvas:
            tot += c['A'][i]
            tot_log += math.log(c['A'][i])
        m = tot / n
        de = 0
        if n > 1:
            m_log = tot_log / n
            s2 = 0
            for c in curvas:
                s2 += (math.log(c['A'][i]) - m_log) ** 2
            de = math.sqrt(s2 / (n - 1))
        media.append(m)
        sup.append(m * math.exp(DE_LIMITES * de))
        inf.append(m * math.exp(-DE_LIMITES * de))
    return {'x': x, 'A': media, 'sup': sup, 'inf': inf, 'n': n}


def calidad(b, m):
    """Lo que muestran los baremos, en % del promedio: el semiancho de la
    banda en MCA1, en MCA2 y el medio de 0 a 5 cm. Con DE_LIMITES = 2, un
    semiancho del 4 % es un coeficiente de variación del 2 %."""
    x = b['x']

    def rel(i):
        return 100 * (b['sup'][i] - b['inf'][i]) / 2 / b['A'][i]

    tot = 0
    n = 0
    for i, xi in enumerate(x):
        if 0.3 <= xi <= X_CONFIABLE:
            tot += rel(i)
            n += 1
    return {'mca1': rel(x.index(m['dist1'])), 'mca2': rel(x.index(m['dist2'])), 'banda05': tot / n}


def registro_de_toma(p, lado, semilla, recetas, bases=None):
    """El registro que deja una toma: el promedio de sus pulsos (las
    recetas de la ventana), con sus límites y sus medidas. `bases` guarda
    curva_del_equipo por estado y errores entre llamadas."""
    bases = {} if bases is None else bases
    curvas = []
    for rc in recetas:
        estado = rc.get('estado') or {}
        errores = rc.get('errores') or {}
        clave = (repr(sorted(estado.items())), tuple(sorted(k for k, v in errores.items() if v)))
        if clave not in bases:
            bases[clave] = curva_del_equipo(p, lado, estado, errores)
        curvas.append(pulso(p, lado, semilla, rc, bases[clave]))
    b = banda(curvas)
    b['medidas'] = medidas(b['x'], b['A'])
    return b


def rehace_fosa(p, lado, estado=None, opciones=None):
    """La fosa de una medición guardada: cada registro desde su toma
    (opciones['registros']: [{semilla, pulsos}]). Las mediciones de antes de
    la toma en vivo (tres registros de una vez) se rehacen con mide_fosa."""
    opciones = opciones or {}
    tomas = [t for t in opciones.get('registros') or [] if t.get('pulsos')]
    if not tomas:
        return mide_fosa(p, lado, estado, opciones)
    bases = {}
    registros = [registro_de_toma(p, lado, t['semilla'], t['pulsos'], bases) for t in tomas]
    ultimo = tomas[-1]['pulsos'][-1].get('estado') or estado
    return fosa(p, lado, ultimo, registros, REGISTROS_PROTOCOLO)


def examen(p, estado=None, opciones=None):
    """Las dos fosas en un estado."""
    estado = estado or {}
    return {'fosas': {'D': mide_fosa(p, 'D', estado, opciones), 'I': mide_fosa(p, 'I', estado, opciones)},
            'estado': dict(estado)}
