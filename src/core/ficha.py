# -*- coding: utf-8 -*-
"""Ficha clínica del paciente: render HTML compartido entre la agenda
(agenda.Agenda._ver_ficha_paciente) y el historial propio del alumno
(core.mis_pacientes) -- ambos parten de la misma fila de agenda + caso, solo
cambia de dónde sacan `shedule` (en memoria vs. recién pedido al backend)."""

import dataclasses
import html
import json
import re
from pathlib import Path

from PySide6.QtCore import QDate, QTime, QDateTime, QRectF, Qt, QUrl
from PySide6.QtGui import QPainter, QPixmap, QTextDocument
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

from core import iconos, tema

from core.helpers import obtener_hora_real_atencion

# Llaves {{N}} dentro de historia_clinica (N = offset en días respecto a la
# fecha de la cita, puede ser negativo). Ej.: "{{-5}} atendido por ORL" se
# resuelve a la fecha real 5 días antes de la cita agendada.
HISTORIA_CLINICA_FECHA_RE = re.compile(r"\{\{([+-]?\d+)\}\}")


def parse_fecha_agenda(texto):
    """Parsea una fecha en formato "dd-MM-yy" (año de 2 dígitos, como se
    guarda en la agenda). QDate::fromString con formato "yy" interpreta
    00-99 como 1900-1999, así que corregimos al siglo 2000 manualmente."""
    fecha = QDate.fromString(texto, "dd-MM-yy") if texto else QDate()
    if fecha.isValid() and fecha.year() < 2000:
        fecha = fecha.addYears(100)
    return fecha


def resolver_fechas_historia_clinica(texto, fecha_cita_str):
    """Reemplaza cada {{N}} en texto por la fecha N días respecto a
    fecha_cita_str (formato "dd-MM-yy", mismo que row.fecha). Si la fecha de
    la cita no es válida, deja la llave tal cual (mejor eso que una fecha
    inventada)."""
    if not texto:
        return texto
    fecha_cita = parse_fecha_agenda(fecha_cita_str)

    def _reemplazar(match):
        if not fecha_cita.isValid():
            return match.group(0)
        return fecha_cita.addDays(int(match.group(1))).toString("dd-MM-yyyy")

    return HISTORIA_CLINICA_FECHA_RE.sub(_reemplazar, texto)


def historial_atenciones(shedule, rut, username, is_admin, practica=False):
    """
    Recopila, para todas las citas (filas de agenda) del mismo paciente (mismo rut),
    las atenciones cerradas por cada alumno, ordenadas cronológicamente.
    Devuelve lista de tuplas (fecha, hora_real, alumno, nota).

    Alumno (is_admin=False): solo ve sus propias notas -- mismo criterio que
    admin/student.php le da al docente sobre cada alumno individual, pero acá
    aplicado a "cada alumno sobre sí mismo".

    `practica`: la ficha es de un intento de práctica deliberada. Los
    intentos y los prácticos no se mezclan: cada lado ve solo su historial.
    """
    historial = []
    for otra_row in shedule.get("agenda_1", {}).values():
        if otra_row.rut != rut:
            continue
        if (getattr(otra_row, "practice_id", None) is not None) != practica:
            continue
        atencion = otra_row.atencion
        fecha = otra_row.fecha
        for alumno, datos in atencion.items():
            if not isinstance(datos, dict) or datos.get("estado") != "atendido":
                continue
            if not is_admin and alumno != username:
                continue
            nota = datos.get("nota", "")
            hora_real = datos.get("hora_real", "")
            historial.append((fecha, hora_real, alumno, nota))

    def _orden(item):
        fecha, hora_real = item[0], item[1]
        dt = QDateTime(
            parse_fecha_agenda(fecha),
            QTime.fromString(hora_real, "HH:mm:ss") if hora_real else QTime(),
        )
        return dt

    historial.sort(key=_orden)
    return historial


# Fecha ya resuelta al principio de una línea de la historia clínica.
HISTORIA_LINEA_RE = re.compile(r"^(\d{2}-\d{2}-\d{4})\s*(.*)$", re.S)

