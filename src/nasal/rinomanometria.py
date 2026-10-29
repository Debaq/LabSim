"""La rinomanometría anterior activa de RinoSim: de la geometría de cada fosa
(modelo.py) a la curva presión-flujo, y de la curva a la resistencia, como la
enseña H26. Port de js/rinomanometria.js.

La física, en el orden en que se usa:

  Rohrer (1915)   cada tramo de fosa cumple ΔP = k₁·V̇ + k₂·V̇² (H26): un
                  término laminar y uno turbulento. Aquí los dos salen del
                  perfil área-distancia A(x):
                    k₁ = C_LAMINAR · Σ dx / A³    (rendija: la resistencia
                         laminar crece con el cubo del angostamiento)
                    k₂ = ½ρ · (K_ORIFICIO / A_min² + K_DISTRIBUIDA · Σ dx / A²)
                  ½ρ·(V̇/A)² es la presión dinámica (Bernoulli): lo que cuesta
                  acelerar el aire por la sección más angosta, perdido al
                  frenarse detrás. Los dos crecen cuando CUALQUIER sección se
                  angosta, así que la resistencia es monótona con la
                  geometría (lo prueba tests/test_nasal_rinomanometria.py).
  válvula         al inspirar, la válvula se cierra según su `colapso` y la
                  presión: colapso · P / (P + P_COLAPSO). Es lo que dobla la
                  curva en meseta (H26) y, con colapso grande, la hace caer.
  la técnica      el tubo de presión en la narina contraria lee la presión de
                  la rinofaringe porque por esa fosa no pasa aire (H26). El
                  modelo arma una red con las dos fosas partidas en la
                  perforación (si la hay), la boca y la fuga del adaptador, y
                  la resuelve: así la perforación, el adaptador sin sellar y
                  la boca abierta dan la curva EQUIVOCADA que daría el equipo,
                  sin reglas aparte para cada error.
  el paciente     respira buscando un flujo inspiratorio pico, hasta una
                  presión máxima: una nariz muy abierta no llega a 150 Pa
                  (Vogt y cols., 2016: 4,5-8,6 % de 20.069 mediciones), una
                  obstruida llega a más.

Las constantes de este archivo son ÓRDENES DE MAGNITUD DEL MODELO, elegidas
para que una fosa normal dé una resistencia del orden de las que cita H26 a
150 Pa; no son medidas de nadie.

Notas del port (la equivalencia con el JS manda, así que se conserva todo):
  * Las sumas son bucles a mano y no sum(): desde Python 3.12 sum() de floats
    compensa el error y daría diferencias de 1 ulp contra el reduce del JS.
  * Las claves de lecturas / verdad / total son enteros (75, 150); en el JSON
    del JS son los mismos números convertidos en texto.
  * Las claves de los resultados van en snake_case (cv_entre_ciclos).
"""

import math

from .azar import a_fijo, a_texto, generador
from .modelo import DX, LADOS, REJILLA, congestion, js_round, perfil
from .referencias import HILBERG_1989, REFERENCIA_UNILATERAL_150

# ½ρ del aire (ρ ≈ 1,2 kg/m³), en Pa por (cm/s)²: ½ρv² con v en cm/s. Física.
RHO_MEDIO = 6e-5
# Órdenes de magnitud del modelo.
C_LAMINAR = 0.0135
K_ORIFICIO = 1.5
K_DISTRIBUIDA = 1.35
# Presión a la que el colapso de la válvula va por la mitad, Pa. Modelo.
P_COLAPSO = 120
# Hasta dónde llega la fosa (coana), cm: lo de atrás no suma resistencia.
X_COANA = 8
# Área de la boca abierta dentro de la máscara, cm². Modelo.
AREA_BOCA = 1.6
# Área de la fuga alrededor de un adaptador que no sella, cm². Modelo.
AREA_FUGA_ADAPTADOR = 0.12
# Fracción del flujo que se escapa por una máscara que no sella. Modelo.
FRACCION_FUGA_MASCARA = 0.3

# Las presiones de referencia que usa H26 (Clement, 1984; Wong y Eccles, 2014).
PRESIONES = [75, 150]
# Radio de Broms (1982), con la escala de ejes 1 Pa ≙ 1 cm³/s (sin verificar en el original).
RADIO_BROMS = 200

I_COANA = js_round(X_COANA / DX)

_INF = math.inf


