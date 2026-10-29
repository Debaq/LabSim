"""La rinoscopía anterior: lo que ve el examinador por el espéculo, dibujado
desde la misma nariz que miden la rinomanometría y la rinometría.

Las fotos libres no alcanzan para esto (decidido con él, 2026-10-29): la
rinoscopía de H25 se mira con la cabeza recta, a 30° y a 60° de extensión, y
en cada posición se ve otra cosa (piso y cornete inferior; cornete y meato
medios; techo). Ninguna foto trae esas tres miradas de un mismo paciente, y
menos con SU desviación y SUS cornetes. Por eso la fosa se arma en 3D a
partir del paciente de RinoSim (nasal/modelo.py) y se dibuja trazando
rayos con numpy (sin módulos de Qt nuevos en el build):

- La fosa es un volumen de aire, en cm: x desde el tabique (0) hacia la
  pared lateral, y desde el piso hacia el techo, z desde la narina hacia la
  coana. Las paredes, los cornetes y los pólipos se describen con una
  función de distancia con signo (positiva en el aire); cada rayo avanza
  hasta chocar.
- El examinador mira desde ~25 cm por la abertura del espéculo: los rayos
  entran por la narina casi paralelos y, al extender la cabeza del
  paciente, suben dentro de la fosa (pivotan en la narina).
- Lo del paciente que cambia la imagen: la desviación (y el espolón, si es
  angosta), el cornete inferior según su hueso y su mucosa congestionada
  (el vasoconstrictor lo achica, como en la RM), los pólipos, la
  perforación, y el aspecto de la mucosa y la secreción (`aspecto`).

La fosa derecha deja el tabique a la DERECHA del examinador; la izquierda
se dibuja con su propio paciente y se espeja.

Las formas son órdenes de magnitud para que la imagen se lea como una
rinoscopía, no una anatomía medida de nadie.
"""
import math

import numpy as np

from nasal import modelo

# Cambiar esto invalida las imágenes guardadas en el equipo (ver la caché de
# nasal/RinoscopiaWindow.py).
VERSION = 2

MUCOSAS = {   # clave -> (texto, tinte sobre el rosado normal)
    'rosada': ('Rosada', (1.0, 1.0, 1.0)),
    'palida': ('Pálida', (1.02, 1.32, 1.42)),
    'violacea': ('Violácea', (0.86, 1.02, 1.22)),
    'roja': ('Roja', (1.06, 0.68, 0.64)),
}
SECRECIONES = {   # clave -> (texto, color, opacidad)
    'no': ('Sin secreción', None, 0.0),
    'acuosa': ('Acuosa', (0.95, 0.85, 0.85), 0.25),
    'mucosa': ('Mucosa', (0.93, 0.90, 0.82), 0.6),
    'purulenta': ('Purulenta', (0.80, 0.78, 0.35), 0.75),
}
ASPECTO_NORMAL = {'mucosa': 'rosada', 'secrecion': 'no'}

COLORES = {   # piso, techo, tabique, pared lateral, cornete inf., cornete medio, pólipo
    0: (0.86, 0.50, 0.48), 1: (0.82, 0.52, 0.52), 2: (0.90, 0.57, 0.54),
    3: (0.84, 0.48, 0.47), 4: (0.86, 0.40, 0.40), 5: (0.85, 0.46, 0.45), 6: (0.78, 0.74, 0.62),
}
FONDO = np.array([0.05, 0.012, 0.012])  # lo de atrás, sin luz: casi negro rojizo

# Umbrales con que el docente lee "lo que hay" (hallazgos()): criterio del
# simulador, en las mismas unidades del modelo.
DESVIACION_MINIMA = 0.15     # cm² de área que quita el tabique
ESPOLON_ANCHO = 0.5          # cm: una desviación más angosta es un espolón
CORNETE_GRANDE = 1.15        # volumen (hueso + mucosa congestionada) sobre el normal (~0,8)
CONTACTO = 0.12              # cm entre cornete y tabique


def aspecto(nasal, lado):
    """Cómo se ve la mucosa de esa fosa: `nasal['rinoscopia'][lado]`, con lo
    que falte en lo normal."""
    crudo = ((nasal or {}).get('rinoscopia') or {}).get(lado) or {}
    out = dict(ASPECTO_NORMAL)
    if crudo.get('mucosa') in MUCOSAS:
        out['mucosa'] = crudo['mucosa']
    if crudo.get('secrecion') in SECRECIONES:
        out['secrecion'] = crudo['secrecion']
    return out


