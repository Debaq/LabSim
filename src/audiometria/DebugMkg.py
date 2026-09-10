# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                    VER. 0.1 - DebugMkg                        #
#                                                               #
#################################################################
"""Panel de depuración de enmascaramiento (solo admin/docente).

Muestra, en texto plano y en vivo:
  - los umbrales cargados del caso, en particular las tablas Aerea_mkg /
    Osea_mkg (las que usa el motor de respuestas, no las que dibuja el
    audiograma), y avisa cuando difieren de Aerea/Osea;
  - el estado actual del audiómetro (prueba, frecuencia, y por canal
    estímulo/oído/transductor/intensidad);
  - los rangos [mkg_min, mkg_max] de la vía aérea y ósea en la frecuencia
    actual, con el umbral real y el de curva sombra, y en qué zona cae el
    ruido que hay puesto ahora mismo;
  - la logoaudiometría completa: SDT del perfil vs el que calcula
    CalculateLogo, óseo de Fletcher, rango de mkg para la intensidad
    actual, el % de discriminación que devolvería el paciente simulado en
    este instante y la curva dB -> % de ambos oídos.

El reporte se arma en build_report(), que es una función pura sobre los
objetos del motor (sin Qt) para poder testearla.
"""

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (QCheckBox, QDialog, QHBoxLayout, QPlainTextEdit,
                               QPushButton, QVBoxLayout)

from core.helpers import Preferences
from core.ui_helpers import style_dialog

class_pref = Preferences()
output_list = class_pref.get("output_list")
stim_list = class_pref.get("stim_list")
trans_list = class_pref.get("trans_list")

# Las tablas de umbrales del caso traen 15 filas: las 9 frecuencias del
# audiograma clásico + las 6 de alta frecuencia (ver h_audio.threshold_basic
# y config_audiometer.json:frecuency_dict).
FRECUENCIAS = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000,
               9000, 10000, 11200, 12500, 14000, 16000]

SIN_CASO = "No hay un caso cargado en el audiómetro (nadie siendo atendido)."


def _fmt_par(par, suf=""):
    """[od, oi] -> 'OD 40 | OI 15'."""
    try:
        return f"OD {par[0]}{suf} | OI {par[1]}{suf}"
    except (TypeError, IndexError, KeyError):
        return f"?? ({par!r})"


def _fmt_umd(umd):
    """UMD es [{'int': dB, 'percentage': %}, ...] por oído."""
    try:
        return " | ".join(
            f"{'OD' if i == 0 else 'OI'} {o['percentage']}% @ {o['int']} dB"
            for i, o in enumerate(umd))
    except (TypeError, IndexError, KeyError):
        return f"?? ({umd!r})"


def _tabla_umbrales(case):
    """Tabla frecuencia x (Aerea, Aerea_mkg, Osea, Osea_mkg). La columna de
    la izquierda marca con ! las filas donde la tabla del motor (_mkg) no
    coincide con la que ve el alumno."""
    lineas = ["", "Umbrales cargados (dB HL) -- *_mkg son las tablas que usa el motor",
              "      Hz  " + "".join(f"{c:<14}" for c in
                                       ("Aerea", "Aerea_mkg", "Osea", "Osea_mkg")),
              "  ------  " + "------------- " * 4]
    aerea = case.get('Aerea') or []
    aerea_m = case.get('Aerea_mkg') or []
    osea = case.get('Osea') or []
    osea_m = case.get('Osea_mkg') or []
    difs = []
    for idx, hz in enumerate(FRECUENCIAS):
        if idx >= len(aerea_m) and idx >= len(osea_m):
            break

        def celda(tabla):
            if idx >= len(tabla):
                return f"{'-':<14}"
            return f"{f'{tabla[idx][0]}/{tabla[idx][1]}':<14}"

        dif = ((idx < len(aerea) and idx < len(aerea_m) and aerea[idx] != aerea_m[idx])
               or (idx < len(osea) and idx < len(osea_m) and osea[idx] != osea_m[idx]))
        if dif:
            difs.append(hz)
        lineas.append(f"{'!' if dif else ' '} {hz:>6}  {celda(aerea)}{celda(aerea_m)}"
                      f"{celda(osea)}{celda(osea_m)}")
    if difs:
        lineas.append(f"  ! Aerea/Osea != *_mkg en: {difs} Hz "
                      "(el paciente responde según *_mkg)")
    return lineas


def _bloque_caso(case):
    lineas = ["=== CASO ===",
              f"id: {case.get('id')}   sector: {case.get('sector')}   "
              f"género: {case.get('gender')}   edad: {case.get('edad')}"]
    if 'SDT' in case:
        lineas.append(f"SDT (perfil):      {_fmt_par(case['SDT'], ' dB')}")
    if 'SRT' in case:
        lineas.append(f"SRT (perfil):      {_fmt_par(case['SRT'], ' dB')}")
    if 'UMD' in case:
        lineas.append(f"UMD (máx. discr.): {_fmt_umd(case['UMD'])}")
    if 'recruit' in case:
        lineas.append(f"Reclutamiento:     {_fmt_par(case['recruit'])}")
    lineas.extend(_tabla_umbrales(case))
    return lineas