# Claves de orden para lo que no trae fecha legible: una línea de la historia
# clínica va al principio (el docente la escribió antes de todo lo demás) y
# una atención sin fecha es la de ahora, así que va al final.
_ORDEN_PRIMERO = QDateTime(QDate(1, 1, 1), QTime(0, 0))
_ORDEN_ULTIMO = QDateTime(QDate(9999, 12, 31), QTime(23, 59))


# Exámenes de los pacientes del libro, con la hoja del libro de cada uno
# (scripts/libro/previos.py). Van con la app y no con el backend para que el
# kiosko los vea igual que todo lo demás de la ficha. indice.json dice qué
# hojas tiene cada ficha: "trae" (los que el paciente llega con hechos, si su
# procedimiento no los nombra) e "historia" (la hoja de un examen que cuenta
# una línea de su historia clínica, por los días de esa línea).
PREVIOS_DIR = Path("resources/libro/previos")
# Días antes de la cita en que se hizo lo que trae: lo bastante cerca para que
# lo deriven con eso, y antes que la cita a la que viene. Si la historia trae
# algo más reciente (el otorrino que lo pide), va después de eso: hacerlo
# antes de que lo pidan no tiene sentido. Mismo cálculo en
# LlmConfig::diasAudiometriaPrevia.
PREVIA_DIAS = 14
# Cómo aparece cada examen en el procedimiento, para saber si el paciente
# viene a hacérselo; en este orden se nombran en la ficha.
EN_PROCEDIMIENTO = {"Audiometría": "audiometr", "Impedanciometría": "impedanciometr", "EOA": "eoa",
                    "AABR": "aabr", "PEATC": "peatc", "ECochG": "ecochg", "VEMP": "vemp",
                    "Corticales": "cortical"}
_indice = None


