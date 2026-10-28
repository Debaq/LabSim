"""
Mandos del audiómetro con la paleta de LabSim.

La ventana sale de UI/Ui_Audiometer.py (Designer). Esa forma se respeta en
lo que es del equipo --la pantalla blanca (`display`) con sus rótulos y
vúmetros no se toca, solo va en una tarjeta-- y acá se reacomodan los mismos widgets en tarjetas:
un canal a cada lado (salida, estímulo, transductor y su perilla) y al
centro frecuencia, pasos, cronómetro, logoaudiometría y monitor.

`rearmar(w)` corre justo después de setupUi y antes de conectar señales: los
QDial se cambian por la perilla de core/perilla.py y los widgets conservan
el nombre que usa Audiometer.py.

`marcar(w)` pinta qué está puesto en cada canal (el equipo real lo dice
con luces en las teclas): lo lee de los rótulos de la pantalla, que son el
estado del audiómetro.
"""
import shiboken6
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy,
                               QVBoxLayout)

from core import tema
from core.perilla import Perilla

QWIDGETSIZE_MAX = (1 << 24) - 1

EXTRA_QSS = f"""
QPushButton {{ padding: 4px 6px; }}
QPushButton[activo="true"] {{
    background: {tema.ACENTO_SUAVE};
    border-color: {tema.ACENTO};
    color: {tema.ACENTO};
    font-weight: 600;
}}
QPushButton[activo="od"] {{ background: {tema.OD_SUAVE}; border-color: {tema.OD}; color: {tema.OD}; font-weight: 600; }}
QPushButton[activo="oi"] {{ background: {tema.OI_SUAVE}; border-color: {tema.OI}; color: {tema.OI}; font-weight: 600; }}
QFrame#centro QPushButton {{ padding: 4px 1px; }}
QPushButton[ruido="true"] {{ padding: 3px 0px; font-size: 8pt; }}
QPushButton[primario="true"] {{
    background: {tema.ACENTO};
    border-color: {tema.ACENTO};
    color: white;
    font-weight: 600;
    padding: 7px 6px;
}}
QPushButton[primario="true"]:hover {{ background: {tema.ACENTO_CLARO}; color: white; }}
QPushButton[primario="true"]:pressed {{ background: {tema.ACENTO}; }}
QLabel[role="campo"] {{ qproperty-alignment: AlignCenter; }}
"""


def _seccion(texto, alinear=Qt.AlignmentFlag.AlignLeft):
    lbl = QLabel(texto)
    lbl.setProperty("role", "seccion")
    lbl.setAlignment(alinear)
    return lbl


def _tarjeta(titulo=None):
    tarjeta = QFrame()
    tarjeta.setProperty("card", "true")
    col = QVBoxLayout(tarjeta)
    col.setContentsMargins(8, 8, 8, 10)
    col.setSpacing(5)
    if titulo:
        col.addWidget(_seccion(titulo))
    return tarjeta, col


def _perilla(w, nombre):
    """Cambia el QDial de Designer por una Perilla con los mismos valores."""
    viejo = getattr(w, nombre)
    nuevo = Perilla(w)
    nuevo.setObjectName(nombre)
    nuevo.setRange(viejo.minimum(), viejo.maximum())
    nuevo.setSingleStep(viejo.singleStep())
    nuevo.setPageStep(viejo.pageStep())
    nuevo.setWrapping(viejo.wrapping())
    nuevo.setTracking(viejo.hasTracking())
    nuevo.setValue(viejo.value())
    nuevo.setEnabled(viejo.isEnabled())
    nuevo.setFixedSize(viejo.maximumSize().boundedTo(QSize(110, 110)))
    viejo.hide()
    viejo.deleteLater()
    setattr(w, nombre, nuevo)
    return nuevo