def _div(a, b):
    """a / b como en JS: división por cero da ±Infinity o NaN, no excepción."""
    if b == 0:
        if a == 0 or a != a:
            return math.nan
        return math.copysign(_INF, a) * math.copysign(1.0, b)
    return a / b


def _signo(x):
    """Math.sign de JS."""
    return 1 if x > 0 else -1 if x < 0 else 0


# ── Rohrer ──────────────────────────────────────────────────────────────────

def flujo(k1, k2, dP):
    """Flujo (cm³/s, con signo) de un elemento de Rohrer con caída ΔP (Pa, con signo)."""
    a = abs(dP)
    if a == 0:
        return 0
    v = (-k1 + math.sqrt(k1 * k1 + 4 * k2 * a)) / (2 * k2) if k2 > 0 else _div(a, k1)
    return _signo(dP) * v


def presion(k1, k2, V):
    """Caída de presión (Pa, con signo) de un elemento de Rohrer con flujo V."""
    return _signo(V) * (k1 * abs(V) + k2 * V * V)


def resistencia_total(rD, rI):
    """Resistencias en paralelo (H26): 1/RT = 1/RD + 1/RI. Una fosa cerrada (∞) no suma."""
    if rD is None or rI is None:
        return None

    def g(r):
        return 1 / r if math.isfinite(r) and r > 0 else 0

    s = g(rD) + g(rI)
    return 1 / s if s > 0 else _INF


def coeficientes(A, i0=0, i1=I_COANA):
    """k₁ y k₂ de un tramo [i0, i1) de un perfil de áreas (cm²) sobre REJILLA.
    Pa/(cm³/s) y Pa/(cm³/s)²."""
    s3 = 0
    s2 = 0
    for i in range(i0, i1):
        s3 += DX / A[i] ** 3
        s2 += DX / A[i] ** 2
    # La pérdida de orificio es una sola, la de la sección más angosta de toda
    # la fosa: se la lleva el tramo que la contiene (si la fosa se parte en dos
    # tramos, la suma de los tramos da la fosa entera).
    imin = 0
    for i in range(1, I_COANA):
        if A[i] < A[imin]:
            imin = i
    amin = A[imin]
    orificio = K_ORIFICIO / amin ** 2 if i0 <= imin < i1 else 0
    return {'k1': C_LAMINAR * s3, 'k2': RHO_MEDIO * (orificio + K_DISTRIBUIDA * s2), 'amin': amin}


# ── Una fosa ────────────────────────────────────────────────────────────────

class Fosa:
    """Una fosa lista para la rinomanometría: el perfil del estado y el peso
    de la válvula para cerrarla al inspirar. `coef(P, i0, i1)` da k₁ y k₂ del
    tramo a la presión P (Pa; positiva = inspiración)."""

    def __init__(self, p, lado, estado=None):
        estado = estado or {}
        self.lado = lado
        self.A = perfil(p, lado, estado)
        self._v = p['lados'][lado]['valvula']
        self.peso = [math.exp(-0.5 * ((x - self._v['pos']) / 0.5) ** 2) for x in REJILLA]
        self._cache = {}
        self.congestion = congestion(p, lado, estado)

    def coef(self, P, i0=0, i1=I_COANA):
        v = self._v
        cierre = (v['colapso'] * P) / (P + P_COLAPSO) if P > 0 else 0
        # La clave redondea el cierre a 5 decimales, como el JS: dos presiones
        # con la misma clave comparten los coeficientes de la primera.
        clave = (a_fijo(cierre, 5), i0, i1)
        c = self._cache.get(clave)
        if c is None:
            if cierre > 0:
                Ad = [max(0.005, a * (1 - cierre * self.peso[i])) for i, a in enumerate(self.A)]
            else:
                Ad = self.A
            c = coeficientes(Ad, i0, i1)
            self._cache[clave] = c
        return c


def fosa(p, lado, estado=None):
    return Fosa(p, lado, estado)


def flujo_fosa(f, P):
    """Flujo verdadero de una fosa sola, sin errores de técnica, a la presión P."""
    c = f.coef(P)
    return flujo(c['k1'], c['k2'], P)


def resistencia_fosa(f, P):
    """Resistencia verdadera de una fosa a la presión P (Pa), Pa/(cm³/s)."""
    return _div(P, flujo_fosa(f, P))


# ── La red: lo que ve el equipo ─────────────────────────────────────────────

