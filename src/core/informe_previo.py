"""El informe de un examen que el paciente trae hecho: encabezado, la hoja
(el gráfico del equipo), la conclusión y la firma del tecnólogo médico.

Antes la hoja era solo el gráfico (o, en las tarjetas del docente, "Pasa" y
"Refiere" por oído): un informe real trae además qué concluyó quien lo hizo
y quién lo firmó. Lo usan scripts/libro/previos.py (las hojas del libro) y
core/ficha.py (los exámenes que marca el docente en el caso).

Las conclusiones dicen lo que muestra el gráfico, con las cuentas del
proyecto: grado BIAP (CaseProfile::GRADES del backend: normal hasta 20 dB HL,
leve 21-40, moderada 41-70, severa 71-90, profunda 91 o más) sobre 500, 1k,
2k y 4k Hz; tipo por la diferencia aéreo-óseo; el veredicto del equipo en
las emisiones; el umbral de la onda V que tiene el caso. Describen hallazgos
y no recomiendan conductas: eso es del docente.

Los firmantes son inventados (no hay personas reales detrás) y salen fijos
por paciente y examen (stable_seed), así la misma hoja trae siempre la misma
firma.
"""
import html
import re

from core.rng import stable_seed

SERVICIO = "Servicio de Otorrinolaringología · Unidad de Audiología"

# (nombre, "a" o "o" para Tecnóloga/Tecnólogo Médica/o)
TECNOLOGOS = (
    ("Carolina Fuentes Rivas", "a"), ("Matías Contreras Soto", "o"),
    ("Valentina Muñoz Araya", "a"), ("Felipe Rojas Navarro", "o"),
    ("Daniela Vergara Pizarro", "a"), ("Sebastián Morales Ibáñez", "o"),
    ("Camila Henríquez Toro", "a"), ("Ignacio Sepúlveda Lagos", "o"),
    ("Fernanda Castillo Bravo", "a"), ("Tomás Riquelme Salinas", "o"),
    ("Javiera Paredes Olivares", "a"), ("Diego Cifuentes Montt", "o"),
)

TITULO = {
    "Audiometría": "Audiometría tonal y logoaudiometría",
    "Impedanciometría": "Impedanciometría",
    "EOA": "Emisiones otoacústicas",
    "PEATC": "Potenciales evocados auditivos de tronco cerebral",
    "ECochG": "Electrococleografía",
    "VEMP": "Potenciales evocados miogénicos vestibulares",
    "Corticales": "Potenciales auditivos corticales",
}

FRECS = (125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000)
BIAP = (2, 3, 4, 6)          # 500, 1k, 2k, 4k
GAP_DB = 15                  # aéreo - óseo desde aquí: componente de conducción
LADOS = (("OD", "Oído derecho"), ("OI", "Oído izquierdo"))

# Hoja
ANCHO_MIN = 560
TINTA, TENUE, LINEA, LAVADO = "#1F2933", "#5B6670", "#C9CED6", "#F3F5F8"
FUENTE = "sans-serif"


# ── Firma ─────────────────────────────────────────────────────────────────
def firmante(ficha, examen):
    """(nombre, cargo) de quien firmó ese examen de ese paciente."""
    nombre, g = TECNOLOGOS[stable_seed("firma", ficha, examen) % len(TECNOLOGOS)]
    return nombre, f"Tecnólog{g} Médic{g} · Mención Otorrinolaringología"


# ── Conclusiones ──────────────────────────────────────────────────────────
def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _columna(tabla, i):
    """Los umbrales de un oído (i = 0 OD, 1 OI) de una tabla [[od, oi], ...]."""
    out = []
    for fila in tabla or []:
        try:
            out.append(_num(fila[i]))
        except (IndexError, TypeError):
            out.append(None)
    return out


def _promedio(valores, indices):
    v = [valores[i] for i in indices if i < len(valores) and valores[i] is not None]
    return sum(v) / len(v) if len(v) == len(indices) else None


def grado(promedio):
    if promedio <= 20:
        return "normal"
    if promedio <= 40:
        return "leve"
    if promedio <= 70:
        return "moderada"
    if promedio <= 90:
        return "severa"
    return "profunda"


def _db(v):
    return f"{v:.1f}".rstrip("0").rstrip(".").replace(".", ",")


