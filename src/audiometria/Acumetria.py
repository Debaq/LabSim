# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.2 - Acumetria                    #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QPushButton, QRadioButton,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

# Mismas claves/valores que CaseBuilder::RINNE_LABELS / WEBER_LABELS en el
# backend PHP (labsim_backend/src/CaseBuilder.php) -- si se agrega una
# opción allá, agregarla acá también.
RINNE_LABELS = {
    'positivo': 'Positivo (CA > CO)',
    'negativo': 'Negativo (CO > CA)',
    'falso_negativo': 'Falso negativo (hipoacusia sensorioneural profunda, cruce óseo contralateral)',
}
WEBER_LABELS = {
    'centrado': 'Sin lateralización (centrado)',
    'od': 'Lateraliza a OD',
    'oi': 'Lateraliza a OI',
}
FREQS = (('500', '500 Hz'), ('1000', '1000 Hz'))


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
        self._rinne_probado = {'mastoides': False, 'conducto': False}

        layout = QVBoxLayout(self)
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

    # ---------------------------------------------------------- Rinne ----

    def _build_rinne_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        fila_freq = QHBoxLayout()
        fila_freq.addWidget(QLabel("Diapasón:"))
        self.rinne_500, self.rinne_1000 = QRadioButton("500 Hz"), QRadioButton("1000 Hz")
        self.rinne_500.setChecked(True)
        grupo_freq = QButtonGroup(tab)
        for rb in (self.rinne_500, self.rinne_1000):
            grupo_freq.addButton(rb)
            fila_freq.addWidget(rb)
        v.addLayout(fila_freq)

        fila_oido = QHBoxLayout()
        fila_oido.addWidget(QLabel("Oído:"))
        self.rinne_od, self.rinne_oi = QRadioButton("Derecho (OD)"), QRadioButton("Izquierdo (OI)")
        self.rinne_od.setChecked(True)
        grupo_oido = QButtonGroup(tab)
        for rb in (self.rinne_od, self.rinne_oi):
            grupo_oido.addButton(rb)
            fila_oido.addWidget(rb)
        v.addLayout(fila_oido)

        for rb in (self.rinne_500, self.rinne_1000, self.rinne_od, self.rinne_oi):
            rb.toggled.connect(lambda checked: checked and self._rinne_reset())

        fila_btn = QHBoxLayout()
        self.btn_mastoides = QPushButton("Apoyar en mastoides (vía ósea)")
        self.btn_conducto = QPushButton("Apoyar frente al conducto (vía aérea)")
        self.btn_mastoides.clicked.connect(self._rinne_probar_mastoides)
        self.btn_conducto.clicked.connect(self._rinne_probar_conducto)
        fila_btn.addWidget(self.btn_mastoides)
        fila_btn.addWidget(self.btn_conducto)
        v.addLayout(fila_btn)

        self.rinne_log = QTextEdit(tab)
        self.rinne_log.setReadOnly(True)
        v.addWidget(self.rinne_log)
        return tab

    def _rinne_seleccion(self):
        hz = '500' if self.rinne_500.isChecked() else '1000'
        lado = 'od' if self.rinne_od.isChecked() else 'oi'
        lado_label = 'derecho' if lado == 'od' else 'izquierdo'
        rinne = (self.data or {}).get('Rinne') or {}
        valor = (rinne.get(hz) or {}).get(lado, 'positivo')
        return hz, lado, lado_label, valor

    def _rinne_reset(self):
        self._rinne_probado = {'mastoides': False, 'conducto': False}
        self.rinne_log.clear()

    def _rinne_probar_mastoides(self):
        if not self.data:
            self.rinne_log.append("Paciente: (no hay un caso cargado)")
            return
        _, _, lado_label, _ = self._rinne_seleccion()
        self.rinne_log.append(f"Tú: apoyas el diapasón en la mastoides del oído {lado_label}.")
        self.rinne_log.append("Paciente: Sí, lo escucho.")
        self._rinne_probado['mastoides'] = True
        self._rinne_evaluar()

    def _rinne_probar_conducto(self):
        if not self.data:
            self.rinne_log.append("Paciente: (no hay un caso cargado)")
            return
        _, _, lado_label, valor = self._rinne_seleccion()
        self.rinne_log.append(f"Tú: apoyas el diapasón frente al conducto auditivo del oído {lado_label}.")
        if valor == 'positivo':
            self.rinne_log.append("Paciente: Sí, y aquí lo escucho más fuerte que en el hueso.")
        elif valor == 'negativo':
            self.rinne_log.append("Paciente: Lo escucho, pero más débil que en el hueso.")
        else:  # falso_negativo
            self.rinne_log.append("Paciente: No... por acá no escucho nada.")
        self._rinne_probado['conducto'] = True
        self._rinne_evaluar()

    def _rinne_evaluar(self):
        if not (self._rinne_probado['mastoides'] and self._rinne_probado['conducto']):
            return
        _, _, _, valor = self._rinne_seleccion()
        self.rinne_log.append(f"Interpretación: {RINNE_LABELS.get(valor, RINNE_LABELS['positivo'])}")

    # ---------------------------------------------------------- Weber ----

    def _build_weber_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        fila_freq = QHBoxLayout()
        fila_freq.addWidget(QLabel("Diapasón:"))
        self.weber_500, self.weber_1000 = QRadioButton("500 Hz"), QRadioButton("1000 Hz")
        self.weber_500.setChecked(True)
        grupo_freq = QButtonGroup(tab)
        for rb in (self.weber_500, self.weber_1000):
            grupo_freq.addButton(rb)
            fila_freq.addWidget(rb)
        v.addLayout(fila_freq)

        for rb in (self.weber_500, self.weber_1000):
            rb.toggled.connect(lambda checked: checked and self.weber_log.clear())

        self.btn_frente = QPushButton("Apoyar en la frente / vértex")
        self.btn_frente.clicked.connect(self._weber_probar)
        v.addWidget(self.btn_frente)

        self.weber_log = QTextEdit(tab)
        self.weber_log.setReadOnly(True)
        v.addWidget(self.weber_log)
        return tab

    def _weber_probar(self):
        if not self.data:
            self.weber_log.append("Paciente: (no hay un caso cargado)")
            return
        hz = '500' if self.weber_500.isChecked() else '1000'
        weber = (self.data or {}).get('Weber') or {}
        valor = weber.get(hz, 'centrado')
        self.weber_log.append("Tú: apoyas el diapasón en la frente / vértex.")
        if valor == 'od':
            self.weber_log.append("Paciente: Lo escucho más fuerte en el oído derecho.")
        elif valor == 'oi':
            self.weber_log.append("Paciente: Lo escucho más fuerte en el oído izquierdo.")
        else:
            self.weber_log.append("Paciente: Lo escucho igual en ambos oídos.")
