"""La hoja de un examen que el paciente trae hecho, dibujada con los datos
del caso: la audiometría con su audiograma (y la logoaudiometría, las
supraliminares y el Fowler en escalera) y la impedanciometría con sus
timpanogramas y la tabla de reflejos.

Antes, un examen marcado por el docente (cases.data["examenes_previos"])
llegaba como una tarjeta con "Normal / Alterado" por oído: una audiometría
sin audiograma no es una audiometría. Los exámenes que no son audiometría ni
impedanciometría (tamizajes) siguen siendo tarjeta (ficha.tarjeta_previo).

Las reglas de dibujo son las de la ficha del backend (CaseCharts.php):
símbolos ASHA, enmascaramiento inferido igual, ósea solo donde el aéreo de
ese oído está alterado (en un examen real no se mide ósea con aéreo
normal), y el Fowler a los lados de la frecuencia: el sano de 20 en 20 desde
su umbral hasta 120 dB o antes de su LDL, el afectado de 5 en 5 hasta
igualar, con el mismo motor que contesta en la cabina (audiometria.Fowler).

SVG simple, sin <svg> anidados ni CSS: lo dibuja QSvgRenderer (SVG Tiny).
"""
import html
import math

from core import tema

FRECS = (125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000)
FRECS_OSEA = (250, 500, 1000, 2000, 3000, 4000)
ATENUACION_AEREA = (35, 40, 40, 40, 40, 45, 45, 50, 50)   # CaseCharts::ATENUACION_AEREA_POR_FREQ
GAP_ENMASCARA_OSEA = 10
TOPE_OSEA_DB = 70
SIN_UMBRAL_DB = 130
NIVEL_MAXIMO_DB = 120
NORMAL_DB = 20
SALIDA_MAX_DB = 120

TINTA, TENUE, GRILLA, LAVADO = "#1F2933", "#5B6670", "#D5DAE0", "#F3F5F8"
FUENTE = "sans-serif"


def _od():
    return tema.color_lado("OD")


def _oi():
    return tema.color_lado("OI")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _col(tabla, j):
    """Columna j (0 OD, 1 OI) de una lista de pares por frecuencia."""
    out = []
    for fila in tabla or []:
        try:
            out.append(_num(fila[j]))
        except (IndexError, TypeError):
            out.append(None)
    return out


def _t(x, y, texto, tam=10, color=TINTA, peso=400, ancla="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{tam}" font-weight="{peso}" fill="{color}" '
            f'text-anchor="{ancla}" font-family="{FUENTE}">{html.escape(str(texto))}</text>')


def _l(x1, y1, x2, y2, color, ancho=1.0, guiones=None):
    d = f' stroke-dasharray="{guiones}"' if guiones else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
            f'stroke-width="{ancho}"{d}/>')


def _poli(pts, color, ancho=1.4, guiones=None):
    d = f' stroke-dasharray="{guiones}"' if guiones else ""
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{ancho}"{d}/>'


# ── Símbolos ASHA ─────────────────────────────────────────────────────────
def _circulo(x, y, c, fondo="none"):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{fondo}" stroke="{c}" stroke-width="1.5"/>'


def _cruz(x, y, c):
    r = 4.2
    return _l(x - r, y - r, x + r, y + r, c, 1.6) + _l(x - r, y + r, x + r, y - r, c, 1.6)


def _triangulo(x, y, c):
    return (f'<polygon points="{x:.1f},{y - 5:.1f} {x - 5:.1f},{y + 4:.1f} {x + 5:.1f},{y + 4:.1f}" '
            f'fill="none" stroke="{c}" stroke-width="1.5"/>')


def _cuadrado(x, y, c):
    return f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" fill="none" stroke="{c}" stroke-width="1.5"/>'


def _osea(x, y, c, lado, enmascarada):
    """"<" / ">" sin enmascarar, "[" / "]" enmascarada; OD a la izquierda."""
    s = -1 if lado == "OD" else 1
    if enmascarada:
        return _poli([(x + s * 4, y - 5), (x, y - 5), (x, y + 5), (x + s * 4, y + 5)], c, 1.5)
    return _poli([(x + s * 4, y - 5), (x, y), (x + s * 4, y + 5)], c, 1.5)


def _flecha(x, y, c, lado):
    s = -1 if lado == "OD" else 1
    return _l(x + s * 3, y + 4, x + s * 8, y + 10, c, 1.2)