def conclusion_audiometria(caso):
    """Una línea por oído: grado BIAP, tipo y la discriminación máxima."""
    lineas = []
    umd = caso.get("UMD") if isinstance(caso.get("UMD"), list) else []
    for i, (lado, _) in enumerate(LADOS):
        aerea = _columna(caso.get("Aerea"), i)
        osea = _columna(caso.get("Osea"), i)
        pa = _promedio(aerea, BIAP)
        if pa is None:
            continue
        po = _promedio(osea, BIAP)
        g = grado(pa)
        if g == "normal":
            agudos = [v for v in aerea[5:] if v is not None]
            texto = ("umbrales normales en el promedio tonal, con descenso en frecuencias agudas"
                     if agudos and max(agudos) > 25 else "audición dentro de rangos normales")
        else:
            gap = None if po is None else pa - po
            if gap is not None and gap >= GAP_DB:
                tipo = "de conducción" if po <= 20 else "mixta"
            else:
                tipo = "sensorioneural"
            texto = f"hipoacusia {tipo} {g}"
        texto += f" (promedio {_db(pa)} dB HL)"
        try:
            d = umd[i] or {}
            pct, nivel = _num(d.get("percentage")), _num(d.get("int"))
        except (IndexError, AttributeError):
            pct = nivel = None
        if pct is not None and nivel is not None:
            texto += f". Discriminación máxima {pct:.0f} % a {nivel:.0f} dB HL"
        lineas.append(f"{lado}: {texto[0].upper()}{texto[1:]}.")
    return lineas


TIPO_CURVA = {"A": "tipo A", "As": "tipo As", "Ad": "tipo Ad", "B": "tipo B (plana)",
              "C": "tipo C (presión negativa)"}
SIN_REFLEJO = 130
FRECS_REFLEJO = (500, 1000, 2000, 4000)


def _reflejos(caso, modo, j):
    """'presentes', 'ausentes' o 'presentes en ..., ausentes en ...' para la
    sonda j (0 OD, 1 OI), de 500 a 4000 Hz."""
    datos = (caso.get("Reflex") or {}).get(modo) or [] if isinstance(caso.get("Reflex"), dict) else []
    si, no = [], []
    for i, f in enumerate(FRECS_REFLEJO):
        try:
            v = _num(datos[i][j])
        except (IndexError, TypeError):
            v = None
        (no if v is None or v >= SIN_REFLEJO else si).append(f)
    if not si and not no:
        return None
    if not no:
        return "presentes"
    if not si:
        return "ausentes"
    hz = lambda fs: ", ".join(f"{f // 1000} kHz" if f >= 1000 else f"{f} Hz" for f in fs)
    return f"presentes en {hz(si)}, ausentes en {hz(no)}"


def conclusion_impedancia(caso, letras=None):
    """Tipo de curva y reflejos por sonda. `letras`: la curva que dibujó la
    hoja ({lado: letra}, con la sonda que se usó); si no, la del caso."""
    lineas = []
    for j, (lado, _) in enumerate(LADOS):
        otro = "OI" if lado == "OD" else "OD"
        letra = (letras or {}).get(lado) or caso.get(f"Z_{lado}")
        if letra == "NR":
            lineas.append(f"{lado}: No realizable.")
            continue
        partes = [f"Timpanograma {TIPO_CURVA.get(letra, f'tipo {letra}')}"] if letra else []
        ipsi = _reflejos(caso, "ipsi", j)
        contra = _reflejos(caso, "contra", j) if caso.get(f"Z_{otro}") != "NR" else None
        if ipsi:
            partes.append(f"reflejos ipsilaterales {ipsi}")
        if contra:
            partes.append(f"contralaterales (estímulo en {otro}) {contra}")
        if partes:
            lineas.append(f"{lado}: " + "; ".join(partes) + ".")
    return lineas


def conclusion_eoa(resultados):
    """resultados: {lado: (pasa_teoae, pasa_dpoae)}; None = no se registró."""
    lineas = []
    for lado, _ in LADOS:
        te, dp = (resultados.get(lado) or (None, None))
        if te is None and dp is None:
            continue
        if te and dp:
            texto = "emisiones transitorias y productos de distorsión presentes (pasa)"
        elif te is False and dp is False:
            texto = "emisiones transitorias y productos de distorsión ausentes (refiere)"
        else:
            partes = []
            if te is not None:
                partes.append(f"emisiones transitorias {'presentes' if te else 'ausentes'}")
            if dp is not None:
                partes.append(f"productos de distorsión {'presentes' if dp else 'ausentes'}")
            texto = "; ".join(partes)
        lineas.append(f"{lado}: {texto[0].upper()}{texto[1:]}.")
    return lineas


def _neural_alterado(neural):
    from abr.ABR_generator import NEURAL_PARAM_DEFAULTS as base
    n = dict(base, **(neural or {}))
    intervalos = any(_num(n.get(k)) is not None and _num(n[k]) > base[k] + 1e-9
                     for k in ("i_iii_ms", "iii_v_ms"))
    morfologia = (n.get("bloqueo") != "ninguno" or n.get("desincronia") != "ninguna")
    return intervalos, morfologia