def resuelve_red(fm, fo, P, perforacion, errores=None):
    """Resuelve la red de la medición de `lado` (fosa abierta) con la otra
    ocluida por el adaptador, para una presión de rinofaringe P (Pa, + inspiración).

    Nodos: aire (0), rinofaringe (P) y tres desconocidos: R, la fosa medida a
    la altura de la perforación; L, la otra fosa a esa altura; N, la narina
    ocluida, donde está el tubo de presión. Aristas, todas de Rohrer:
      aire–R   la fosa medida, de la narina a la perforación.
      R–rino   la fosa medida, de la perforación a la coana.
      L–rino   la otra fosa, de la perforación a la coana.
      R–L      la perforación (si la hay).
      N–L      la otra fosa, de la narina a la perforación.
      N–aire   la fuga alrededor del adaptador (si no sella), hacia la máscara.
      aire–rino  la boca (si respira por la boca), dentro de la máscara.
    Devuelve la presión que lee el tubo (la de N), el flujo que pasa por el
    neumotacógrafo (lo que entra a la máscara) y el que llega a la rinofaringe.
    """
    errores = errores or {}
    # Sin perforación, el corte de las fosas en dos tramos da lo mismo: se
    # pone a mitad de camino para que ningún tramo quede vacío.
    ip = js_round((perforacion['pos'] if perforacion and perforacion['area'] > 0 else X_COANA / 2) / DX)
    am = fm.coef(P, 0, ip)
    pm = fm.coef(P, ip, I_COANA)
    ao = fo.coef(P, 0, ip)
    po = fo.coef(P, ip, I_COANA)
    perf = ({'k1': 0.002, 'k2': (RHO_MEDIO * 1.5) / perforacion['area'] ** 2}
            if perforacion and perforacion['area'] > 0 else None)
    fuga = {'k1': 0, 'k2': RHO_MEDIO / AREA_FUGA_ADAPTADOR ** 2} if errores.get('adaptador') else None
    boca = {'k1': 0.004, 'k2': RHO_MEDIO / AREA_BOCA ** 2} if errores.get('boca') else None

    def F(e, a, b):  # de a hacia b
        return flujo(e['k1'], e['k2'], b - a) if e else 0

    phi = {'R': P / 2, 'L': P, 'N': P}

    # Lo que entra a cada nodo menos lo que sale, con su potencial en `v`.
    def neto_R(v):
        return F(am, 0, v) - F(pm, v, P) - F(perf, v, phi['L'])

    def neto_L(v):
        return F(perf, phi['R'], v) + F(ao, phi['N'], v) - F(po, v, P)

    def neto_N(v):
        return F(fuga, 0, v) - F(ao, v, phi['L'])

    neto = {'R': neto_R, 'L': neto_L, 'N': neto_N}
    lo = min(0, P)
    hi = max(0, P)
    for _barrido in range(40):
        cambio = 0
        for n in ('R', 'L', 'N'):
            # El aire va hacia la succión mayor: subir el potencial del nodo
            # aumenta lo que entra y baja lo que sale. El neto crece: bisección.
            a = lo
            b = hi
            fn = neto[n]
            for _k in range(48):
                m = (a + b) / 2
                if fn(m) > 0:
                    b = m
                else:
                    a = m
            nuevo = (a + b) / 2
            cambio = max(cambio, abs(nuevo - phi[n]))
            phi[n] = nuevo
        if cambio < 1e-4 * (hi - lo + 1):
            break
    mascara = F(am, 0, phi['R']) + F(fuga, 0, phi['N']) + F(boca, 0, P)
    pulmon = F(pm, phi['R'], P) + F(po, phi['L'], P) + F(boca, 0, P)
    return {'sensor': phi['N'], 'mascara': mascara, 'pulmon': pulmon}


# ── La medición ─────────────────────────────────────────────────────────────

# Flujo pico que busca el paciente y presión máxima que hace, por maniobra. Modelo.
ESFUERZO = {
    'normal': {'flujo': 650, 'pmax': 420},
    'forzada': {'flujo': 1500, 'pmax': 900},
}


