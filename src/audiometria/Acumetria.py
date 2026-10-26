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
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

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
    diapasón + posición (mastoides/conducto para Rinne, frente para Weber) y
    "pregunta" al paciente -- la respuesta sale del caso cargado
    (cases.data.Rinne/Weber, ver CaseBuilder.php). Sin esas claves (casos
    viejos) se responde como normal (Rinne positivo / Weber centrado)."""

    def __init__(self, thr=None):
        super().__init__()
        self.data = None
        self.appointment_id = None
        self._rinne_probado = {'mastoides': False, 'pabellon': False}

        tema.aplicar_estilo(self, EXTRA_QSS)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 12)
        tabs = QTabWidget(self)
        layout.addWidget(tabs)
        tabs.addTab(self._build_rinne_tab(), "Rinne")
        tabs.addTab(self._build_weber_tab(), "Weber")

        self.la_super(thr)

    def la_super(self, data, appointment_id=None):
        """Hidrata (o deshidrata, data=None) el módulo con el caso actual --
        mismo patrón que Audiometer.la_super()/ListWords.la_super(), llamado
        por MainWindow._hydrate_modules() cada vez que cambia el caso activo."""
        self.data = data
        self.appointment_id = appointment_id

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
        tab_ref = QWidget()  # dueño de los QButtonGroup

        v.addWidget(self._seccion("DIAPASÓN"))
        fila, (self.rinne_500, self.rinne_1000) = self._segmentado(
            tab_ref, (("500 Hz", "500"), ("1000 Hz", "1000")))
        v.addLayout(fila)

        v.addWidget(self._seccion("OÍDO"))
        fila, (self.rinne_od, self.rinne_oi) = self._segmentado(
            tab_ref, (("Derecho (OD)", "od"), ("Izquierdo (OI)", "oi")), lado=True)
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

        self.btn_comparar = self._paso("Preguntar dónde lo escucha más fuerte", "mensaje")
        self.btn_comparar.clicked.connect(self._rinne_comparar)
        v.addWidget(self.btn_comparar)
        v.addStretch(1)

        self.rinne_log = self._conversacion("Prueba mastoides y pabellón en un oído y luego compara.")
        tab = self._armar_tab(panel, "CONVERSACIÓN", self.rinne_log)
        tab_ref.setParent(tab)
        return tab

    def _rinne_seleccion(self):
        hz = '500' if self.rinne_500.isChecked() else '1000'
        lado = 'od' if self.rinne_od.isChecked() else 'oi'
        lado_label = 'derecho' if lado == 'od' else 'izquierdo'
        rinne = (self.data or {}).get('Rinne') or {}
        valor = (rinne.get(hz) or {}).get(lado, 'positivo')
        return hz, lado, lado_label, valor

    def _rinne_reset(self):
        self._rinne_probado = {'mastoides': False, 'pabellon': False}
        self.rinne_log.clear()

    def _rinne_probar_mastoides(self):
        if not self.data:
            self._decir(self.rinne_log, "Paciente: (no hay un caso cargado)")
            return
        _, _, lado_label, _ = self._rinne_seleccion()
        self._decir(self.rinne_log, f"Tú: apoyas el diapasón en la mastoides del oído {lado_label}.")
        self._decir(self.rinne_log, "Paciente: Sí, lo escucho.")
        self._rinne_probado['mastoides'] = True

    def _rinne_probar_pabellon(self):
        if not self.data:
            self._decir(self.rinne_log, "Paciente: (no hay un caso cargado)")
            return
        _, _, lado_label, valor = self._rinne_seleccion()
        self._decir(self.rinne_log, f"Tú: presentas el diapasón frente al pabellón auricular del oído {lado_label}.")
        if valor == 'positivo':
            self._decir(self.rinne_log, "Paciente: Sí, también lo escucho aquí.")
        elif valor == 'negativo':
            self._decir(self.rinne_log, "Paciente: Sí, lo escucho, pero se siente más débil.")
        else:  # falso_negativo
            self._decir(self.rinne_log, "Paciente: No... por acá no escucho nada.")
        self._rinne_probado['pabellon'] = True

    def _rinne_comparar(self):
        if not self.data:
            self._decir(self.rinne_log, "Paciente: (no hay un caso cargado)")
            return
        if not (self._rinne_probado['mastoides'] and self._rinne_probado['pabellon']):
            self._decir(self.rinne_log, "Tú: (primero hay que probar mastoides y pabellón en este oído/diapasón)")
            return
        _, _, _, valor = self._rinne_seleccion()
        self._decir(self.rinne_log, "Tú: ¿en cuál posición lo escuchas más fuerte?")
        if valor == 'positivo':
            self._decir(self.rinne_log, "Paciente: Frente al pabellón, y por más tiempo.")
        else:  # negativo y falso_negativo suenan igual para el paciente -- la trampa del falso negativo
            self._decir(self.rinne_log, "Paciente: En la mastoides.")
        # Sin "Interpretación: ..." acá -- si lo da positivo/negativo (o si
        # es un falso negativo) lo tiene que concluir el alumno con esta
        # respuesta, no leerlo hecho.

    # ---------------------------------------------------------- Weber ----

    def _build_weber_tab(self):
        panel, v = self._tarjeta()
        tab_ref = QWidget()

        v.addWidget(self._seccion("DIAPASÓN"))
        fila, (self.weber_500, self.weber_1000) = self._segmentado(
            tab_ref, (("500 Hz", "500"), ("1000 Hz", "1000")))
        v.addLayout(fila)

        v.addSpacing(6)
        v.addWidget(self._seccion("PRUEBA"))
        self.btn_frente = self._paso("Apoyar en la frente / vértex", "diapason")
        self.btn_frente.clicked.connect(self._weber_probar)
        v.addWidget(self.btn_frente)
        v.addStretch(1)

        self.weber_log = self._conversacion("Apoya el diapasón en la frente y observa dónde lo escucha.")
        for rb in (self.weber_500, self.weber_1000):
            rb.toggled.connect(lambda checked: checked and self.weber_log.clear())
        tab = self._armar_tab(panel, "CONVERSACIÓN", self.weber_log)
        tab_ref.setParent(tab)
        return tab

    def _weber_probar(self):
        if not self.data:
            self._decir(self.weber_log, "Paciente: (no hay un caso cargado)")
            return
        hz = '500' if self.weber_500.isChecked() else '1000'
        weber = (self.data or {}).get('Weber') or {}
        valor = weber.get(hz, 'centrado')
        self._decir(self.weber_log, "Tú: apoyas el diapasón en la frente / vértex.")
        if valor == 'od':
            self._decir(self.weber_log, "Paciente: Lo escucho más fuerte en el oído derecho.")
        elif valor == 'oi':
            self._decir(self.weber_log, "Paciente: Lo escucho más fuerte en el oído izquierdo.")
        else:
            self._decir(self.weber_log, "Paciente: Lo escucho igual en ambos oídos.")