def conclusion_peatc(caso, niveles, umbrales, estimulo="click"):
    """Hasta dónde se ve la onda V en los niveles que trae la hoja.
    umbrales: {lado: dB nHL o None (sin respuesta)}, como motor.abr._umbrales."""
    niveles = sorted({int(n) for n in niveles or []}, reverse=True)
    lineas = []
    for lado, _ in LADOS:
        if lado not in umbrales or not niveles:
            continue
        u = umbrales[lado]
        caso_lado = (caso.get("ABR") or {}).get(lado) or {}
        if u is None or u > niveles[0]:
            texto = f"sin respuesta identificable a {niveles[0]} dB nHL"
        else:
            hasta = min(n for n in niveles if n >= u)
            texto = f"onda V identificable hasta {hasta} dB nHL"
            if hasta == niveles[-1]:
                texto += " (menor nivel explorado)"
            intervalos, morfologia = _neural_alterado(caso_lado.get("neural"))
            if morfologia:
                texto += "; morfología alterada"
            elif intervalos:
                texto += "; intervalos interpico prolongados"
            else:
                texto += "; intervalos interpico I-III, III-V e I-V dentro de rangos normales"
        lineas.append(f"{lado}: {texto[0].upper()}{texto[1:]} ({estimulo}).")
    return lineas


def conclusion_ecochg(medidas, limite):
    """medidas: {lado: razón PS/PA o None si no hubo complejo}."""
    lineas = []
    for lado, _ in LADOS:
        if lado not in medidas:
            continue
        r = medidas[lado]
        if r is None:
            lineas.append(f"{lado}: Sin complejo PS-PA identificable.")
            continue
        juicio = "aumentada" if r > limite else "dentro de lo esperado"
        lineas.append(f"{lado}: Razón PS/PA {_db(round(r, 2))} ({juicio}; límite {_db(limite)}).")
    return lineas


def conclusion_vemp(resumen, nombre="cVEMP"):
    """resumen: Sesion.resumen del módulo VEMP (amplitudes y razón de asimetría)."""
    lineas = []
    for lado, clave in (("OD", "od"), ("OI", "oi")):
        amp = _num(resumen.get(clave))
        if amp is None:
            continue
        lineas.append(f"{lado}: {nombre} {'presente' if amp > 0 else 'ausente'}"
                      + (f" (P-N {_db(amp)} µV)." if amp > 0 else "."))
    ratio = _num(resumen.get("ratio"))
    if ratio is not None:
        lineas.append(f"Razón de asimetría {_db(ratio)} %.")
    return lineas


def conclusion_tamizaje(prueba, od, oi):
    """Las tarjetas del docente: el resultado de cada oído, dicho en una línea."""
    def bien(r):
        return r.strip().lower() in ("pasa", "normal")
    od, oi = (od or "—").strip(), (oi or "—").strip()
    if bien(od) and bien(oi) and od.lower() == oi.lower():
        return [f"{od.capitalize()} en ambos oídos."]
    return [f"OD: {od.capitalize()}.", f"OI: {oi.capitalize()}."]


# ── La hoja ───────────────────────────────────────────────────────────────
def _partir(texto, ancho_px, tam):
    """Corta un texto en líneas que entren en ancho_px (sin medir: ~0,55 tam
    por carácter, que es lo que ocupa una sans-serif)."""
    por_linea = max(20, int(ancho_px / (tam * 0.55)))
    lineas, actual = [], ""
    for palabra in texto.split():
        if actual and len(actual) + 1 + len(palabra) > por_linea:
            lineas.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}".strip()
    if actual:
        lineas.append(actual)
    return lineas


def _figura(svg):
    """(ancho, alto, <g> con el contenido): el gráfico entra como grupo
    desplazado, no como <svg> anidado, que el lector de Qt (SVG Tiny) no
    dibuja (ver _apilar en scripts/libro/previos.py)."""
    raiz = re.search(r"<svg ([^>]*)>", svg)
    at = dict(re.findall(r'([\w:-]+)="([^"]*)"', raiz.group(1)))
    w, h = float(re.sub(r"[^\d.]", "", at["width"])), float(re.sub(r"[^\d.]", "", at["height"]))
    vx, vy, vw, vh = (float(v) for v in at.get("viewBox", f"0 0 {w} {h}").replace(",", " ").split())
    cuerpo = svg[raiz.end():svg.rindex("</svg>")]
    cuerpo = re.sub(r"<metadata[^>]*>.*?</metadata>", "", cuerpo, flags=re.S)
    fuente = f' font-family="{at["font-family"]}"' if "font-family" in at else ""
    return w, h, (f'<g transform="translate({{x}},{{y}}) scale({w / vw},{h / vh}) '
                  f'translate({-vx},{-vy})"{fuente}>{cuerpo}</g>')


