# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - Acumetria                    #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

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
ACUMETRIA_FREQS = ('500', '1000')


class Acumetria(QWidget):
    """Ventana simple de acumetría (Rinne/Weber, diapasones 500 y 1000 Hz).

    Interfaz mínima: el alumno pincha "Ver resultado" y se muestra lo que
    trae el caso (guardado desde la ficha admin, ver CaseBuilder.php). Un
    caso sin esas claves (creado antes de que existiera acumetría) se
    muestra como normal (Rinne positivo / Weber centrado) en vez de vacío.
    """

    def __init__(self, thr=None):
        super().__init__()
        self.data = None
        self.appointment_id = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Acumetría</b>"))
        layout.addWidget(QLabel("Diapasones 500 y 1000 Hz (Rinne / Weber)."))
        self.btn_resultado = QPushButton("Ver resultado")
        self.btn_resultado.clicked.connect(self.mostrar_resultado)
        layout.addWidget(self.btn_resultado)
        layout.addStretch()

        self.la_super(thr)

    def la_super(self, data, appointment_id=None):
        """Hidrata (o deshidrata, data=None) el módulo con el caso actual --
        mismo patrón que Audiometer.la_super()/ListWords.la_super(), llamado
        por MainWindow._hydrate_modules() cada vez que cambia el caso activo."""
        self.data = data
        self.appointment_id = appointment_id

    def _rinne(self, hz):
        rinne = (self.data or {}).get('Rinne') or {}
        lado = rinne.get(hz) or {}
        od = RINNE_LABELS.get(lado.get('od'), RINNE_LABELS['positivo'])
        oi = RINNE_LABELS.get(lado.get('oi'), RINNE_LABELS['positivo'])
        return od, oi

    def _weber(self, hz):
        weber = (self.data or {}).get('Weber') or {}
        return WEBER_LABELS.get(weber.get(hz), WEBER_LABELS['centrado'])

    def mostrar_resultado(self):
        if not self.data:
            QMessageBox.information(self, "Acumetría", "No hay un caso cargado.")
            return

        lineas = []
        for hz in ACUMETRIA_FREQS:
            od, oi = self._rinne(hz)
            lineas.append(f"{hz} Hz")
            lineas.append(f"  Rinne OD: {od}")
            lineas.append(f"  Rinne OI: {oi}")
            lineas.append(f"  Weber: {self._weber(hz)}")
        QMessageBox.information(self, "Resultado acumetría", "\n".join(lineas))