def mide_fosa(p, lado, estado=None, opciones=None):
    """Mide una fosa como el equipo: varios ciclos respiratorios, la curva
    promedio y la resistencia a 75 y 150 Pa (y en el radio de Broms).

    opciones:
      ciclos      cuántos ciclos promedia el equipo (3-5; Vogt y cols., 2016).
      semilla     para la variabilidad entre ciclos.
      errores     {mascara, adaptador, boca, irregular}: los errores de H26.
      forzada     inspiración forzada (no es un error: una maniobra).
    """
    estado = estado or {}
    opciones = opciones or {}
    ciclos = opciones.get('ciclos', 4)
    semilla = opciones.get('semilla', 1)
    errores = opciones.get('errores') or {}
    forzada = opciones.get('forzada', False)
    otro = 'I' if lado == 'D' else 'D'
    fm = fosa(p, lado, estado)
    fo = fosa(p, otro, estado)
    esfuerzo = ESFUERZO['forzada' if forzada else 'normal']
    minuto = estado.get('minuto')
    r = generador(f"rm/{a_texto(semilla)}/{lado}/{'vc' if estado.get('vc') else 'reposo'}/{a_texto(0 if minuto is None else minuto)}")

    # La curva estática de la red, en una rejilla de presiones de rinofaringe.
    paso = 2
    tope = esfuerzo['pmax'] * 1.25
    tabla = []
    P = -tope
    while P <= tope + 1e-9:
        t = resuelve_red(fm, fo, P, p['perforacion'], errores)
        t['P'] = P
        tabla.append(t)
        P += paso

    def en_tabla(P, campo):
        t = max(0, min(len(tabla) - 1.000001, (P + tope) / paso))
        i = math.floor(t)
        return tabla[i][campo] + (tabla[i + 1][campo] - tabla[i][campo]) * (t - i)

    # El paciente: la menor presión con la que llega a su flujo, o su máximo.
    def presion_pico(signo, objetivo, pmax):
        P = 2
        while P <= pmax:
            if abs(en_tabla(signo * P, 'pulmon')) >= objetivo:
                return P
            P += 1
        return pmax

    pico_insp = presion_pico(1, esfuerzo['flujo'], esfuerzo['pmax'])
    pico_esp = presion_pico(-1, 0.9 * esfuerzo['flujo'], 0.9 * esfuerzo['pmax'])

    # Los ciclos: la presión va y viene como un seno; el flujo la sigue con un
    # pequeño retraso (la inercia del aire), que abre la curva en un lazo.
    irregular = bool(errores.get('irregular'))
    cv = 0.3 if irregular else 0.05
    retraso = 0.08 if irregular else 0.015
    N = 160
    lista = []
    for _c in range(ciclos):
        a = max(0.35, r.normal(1, cv))
        pi = min(tope, pico_insp * a)
        pe = min(tope, pico_esp * max(0.35, r.normal(1, cv)))
        # Una pausa (traga, aguanta) en algún ciclo de la respiración irregular.
        pausa = r.entre(0.3, 5.5) if irregular and r.uniforme() < 0.6 else None
        # Y respira cada ciclo distinto, y la máscara se mueve: cada ciclo con
        # su propio retraso y su propia ganancia del flujo.
        atraso = max(0, r.normal(retraso, 0.06)) if irregular else retraso
        ganancia = r.normal(1, 0.12) if irregular else 1
        Ps = []
        Vs = []
        fase = []
        for k in range(N + 1):
            th = (2 * math.pi * k) / N

            def pnp(t):
                return (pi if t < math.pi else pe) * math.sin(t)

            thr = max(0, th - atraso)
            v = ganancia * en_tabla(pnp(thr), 'mascara')
            if pausa is not None and th > pausa and th < pausa + 0.6:
                v *= 0.05
            if errores.get('mascara'):
                v *= 1 - FRACCION_FUGA_MASCARA
            Ps.append(en_tabla(pnp(th), 'sensor') + r.normal(0, 1.2))
            Vs.append(v + r.normal(0, 12 if irregular else 4))
            fase.append('insp' if th < math.pi else 'esp')
        lista.append({'P': Ps, 'V': Vs, 'fase': fase, 'pico': {'insp': pi, 'esp': pe}})

    media = {'insp': _promedio(lista, 'insp'), 'esp': _promedio(lista, 'esp')}

    def lectura(rama, Pref):
        v = lee_en(media[rama], Pref)
        return None if v is None else {'P': Pref, 'V': v, 'R': _div(Pref, v)}

    resultado = {
        'lado': lado,
        'estado': dict(estado),
        'ciclos': lista,
        'media': media,
        'pico': {'insp': max([q[0] for q in media['insp']] + [0]),
                 'esp': max([q[0] for q in media['esp']] + [0])},
        'lecturas': {},
        'broms': broms(media['insp']),
        'avisos': [],
    }
    for Pref in PRESIONES:
        resultado['lecturas'][Pref] = {'insp': lectura('insp', Pref), 'esp': lectura('esp', Pref)}

    # Lo que el equipo sí avisa: no llegó a la presión, ciclos que no se parecen.
    if not resultado['lecturas'][150]['insp']:
        resultado['avisos'].append(
            'No alcanza 150 Pa en inspiración: leer a 75 Pa y decir a qué presión.'
            if resultado['lecturas'][75]['insp']
            else 'No alcanza 75 Pa en inspiración: la curva no se puede leer.')
    cvR = _variacion_entre_ciclos(lista)
    resultado['cv_entre_ciclos'] = cvR
    # Umbral de aviso: criterio del simulador, no una norma.
    if cvR is not None and cvR > 0.12:
        resultado['avisos'].append(f'Ciclos poco reproducibles (variación {a_fijo(cvR * 100, 0)} %): repetir la medición.')

    # Lo que el equipo NO sabe: la resistencia verdadera de esa fosa, sin
    # errores de técnica ni perforación. Para el docente y para los tests.
    resultado['verdad'] = {}
    for Pref in PRESIONES:
        resultado['verdad'][Pref] = resistencia_fosa(fm, Pref)
    resultado['congestion'] = fm.congestion
    return resultado


