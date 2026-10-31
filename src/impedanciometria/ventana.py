"""
El impedanciómetro a pantalla completa, como el audiómetro: las
instrucciones al paciente a la izquierda, el equipo escalado al centro (ver
core/reparto.py) y la derecha libre por ahora; ahí irá la cabeza del
paciente para ponerle la sonda.
"""
from PySide6.QtWidgets import QVBoxLayout, QWidget

from audiometria.comandos_voz import SILENCIO
from core import tema
from core.reparto import Reparto
from impedanciometria.instrucciones import InstruccionesZ
from impedanciometria.Z import ZControl


class ImpedanciometriaWindow(QWidget):

    def __init__(self):
        super().__init__()
        tema.aplicar_estilo(self)
        self.z = ZControl()
        self.instrucciones = InstruccionesZ()
        self.equipo = Reparto(self.z)
        self.escalado = self.equipo.escalado
        self.col_izq, self.col_der = self.equipo.col_izq, self.equipo.col_der
        self.equipo.izq.addWidget(self.instrucciones)
        self.equipo.der.addStretch(1)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.addWidget(self.equipo)
        self.instrucciones.btn_checked.connect(self._instruccion)

    def la_super(self, data, appointment_id=None):
        self.instrucciones.callar()
        self.instrucciones.silencio()
        self.z.la_super(data, appointment_id)

    def _instruccion(self, clave):
        if clave != SILENCIO:
            self.z._log("z_instruccion", clave=clave, side=self.z.Z.get_side())

    def hideEvent(self, event):
        super().hideEvent(event)
        self.instrucciones.callar()