def _suave(t, a, b):
    t = np.clip((t - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def _smin(a, b, k):
    """Mínimo suave: redondea la esquina donde se juntan dos superficies."""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def _capsula(P, a, b, r, escala_y=1.0):
    """Distancia a un cilindro de puntas redondas entre a y b (radio r),
    aplastado o estirado en y."""
    Q = P.copy()
    Q[:, 1] = (Q[:, 1] - a[1]) / escala_y + a[1]
    ab = np.asarray(b) - np.asarray(a)
    t = np.clip(((Q - a) @ ab) / ab.dot(ab), 0, 1)
    return np.linalg.norm(Q - (np.asarray(a) + t[:, None] * ab), axis=1) - r


class Fosa:
    """Una fosa armada en 3D desde el paciente de RinoSim."""

    def __init__(self, p, lado='D', estado=None, aspecto_fosa=None):
        s = p['lados'][lado]
        c = modelo.congestion(p, lado, estado or {})
        # El cornete inferior: hueso + lo que la mucosa ocupa ahora.
        self.vol_ci = s['cornete']['oseo'] + s['cornete']['mucosa'] * c
        self.r_ci = 0.16 + 0.24 * self.vol_ci
        self.z_ci = max(1.2, s['cornete']['pos'] - 1.3)
        self.r_cm = 0.2 + 0.1 * c
        d = s['desviacion']
        self.dev = dict(B=min(0.75, d['area'] * 2.0), z=max(1.0, d['pos']), w=max(0.35, d['ancho'] * 0.7),
                        area=d['area'], ancho=d['ancho'])
        # La desviación hacia la otra fosa deja este lado del tabique
        # cóncavo: la fosa es más ancha ahí.
        o = p['lados']['I' if lado == 'D' else 'D']['desviacion']
        self.concavo = dict(B=min(0.75, o['area'] * 2.0) * 0.8, z=max(1.0, o['pos']), w=max(0.45, o['ancho'] * 0.9))
        self.polipos = s['polipos']
        rng = np.random.default_rng(7)
        self.pol = [(rng.uniform(0.3, 0.75), rng.uniform(1.75, 2.15), rng.uniform(3.2, 5.4),
                     0.12 + 0.06 * self.polipos * rng.uniform(0.6, 1.0))
                    for _ in range(int(2 + self.polipos * 2))] if self.polipos > 0 else []
        perf = p.get('perforacion') or {}
        # Una perforación en el tercio anterior, a media altura: radio desde
        # el área.
        self.perf = (perf['pos'], math.sqrt(perf['area'] / math.pi)) if perf.get('area', 0) > 0 else None
        self.aspecto = dict(ASPECTO_NORMAL, **(aspecto_fosa or {}))

    # --- geometría --------------------------------------------------------

    def techo(self, z):
        return 2.6 + 1.9 * _suave(z, 0.4, 3.0)

    def lateral(self, y, z):
        # Ancha abajo y cerrándose hacia el techo (hendidura olfatoria).
        u = np.clip(y / self.techo(z), 0, 1)
        w = 0.18 + 1.25 * (1 - u ** 1.7)
        return w * (0.85 + 0.15 * _suave(z, 0.7, 2.0))

    def tabique(self, y, z):
        d, c = self.dev, self.concavo
        alto = np.exp(-0.5 * ((y - 1.0) / 0.8) ** 2)
        return (d['B'] * np.exp(-0.5 * ((z - d['z']) / d['w']) ** 2)
                - c['B'] * np.exp(-0.5 * ((z - c['z']) / c['w']) ** 2)) * alto

    def x_cornete(self):
        return 1.35 * 0.98 - 0.15

    def campo(self, P):
        """Distancia con signo (positiva en el aire) y qué superficie es."""
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        piso = y + 0.18 * (x - 0.6) ** 2 - 0.05
        tabique = x - self.tabique(y, z)
        if self.perf is not None:
            # Por el agujero el rayo pasa a la otra fosa (que queda a oscuras).
            pos, r = self.perf
            dentro = r - np.sqrt((z - pos) ** 2 + (y - 1.1) ** 2)
            tabique = np.where(dentro > 0, np.maximum(tabique, x + 2.0), tabique)
        partes = [piso, self.techo(z) - y, tabique, self.lateral(y, z) - x]
        tipos = [0, 1, 2, 3]
        # Cornete inferior: un reborde a lo largo de la pared lateral, con la
        # cabeza adelante. El medio, más alto y más atrás.
        xi, yi = self.x_cornete(), 0.95
        partes.append(_capsula(P, [xi, yi, self.z_ci], [xi + 0.05, yi - 0.1, self.z_ci + 4.5], self.r_ci + 0.15, 1.5))
        tipos.append(4)
        ym = 2.45
        xm = float(self.lateral(np.array([ym]), np.array([4.0]))[0]) - 0.05
        partes.append(_capsula(P, [xm, ym, 3.1], [xm, ym + 0.2, 6.5], self.r_cm + 0.12, 1.7))
        tipos.append(5)
        for cx, cy, cz, rr in self.pol:
            partes.append(np.sqrt(((P - [cx, cy, cz]) ** 2).sum(-1)) - rr)
            tipos.append(6)
        D = np.stack(partes, -1)
        i = D.argmin(-1)
        dist = D[:, 0]
        for k in range(1, D.shape[1]):
            dist = _smin(dist, D[:, k], 0.12)
        return dist, np.array(tipos)[i]


def _hash(i):
    return np.modf(np.sin(i @ np.array([127.1, 311.7, 74.7])) * 43758.5453)[0] % 1.0


def _ruido_valor(P):
    """Ruido de valor 3D (interpolado en una grilla): manchas sin patrón."""
    i = np.floor(P)
    f = P - i
    f = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = ((f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1])
                     * (f[:, 2] if dz else 1 - f[:, 2]))
                out = out + w * _hash(i + [dx, dy, dz])
    return out


def _textura(P):
    """Mucosa: manchas suaves y vasos finos (donde el ruido cruza 0,5)."""
    manchas = _ruido_valor(P * 6) * 0.6 + _ruido_valor(P * 14) * 0.4
    vasos = np.exp(-((_ruido_valor(P * 7 + 3.1) - 0.5) / 0.012) ** 2) * _ruido_valor(P * 3 + 9.7)
    return manchas, vasos


def render(fosa, grados, tam=280, espejo=False):
    """La imagen por el espéculo con la cabeza a `grados` de extensión, como
    arreglo (tam, tam, 3) uint8. `espejo`: la fosa izquierda."""
    a = math.radians(2 + 0.85 * grados)
    # Algo hacia medial: el tabique se ve de lado, no de canto.
    adelante = np.array([-0.055, math.sin(a), math.cos(a)])
    adelante /= np.linalg.norm(adelante)
    xc, yc, hx, hy = 0.62, 0.95, 0.62, 0.95     # abertura del espéculo, cm
    u = np.linspace(-1, 1, tam)
    U, V = np.meshgrid(u, -u)
    abierto = (U ** 2 + V ** 2 <= 1).reshape(-1)
    # Tabique a la derecha del examinador (x chico a la derecha).
    W = np.stack([xc - U * hx, yc + V * hy, np.zeros_like(U)], -1).reshape(-1, 3)
    ojo = np.array([xc, yc, 0.0]) - adelante * 25
    dirs = W - ojo
    dirs /= np.linalg.norm(dirs, axis=1)[:, None]
    org = W - dirs * 0.3
    t = np.zeros(len(dirs))
    vivo = abierto.copy()
    golpe = np.zeros(len(dirs), bool)
    tipo = np.zeros(len(dirs), int)
    for _ in range(180):
        if not vivo.any():
            break
        idx = np.nonzero(vivo)[0]
        Q = org[idx] + dirs[idx] * t[idx, None]
        d, ti = fosa.campo(Q)
        choca = d < 0.004
        golpe[idx[choca]] = True
        tipo[idx[choca]] = ti[choca]
        vivo[idx[choca]] = False
        t[idx[~choca]] += np.maximum(d[~choca] * 0.7, 0.004)
        sale = (Q[:, 2] > 8.2) | (Q[:, 0] < -1.5) | (t[idx] > 14)
        vivo[idx[sale & ~choca]] = False
    img = np.zeros((len(dirs), 3))
    img[abierto & ~golpe] = FONDO
    k = np.nonzero(golpe)[0]
    Q = org[k] + dirs[k] * t[k, None]
    e = 0.004
    n = np.stack([fosa.campo(Q + [e, 0, 0])[0] - fosa.campo(Q - [e, 0, 0])[0],
                  fosa.campo(Q + [0, e, 0])[0] - fosa.campo(Q - [0, e, 0])[0],
                  fosa.campo(Q + [0, 0, e])[0] - fosa.campo(Q - [0, 0, e])[0]], -1)
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-9
    lam = np.clip((n * -dirs[k]).sum(1), 0, 1)   # luz del espejo frontal, coaxial
    tk = tipo[k]
    esp = lam ** 50 * 0.5 + (tk == 6) * lam ** 12 * 0.25   # mucosa húmeda; el pólipo (edema) más
    # Lo profundo recibe menos luz: la fosa se angosta y hace sombra; cerca
    # de la coana ya es casi el fondo (sin borde duro contra él).
    zq = np.maximum(Q[:, 2], 0)
    caida = (1.0 / (1.0 + (zq / 3.2) ** 2.6)) * (1 - _suave(zq, 6.0, 8.2))
    base = np.array([COLORES[i] for i in tk])
    tinte = np.array(MUCOSAS[fosa.aspecto['mucosa']][1])
    mucosa = tk != 6
    base[mucosa] = np.clip(base[mucosa] * tinte, 0, 1)
    manchas, vasos = _textura(Q)
    base *= (0.9 + 0.2 * manchas)[:, None]
    # Vasos solo en el tabique anterior (área de Kiesselbach), tenues.
    vasos = vasos * ((tk == 2) & (Q[:, 2] < 2.2)) * 0.35
    base = base * (1 - vasos[:, None]) + np.array([0.62, 0.12, 0.14]) * vasos[:, None]
    _, color_sec, opac = SECRECIONES[fosa.aspecto['secrecion']]
    if color_sec is not None:
        # La secreción se junta en el piso y baja del meato medio por la
        # cara del cornete inferior; en manchas, no pareja.
        y = Q[:, 1]
        piso = _suave(-y, -0.5, -0.15)                                   # y < ~0,3
        meato = _suave(y, 1.5, 1.75) * (1 - _suave(y, 2.15, 2.4)) * (tk != 2)
        cara = (tk == 4) * _suave(y, 0.8, 1.2)                           # baja por el cornete
        donde = np.clip(piso + meato + cara, 0, 1)
        capa = donde * opac * np.clip(manchas * 1.6 - 0.25, 0, 1)
        base = base * (1 - capa[:, None]) + np.array(color_sec) * capa[:, None]
        esp = esp + donde * lam ** 20 * 0.3   # brilla: está mojada
    difusa = 0.38 + 0.62 * lam
    img[k] = (base * difusa[:, None] + esp[:, None]) * caida[:, None] + FONDO * (1 - caida)[:, None]
    # Fuera de la abertura no hay nada: el aro del espéculo lo dibuja el
    # visor (suavizado, a cualquier tamaño).
    img = (np.clip(img, 0, 1) ** (1 / 2.2)).reshape(tam, tam, 3)
    if espejo:
        img = img[:, ::-1]
    return np.ascontiguousarray((img * 255).astype(np.uint8))


def fosa_del_paciente(p, nasal, lado, estado):
    return Fosa(p, lado, estado, aspecto(nasal, lado))


def hallazgos(p, nasal, lado, estado):
    """Lo que hay en la fosa, leído del paciente con los umbrales de arriba:
    lo que el docente compara contra el informe del alumno."""
    f = fosa_del_paciente(p, nasal, lado, estado)
    d = f.dev
    if d['area'] < DESVIACION_MINIMA:
        tabique = 'centrado'
    else:
        tabique = 'espolon' if d['ancho'] < ESPOLON_ANCHO else 'desviado'
    medial = f.x_cornete() - (f.r_ci + 0.15)
    contacta = medial - d['B'] * math.exp(-0.5 * ((f.z_ci - d['z']) / d['w']) ** 2) < CONTACTO
    cornete = 'contacta' if contacta else ('hipertrofico' if f.vol_ci > CORNETE_GRANDE else 'normal')
    return {
        'tabique': tabique,
        'perforacion': f.perf is not None,
        'cornete_inferior': cornete,
        'polipos': f.polipos > 0,
        'mucosa': f.aspecto['mucosa'],
        'secrecion': f.aspecto['secrecion'],
    }