def _promedio(lista, rama):
    """Curva promedio de una rama, como la dibuja el equipo: cada ciclo se lee
    en una rejilla de |P| cada 5 Pa, en su subida y en su bajada (el centro del
    lazo), y se promedian los ciclos que llegaron a esa presión (al menos dos)."""
    ancho = 5
    suma = {}
    n = {}
    for c in lista:
        pts = []
        # Una rama es donde presión y flujo van en el mismo sentido: el equipo
        # separa inspiración y espiración por el sentido del flujo, y deja fuera
        # el cruce por cero, donde el flujo todavía va atrasado.
        s = 1 if rama == 'insp' else -1
        for k in range(len(c['P'])):
            if c['fase'][k] == rama and s * c['P'][k] > 0 and s * c['V'][k] > 0:
                pts.append((abs(c['P'][k]), abs(c['V'][k])))
        if len(pts) < 3:
            continue
        ip = 0
        for k in range(1, len(pts)):
            if pts[k][0] > pts[ip][0]:
                ip = k
        sube = pts[:ip + 1]
        baja = pts[ip:][::-1]
        b = 1
        while b * ancho <= pts[ip][0]:
            P = b * ancho
            vs = [v for v in (_en_rama(sube, P), _en_rama(baja, P)) if v is not None]
            if vs:
                tot = 0
                for v in vs:
                    tot += v
                suma[b] = suma.get(b, 0) + tot / len(vs)
                n[b] = n.get(b, 0) + 1
            b += 1
    minimo = min(2, len(lista))
    largo = (max(suma) + 1) if suma else 0  # suma.length de un arreglo disperso
    out = [[0, 0]]
    huecos = 0
    for b in range(1, largo):
        if not n.get(b) or n[b] < minimo:
            # Cerca del cero el flujo todavía cambia de sentido: se salta. Más
            # arriba, un hueco largo es el final de la curva.
            if len(out) > 1:
                huecos += 1
                if huecos > 3:
                    break
            continue
        huecos = 0
        out.append([b * ancho, suma[b] / n[b]])
    return out


def _en_rama(pts, P):
    """V en la presión P de una rama monótona en P (aprox.), o None."""
    for i in range(1, len(pts)):
        p0, v0 = pts[i - 1]
        p1, v1 = pts[i]
        if (P - p0) * (P - p1) <= 0 and p1 != p0:
            return v0 + ((v1 - v0) * (P - p0)) / (p1 - p0)
    return None


def lee_en(curva, P):
    """Flujo de una curva [[P, V]] a la presión P, o None si no llega."""
    for i in range(1, len(curva)):
        p0, v0 = curva[i - 1]
        p1, v1 = curva[i]
        if P >= p0 and P <= p1 and p1 > p0:
            return v0 + ((v1 - v0) * (P - p0)) / (p1 - p0)
    return None