def _ldl(x, y, c):
    # Triángulo vacío apuntando abajo (tradición chilena).
    return (f'<polygon points="{x - 4.5:.1f},{y - 4:.1f} {x + 4.5:.1f},{y - 4:.1f} {x:.1f},{y + 4:.1f}" '
            f'fill="none" stroke="{c}" stroke-width="1.3"/>')


# ── Fowler ────────────────────────────────────────────────────────────────
def escalera_fowler(th_od, th_oi, patron, ldl_od=130, ldl_oi=130):
    """Pares [OD, OI] de igual sonoridad (CaseBuilder::fowlerEscalera)."""
    from audiometria.Fowler import FOWLER_PATTERNS, Fowler
    f = Fowler()
    f.set_th(int(th_od), int(th_oi))
    f.set_cut(*FOWLER_PATTERNS.get(patron, FOWLER_PATTERNS["none"]))
    ref_od = th_od < th_oi
    th_ref, th_est = (th_od, th_oi) if ref_od else (th_oi, th_od)
    techo_ref = min(SALIDA_MAX_DB, (ldl_od if ref_od else ldl_oi) - 5)
    techo_est = min(SALIDA_MAX_DB, (ldl_oi if ref_od else ldl_od) - 5)
    pares, est, ref = [], int(th_est), int(th_ref)
    while ref <= techo_ref:
        igualo = False
        while est <= techo_est:
            if f.evaluate(*((ref, est) if ref_od else (est, ref)))[0]:
                igualo = True
                break
            est += 5
        if not igualo:
            break
        pares.append([ref, est] if ref_od else [est, ref])
        ref += 20
    return pares


def escaleras_del_caso(caso):
    """{índice de frecuencia: pares} de las frecuencias con Fowler."""
    patrones = ((caso.get("Fowler") or {}).get("patterns") or {}) if isinstance(caso.get("Fowler"), dict) else {}
    aerea = [_col(caso.get("Aerea"), j) for j in (0, 1)]
    ldl = [_col(caso.get("LDL"), j) for j in (0, 1)]
    out = {}
    for k, patron in patrones.items():
        try:
            i = int(k)
            a_od, a_oi = aerea[0][i], aerea[1][i]
        except (ValueError, IndexError):
            continue
        if a_od is None or a_oi is None:
            continue
        out[i] = escalera_fowler(a_od, a_oi, str(patron),
                                 int(ldl[0][i] or 130) if i < len(ldl[0]) else 130,
                                 int(ldl[1][i] or 130) if i < len(ldl[1]) else 130)
    return out