def _columna(titulo, botones, ruidos=None):
    col = QVBoxLayout()
    col.setSpacing(4)
    col.addWidget(_seccion(titulo, Qt.AlignmentFlag.AlignCenter))
    for b in botones:
        b.setMaximumHeight(QWIDGETSIZE_MAX)
        col.addWidget(b)
    if ruidos:
        grilla = QGridLayout()
        grilla.setSpacing(4)
        for i, b in enumerate(ruidos):
            b.setProperty("ruido", "true")
            b.setMinimumWidth(0)
            b.setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
            b.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            grilla.addWidget(b, i // 2, i % 2)
        col.addLayout(grilla)
    col.addStretch(1)
    return col


def _canal(w, ch):
    """Una tarjeta por canal: selectores arriba, perilla y teclas abajo.
    El canal 2 va en espejo, como en el equipo."""
    s = f"_ch{ch}"
    tarjeta, col = _tarjeta(f"CANAL {ch + 1}")
    selectores = QHBoxLayout()
    selectores.setSpacing(4)
    columnas = [
        _columna("SALIDA", [getattr(w, f"btn_output_{x}{s}") for x in ("der", "izq", "sim")]),
        _columna("ESTÍMULO", [getattr(w, f"btn_stim_{x}{s}") for x in ("tone", "fm", "speech")],
                 [getattr(w, f"btn_stim_{x}{s}") for x in ("wn", "nbn", "pn", "sn")]),
        _columna("TRANSDUCTOR", [getattr(w, f"btn_trans_{x}{s}") for x in ("aer", "ose", "cl")]),
    ]
    for c in (columnas if ch == 0 else columnas[::-1]):
        selectores.addLayout(c, 1)
    col.addLayout(selectores)

    linea = QFrame()
    linea.setFixedHeight(1)
    linea.setStyleSheet(f"background: {tema.BORDE};")
    col.addWidget(linea)

    abajo = QHBoxLayout()
    abajo.setSpacing(10)
    dial = _perilla(w, "dial_ch0" if ch == 0 else "dial_izq")
    dial.setFixedSize(QSize(96, 96))
    teclas = QVBoxLayout()
    teclas.setSpacing(5)
    estimulo = getattr(w, f"btn_stim{s}")
    estimulo.setProperty("primario", "true")
    for b in (getattr(w, f"btn_puls{s}"), getattr(w, f"btn_rever{s}"), estimulo):
        b.setMaximumHeight(QWIDGETSIZE_MAX)
        teclas.addWidget(b)
    if ch == 0:
        abajo.addWidget(dial)
        abajo.addLayout(teclas, 1)
    else:
        abajo.addLayout(teclas, 1)
        abajo.addWidget(dial)
    col.addLayout(abajo)
    return tarjeta


def _fila(*widgets):
    fila = QHBoxLayout()
    fila.setSpacing(4)
    for wd in widgets:
        wd.setMaximumHeight(QWIDGETSIZE_MAX)
        fila.addWidget(wd, 1)
    return fila


def _centro(w):
    tarjeta, col = _tarjeta()
    col.addWidget(_seccion("FRECUENCIA"))
    w.btn_freq_minus.setText("‹")
    w.btn_freq_plus.setText("›")
    col.addLayout(_fila(w.btn_freq_minus, w.btn_alt_frec, w.btn_freq_plus))
    col.addWidget(_seccion("PASOS"))
    col.addLayout(_fila(w.btn_step_1, w.btn_step_3, w.btn_step_5, w.btn_ext_range))
    w.btn_ext_range.setText("Ext.")
    w.btn_ext_range.setToolTip("Extender rango")
    col.addWidget(_seccion("TIEMPO"))
    col.addLayout(_fila(w.btn_time_start, w.btn_time_stop, w.btn_time_clear))
    col.addWidget(_seccion("LOGOAUDIOMETRÍA"))
    col.addLayout(_fila(w.btn_correcta, w.btn_borrar, w.btn_incorrecta))
    col.addSpacing(4)
    col.addLayout(_fila(w.btn_talkback, w.btn_alternado))
    col.addStretch(1)

    # Monitor de cada canal y talkback: perillas chicas al pie.
    pie = QGridLayout()
    pie.setHorizontalSpacing(6)
    pie.setVerticalSpacing(0)
    for i, (nombre, rotulo) in enumerate((("dial_monitor_ch1", "Monitor 1"),
                                          ("dial_monitor_ch2", "Monitor 2"),
                                          ("dial_talkback", "Talkback"))):
        dial = _perilla(w, nombre)
        dial.setFixedSize(QSize(42, 42))
        lbl = QLabel(rotulo)
        lbl.setProperty("role", "campo")
        pie.addWidget(dial, 0, i, Qt.AlignmentFlag.AlignHCenter)
        pie.addWidget(lbl, 1, i)
    col.addLayout(pie)
    return tarjeta


def rearmar(w):
    tema.aplicar_estilo(w, EXTRA_QSS)
    # Designer lo dejaba fijo en 740-830 x 500-504: ahora crece con la ventana.
    w.setMinimumSize(0, 0)
    w.setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)

    # Fuera el layout de Designer (los widgets quedan, son hijos de w) y
    # los separadores y rótulos que ahora dan las tarjetas.
    shiboken6.delete(w.layout())
    for nombre in ("line", "line_2", "line_3", "line_4", "line_5", "line_8", "line_11", "line_12",
                   "label", "label_2", "label_3", "label_4", "label_5",
                   "label_10", "label_11", "label_12", "label_13", "label_14", "label_15"):
        viejo = getattr(w, nombre, None)
        if viejo is not None:
            viejo.hide()
            viejo.deleteLater()

    raiz = QVBoxLayout(w)
    raiz.setContentsMargins(12, 8, 12, 10)
    raiz.setSpacing(8)

    # La pantalla del equipo, en una tarjeta: el borde lo da la tarjeta.
    w.display.setFrameShape(QFrame.Shape.NoFrame)
    pantalla, caja = _tarjeta()
    caja.setContentsMargins(6, 6, 6, 6)
    caja.addWidget(w.display)
    raiz.addWidget(pantalla)

    mandos = QHBoxLayout()
    mandos.setSpacing(8)
    mandos.addWidget(_canal(w, 0), 1)
    centro = _centro(w)
    centro.setObjectName("centro")
    centro.setFixedWidth(178)
    mandos.addWidget(centro)
    mandos.addWidget(_canal(w, 1), 1)
    raiz.addLayout(mandos, 1)

    # El marco de Alta frec./Pasos/Ext. Rango quedó vacío: sus botones ya
    # están en la tarjeta del centro.
    w.verticalFrame2.hide()
    w.verticalFrame2.deleteLater()