def broms(curva, radio=RADIO_BROMS):
    """Broms: el punto donde la curva corta el círculo de RADIO_BROMS; R = P/V ahí."""
    for i in range(1, len(curva)):
        p0, v0 = curva[i - 1]
        p1, v1 = curva[i]
        r0 = math.hypot(p0, v0)
        r1 = math.hypot(p1, v1)
        if r0 <= radio and r1 >= radio and r1 > r0:
            t = (radio - r0) / (r1 - r0)
            P = p0 + t * (p1 - p0)
            V = v0 + t * (v1 - v0)
            return {'P': P, 'V': V, 'R': _div(P, V)}
    return None


def _variacion_entre_ciclos(lista):
    """Coeficiente de variación de la resistencia entre ciclos, en la rama inspiratoria."""
    rs = []
    for c in lista:
        pts = []
        k = 0
        while k < len(c['P']) and c['fase'][k] == 'insp':
            pts.append((abs(c['P'][k]), abs(c['V'][k])))
            k += 1
        pico = max(q[0] for q in pts)
        Pref = 150 if pico >= 150 else 75 if pico >= 75 else None
        if not Pref:
            continue
        for i in range(1, len(pts)):
            if pts[i - 1][0] <= Pref and pts[i][0] >= Pref and pts[i][0] > pts[i - 1][0]:
                t = (Pref - pts[i - 1][0]) / (pts[i][0] - pts[i - 1][0])
                rs.append(_div(Pref, pts[i - 1][1] + t * (pts[i][1] - pts[i - 1][1])))
                break
    if len(rs) < 2:
        return None
    tot = 0
    for x in rs:
        tot += x
    m = tot / len(rs)
    sq = 0
    for x in rs:
        sq += (x - m) ** 2
    de = math.sqrt(sq / (len(rs) - 1))
    return _div(de, m)


def examen(p, estado=None, opciones=None):
    """El examen completo de un estado: las dos fosas y la total a 75 y 150 Pa.
    La total se calcula como en H26 (paralelo), con las lecturas inspiratorias."""
    estado = estado or {}
    fosas = {}
    for lado in LADOS:
        fosas[lado] = mide_fosa(p, lado, estado, opciones)
    total = {}
    for Pref in PRESIONES:
        li = fosas['D']['lecturas'][Pref]['insp']
        ri = fosas['I']['lecturas'][Pref]['insp']
        total[Pref] = resistencia_total(li['R'] if li else None, ri['R'] if ri else None)
    return {'fosas': fosas, 'total': total, 'estado': dict(estado)}


# Criterio del SIMULADOR para decir "igual que en reposo": un cambio menor que
# la variación de la rinomanometría entre mediciones (coeficiente de
# variación de 15 %, Hilberg y cols., 1989, citado en H27). H26 no fija un
# porcentaje; este umbral es una elección del simulador, no una norma.
UMBRAL_SIN_CAMBIO = HILBERG_1989['cv_rinomanometria']


def lectura_vasoconstrictor(rReposo, rVc, referencia=REFERENCIA_UNILATERAL_150['valor']):
    """La lectura de la prueba con vasoconstrictor según la tabla de H26, para
    una fosa con su resistencia a 150 Pa en reposo y después."""
    if rReposo is None or rVc is None:
        return None
    cambio = _div(rVc - rReposo, rReposo)
    # H26, paso 7: el vasoconstrictor se aplica solo en la fosa que supera la referencia.
    if rReposo <= referencia:
        return {'cambio': cambio, 'tipo': 'normal', 'texto': 'Dentro de la referencia en reposo: según H26 esta fosa no necesita la prueba'}
    if cambio > UMBRAL_SIN_CAMBIO:
        return {'cambio': cambio, 'tipo': 'sube', 'texto': 'Sube respecto del reposo: revisar ciclo, sello y respiración antes de informar'}
    if abs(cambio) <= UMBRAL_SIN_CAMBIO:
        return {'cambio': cambio, 'tipo': 'mecanica', 'texto': 'Igual que en reposo: mecánica (estructural)'}
    if rVc <= referencia:
        return {'cambio': cambio, 'tipo': 'vasomotora', 'texto': 'Baja hasta la referencia: vasomotora (mucosa)'}
    return {'cambio': cambio, 'tipo': 'mixta', 'texto': 'Baja sin llegar a la referencia: mixta'}
