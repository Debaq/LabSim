# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.2 - Acumetria                    #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
import html

from core import iconos, tema
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QStackedLayout, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from audiometria import no_realizable
from audiometria.comandos_voz import SILENCIO
from audiometria.frases_habladas import FrasesHabladas
from backend.log_queue import get_log_queue

# Reglas propias de la ventana (el resto sale de core/tema.py): pestañas con
# subrayado, y los botones de oído con el color de su lado cuando están
# marcados.
EXTRA_QSS = f"""
QTabWidget::pane {{ border: none; background: transparent; top: 0px; }}
QTabBar::tab {{
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 7px 16px;
    margin-right: 4px;
    font-size: 9pt;
    font-weight: 600;
    color: {tema.TEXTO_TENUE};
}}
QTabBar::tab:selected {{ color: {tema.ACENTO}; border-bottom-color: {tema.ACENTO}; }}
QTabBar::tab:hover:!selected {{ color: {tema.TEXTO_SUAVE}; }}
QPushButton[lado="od"]:checked {{ background: {tema.OD_SUAVE}; border-color: {tema.OD}; color: {tema.OD}; }}
QPushButton[lado="oi"]:checked {{ background: {tema.OI_SUAVE}; border-color: {tema.OI}; color: {tema.OI}; }}
QPushButton[paso="true"] {{ text-align: left; padding: 8px 12px; }}
QTextEdit[conversacion="true"] {{ border: none; background: transparent; font-size: 10pt; }}
"""

# Lo que el evaluador le dice al paciente (audiometria/frases_habladas.py).
# Las claves son también el nombre del audio (resources/audio/comandos_ac/,
# scripts/voces_comandos.py --ac): no se cambian aunque cambie el rótulo.
GRUPOS = (
    ("PREPARAR", (
        ("Explicar el examen", "explicar_diapasones"),
    )),
    ("INSTRUCCIONES", (
        ("Avíseme si lo escucha", "avise_si_escucha"),
        ("Compare dónde suena más fuerte", "compare_sonidos"),
        ("Dígame dónde lo escucha", "diga_donde"),
    )),
    ("PREGUNTAS", (
        ("¿Lo escucha?", "lo_escucha"),
        ("¿Dónde lo escuchó más fuerte?", "donde_mas_fuerte"),
        ("¿Igual en los dos oídos?", "igual_ambos"),
    )),
)
PRUEBA = {"compare_sonidos": "Rinne", "diga_donde": "Weber", "igual_ambos": "Weber"}
INSTRUCCIONES = {"avise_si_escucha", "compare_sonidos", "diga_donde"}
# Para qué prueba sirve cada instrucción: con otra, el paciente no sabe qué
# hacer cuando siente el diapasón.
SIRVE_PARA = {"avise_si_escucha": {"rinne", "weber"}, "compare_sonidos": {"rinne"},
              "diga_donde": {"weber"}}
NO_SABE = "¿Y qué tengo que hacer?"
DONDE_WEBER = {"od": "En el oído derecho.", "oi": "En el oído izquierdo.",
               "centrado": "Al medio, en toda la cabeza."}

# Rinne no expone la etiqueta final (positivo/negativo/falso_negativo) --
# eso lo concluye el alumno con la respuesta del paciente a la comparación.
# Weber sí es directo: la lateralización que reporta el paciente ES el
# hallazgo del examen, no hay nada que inferir aparte.
WEBER_LABELS = {
    'centrado': 'Sin lateralización (centrado)',
    'od': 'Lateraliza a OD',
    'oi': 'Lateraliza a OI',
}


