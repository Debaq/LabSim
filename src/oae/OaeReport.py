"""Panel de informe EOA (hallazgos + conclusión + aviso de guardado).

Mismo patrón que AbrReport/VempReport: el alumno escribe la descripción y
la conclusión, y el PDF lo arma el backend (report_pdf.php) con las
capturas de los 4 tabs. Se guarda solo mientras se atiende, como todos
los módulos de examen (ver core/report_autosave.py): hasta 2026-10-08 había
un botón "Guardar informe" propio de EOA.
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.estado_informe import EstadoInforme


def _tarjeta():
    tarjeta = QFrame()
    tarjeta.setProperty("card", "true")
    col = QVBoxLayout(tarjeta)
    col.setContentsMargins(14, 10, 14, 12)
    col.setSpacing(6)
    return tarjeta, col


def _seccion(texto):
    lbl = QLabel(texto)
    lbl.setProperty("role", "seccion")
    return lbl


class OaeReport(QWidget):
    """Tab 'Informe' del módulo EOA."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.evaluador = ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 10, 0, 0)
        outer.setSpacing(10)

        # Cabecera: quién, cuándo y de qué atención, más lo capturado. El
        # alumno tiene que ver QUÉ se va a adjuntar (si olvidó capturar un
        # oído, acá se nota; en el PDF ya sería tarde).
        cab, col = _tarjeta()
        col.addWidget(_seccion("INFORME DE EMISIONES OTOACÚSTICAS"))
        datos = QHBoxLayout()
        datos.setSpacing(24)
        self.lbl_eva = QLabel("-")
        self.lbl_date = QLabel(datetime.now().strftime("%d/%m/%Y"))
        # El módulo recibe el caso (data['EOAS']), no la ficha del paciente:
        # se identifica la atención, que es lo que ata el informe al perfil.
        self.lbl_atencion = QLabel("Sin atención abierta")
        for titulo, valor in (("Evaluador/a", self.lbl_eva), ("Fecha", self.lbl_date),
                              ("Atención", self.lbl_atencion)):
            campo = QVBoxLayout()
            campo.setSpacing(0)
            t = QLabel(titulo)
            t.setProperty("role", "campo")
            valor.setProperty("role", "titulo")
            campo.addWidget(t)
            campo.addWidget(valor)
            datos.addLayout(campo)
        datos.addStretch(1)
        col.addLayout(datos)
        col.addWidget(_seccion("PRUEBAS CAPTURADAS (SE ADJUNTAN AL PDF)"))
        self.lbl_capturas = QLabel("--")
        self.lbl_capturas.setWordWrap(True)
        col.addWidget(self.lbl_capturas)
        outer.addWidget(cab)

        # Hallazgos y conclusión lado a lado: sobra ancho, falta alto.
        textos = QHBoxLayout()
        textos.setSpacing(10)
        tarjeta, col = _tarjeta()
        col.addWidget(_seccion("DESCRIPCIÓN DE LOS HALLAZGOS"))
        self.text_edit_1 = QTextEdit()
        self.text_edit_1.setPlaceholderText(
            "TEOAE / DPOAE por oído: bandas o frecuencias presentes y ausentes, "
            "SNR, reproducibilidad, piso de ruido, calidad del sello..."
        )
        col.addWidget(self.text_edit_1, 1)
        textos.addWidget(tarjeta, 1)
        tarjeta, col = _tarjeta()
        col.addWidget(_seccion("CONCLUSIÓN"))
        self.text_edit_2 = QTextEdit()
        self.text_edit_2.setPlaceholderText(
            "Interpretación clínica: función coclear por oído, correlación con "
            "el resto de la evaluación y sugerencias."
        )
        col.addWidget(self.text_edit_2, 1)
        textos.addWidget(tarjeta, 1)
        outer.addLayout(textos, 1)

        self.estado = EstadoInforme()
        outer.addWidget(self.estado)

    # ------------------------------------------------------------------
    def set_evaluador(self, text):
        self.evaluador = text or ""
        self.lbl_eva.setText(self.evaluador or "-")

    def set_atencion(self, appointment_id):
        self.lbl_atencion.setText(
            f"N° {appointment_id}" if appointment_id else "Sin atención abierta")

    def set_capturas(self, resumen):
        """`resumen`: lista de strings tipo 'TEOAE: OD, OI'."""
        self.lbl_capturas.setText(", ".join(resumen) if resumen
                                  else "Todavía no hay capturas.")

    def clear_texts(self):
        self.text_edit_1.clear()
        self.text_edit_2.clear()
        self.estado.limpiar()