def indice_previos():
    """indice.json, leído una vez. Vacío si no está (un build sin libro)."""
    global _indice
    if _indice is None:
        try:
            _indice = json.loads((PREVIOS_DIR / "indice.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _indice = {}
    return _indice


def dias_audiometria_previa(historia_clinica):
    """Días respecto de la cita (negativo) en que se hizo lo que trae."""
    pasados = [int(n) for n in HISTORIA_CLINICA_FECHA_RE.findall(historia_clinica or "") if int(n) < 0]
    ultima = max(pasados, default=-PREVIA_DIAS - 1)
    return min(max(-PREVIA_DIAS, ultima + 1), -1)


def _ficha_de(row, caso):
    case_id = getattr(row, "case_id", None) or (caso.get("id") if isinstance(caso, dict) else None)
    return str(case_id) if case_id else None


def examenes_que_trae(row, caso):
    """[(examen, ruta)] de lo que el paciente llega con hecho, en orden.

    Solo en la práctica libre, y solo lo que su procedimiento no nombra: el
    procedimiento dice lo que enseña el capítulo (FOCO en sql_practica.py) y
    el resto de los exámenes que el libro muestra de ese paciente ya los trae.
    Si el alumno los repite, quedan como una atención más en su historial. En
    una cita del docente no sale nada: qué trae el paciente lo decide él.

    Si viene a otoscopía no trae nada: todo lo demás va después de mirarle
    el oído.
    """
    if getattr(row, "practice_id", None) is None:
        return []
    procedimiento = (getattr(row, "procedimiento", "") or "").lower()
    if "otoscop" in procedimiento:
        return []
    hojas = indice_previos().get(_ficha_de(row, caso) or "", {})
    trae = hojas.get("trae", {})
    # Lo que muestra la ficha del libro en el capítulo de esa carpeta (el
    # procedimiento la distingue); sin ella (un intento de antes del cambio),
    # todo lo que hay del paciente.
    candidatos = hojas.get("por_procedimiento", {}).get(getattr(row, "procedimiento", "") or "")
    if candidatos is not None:
        trae = {e: trae[e] for e in candidatos if e in trae}
    # Lo que ya cuenta su historia (el PEAT que le hicieron hace tres meses)
    # tiene su hoja en esa línea: no se repite como algo que trae.
    en_la_historia = {h["examen"] for h in hojas.get("historia", [])}
    return [(examen, PREVIOS_DIR / trae[examen]) for examen, clave in EN_PROCEDIMIENTO.items()
            if examen in trae and examen not in en_la_historia and clave not in procedimiento
            and (PREVIOS_DIR / trae[examen]).is_file()]


def audiometria_previa(row, caso):
    """La audiometría que trae el paciente (ruta del SVG), o None."""
    return dict(examenes_que_trae(row, caso)).get("Audiometría")


def _nombre(examen):
    """Como se escribe dentro de una frase: "audiometría", pero "EOA"."""
    return examen.lower() if examen.istitle() and examen[1:].islower() else examen


def _y(nombres):
    """"a, b y c" ("e" antes de "i": "audiometría e impedanciometría")."""
    if len(nombres) == 1:
        return nombres[0]
    union = " e " if nombres[-1].lower().startswith(("i", "hi")) else " y "
    return ", ".join(nombres[:-1]) + union + nombres[-1]


def _enlace_a(examen, ruta):
    return (f"Ver {_nombre(examen)}", f"previo:{ruta.relative_to(PREVIOS_DIR).as_posix()}")


def entrada_lo_que_trae(row, caso, historia_clinica):
    """(días, texto, enlaces) de la entrada "Audiometría e impedanciometría.
    Trae los informes.", o None si no trae nada."""
    trae = examenes_que_trae(row, caso)
    if not trae:
        return None
    nombres = _y([_nombre(e) for e, _ in trae])
    texto = (nombres[0].upper() + nombres[1:] + ". "
             + ("Trae el informe." if len(trae) == 1 else "Trae los informes."))
    return dias_audiometria_previa(historia_clinica), texto, [_enlace_a(e, r) for e, r in trae]


def enlaces_de_la_historia(row, caso):
    """{días: [(texto, href)]}: las líneas de la historia que cuentan un
    examen hecho llevan su hoja (ver indice.json, "historia")."""
    enlaces = {}
    for h in indice_previos().get(_ficha_de(row, caso) or "", {}).get("historia", []):
        ruta = PREVIOS_DIR / h["svg"]
        if ruta.is_file():
            enlaces.setdefault(int(h["dias"]), []).append(_enlace_a(h["examen"], ruta))
    return enlaces


def fila_de_practica(row, item):
    """La fila del caso como la ve el alumno en la práctica libre.

    El docente abre un paciente de práctica con la fila del caso (sin
    intento): sin esto su ficha y su chat de prueba llevaban el
    procedimiento de la ficha del caso y no el de la carpeta, y no salía la
    audiometría que el alumno sí ve. `item`: el paciente de la carpeta
    (api/practica.php, con id y procedimiento).
    """
    return dataclasses.replace(row, procedimiento=item.get("procedimiento") or row.procedimiento,
                               practice_id=int(item["id"]))


def linea_tiempo(historia_clinica, fecha_cita, historial, previos=(), enlaces_historia=None):
    """Atenciones previas del caso + atenciones cerradas, en un solo orden.

    Devuelve dicts {fecha, hora, alumno, texto, enlaces}: `alumno` vacío en
    las entradas que vienen de la historia clínica del caso, que no son de
    nadie en particular. `previos`: (días respecto a la cita, texto, enlaces)
    de los exámenes que el paciente trae hechos. `enlaces_historia`: {días:
    enlaces} para las líneas de la historia que cuentan un examen. Cada
    enlace es (texto, href) y abre el informe desde la ficha.
    """
    entradas = []
    fecha_cita_q = parse_fecha_agenda(fecha_cita)
    enlaces_historia = enlaces_historia or {}

    for cruda in (historia_clinica or "").splitlines():
        dias = re.match(r"\s*\{\{([+-]?\d+)\}\}", cruda)
        linea = resolver_fechas_historia_clinica(cruda, fecha_cita).strip()
        if not linea:
            continue
        match = HISTORIA_LINEA_RE.match(linea)
        fecha = match.group(1) if match else ""
        texto = match.group(2).strip() if match else linea
        orden = QDateTime(QDate.fromString(fecha, "dd-MM-yyyy"), QTime(0, 0)) if fecha else None
        entradas.append((orden if orden and orden.isValid() else _ORDEN_PRIMERO,
                         {"fecha": fecha, "hora": "", "alumno": "", "texto": texto,
                          "enlaces": enlaces_historia.get(int(dias.group(1)), []) if dias else []}))

    for dias, texto, enlaces in previos:
        fecha_q = fecha_cita_q.addDays(dias) if fecha_cita_q.isValid() else QDate()
        entradas.append((QDateTime(fecha_q, QTime(0, 0)) if fecha_q.isValid() else _ORDEN_PRIMERO,
                         {"fecha": fecha_q.toString("dd-MM-yyyy") if fecha_q.isValid() else "",
                          "hora": "", "alumno": "", "texto": texto, "enlaces": enlaces}))

    for fecha, hora_real, alumno, nota in historial:
        fecha_q = parse_fecha_agenda(fecha)
        orden = QDateTime(
            fecha_q,
            QTime.fromString(hora_real, "HH:mm:ss") if hora_real else QTime(0, 0),
        )
        # La agenda guarda "dd-MM-yy" y la historia clínica queda en
        # "dd-MM-yyyy": mezclados en una misma lista se leen como si fueran
        # formatos distintos de fechas distintas.
        fecha_txt = fecha_q.toString("dd-MM-yyyy") if fecha_q.isValid() else fecha
        entradas.append((orden if fecha_q.isValid() else _ORDEN_ULTIMO,
                         {"fecha": fecha_txt, "hora": hora_real, "alumno": alumno, "texto": nota,
                          "enlaces": []}))

    # sorted es estable: a igual fecha, la historia del caso queda antes que
    # las atenciones, que es el orden en que se cargaron.
    entradas.sort(key=lambda par: par[0])
    return [dato for _, dato in entradas]


# Iconos que usa el HTML de la ficha (<img src="ico:NOMBRE">): el documento que
# lo muestra los tiene que registrar antes (ver poner_html).
_ICONOS_FICHA = {"persona": tema.ACENTO, "reloj": tema.ACENTO, "libro": tema.ACENTO,
                 "calendario": tema.ACENTO}


def poner_html(editor, html_ficha):
    """Muestra la ficha en un QTextBrowser, con sus iconos y sus enlaces
    (la audiometría que trae el paciente se abre desde el historial)."""
    documento = editor.document()
    for nombre, color in _ICONOS_FICHA.items():
        documento.addResource(QTextDocument.ResourceType.ImageResource,
                              QUrl(f"ico:{nombre}"), iconos.pixmap(nombre, color, 18))
    if isinstance(editor, QTextBrowser) and not editor.property("enlaces_ficha"):
        # Sin esto el QTextBrowser "navega" al href y deja la ficha en blanco
        editor.setOpenLinks(False)
        editor.anchorClicked.connect(lambda url: abrir_enlace(url, editor))
        editor.setProperty("enlaces_ficha", True)
    editor.setHtml(html_ficha)


# Archivo de cada hoja -> el examen, para el título de su subventana
_EXAMEN_DE_ARCHIVO = {"audiometria": "Audiometría", "impedanciometria": "Impedanciometría", "eoa": "EOA",
                      "aabr": "AABR", "peatc": "PEATC", "ecochg": "ECochG", "vemp": "VEMP",
                      "corticales": "Corticales"}


def abrir_enlace(url, editor):
    """Un enlace de la ficha: "previo:<ficha>/<hoja>.svg" abre esa hoja en su
    subventana del MDI (main.abrir_previo)."""
    if url.scheme() != "previo":
        return
    ruta = PREVIOS_DIR / url.path()
    ventana = editor.window()
    if ruta.is_file() and hasattr(ventana, "abrir_previo"):
        examen = _EXAMEN_DE_ARCHIVO.get(ruta.stem.split("_")[-1], "Examen")
        ventana.abrir_previo(ruta, examen)


class HojaPrevia(QWidget):
    """El informe de un examen que el paciente trae hecho, como lo dibuja el
    libro. Vive en el MDI (self.subw["PREVIO"] en main.py) para tenerlo al
    lado mientras se examina; se dibuja al ancho de la subventana."""

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"HojaPrevia {{ background: white; }}")
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(8, 8, 8, 8)
        self.hoja = QLabel(self)
        self.hoja.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hoja.setMinimumSize(1, 1)
        raiz.addWidget(self.hoja, 1)
        self.ruta = None
        self._svg = None

    def set_hoja(self, ruta):
        self.ruta = Path(ruta)
        self._svg = QSvgRenderer(str(ruta))
        self._dibujar()

    def ficha(self):
        """Número de ficha de la hoja que se ve, o None."""
        return self.ruta.parent.name if self.ruta else None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._dibujar()

    def _dibujar(self):
        if self._svg is None or not self._svg.isValid():
            return
        tam = self._svg.defaultSize().scaled(self.hoja.size(), Qt.AspectRatioMode.KeepAspectRatio)
        if tam.isEmpty():
            return
        escala = self.devicePixelRatioF()
        pixmap = QPixmap(tam * escala)
        pixmap.setDevicePixelRatio(escala)
        pixmap.fill(Qt.GlobalColor.white)
        pintor = QPainter(pixmap)
        self._svg.render(pintor, QRectF(0, 0, tam.width(), tam.height()))
        pintor.end()
        self.hoja.setPixmap(pixmap)


def _etiqueta(texto):
    return (f'<span style="font-size:7.5pt; font-weight:600; color:{tema.TEXTO_TENUE}; '
            f'letter-spacing:1px;">{html.escape(texto.upper())}</span>')


def _dato(titulo, valor):
    """Un dato de la ficha: rótulo chico arriba, valor abajo."""
    valor = html.escape(str(valor)) if valor else f'<span style="color:{tema.TEXTO_TENUE};">—</span>'
    return (f'{_etiqueta(titulo)}<br>'
            f'<span style="font-size:10pt; font-weight:600; color:{tema.TEXTO};">{valor}</span>')


def _seccion(icono, titulo, cuerpo):
    """Un bloque de la ficha: título con icono y una tarjeta blanca."""
    return (
        '<table width="100%" cellspacing="0" cellpadding="0"><tr>'
        f'<td width="24"><img src="ico:{icono}" width="18" height="18"></td>'
        f'<td>{_etiqueta(titulo)}</td></tr></table>'
        '<table width="100%" cellspacing="0" cellpadding="12" '
        f'style="background-color:{tema.TARJETA}; border:1px solid {tema.BORDE};"><tr><td>'
        f'{cuerpo}</td></tr></table><p style="margin:0;">&nbsp;</p>')


def _enlaces(enlaces):
    """"Ver audiometría · Ver impedanciometría" al final de una entrada del
    historial que trae informes."""
    if not enlaces:
        return ""
    return " " + " · ".join(
        f'<a href="{html.escape(href)}" style="color:{tema.ACENTO}; font-weight:700;">{html.escape(texto)}</a>'
        for texto, href in enlaces)


def _pastilla(texto, color):
    return (f'<span style="color:{color}; font-weight:700;">&#9679; {html.escape(texto)}</span>')


def edad_de_rut(rut):
    """Edad en años del paciente a partir de su RUT (como lo hace el chat), o None."""
    from core.helpers import CreatePatient
    try:
        return CreatePatient().get_age_from_rut(int(rut))[0]
    except (TypeError, ValueError):
        return None


def render_ficha_html(row, caso, shedule, username, is_admin):
    """Arma el HTML de la ficha clínica para `row` (AgendaEntry) + `caso`
    (dict del caso clínico) -- datos del paciente, puntualidad de esta cita
    puntual y el historial de atenciones cerradas del paciente."""
    nombre = f"{row.nombre} {row.apellido}".strip()
    edad = edad_de_rut(row.rut) if row.rut else None
    nacimiento = row.fecha_nac + (f" ({edad} años)" if edad and row.fecha_nac else "")
    fecha_hora = f"{row.fecha} {row.hora}".strip()

    datos = (
        '<table width="100%" cellspacing="0" cellpadding="6">'
        f'<tr><td width="50%">{_dato("Nombre", nombre)}</td>'
        f'<td width="25%">{_dato("RUT", row.rut)}</td>'
        f'<td width="25%">{_dato("Nacimiento", nacimiento)}</td></tr>'
        f'<tr><td>{_dato("Procedimiento", row.procedimiento)}</td>'
        f'<td colspan="2">{_dato("Cita agendada", fecha_hora or "sin agendar")}</td></tr>'
        '</table>')
    partes = [_seccion("persona", "Datos del paciente", datos)]

    hora_real = obtener_hora_real_atencion(row, username)
    if hora_real:
        hora_agendada = QTime.fromString(row.hora, "HH:mm")
        hora_inicio = QTime.fromString(hora_real, "HH:mm:ss")
        if hora_agendada.isValid() and hora_inicio.isValid():
            minutos = hora_agendada.secsTo(hora_inicio) // 60
            resumen = (_pastilla("A tiempo", tema.OK) if minutos <= 0
                       else _pastilla(f"{minutos} min de atraso", tema.AVISO))
        else:
            resumen = ""
        puntualidad = (
            '<table width="100%" cellspacing="0" cellpadding="6"><tr>'
            f'<td width="30%">{_dato("Hora agendada", row.hora)}</td>'
            f'<td width="30%">{_dato("Inicio real", hora_real)}</td>'
            f'<td>{resumen}</td></tr></table>')
        partes.append(_seccion("reloj", "Puntualidad", puntualidad))

    # Una sola línea de tiempo: lo que le hicieron al paciente antes de
    # llegar (historia clínica del caso) y las atenciones cerradas, en orden.
    # La evolución que escribió el alumno tiene que quedar DESPUÉS de las
    # atenciones previas, que es como se lee una ficha de verdad.
    historia_clinica = caso.get("historia_clinica", "") if isinstance(caso, dict) else ""
    # Sin cita con fecha (un caso suelto, o la práctica libre abierta por el
    # docente) al paciente se lo ve hoy: "{{-30}}" es 30 días antes de hoy.
    # Antes quedaba la llave a la vista, con "sin fecha" al lado.
    fecha_base = (row.fecha if parse_fecha_agenda(row.fecha).isValid()
                  else QDate.currentDate().toString("dd-MM-yy"))
    trae = entrada_lo_que_trae(row, caso, historia_clinica)
    previos = [trae] if trae else []
    entradas = linea_tiempo(historia_clinica, fecha_base,
                            historial_atenciones(shedule, row.rut, username, is_admin,
                                                 getattr(row, "practice_id", None) is not None),
                            previos, enlaces_de_la_historia(row, caso))

    if entradas:
        # Escapado: son textos libres (historia del caso, nota del alumno) y
        # un "<" suelto rompía el resto de la ficha sin dejar rastro de por
        # qué -- una otoscopia que dice "conducto <2 mm", por ejemplo.
        # El alumno ve todas las entradas IGUAL: una ficha real no distingue
        # "lo que traía el paciente" de "lo que escribí yo", y marcarlo rompe
        # el realismo que la ficha aporta. El docente sí ve quién escribió
        # cada nota -- ahí la ficha es una herramienta de corrección, no el
        # registro que el alumno está aprendiendo a leer.
        filas = []
        for i, e in enumerate(entradas):
            fondo = tema.TARJETA if i % 2 == 0 else tema.TARJETA_ALT
            # Las entradas del caso no tienen hora: sin ella no se pone nada.
            hora = (f'<br><span style="font-size:8pt; color:{tema.TEXTO_TENUE};">'
                    f'{html.escape(e["hora"])}</span>') if e["hora"] else ""
            quien = (f'<span style="color:{tema.OI}; font-weight:600;">{html.escape(e["alumno"])}</span><br>'
                     if (is_admin and e["alumno"]) else "")
            filas.append(
                f'<tr><td width="90" valign="top" bgcolor="{fondo}" '
                f'style="border-top:1px solid {tema.GRILLA};">'
                f'<span style="font-weight:700; color:{tema.ACENTO};">'
                f'{html.escape(e["fecha"] or "sin fecha")}</span>{hora}</td>'
                f'<td valign="top" bgcolor="{fondo}" style="border-top:1px solid {tema.GRILLA};">'
                f'{quien}{html.escape(e["texto"] or "sin comentario")}{_enlaces(e["enlaces"])}</td></tr>')
        cuerpo = ('<table width="100%" cellspacing="0" cellpadding="8">' + "".join(filas) + "</table>")
    else:
        cuerpo = (f'<span style="color:{tema.TEXTO_SUAVE};">'
                  'Sin historial registrado para este paciente.</span>')
    partes.append(_seccion("libro", "Historial del paciente", cuerpo))

    return "".join(partes)