def marcar(w, output_list, stim_list, trans_list, tone_list, reverse_list):
    """Marca en cada canal la salida, el estímulo, el transductor, pulsado
    e invertido que muestra la pantalla."""
    for ch in (0, 1):
        salida = w.lbl_output[ch].text()
        for i, b in enumerate(w.output_btns[ch]):
            b.setProperty("activo", ("od", "oi", "true")[i] if output_list[i] == salida else "")
        for btns, lbl, opciones in ((w.stim_btns[ch], w.lbl_stim[ch], stim_list),
                                    (w.trans_btns[ch], w.lbl_trans[ch], trans_list)):
            for b, op in zip(btns, opciones):
                b.setProperty("activo", "true" if op == lbl.text() else "")
        getattr(w, f"btn_puls_ch{ch}").setProperty(
            "activo", "true" if w.lbl_contin[ch].text() == tone_list[1] else "")
        getattr(w, f"btn_rever_ch{ch}").setProperty(
            "activo", "true" if w.lbl_revers[ch].text() == reverse_list[1] else "")
    w.btn_alternado.setProperty("activo", "true" if w.lbl_contin[0].text() == tone_list[2] else "")
    for b in (*w.output_btns[0], *w.output_btns[1], *w.stim_btns[0], *w.stim_btns[1],
              *w.trans_btns[0], *w.trans_btns[1], w.btn_puls_ch0, w.btn_puls_ch1,
              w.btn_rever_ch0, w.btn_rever_ch1, w.btn_alternado):
        tema.repintar(b)