class Acumetria(QWidget):
    """Acumetría (Rinne/Weber, diapasones 500 y 1000 Hz): el alumno elige
    diapasón + posición (mastoides/pabellón para Rinne, frente para Weber)
    y le habla al paciente con el panel de frases (GRUPOS): instrucciones y
    preguntas, como en el audiómetro. El paciente contesta lo que le
    instruyeron o le preguntaron, con lo que dice el caso
    (cases.data.Rinne/Weber, ver CaseBuilder.php); sin instrucción no sabe
    qué hacer cuando siente el diapasón. Sin esas claves (casos viejos) se
    responde como normal (Rinne positivo / Weber centrado)."""

    def __init__(self, thr=None):
        super().__init__()
        self.data = None
        self.appointment_id = None
        self._rinne_probado = {'mastoides': False, 'pabellon': False}
        self._rinne_ultimo = None     # dónde está el diapasón ahora en el Rinne
        self._weber_puesto = False    # si ya se apoyó en la frente con este diapasón
        self._instruccion = None      # la instrucción vigente (INSTRUCCIONES)
        self.log_queue = get_log_queue()

        tema.aplicar_estilo(self, EXTRA_QSS)
        self.equipo = QWidget()
        layout = QHBoxLayout(self.equipo)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(12)
        # Lo que se le dice al paciente, a la izquierda como en el
        # audiómetro y el impedanciómetro
        self.frases = FrasesHabladas(GRUPOS, PRUEBA, "comandos_ac")
        self.frases.setFixedWidth(250)
        self.frases.btn_checked.connect(self._frase)
        layout.addWidget(self.frases)
        self.tabs = tabs = QTabWidget(self.equipo)
        layout.addWidget(tabs, 1)
        tabs.addTab(self._build_rinne_tab(), "Rinne")
        tabs.addTab(self._build_weber_tab(), "Weber")
        # Con un bebé, en lugar de los diapasones va el aviso
        self.aviso_bebe = no_realizable.AvisoNoRealizable("Acumetría no realizable")
        self.pila = QStackedLayout(self)
        self.pila.addWidget(self.equipo)
        self.pila.addWidget(self.aviso_bebe)

        self.la_super(thr)

    def la_super(self, data, appointment_id=None):
        """Hidrata (o deshidrata, data=None) el módulo con el caso actual --
        mismo patrón que Audiometer.la_super()/ListWords.la_super(), llamado
        por MainWindow._hydrate_modules() cada vez que cambia el caso activo."""
        self.data = data
        self.appointment_id = appointment_id
        # Paciente nuevo: no le han dicho nada todavía
        self._instruccion = None
        self.frases.callar()
        self.frases.silencio()
        self._rinne_reset()
        self.weber_log.clear()
        self._weber_puesto = False
        motivo = no_realizable.motivo(data, "acumetría")
        if motivo:
            self.aviso_bebe.texto.setText(motivo)
        self.pila.setCurrentWidget(self.aviso_bebe if motivo else self.equipo)

    def callar(self):
        self.frases.callar()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.frases.callar()

    def _log(self, action, **payload):
        """Encola una acción del alumno con los diapasones (prefijo ac_, ver
        backend/log_queue.py), igual que Audiometer._log/Z._log. El payload
        lleva la verdad del caso (resultado) para que el backend lea qué
        respondió el paciente sin recalcularlo."""
        case_id = self.data.get("id") if self.data else None
        if case_id is not None:
            payload.setdefault("case_id", case_id)
        payload.setdefault("appointment_id", self.appointment_id)
        payload.setdefault("con_paciente", case_id is not None)
        self.log_queue.push(action, payload)

    # ------------------------------------------------------ piezas comunes ----

    @staticmethod
    def _tarjeta():
        tarjeta = QFrame()
        tarjeta.setProperty("card", "true")
        col = QVBoxLayout(tarjeta)
        col.setContentsMargins(14, 12, 14, 14)
        col.setSpacing(8)
        return tarjeta, col

    @staticmethod
    def _seccion(texto):
        lbl = QLabel(texto)
        lbl.setProperty("role", "seccion")
        return lbl

    @staticmethod
    def _segmentado(tab, opciones, lado=False):
        """Botones marcables excluyentes (uno siempre marcado). Devuelve
        (fila, [botones]); el primero queda marcado. `lado`: pintan con el
        color de su oído al marcarse (OD rojo, OI azul)."""
        fila = QHBoxLayout()
        fila.setSpacing(6)
        # Dueño: la ventana (self). Antes era un QWidget suelto que después
        # se metía en la pestaña sin layout: Qt lo mostraba de 640x480 en la
        # esquina, encima del panel, y se tragaba todos los clics (los
        # diapasones no respondían, 2026-11-06).
        grupo = QButtonGroup(tab)
        botones = []
        for texto, clave in opciones:
            btn = QPushButton(texto)
            btn.setCheckable(True)
            if lado:
                btn.setProperty("lado", clave)
            grupo.addButton(btn)
            fila.addWidget(btn, 1)
            botones.append(btn)
        botones[0].setChecked(True)
        return fila, botones

    @staticmethod
    def _paso(texto, icono):
        btn = QPushButton(" " + texto)
        btn.setIcon(iconos.icono(icono, tema.ACENTO, 18))
        btn.setProperty("paso", "true")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    @staticmethod
    def _conversacion(placeholder):
        """Registro de lo dicho, para la tarjeta de la derecha."""
        log = QTextEdit()
        log.setReadOnly(True)
        log.setProperty("conversacion", "true")
        log.setPlaceholderText(placeholder)
        return log

    @staticmethod
    def _decir(log, texto):
        """Una línea del registro: "Tú:" y "Paciente:" con su color."""
        quien, sep, resto = texto.partition(": ")
        if sep and quien in ("Tú", "Paciente"):
            color = tema.ACENTO if quien == "Tú" else tema.TEXTO_SUAVE
            log.append(f'<p style="margin:0 0 6px 0"><b style="color:{color}">{quien}</b> '
                       f'<span style="color:{tema.TEXTO}">{html.escape(resto)}</span></p>')
        else:
            log.append(html.escape(texto))

    def _armar_tab(self, panel, titulo_log, log):
        """Panel de mandos a la izquierda (angosto) y registro a la derecha:
        sobra ancho, falta alto."""
        tab = QWidget()
        h = QHBoxLayout(tab)
        h.setContentsMargins(0, 10, 0, 0)
        h.setSpacing(10)
        panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        panel.setFixedWidth(330)
        h.addWidget(panel)
        derecha, col = self._tarjeta()
        col.addWidget(self._seccion(titulo_log))
        col.addWidget(log, 1)
        h.addWidget(derecha, 1)
        return tab

    # ---------------------------------------------------------- Rinne ----

    def _build_rinne_tab(self):
        panel, v = self._tarjeta()

        v.addWidget(self._seccion("DIAPASÓN"))
        fila, (self.rinne_500, self.rinne_1000) = self._segmentado(
            self, (("500 Hz", "500"), ("1000 Hz", "1000")))
        v.addLayout(fila)

        v.addWidget(self._seccion("OÍDO"))
        fila, (self.rinne_od, self.rinne_oi) = self._segmentado(
            self, (("Derecho (OD)", "od"), ("Izquierdo (OI)", "oi")), lado=True)
        v.addLayout(fila)

        for rb in (self.rinne_500, self.rinne_1000, self.rinne_od, self.rinne_oi):
            rb.toggled.connect(lambda checked: checked and self._rinne_reset())

        v.addSpacing(6)
        v.addWidget(self._seccion("PRUEBA"))
        self.btn_mastoides = self._paso("Apoyar en mastoides (vía ósea)", "oido")
        self.btn_pabellon = self._paso("Frente al pabellón (vía aérea)", "diapason")
        self.btn_mastoides.clicked.connect(self._rinne_probar_mastoides)
        self.btn_pabellon.clicked.connect(self._rinne_probar_pabellon)
        v.addWidget(self.btn_mastoides)
        v.addWidget(self.btn_pabellon)

        v.addStretch(1)

        self.rinne_log = self._conversacion("Lo que le digas al paciente y lo que él conteste.")
        tab = self._armar_tab(panel, "CONVERSACIÓN", self.rinne_log)
        return tab

    def _rinne_seleccion(self):
        hz = '500' if self.rinne_500.isChecked() else '1000'
        lado = 'od' if self.rinne_od.isChecked() else 'oi'
        lado_label = 'derecho' if lado == 'od' else 'izquierdo'
        rinne = (self.data or {}).get('Rinne') or {}
        valor = (rinne.get(hz) or {}).get(lado, 'positivo')
        return hz, lado, lado_label, valor

    def _rinne_reset(self):
        """Otro diapasón u otro oído: se empieza de nuevo (la instrucción
        dada sigue valiendo, el paciente no la olvida)."""
        self._rinne_probado = {'mastoides': False, 'pabellon': False}
        self._rinne_ultimo = None
        self.rinne_log.clear()

    def _rinne_comparacion(self, valor):
        """Lo que contesta al comparar las dos posiciones. Negativo y falso
        negativo suenan igual para el paciente: la trampa del falso
        negativo la descubre el alumno, no el paciente."""
        if valor == 'positivo':
            return "Adelante, frente a la oreja. Ahí suena más fuerte y dura más."
        return "Atrás, en el hueso. Ahí suena más fuerte."

    def _rinne_poner(self, donde):
        """Apoya el diapasón (mastoides) o lo pone frente al pabellón. El
        paciente contesta solo si le dijeron qué hacer."""
        if not self.data:
            self._decir(self.rinne_log, "Paciente: (no hay un caso cargado)")
            return
        hz, lado, lado_label, valor = self._rinne_seleccion()
        self._log(f"ac_rinne_{donde}", hz=hz, oido=lado, resultado=valor, instruccion=self._instruccion)
        if donde == 'mastoides':
            self._decir(self.rinne_log, f"Tú: apoyas el diapasón en la mastoides del oído {lado_label}.")
        else:
            self._decir(self.rinne_log, f"Tú: pones el diapasón frente al pabellón del oído {lado_label}.")
        self._rinne_probado[donde] = True
        self._rinne_ultimo = donde
        oye = donde == 'mastoides' or valor != 'falso_negativo'
        if self._instruccion not in SIRVE_PARA or 'rinne' not in SIRVE_PARA[self._instruccion]:
            self._decir(self.rinne_log, f"Paciente: {NO_SABE}")
        elif self._instruccion == 'avise_si_escucha':
            self._decir(self.rinne_log, "Paciente: Sí, lo escucho." if oye else "Paciente: No... no escucho nada.")
        elif self._rinne_probado['mastoides'] and self._rinne_probado['pabellon']:
            # compare_sonidos: con las dos posiciones, compara solo
            self._decir(self.rinne_log, f"Paciente: {self._rinne_comparacion(valor)}")
        else:
            self._decir(self.rinne_log, "Paciente: Ya." if oye else "Paciente: Mm... no escucho nada.")

    def _rinne_probar_mastoides(self):
        self._rinne_poner('mastoides')

    def _rinne_probar_pabellon(self):
        self._rinne_poner('pabellon')

    # ---------------------------------------------------------- Weber ----

    def _build_weber_tab(self):
        panel, v = self._tarjeta()

        v.addWidget(self._seccion("DIAPASÓN"))
        fila, (self.weber_500, self.weber_1000) = self._segmentado(
            self, (("500 Hz", "500"), ("1000 Hz", "1000")))
        v.addLayout(fila)

        v.addSpacing(6)
        v.addWidget(self._seccion("PRUEBA"))
        self.btn_frente = self._paso("Apoyar en la frente / vértex", "diapason")
        self.btn_frente.clicked.connect(self._weber_probar)
        v.addWidget(self.btn_frente)
        v.addStretch(1)

        self.weber_log = self._conversacion("Lo que le digas al paciente y lo que él conteste.")
        for rb in (self.weber_500, self.weber_1000):
            rb.toggled.connect(lambda checked: checked and self._weber_reset())
        tab = self._armar_tab(panel, "CONVERSACIÓN", self.weber_log)
        return tab

    def _weber_reset(self):
        self._weber_puesto = False
        self.weber_log.clear()

    def _weber_probar(self):
        if not self.data:
            self._decir(self.weber_log, "Paciente: (no hay un caso cargado)")
            return
        hz = '500' if self.weber_500.isChecked() else '1000'
        valor = ((self.data or {}).get('Weber') or {}).get(hz, 'centrado')
        self._log("ac_weber", hz=hz, resultado=valor, instruccion=self._instruccion)
        self._decir(self.weber_log, "Tú: apoyas el diapasón en la frente / vértex.")
        self._weber_puesto = True
        if self._instruccion not in SIRVE_PARA or 'weber' not in SIRVE_PARA[self._instruccion]:
            self._decir(self.weber_log, f"Paciente: {NO_SABE}")
        elif self._instruccion == 'diga_donde':
            self._decir(self.weber_log, f"Paciente: {DONDE_WEBER.get(valor, DONDE_WEBER['centrado'])}")
        else:
            self._decir(self.weber_log, "Paciente: Sí, lo escucho.")

    # --------------------------------------------- lo que se le dice ----

    def _prueba_actual(self):
        return "weber" if self.tabs.currentIndex() == 1 else "rinne"

    def _frase(self, clave):
        """Una frase del panel: se dice (FrasesHabladas), queda en la
        conversación de la prueba que está a la vista y el paciente la
        contesta. Una instrucción queda vigente hasta que se dé otra; una
        pregunta se contesta y no la reemplaza."""
        if clave == SILENCIO:
            return
        prueba = self._prueba_actual()
        log = self.weber_log if prueba == "weber" else self.rinne_log
        texto = next((t for _g, frases in GRUPOS for t, c in frases if c == clave), clave)
        self._decir(log, f"Tú: «{texto}»")
        if not self.data:
            self._decir(log, "Paciente: (no hay un caso cargado)")
            return
        if clave == "explicar_diapasones":
            respuesta = "Bueno, ya."
        elif clave in INSTRUCCIONES:
            self._instruccion = clave
            respuesta = "Ya, bueno."
        else:
            respuesta = self._contestar(clave, prueba)
        self._decir(log, f"Paciente: {respuesta}")
        tipo = "ac_pregunta" if clave not in INSTRUCCIONES and clave != "explicar_diapasones" else "ac_instruccion"
        extra = {}
        if prueba == "rinne":
            hz, lado, _l, valor = self._rinne_seleccion()
            extra = {"hz": hz, "oido": lado, "resultado": valor, "posicion": self._rinne_ultimo}
        else:
            hz = '500' if self.weber_500.isChecked() else '1000'
            extra = {"hz": hz, "resultado": ((self.data or {}).get('Weber') or {}).get(hz, 'centrado'),
                     "puesto": self._weber_puesto}
        self._log(tipo, clave=clave, prueba=prueba, respuesta=respuesta, **extra)

    def _contestar(self, clave, prueba):
        if prueba == "rinne":
            _hz, _lado, _l, valor = self._rinne_seleccion()
            if clave == "lo_escucha":
                if self._rinne_ultimo is None:
                    return "¿Qué cosa? No siento nada."
                oye = self._rinne_ultimo == 'mastoides' or valor != 'falso_negativo'
                return "Sí." if oye else "No, nada."
            if clave == "donde_mas_fuerte":
                if self._rinne_probado['mastoides'] and self._rinne_probado['pabellon']:
                    return self._rinne_comparacion(valor)
                if self._rinne_ultimo is None:
                    return "¿Qué cosa?"
                return "No sé... me lo puso en un solo lado."
            return "No sé, lo siento de este lado nomás."
        # Weber
        hz = '500' if self.weber_500.isChecked() else '1000'
        valor = ((self.data or {}).get('Weber') or {}).get(hz, 'centrado')
        if not self._weber_puesto:
            return "¿Qué cosa?"
        if clave == "lo_escucha":
            return "Sí."
        if clave == "igual_ambos":
            return {"od": "No, más en el derecho.", "oi": "No, más en el izquierdo."}.get(
                valor, "Sí, igual en los dos.")
        return DONDE_WEBER.get(valor, DONDE_WEBER["centrado"])