# ── Audiometría ───────────────────────────────────────────────────────────
def audiograma(caso, x0=0.0, y0=0.0, ancho=520.0, alto=330.0):
    """(partes SVG, alto usado) del audiograma del caso."""
    od_c, oi_c = _od(), _oi()
    px, py = x0 + 38, y0 + 22
    pw, ph = ancho - 50, alto - 40
    lmin, lmax = math.log2(125), math.log2(8000)
    aire = pw * 0.05

    def fx(hz):
        return px + aire + (math.log2(hz) - lmin) / (lmax - lmin) * (pw - 2 * aire)

    def fy(db):
        return py + (max(-10.0, min(120.0, db)) + 10) / 130 * ph

    p = []
    for hz in FRECS:
        x = fx(hz)
        p.append(_l(x, py, x, py + ph, GRILLA, 0.6))
        etiqueta = f"{hz // 1000}k" if hz >= 1000 else str(hz)
        p.append(_t(x, py - 6, etiqueta, 8.5, TENUE, 400, "middle"))
    for db in range(-10, 121, 10):
        y = fy(db)
        marcada = db in (0, NORMAL_DB)
        p.append(_l(px, y, px + pw, y, "#8A949E" if marcada else GRILLA, 1.2 if marcada else 0.6))
        if db % 20 == 0:
            p.append(_t(px - 5, y + 3, db, 8.5, TENUE, 400, "end"))
    p.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="none" '
             f'stroke="#8A949E" stroke-width="1"/>')
    p.append(_t(px - 30, py + ph + 14, "dB HL", 8, TENUE))
    p.append(_t(px + pw, py + ph + 14, "Hz", 8, TENUE, 400, "end"))

    aerea = [_col(caso.get("Aerea"), 0), _col(caso.get("Aerea"), 1)]
    osea = [_col(caso.get("Osea"), 0), _col(caso.get("Osea"), 1)]
    ldl = [_col(caso.get("LDL"), 0), _col(caso.get("LDL"), 1)]
    colores = (od_c, oi_c)
    lados = ("OD", "OI")

    # Líneas
    for j in (0, 1):
        tramo = []
        for i, hz in enumerate(FRECS):
            v = aerea[j][i] if i < len(aerea[j]) else None
            if v is None or v >= SIN_UMBRAL_DB:
                if len(tramo) > 1:
                    p.append(_poli(tramo, colores[j], 1.4))
                tramo = []
                continue
            tramo.append((fx(hz), fy(v)))
        if len(tramo) > 1:
            p.append(_poli(tramo, colores[j], 1.4))

    # Símbolos aéreos y óseos
    for i, hz in enumerate(FRECS):
        x = fx(hz)
        for j in (0, 1):
            a = aerea[j][i] if i < len(aerea[j]) else None
            if a is None:
                continue
            o_otro = osea[1 - j][i] if i < len(osea[1 - j]) else None
            masc = o_otro is not None and (a - o_otro) >= ATENUACION_AEREA[i]
            sin = a >= SIN_UMBRAL_DB
            y = fy(NIVEL_MAXIMO_DB if sin else a)
            if j == 0:
                p.append(_triangulo(x, y, colores[j]) if masc else _circulo(x, y, colores[j]))
            else:
                p.append(_cuadrado(x, y, colores[j]) if masc else _cruz(x, y, colores[j]))
            if sin:
                p.append(_flecha(x, y, colores[j], lados[j]))
            # Ósea: solo donde se mide y donde el aéreo de ese oído no es normal.
            o = osea[j][i] if i < len(osea[j]) else None
            if hz in FRECS_OSEA and o is not None and a > NORMAL_DB:
                mejor = min(v for v in (o, o_otro) if v is not None)
                masc_o = (a - mejor) >= GAP_ENMASCARA_OSEA
                tope = o > TOPE_OSEA_DB
                xo = x + (-7 if j == 0 else 7)
                yo = fy(TOPE_OSEA_DB if tope else o)
                p.append(_osea(xo, yo, colores[j], lados[j], masc_o))
                if tope:
                    p.append(_flecha(xo, yo, colores[j], lados[j]))

    # LDL, si se midió
    for j in (0, 1):
        valores = [v for v in ldl[j] if v is not None]
        if not valores or all(v >= SIN_UMBRAL_DB for v in valores):
            continue
        tramo = []
        for i, hz in enumerate(FRECS):
            if hz not in FRECS_OSEA or i >= len(ldl[j]) or ldl[j][i] is None:
                continue
            v = ldl[j][i]
            y = fy(NIVEL_MAXIMO_DB if v >= SIN_UMBRAL_DB else v)
            x = fx(hz) + (-3 if j == 0 else 3)
            p.append(_ldl(x, y, colores[j]))
            if v < SIN_UMBRAL_DB:
                tramo.append((x, y))
        if len(tramo) > 1:
            p.append(_poli(tramo, colores[j], 1.0, "4,3"))

    # Fowler en escalera
    for i, pares in escaleras_del_caso(caso).items():
        x = fx(FRECS[i])
        for n_od, n_oi in pares:
            y_od, y_oi = fy(n_od), fy(n_oi)
            p.append(_l(x - 13, y_od, x + 13, y_oi, "#555555", 0.9))
            p.append(_circulo(x - 13, y_od, od_c, "#ffffff"))
            p.append(_cruz(x + 13, y_oi, oi_c))
    return p, alto


def _celda_tabla(x, y, filas, anchos, alto_fila=16):
    """Tabla simple: primera fila encabezado. Devuelve (partes, y final)."""
    p = []
    total = sum(anchos)
    for n, fila in enumerate(filas):
        if n == 0:
            p.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{total:.1f}" height="{alto_fila}" fill="{LAVADO}"/>')
        cx = x
        for k, celda in enumerate(fila):
            texto, color = celda if isinstance(celda, tuple) else (celda, TINTA)
            p.append(_t(cx + 5, y + alto_fila - 4.5, texto, 9, color, 700 if n == 0 or k == 0 else 400))
            cx += anchos[k]
        y += alto_fila
        p.append(_l(x, y, x + total, y, GRILLA, 0.6))
    return p, y


def _db(v):
    return "—" if v is None else f"{v:.0f} dB"