def _t(x, y, texto, tam=11, color=TINTA, peso=400, ancla="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{tam}" font-weight="{peso}" fill="{color}" '
            f'text-anchor="{ancla}" font-family="{FUENTE}">{html.escape(str(texto))}</text>')


def informe(figura_svg, examen, paciente, conclusion, firma, prueba=None):
    """El informe completo como SVG.

    paciente: {'nombre': ..., 'edad': ..., 'rut': ...} (lo que haya).
    conclusion: lista de líneas (una por oído, en general).
    firma: (nombre, cargo), ver firmante.
    prueba: el título si no es el del examen (las tarjetas del docente).
    """
    fw, fh, grupo = _figura(figura_svg)
    W = max(ANCHO_MIN, fw + 32)
    m = 16
    partes = []
    y = 26
    partes.append(_t(m, y, prueba or TITULO.get(examen, examen), 15, TINTA, 700))
    y += 16
    partes.append(_t(m, y, SERVICIO, 10, TENUE))
    datos = [f"Paciente: {paciente['nombre']}" if paciente.get("nombre") else None,
             f"Edad: {paciente['edad']}" if paciente.get("edad") not in (None, "") else None,
             f"RUT: {formato_rut(paciente['rut'])}" if paciente.get("rut") else None,
             f"Fecha: {paciente['fecha']}" if paciente.get("fecha") else None]
    datos = "   ·   ".join(d for d in datos if d)
    if datos:
        y += 16
        partes.append(_t(m, y, datos, 10.5, TINTA))
    y += 10
    partes.append(f'<line x1="{m}" y1="{y}" x2="{W - m}" y2="{y}" stroke="{LINEA}" stroke-width="1"/>')
    y += 12
    partes.append(grupo.replace("{x}", f"{(W - fw) / 2:.1f}").replace("{y}", f"{y:.1f}"))
    y += fh + 14
    # Conclusión
    lineas = []
    for c in conclusion or ["Sin conclusión registrada."]:
        lineas += _partir(c, W - 2 * m - 24, 11)
    alto_caja = 30 + 15 * len(lineas)
    partes.append(f'<rect x="{m}" y="{y}" width="{W - 2 * m}" height="{alto_caja}" rx="6" fill="{LAVADO}"/>')
    partes.append(_t(m + 12, y + 19, "Conclusión", 11, TINTA, 700))
    for i, linea in enumerate(lineas):
        partes.append(_t(m + 12, y + 37 + 15 * i, linea, 11, TINTA))
    y += alto_caja + 34
    # Firma
    nombre, cargo = firma
    cx = W - m - 110
    partes.append(f'<path d="M{cx - 70:.1f},{y - 6:.1f} c18,-14 30,8 46,-4 s22,-10 34,2 s26,6 40,-6 '
                  f's18,4 28,0" fill="none" stroke="#33415C" stroke-width="1.3"/>')
    partes.append(f'<line x1="{cx - 100}" y1="{y + 2}" x2="{cx + 100}" y2="{y + 2}" stroke="{TENUE}" stroke-width="0.8"/>')
    partes.append(_t(cx, y + 17, f"TM {nombre}", 10.5, TINTA, 600, "middle"))
    partes.append(_t(cx, y + 31, cargo, 9, TENUE, 400, "middle"))
    alto = y + 44
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{alto:.0f}" '
            f'viewBox="0 0 {W:.0f} {alto:.0f}"><rect width="100%" height="100%" fill="#ffffff"/>'
            + "".join(partes) + "</svg>")


def formato_rut(rut):
    """12345678 -> 12.345.678-5 (con el dígito verificador, módulo 11). Uno
    que ya trae puntos o guion queda como viene."""
    rut = str(rut).strip()
    if not rut.isdigit():
        return rut
    suma, factor = 0, 2
    for d in reversed(rut):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    dv = 11 - suma % 11
    dv = "0" if dv == 11 else "K" if dv == 10 else str(dv)
    return f"{int(rut):,}".replace(",", ".") + f"-{dv}"


def paciente_del_caso(caso):
    """Nombre, edad y RUT del caso (paciente_snapshot), lo que haya."""
    snap = caso.get("paciente_snapshot") if isinstance(caso, dict) else None
    snap = snap if isinstance(snap, dict) else {}
    nombre = " ".join(p for p in (snap.get("nombre"), snap.get("apellido")) if p).strip()
    edad = _num(caso.get("edad")) if isinstance(caso, dict) else None
    if edad is None:
        texto_edad = None
    elif edad < 1:
        meses = int(round(edad * 12))
        texto_edad = f"{meses} mes{'es' if meses != 1 else ''}" if meses else "recién nacido"
    else:
        texto_edad = f"{int(edad)} años"
    rut = str(snap.get("rut") or "").strip()
    return {"nombre": nombre or None, "edad": texto_edad, "rut": rut or None}