def _bloque_equipo(response, audio):
    freq_idx = audio['freq']
    try:
        hz = response.frecuency[freq_idx]
    except (IndexError, TypeError):
        hz = "?"
    lineas = ["", "=== EQUIPO (estado actual) ===",
              f"Prueba: {audio['test']}   Frecuencia: {hz} Hz (índice {freq_idx})"]
    for ch in (0, 1):
        stim = audio['stim'][ch]
        lineas.append(
            f"ch{ch}: {stim_list[stim] if stim < len(stim_list) else stim:<18}"
            f"{output_list[audio['output'][ch]]:<11}"
            f"{trans_list[audio['trans'][ch]]:<13}"
            f"{audio['int'][ch]:>4} dB HL   "
            f"{'ESTIMULANDO' if audio['stimOn'][ch] else 'en silencio'}   "
            f"{audio['contin'][ch]}")
    if response.history_command:
        lineas.append(f"Último comando de voz: {response.history_command[0]}")
    return lineas


def _zona(rango, int_mkg):
    if int_mkg < rango['mkg_min']:
        return "SUB-ENMASCARADO -> responde por curva sombra (cruce al otro oído)"
    if int_mkg > rango['mkg_max']:
        return "SOBRE-ENMASCARADO -> no responde (umbral 130)"
    return "DENTRO del rango -> responde con su umbral real"


def _bloque_tonal(response, audio):
    freq_idx = audio['freq']
    lineas = ["", "=== ENMASCARAMIENTO TONAL (frecuencia actual) ==="]
    for via in ('aerea', 'osea'):
        for o_e in (0, 1):
            o_n = int(not o_e)
            try:
                r = response._masking_calc(via, freq_idx, o_e, o_n)
            except (IndexError, KeyError, TypeError) as exc:
                lineas.append(f"{via} estudiando {'OD' if o_e == 0 else 'OI'}: "
                              f"no se pudo calcular ({exc})")
                continue
            at = response.attenuations[freq_idx] if via == 'aerea' else 0
            lineas.append(
                f"{via.upper():6} estudio {'OD' if o_e == 0 else 'OI'}, "
                f"enmascaro {'OI' if o_e == 0 else 'OD'}:  "
                f"rango {r['mkg_min']:g} .. {r['mkg_max']:g} dB   "
                f"(at={at}, real={r['real']:g}, sombra={r['shadow']:g})")

    # Qué está pasando ahora mismo, con el ruido que hay puesto
    stim = audio['stim']
    if audio['output'][0] != audio['output'][1] and 3 in stim:
        ch_tone = 0 if stim[0] == 0 else 1
        ch_mkg = int(not ch_tone)
        o_e = audio['output'][ch_tone]
        o_n = int(not o_e)
        via = 'osea' if audio['trans'][ch_tone] == 1 else 'aerea'
        int_mkg = audio['int'][ch_mkg]
        try:
            r = response._masking_calc(via, freq_idx, o_e, o_n)
            umbral = response._resolve_masked_threshold(via, freq_idx, o_e, o_n, int_mkg)
            lineas.append(
                f"AHORA: NBN {int_mkg} dB en {'OD' if o_n == 0 else 'OI'} "
                f"sobre {via} de {'OD' if o_e == 0 else 'OI'} -> {_zona(r, int_mkg)}")
            lineas.append(
                f"       umbral aparente {umbral:g} dB, tono en "
                f"{audio['int'][ch_tone]} dB -> "
                f"{'RESPONDE' if umbral <= audio['int'][ch_tone] else 'no responde'}")
        except (IndexError, KeyError, TypeError) as exc:
            lineas.append(f"AHORA: no se pudo calcular ({exc})")
    else:
        lineas.append("AHORA: no hay tono + NBN en oídos distintos (nada que enmascarar)")
    return lineas