def hoja_audiometria(caso):
    """SVG de la audiometría: audiograma + logoaudiometría y supraliminares."""
    W = 540
    partes, alto = audiograma(caso, 10, 6, 520, 330)
    y = 6 + alto + 12
    od_c, oi_c = _od(), _oi()
    srt = caso.get("SRT") or [None, None]
    sdt = caso.get("SDT") or [None, None]
    umd = caso.get("UMD") or [{}, {}]
    sisi = caso.get("SISI") or [None, None]

    def umd_txt(j):
        try:
            d = umd[j] or {}
            return f"{_num(d.get('percentage')):.0f} % a {_num(d.get('int')):.0f} dB"
        except (TypeError, ValueError, IndexError, AttributeError):
            return "—"

    def lado(j, k):
        try:
            return _num(k[j])
        except (IndexError, TypeError):
            return None

    filas = [("", ("OD", od_c), ("OI", oi_c)),
             ("SDT", _db(lado(0, sdt)), _db(lado(1, sdt))),
             ("SRT", _db(lado(0, srt)), _db(lado(1, srt))),
             ("Discriminación máxima", umd_txt(0), umd_txt(1)),
             ("SISI", f"{lado(0, sisi) or 0:.0f} %", f"{lado(1, sisi) or 0:.0f} %")]
    t, y = _celda_tabla(20, y, filas, (190, 160, 160))
    partes += t
    weber = caso.get("Weber") or {}
    if isinstance(weber, dict) and weber:
        txt = []
        for f, v in weber.items():
            dice = {"od": "lateraliza a OD", "oi": "lateraliza a OI"}.get(str(v).lower(), "indiferente")
            txt.append(f"{f} Hz {dice}")
        y += 16
        partes.append(_t(20, y, "Weber: " + " · ".join(txt), 9, TINTA))
    if escaleras_del_caso(caso):
        y += 14
        partes.append(_t(20, y, "Fowler graficado en el audiograma (pares unidos = igual sonoridad).", 8.5, TENUE))
    alto_total = y + 10
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{alto_total:.0f}" '
            f'viewBox="0 0 {W} {alto_total:.0f}" font-family="{FUENTE}">'
            f'<rect width="{W}" height="{alto_total:.0f}" fill="#ffffff"/>' + "".join(partes) + "</svg>")


def conclusion_audiometria(caso):
    """La de informe_previo más lo que la hoja muestra y esa no dice:
    rollover, Weber y Fowler."""
    from core import informe_previo as IP
    lineas = IP.conclusion_audiometria(caso)
    escaleras = escaleras_del_caso(caso)
    patrones = (caso.get("Fowler") or {}).get("patterns") or {}
    if escaleras:
        nombres = {"none": "sin reclutamiento", "partial": "reclutamiento parcial",
                   "complete": "reclutamiento completo", "over": "sobre-reclutamiento"}
        por = {}
        for k, pat in patrones.items():
            try:
                hz = FRECS[int(k)]
            except (ValueError, IndexError):
                continue
            por.setdefault(nombres.get(pat, pat), []).append(f"{hz // 1000} kHz" if hz >= 1000 else f"{hz} Hz")
        a = [_col(caso.get("Aerea"), j) for j in (0, 1)]
        i0 = int(next(iter(patrones)))
        peor = "OD" if (a[0][i0] or 0) > (a[1][i0] or 0) else "OI"
        lineas.append("Fowler (" + peor + "): " + "; ".join(f"{v} en {', '.join(fs)}" for v, fs in por.items()) + ".")
    weber = caso.get("Weber") or {}
    if isinstance(weber, dict) and weber:
        lados = {str(v).lower() for v in weber.values()}
        if lados <= {"od"}:
            lineas.append("Weber lateraliza a OD.")
        elif lados <= {"oi"}:
            lineas.append("Weber lateraliza a OI.")
    return lineas


# ── Impedanciometría ──────────────────────────────────────────────────────
FORMAS = {"A": (0.3, 1.6, -100, 20), "As": (0.1, 0.3, -100, 20), "Ad": (1.8, 3.0, -100, 20),
          "C": (0.3, 1.6, -250, -110), "Cs": (0.1, 0.3, -250, -110), "B": (0.0, 0.003, -100, 20)}
ANCHOS_TW = {"A": 80.0, "As": 80.0, "Ad": 60.0, "C": 100.0, "Cs": 160.0, "B": 400.0}


def _timpanograma(x0, y0, w, h, letra, color, titulo):
    p = [_t(x0 + w / 2, y0, titulo, 10, color, 700, "middle")]
    px, py, pw, ph = x0 + 28, y0 + 10, w - 36, h - 34
    pmin, pmax, cmax = -400.0, 200.0, 3.0

    def fx(pr):
        return px + (pr - pmin) / (pmax - pmin) * pw

    def fy(c):
        return py + ph - min(c, cmax) / cmax * ph

    for pr in range(-400, 201, 100):
        p.append(_l(fx(pr), py, fx(pr), py + ph, GRILLA, 0.6))
        p.append(_t(fx(pr), py + ph + 11, pr, 7.5, TENUE, 400, "middle"))
    for c in (0, 1, 2, 3):
        p.append(_l(px, fy(c), px + pw, fy(c), GRILLA, 0.6))
        p.append(_t(px - 4, fy(c) + 3, c, 7.5, TENUE, 400, "end"))
    p.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="none" stroke="#8A949E" stroke-width="1"/>')
    p.append(_t(px + pw / 2, py + ph + 22, "daPa", 7.5, TENUE, 400, "middle"))
    p.append(_t(px - 24, py - 2, "ml", 7.5, TENUE))
    if letra == "NR":
        p.append(_t(px + pw / 2, py + ph / 2, "No realizable", 10, TENUE, 700, "middle"))
        return p
    c_min, c_max, p_min, p_max = FORMAS.get(letra, FORMAS["A"])
    altura, pico = (c_min + c_max) / 2, (p_min + p_max) / 2
    ancho = ANCHOS_TW.get(letra, 80.0) / (2 * math.log(2))
    pts = [(fx(pr), fy(altura * math.exp(-abs(pr - pico) / ancho))) for pr in range(-400, 201, 5)]
    p.append(_poli(pts, color, 1.6))
    p.append(_t(px + pw - 4, py + 12, f"Tipo {letra}", 9, color, 700, "end"))
    return p


def hoja_impedancia(caso):
    """SVG de la impedanciometría: un timpanograma por oído y los reflejos."""
    W = 540
    od_c, oi_c = _od(), _oi()
    p = []
    p += _timpanograma(10, 14, 260, 170, caso.get("Z_OD") or "A", od_c, "Oído derecho")
    p += _timpanograma(275, 14, 260, 170, caso.get("Z_OI") or "A", oi_c, "Oído izquierdo")
    y = 200
    reflex = caso.get("Reflex") if isinstance(caso.get("Reflex"), dict) else {}
    frecs = ("500", "1k", "2k", "4k")

    def fila(modo, j, etiqueta, color):
        datos = (reflex.get(modo) or [])
        celdas = [(etiqueta, color)]
        for i in range(4):
            try:
                v = _num(datos[i][j])
            except (IndexError, TypeError):
                v = None
            celdas.append("Ausente" if v is None or v >= SIN_UMBRAL_DB else f"{v:.0f} dB")
        return tuple(celdas)

    decay = reflex.get("decay") or {}
    filas = [("Reflejo estapedial", *frecs),
             fila("ipsi", 0, "Ipsi OD (sonda OD)", od_c),
             fila("ipsi", 1, "Ipsi OI (sonda OI)", oi_c),
             fila("contra", 1, "Contra, estímulo OD", od_c),
             fila("contra", 0, "Contra, estímulo OI", oi_c)]
    t, y = _celda_tabla(20, y, filas, (170, 85, 85, 85, 85))
    p += t
    # Decay solo donde hubo reflejo que sostener (ipsi de ese oído presente).
    medibles = []
    for j, k in enumerate(("od", "oi")):
        presentes = [c for c in fila("ipsi", j, "", TINTA)[1:] if c != "Ausente"]
        if presentes and isinstance(decay, dict) and k in decay:
            medibles.append(f"{k.upper()} {'positivo' if decay.get(k) else 'negativo'}")
    if medibles:
        y += 16
        p.append(_t(20, y, "Decay del reflejo: " + " · ".join(medibles), 9, TINTA))
    alto = y + 12
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{alto:.0f}" '
            f'viewBox="0 0 {W} {alto:.0f}" font-family="{FUENTE}">'
            f'<rect width="{W}" height="{alto:.0f}" fill="#ffffff"/>' + "".join(p) + "</svg>")