def _bloque_logo(logo, case, audio, logo_state):
    lineas = ["", "=== LOGOAUDIOMETRÍA ==="]
    if logo is None:
        lineas.append("Listas de palabras sin caso cargado: no hay CalculateLogo.")
        return lineas
    lineas.append(f"SDT calculado por CalculateLogo (Fletcher aéreo): {_fmt_par(logo.sdt, ' dB')}")
    lineas.append(f"SDT del perfil (el que usa response.py):          "
                  f"{_fmt_par(case.get('SDT', ['-', '-']), ' dB')}")
    lineas.append(f"Óseo de Fletcher: {_fmt_par(logo._bone_sdt(), ' dB')}   "
                  f"atenuación logo: {logo.logo_attenuation} dB")

    # Estado que le llegó a ListWords desde el audiómetro
    playable, inten, side, with_mkg, int_mkg = (list(logo_state) + [None] * 5)[:5]
    lineas.append(f"Estado recibido en Listas: dictando={bool(playable)}  "
                  f"oído={'OD' if side == 0 else 'OI' if side == 1 else side}  "
                  f"habla={inten} dB  con_mkg={with_mkg}  ruido={int_mkg} dB")

    for side_i in (0, 1):
        nombre = 'OD' if side_i == 0 else 'OI'
        try:
            inten_calc = inten if (side_i == side and inten is not None) else 0
            r = logo._masking_range(side_i, int(not side_i), inten_calc)
        except (IndexError, KeyError, TypeError) as exc:
            lineas.append(f"{nombre}: no se pudo calcular el rango ({exc})")
            continue
        lineas.append(f"{nombre}: rango de mkg para habla a {inten_calc} dB: "
                      f"{r['mkg_min']:g} .. {r['mkg_max']:g} dB")

    if side in (0, 1) and inten is not None:
        try:
            r = logo._masking_range(side, int(not side), inten)
            usado = int_mkg if (with_mkg and int_mkg is not None) else 0
            pct = logo.get(side, with_mkg, inten, int_mkg)
            lineas.append(f"AHORA: ruido usado {usado} dB -> {_zona(r, usado)}")
            lineas.append(f"       discriminación que responde el paciente: {pct}% "
                          f"({int(pct / 4)} de 25 palabras)")
        except (KeyError, IndexError, TypeError) as exc:
            lineas.append(f"AHORA: no se pudo calcular el % ({exc})")

    escala = sorted(logo.data[0], key=int)
    lineas.append("")
    lineas.append("Curva de discriminación (dB HL -> %)")
    lineas.append("  dB " + "".join(f"{db:>5}" for db in escala))
    for side_i in (0, 1):
        nombre = 'OD' if side_i == 0 else 'OI'
        lineas.append(f"  {nombre} " + "".join(f"{logo.data[side_i][db]:>5}" for db in escala))
    return lineas


def build_report(response, logo=None, logo_state=(), case=None):
    """Arma el texto del panel. response = ResponseAudiometry del audiómetro,
    logo = CalculateLogo de las listas de palabras (o None), logo_state = el
    'playable' de ListWords ([dictando, dB, oído, con_mkg, dB ruido])."""
    case = case if case is not None else getattr(response, 'dbdata', None)
    if not case:
        return SIN_CASO
    audio = response.data['audio']
    lineas = _bloque_caso(case)
    lineas += _bloque_equipo(response, audio)
    lineas += _bloque_tonal(response, audio)
    lineas += _bloque_logo(logo, case, audio, logo_state)
    return "\n".join(lineas)


class DebugMkgDialog(QDialog):
    """Ventana no modal con el reporte. Se refresca a mano o cada segundo,
    para poder mover perillas del audiómetro y ver el efecto al toque."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Depuración de enmascaramiento (docente)")
        self.resize(900, 640)
        style_dialog(self)

        self.texto = QPlainTextEdit(self)
        self.texto.setReadOnly(True)
        self.texto.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        fuente = QFont("Monospace")
        fuente.setStyleHint(QFont.StyleHint.TypeWriter)
        fuente.setPointSize(9)
        self.texto.setFont(fuente)

        self.btn_refresh = QPushButton("Actualizar", self)
        self.btn_refresh.clicked.connect(self.refresh)
        self.chk_auto = QCheckBox("Auto (1 s)", self)
        self.chk_auto.setChecked(True)
        self.chk_auto.toggled.connect(self._toggle_auto)
        self.btn_copy = QPushButton("Copiar", self)
        self.btn_copy.clicked.connect(self._copiar)

        barra = QHBoxLayout()
        barra.addWidget(self.btn_refresh)
        barra.addWidget(self.chk_auto)
        barra.addWidget(self.btn_copy)
        barra.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(barra)
        layout.addWidget(self.texto)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def _toggle_auto(self, activo):
        self.timer.start() if activo else self.timer.stop()

    def _copiar(self):
        QGuiApplication.clipboard().setText(self.texto.toPlainText())

    def refresh(self):
        # Conservar el scroll: con auto-refresh, saltar al inicio cada
        # segundo haría inservible la tabla de umbrales.
        barra = self.texto.verticalScrollBar()
        pos = barra.value()
        self.texto.setPlainText(self._reporte())
        barra.setValue(min(pos, barra.maximum()))

    def _reporte(self):
        subw = getattr(self.main_window, 'subw', None) or {}
        aud = subw.get("A")
        if aud is None:
            return SIN_CASO
        listas = subw.get("W")
        logo = getattr(listas.obj, 'prev', None) if listas is not None else None
        estado = getattr(listas.obj, 'playable', ()) if listas is not None else ()
        try:
            return build_report(aud.obj.response, logo, estado,
                                self.main_window.data_current)
        except Exception as exc:  # panel de depuración: nunca voltear la app
            return f"No se pudo armar el reporte: {exc!r}"
